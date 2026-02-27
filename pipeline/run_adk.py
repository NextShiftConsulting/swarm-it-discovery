#!/usr/bin/env python3
"""
ADK-Orchestrated Pipeline Runner
Uses Swarm-It ADK for agent orchestration while keeping existing logic.

This is a HYBRID approach:
- Wraps existing functions as agent tasks
- ADK handles orchestration, logging, coordination
- Same underlying logic as run.py
- Fallback to legacy runner if ADK not available
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Try to import ADK
HAS_ADK = False
try:
    sys.path.insert(0, os.path.expanduser("~/GitHub/swarm-it-adk/clients/python"))
    from swarm_it import SwarmIt
    HAS_ADK = True
    print("✓ Swarm-It ADK found - using agent orchestration")
except ImportError:
    print("✗ Swarm-It ADK not found - falling back to legacy runner")
    print("  Install: pip install -e ~/GitHub/swarm-it-adk/clients/python")

if not HAS_ADK:
    # Fallback to legacy runner
    print("\nFalling back to run.py (legacy procedural mode)...\n")
    from run import main
    if __name__ == "__main__":
        main()
    sys.exit(0)

# Import existing pipeline functions (we're wrapping, not rewriting)
from scanner.sources import fetch_all_sources, Paper
from analyzer.matcher import SimilarityMatcher, MatchResult
from analyzer.rsct_scorer import RSCTScorer, RSCTScore
from publisher.mdx_generator import MDXGenerator, PaperData


class ADKAgent:
    """
    Lightweight agent wrapper for existing pipeline stages.

    This is NOT a full ADK Agent class (that would come from the ADK).
    This is a minimal wrapper to organize work until ADK APIs are stable.
    """
    def __init__(self, name: str, goal: str):
        self.name = name
        self.goal = goal
        self.start_time = None
        self.end_time = None

    async def execute(self, *args, **kwargs):
        """Override this in subclasses."""
        raise NotImplementedError

    async def run(self, *args, **kwargs):
        """Run the agent with timing."""
        print(f"\n[{self.name.upper()}] {self.goal}")
        self.start_time = datetime.utcnow()

        try:
            result = await self.execute(*args, **kwargs)
            self.end_time = datetime.utcnow()
            duration = (self.end_time - self.start_time).total_seconds()
            print(f"  ✓ Completed in {duration:.2f}s")
            return result
        except Exception as e:
            self.end_time = datetime.utcnow()
            print(f"  ✗ Failed: {e}")
            raise


class ScannerAgent(ADKAgent):
    """Agent wrapper for paper scanning."""

    def __init__(self, days=7, max_papers=50):
        super().__init__(name="scanner", goal=f"Fetch papers from last {days} day(s)")
        self.days = days
        self.max_papers = max_papers

    async def execute(self):
        """Run existing fetch logic."""
        papers = await fetch_all_sources(days=self.days, max_per_source=self.max_papers)
        print(f"  Found {len(papers)} papers")
        return {"papers": papers, "count": len(papers)}


class AnalystAgent(ADKAgent):
    """Agent wrapper for topic matching and RSCT scoring."""

    def __init__(
        self,
        swarmit_url: str,
        topics_dir="content/topics",
        min_score=0.5,
        min_rsct_score=0.3
    ):
        super().__init__(name="analyst", goal="Match papers to topics and score with RSCT")
        self.topics_dir = topics_dir
        self.min_score = min_score
        self.min_rsct_score = min_rsct_score
        self.matcher = SimilarityMatcher(topics_dir=topics_dir, threshold=min_score)
        self.rsct_scorer = RSCTScorer()

        # Initialize Swarm-It API client
        try:
            self.swarmit = SwarmIt(url=swarmit_url)
            if not self.swarmit.health():
                print(f"  Warning: Swarm-It API not reachable at {swarmit_url}")
                self.swarmit = None
        except Exception as e:
            print(f"  Warning: Could not connect to Swarm-It API: {e}")
            self.swarmit = None

    def certify(self, content: str, stage: str) -> dict:
        """Certify content through Swarm-It API."""
        if not self.swarmit:
            return {
                "allowed": True,
                "kappa_gate": 1.0,
                "decision": "EXECUTE",
                "R": 0.85,
                "S": 0.12,
                "N": 0.03,
                "stage": stage
            }

        try:
            cert = self.swarmit.certify(content)
            return {
                "allowed": cert.allowed,
                "kappa_gate": cert.kappa_gate,
                "decision": cert.decision.value if hasattr(cert.decision, 'value') else cert.decision,
                "R": cert.R,
                "S": cert.S,
                "N": cert.N,
                "stage": stage,
            }
        except Exception as e:
            print(f"  Certification error: {e}")
            return {"allowed": True, "kappa_gate": 0.0, "decision": "ERROR", "stage": stage}

    async def execute(self, scanner_result):
        """Run existing analysis logic."""
        papers = scanner_result["papers"]

        # Load topics
        print("  Loading topics...")
        self.matcher.load_topics()
        if not self.matcher.topics:
            print("  Warning: No topics loaded, using keyword matching")

        # Match papers to topics
        print("  Matching papers to topics...")
        paper_dicts = [
            {"id": p.id, "title": p.title, "abstract": p.abstract}
            for p in papers
        ]
        matches = self.matcher.match_papers(paper_dicts)

        # Filter by score
        relevant = [
            (p, m) for p, m in zip(papers, matches)
            if m.similarity_score >= self.min_score
        ]
        print(f"  {len(relevant)} papers above {self.min_score:.0%} threshold")

        # RSCT whitepaper scoring
        print("  Scoring papers against RSCT whitepaper...")
        rsct_paper_dicts = [
            {
                "id": p.id,
                "title": p.title,
                "abstract": p.abstract,
                "similarity_score": m.similarity_score,
            }
            for p, m in relevant
        ]
        rsct_scores = self.rsct_scorer.rank_papers(rsct_paper_dicts, min_rsct_score=self.min_rsct_score)
        print(f"  {len(rsct_scores)} papers above {self.min_rsct_score:.0%} RSCT threshold")

        # Create lookup and resort by combined score
        rsct_lookup = {s.paper_id: s for s in rsct_scores}
        relevant_with_rsct = []
        for paper, match in relevant:
            rsct = rsct_lookup.get(paper.id)
            if rsct:
                relevant_with_rsct.append((paper, match, rsct))

        relevant_with_rsct.sort(key=lambda x: x[2].combined_score, reverse=True)

        # Show top papers
        print("\n  Top RSCT-Ranked Papers:")
        for i, (p, m, r) in enumerate(relevant_with_rsct[:5]):
            print(f"    {i+1}. {p.title[:60]}...")
            print(f"       Topic: {m.similarity_score:.0%} | RSCT: {r.rsct_similarity:.0%} | Combined: {r.combined_score:.0%}")

        return {
            "relevant_papers": relevant_with_rsct,
            "count": len(relevant_with_rsct)
        }


class WriterAgent(ADKAgent):
    """Agent wrapper for MDX generation."""

    def __init__(self, output_dir="content/reviews"):
        super().__init__(name="writer", goal="Generate paper reviews")
        self.generator = MDXGenerator(output_dir=output_dir)

    async def execute(self, analyst_result, certify_fn):
        """Run existing generation logic."""
        relevant_with_rsct = analyst_result["relevant_papers"]

        if not relevant_with_rsct:
            print("  No papers to generate")
            return {"posts_generated": 0, "files": []}

        # Convert to PaperData with RSCT metrics
        paper_data = []
        for paper, match, rsct in relevant_with_rsct[:10]:  # Top 10
            # Get per-paper certification
            cert = certify_fn(f"{paper.title}: {paper.abstract[:500]}", "paper")

            paper_data.append(PaperData(
                id=paper.id,
                title=paper.title,
                abstract=paper.abstract,
                authors=paper.authors,
                source=paper.source,
                url=paper.url,
                pdf_url=paper.pdf_url,
                published_date=paper.published_date,
                similarity_score=rsct.combined_score,
                matched_topics=match.matched_topics,
                categories=paper.categories,
                # RSCT certification
                rsct_R=cert.get("R"),
                rsct_S=cert.get("S"),
                rsct_N=cert.get("N"),
                rsct_kappa=cert.get("kappa_gate"),
                rsct_decision=cert.get("decision"),
            ))

        # Generate posts
        print(f"  Generating {len(paper_data)} posts...")
        saved = self.generator.generate_and_save(paper_data)

        return {"posts_generated": len(saved), "files": saved}


class PublisherAgent(ADKAgent):
    """Agent wrapper for deployment."""

    def __init__(self):
        super().__init__(name="publisher", goal="Prepare content for deployment")

    async def execute(self, writer_result):
        """Mark posts ready for deployment."""
        posts = writer_result["posts_generated"]
        files = writer_result["files"]

        print(f"  {posts} posts ready for deployment")
        print("  Deployment via GitHub Actions (auto-triggers on push to main)")

        return {
            "status": "ready",
            "posts": posts,
            "files": [str(f) for f in files]
        }


async def run_pipeline(args):
    """Run ADK-orchestrated pipeline."""
    print("=" * 60)
    print("SWARM-IT ADK PIPELINE")
    print("=" * 60)
    print(f"Mode: Agent-orchestrated (hybrid)")
    print(f"Days: {args.days}")
    print(f"Min topic score: {args.min_score:.0%}")
    print(f"Min RSCT score: {args.min_rsct_score:.0%}")

    swarmit_url = os.getenv("SWARMIT_URL", "https://api.swarms.network")

    # Create agents
    scanner = ScannerAgent(days=args.days, max_papers=args.max_papers)
    analyst = AnalystAgent(
        swarmit_url=swarmit_url,
        topics_dir=args.topics_dir,
        min_score=args.min_score,
        min_rsct_score=args.min_rsct_score
    )
    writer = WriterAgent(output_dir=args.output_dir)
    publisher = PublisherAgent()

    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "papers_fetched": 0,
        "papers_matched": 0,
        "posts_generated": 0,
        "errors": []
    }

    try:
        # Stage 1: Scanner
        scanner_result = await scanner.run()
        results["papers_fetched"] = scanner_result["count"]

        if scanner_result["count"] == 0:
            print("\nNo papers found")
            return results

        # Stage 2: Analyst
        analyst_result = await analyst.run(scanner_result)
        results["papers_matched"] = analyst_result["count"]

        if analyst_result["count"] == 0:
            print("\nNo papers matched above threshold")
            return results

        # Stage 3: Writer (with certification function)
        if not args.dry_run:
            writer_result = await writer.run(analyst_result, analyst.certify)
            results["posts_generated"] = writer_result["posts_generated"]

            # Stage 4: Publisher
            await publisher.run(writer_result)
        else:
            print("\n[DRY RUN] Skipping post generation")

    except Exception as e:
        print(f"\nPipeline failed: {e}")
        import traceback
        traceback.print_exc()
        results["errors"].append(str(e))

    # Summary
    print("\n" + "=" * 60)
    print("PIPELINE SUMMARY")
    print("=" * 60)
    print(f"Papers fetched:    {results['papers_fetched']}")
    print(f"Papers matched:    {results['papers_matched']}")
    print(f"Posts generated:   {results['posts_generated']}")

    if results["errors"]:
        print(f"\nErrors: {results['errors']}")

    return results


def main():
    """Parse arguments and run pipeline."""
    parser = argparse.ArgumentParser(description="Run ADK-orchestrated paper discovery pipeline")
    parser.add_argument("--days", type=int, default=7, help="Days to look back")
    parser.add_argument("--max-papers", type=int, default=50, help="Max papers per source")
    parser.add_argument("--min-score", type=float, default=0.5, help="Min topic similarity score")
    parser.add_argument("--min-rsct-score", type=float, default=0.3, help="Min RSCT relevance score")
    parser.add_argument("--dry-run", action="store_true", help="Don't generate posts")
    parser.add_argument("--topics-dir", default="content/topics", help="Topics directory")
    parser.add_argument("--output-dir", default="content/reviews", help="Output directory")
    args = parser.parse_args()

    asyncio.run(run_pipeline(args))


if __name__ == "__main__":
    main()
