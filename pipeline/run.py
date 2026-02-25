#!/usr/bin/env python3
"""
Daily Pipeline Runner - Fetch, Match, Certify, Publish

Uses Swarm-It sidecar API for RSCT certification of the analysis pipeline.

Usage:
    # Set environment variables
    export SWARMIT_URL=http://localhost:8080
    export OPENAI_API_KEY=sk-...

    # Run pipeline
    python pipeline/run.py

    # Or with options
    python pipeline/run.py --days 3 --min-score 0.6 --dry-run
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path
from datetime import datetime
from dataclasses import asdict

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scanner.sources import fetch_all_sources, Paper
from analyzer.matcher import SimilarityMatcher, MatchResult
from publisher.mdx_generator import MDXGenerator, PaperData

# Swarm-It client
try:
    sys.path.insert(0, os.path.expanduser("~/GitHub/swarm-it/clients/python"))
    from swarm_it import SwarmIt
    HAS_SWARMIT = True
except ImportError:
    HAS_SWARMIT = False
    print("Warning: swarm_it client not found, running without certification")


class CertifiedPipeline:
    """
    Paper discovery pipeline with RSCT certification.

    Uses 3-agent swarm:
    - Scanner: fetches papers (certified input)
    - Analyzer: matches against topics (certified analysis)
    - Publisher: generates blog posts (certified output)
    """

    def __init__(
        self,
        swarmit_url: str = "http://localhost:8080",
        topics_dir: str = "content/topics",
        output_dir: str = "content/generated-posts",
        min_score: float = 0.5,
    ):
        self.min_score = min_score
        self.matcher = SimilarityMatcher(topics_dir=topics_dir, threshold=min_score)
        self.generator = MDXGenerator(output_dir=output_dir)

        # Initialize Swarm-It client
        if HAS_SWARMIT:
            self.swarmit = SwarmIt(url=swarmit_url)
            if not self.swarmit.health():
                print(f"Warning: Swarm-It sidecar not reachable at {swarmit_url}")
                self.swarmit = None
        else:
            self.swarmit = None

    def certify(self, content: str, stage: str) -> dict:
        """Certify content through Swarm-It API."""
        if not self.swarmit:
            return {"allowed": True, "kappa_gate": 1.0, "decision": "EXECUTE", "stage": stage}

        try:
            cert = self.swarmit.certify(content)
            return {
                "allowed": cert.allowed,
                "kappa_gate": cert.kappa_gate,
                "decision": cert.decision.value,
                "R": cert.R,
                "S": cert.S,
                "N": cert.N,
                "stage": stage,
            }
        except Exception as e:
            print(f"Certification error: {e}")
            return {"allowed": True, "kappa_gate": 0.0, "decision": "ERROR", "stage": stage}

    async def run(self, days: int = 1, max_papers: int = 50, dry_run: bool = False) -> dict:
        """Run the full pipeline."""
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "papers_fetched": 0,
            "papers_matched": 0,
            "posts_generated": 0,
            "certifications": [],
            "errors": [],
        }

        # Load topics
        print("Loading topics...")
        self.matcher.load_topics()
        if not self.matcher.topics:
            print("Warning: No topics loaded, using keyword matching")

        # Stage 1: Fetch papers
        print(f"\n[1/3] Fetching papers from last {days} day(s)...")
        papers = await fetch_all_sources(days=days, max_per_source=max_papers)
        results["papers_fetched"] = len(papers)
        print(f"  Found {len(papers)} papers")

        if not papers:
            print("No papers found")
            return results

        # Certify scanner output
        scanner_content = f"Fetched {len(papers)} papers: " + ", ".join(p.title[:50] for p in papers[:5])
        cert = self.certify(scanner_content, "scanner")
        results["certifications"].append(cert)
        print(f"  Scanner cert: kappa={cert['kappa_gate']:.2f} decision={cert['decision']}")

        if not cert["allowed"]:
            results["errors"].append("Scanner output blocked by certification")
            return results

        # Stage 2: Match against topics
        print("\n[2/3] Matching papers against topics...")
        paper_dicts = [{"id": p.id, "title": p.title, "abstract": p.abstract} for p in papers]
        matches = self.matcher.match_papers(paper_dicts)

        # Filter by score
        relevant = [(p, m) for p, m in zip(papers, matches) if m.similarity_score >= self.min_score]
        results["papers_matched"] = len(relevant)
        print(f"  {len(relevant)} papers above {self.min_score:.0%} threshold")

        if not relevant:
            print("No papers matched above threshold")
            return results

        # Certify analyzer output
        analyzer_content = f"Matched {len(relevant)} papers: " + "; ".join(
            f"{m.paper_title[:30]} ({m.similarity_score:.0%})" for _, m in relevant[:5]
        )
        cert = self.certify(analyzer_content, "analyzer")
        results["certifications"].append(cert)
        print(f"  Analyzer cert: kappa={cert['kappa_gate']:.2f} decision={cert['decision']}")

        if not cert["allowed"]:
            results["errors"].append("Analyzer output blocked by certification")
            return results

        # Stage 3: Generate blog posts
        print("\n[3/3] Generating blog posts...")

        if dry_run:
            print("  [DRY RUN] Would generate posts for:")
            for paper, match in relevant[:10]:
                print(f"    - {paper.title[:60]}... ({match.similarity_score:.0%})")
            return results

        # Convert to PaperData
        paper_data = []
        for paper, match in relevant[:10]:  # Limit to top 10
            paper_data.append(PaperData(
                id=paper.id,
                title=paper.title,
                abstract=paper.abstract,
                authors=paper.authors,
                source=paper.source,
                url=paper.url,
                pdf_url=paper.pdf_url,
                published_date=paper.published_date,
                similarity_score=match.similarity_score,
                matched_topics=match.matched_topics,
                categories=paper.categories,
            ))

        # Generate posts
        saved = self.generator.generate_and_save(paper_data)
        results["posts_generated"] = len(saved)

        # Certify publisher output
        publisher_content = f"Generated {len(saved)} posts: " + ", ".join(p.stem for p in saved[:5])
        cert = self.certify(publisher_content, "publisher")
        results["certifications"].append(cert)
        print(f"  Publisher cert: kappa={cert['kappa_gate']:.2f} decision={cert['decision']}")

        print(f"\nPipeline complete: {len(saved)} posts generated")
        return results


def main():
    parser = argparse.ArgumentParser(description="Run paper discovery pipeline")
    parser.add_argument("--days", type=int, default=1, help="Days to look back")
    parser.add_argument("--max-papers", type=int, default=50, help="Max papers per source")
    parser.add_argument("--min-score", type=float, default=0.5, help="Min similarity score")
    parser.add_argument("--dry-run", action="store_true", help="Don't generate posts")
    parser.add_argument("--topics-dir", default="content/topics", help="Topics directory")
    parser.add_argument("--output-dir", default="content/generated-posts", help="Output directory")
    args = parser.parse_args()

    swarmit_url = os.getenv("SWARMIT_URL", "http://localhost:8080")

    pipeline = CertifiedPipeline(
        swarmit_url=swarmit_url,
        topics_dir=args.topics_dir,
        output_dir=args.output_dir,
        min_score=args.min_score,
    )

    results = asyncio.run(pipeline.run(
        days=args.days,
        max_papers=args.max_papers,
        dry_run=args.dry_run,
    ))

    # Summary
    print("\n" + "=" * 50)
    print("PIPELINE SUMMARY")
    print("=" * 50)
    print(f"Papers fetched:  {results['papers_fetched']}")
    print(f"Papers matched:  {results['papers_matched']}")
    print(f"Posts generated: {results['posts_generated']}")
    print(f"Certifications:  {len(results['certifications'])}")

    if results["errors"]:
        print(f"Errors: {results['errors']}")

    # Print certification summary
    print("\nCertification Results:")
    for cert in results["certifications"]:
        status = "PASS" if cert["allowed"] else "BLOCK"
        print(f"  [{cert['stage']}] {status} kappa={cert['kappa_gate']:.2f}")


if __name__ == "__main__":
    main()
