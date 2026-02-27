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
from analyzer.rsct_scorer import RSCTScorer, RSCTScore
from publisher.mdx_generator import MDXGenerator, PaperData
from publisher.pdf_generator import PDFReviewGenerator

# Swarm-It ADK client
try:
    sys.path.insert(0, os.path.expanduser("~/GitHub/swarm-it-adk/clients/python"))
    from swarm_it import SwarmIt
    HAS_SWARMIT = True
except ImportError:
    HAS_SWARMIT = False
    print("Warning: Swarm-It ADK client not found, running without certification")


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
        pdf_output_dir: str = "content/pdf-reviews",
        whitepaper_path: str = None,
        min_score: float = 0.5,
        min_rsct_score: float = 0.3,
    ):
        self.min_score = min_score
        self.min_rsct_score = min_rsct_score
        self.matcher = SimilarityMatcher(topics_dir=topics_dir, threshold=min_score)
        self.generator = MDXGenerator(output_dir=output_dir)
        self.rsct_scorer = RSCTScorer(whitepaper_path=whitepaper_path)
        self.pdf_generator = PDFReviewGenerator(output_dir=pdf_output_dir)

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

    async def run(self, days: int = 1, max_papers: int = 50, dry_run: bool = False, generate_pdfs: bool = True) -> dict:
        """Run the full pipeline."""
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "papers_fetched": 0,
            "papers_matched": 0,
            "papers_rsct_ranked": 0,
            "posts_generated": 0,
            "pdfs_generated": 0,
            "certifications": [],
            "top_papers": [],
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

        # Stage 2.5: RSCT Whitepaper Scoring
        print("\n[2.5/4] Scoring papers against RSCT whitepaper...")
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
        results["papers_rsct_ranked"] = len(rsct_scores)
        print(f"  {len(rsct_scores)} papers above {self.min_rsct_score:.0%} RSCT threshold")

        # Create lookup for RSCT scores
        rsct_lookup = {s.paper_id: s for s in rsct_scores}

        # Resort relevant papers by RSCT combined score
        relevant_with_rsct = []
        for paper, match in relevant:
            rsct = rsct_lookup.get(paper.id)
            if rsct:
                relevant_with_rsct.append((paper, match, rsct))

        # Sort by combined RSCT score
        relevant_with_rsct.sort(key=lambda x: x[2].combined_score, reverse=True)

        # Show top papers
        print("\n  Top RSCT-Ranked Papers:")
        for i, (p, m, r) in enumerate(relevant_with_rsct[:5]):
            print(f"    {i+1}. {p.title[:50]}...")
            print(f"       Topic: {m.similarity_score:.0%} | RSCT: {r.rsct_similarity:.0%} | Combined: {r.combined_score:.0%}")
            results["top_papers"].append({
                "title": p.title,
                "topic_score": m.similarity_score,
                "rsct_score": r.rsct_similarity,
                "combined_score": r.combined_score,
                "key_overlaps": r.key_overlaps,
            })

        if not cert["allowed"]:
            results["errors"].append("Analyzer output blocked by certification")
            return results

        # Stage 3: Generate blog posts
        print("\n[3/4] Generating blog posts...")

        if dry_run:
            print("  [DRY RUN] Would generate posts for:")
            for paper, match, rsct in relevant_with_rsct[:10]:
                print(f"    - {paper.title[:50]}... (combined: {rsct.combined_score:.0%})")
            return results

        # Convert to PaperData with RSCT metrics
        paper_data = []
        for paper, match, rsct in relevant_with_rsct[:10]:  # Limit to top 10
            # Get per-paper RSCT certification
            cert = self.certify(f"{paper.title}: {paper.abstract[:500]}", "paper")

            paper_data.append(PaperData(
                id=paper.id,
                title=paper.title,
                abstract=paper.abstract,
                authors=paper.authors,
                source=paper.source,
                url=paper.url,
                pdf_url=paper.pdf_url,
                published_date=paper.published_date,
                similarity_score=rsct.combined_score,  # Use combined score
                matched_topics=match.matched_topics,
                categories=paper.categories,
                # RSCT certification from sidecar
                rsct_R=cert.get("R"),
                rsct_S=cert.get("S"),
                rsct_N=cert.get("N"),
                rsct_kappa=cert.get("kappa_gate"),
                rsct_decision=cert.get("decision"),
            ))

        # Generate posts
        saved = self.generator.generate_and_save(paper_data)
        results["posts_generated"] = len(saved)

        # Certify publisher output
        publisher_content = f"Generated {len(saved)} posts: " + ", ".join(p.stem for p in saved[:5])
        cert = self.certify(publisher_content, "publisher")
        results["certifications"].append(cert)
        print(f"  Publisher cert: kappa={cert['kappa_gate']:.2f} decision={cert['decision']}")

        # Stage 4: Generate PDF reviews for top papers
        if generate_pdfs and relevant_with_rsct:
            print("\n[4/4] Generating PDF reviews for top papers...")
            top_for_pdf = relevant_with_rsct[:5]  # Top 5 for detailed PDF reviews

            pdf_papers = []
            for paper, match, rsct in top_for_pdf:
                cert = self.certify(f"{paper.title}: {paper.abstract[:500]}", "paper_pdf")
                pdf_papers.append({
                    "id": paper.id,
                    "title": paper.title,
                    "abstract": paper.abstract,
                    "authors": paper.authors,
                    "url": paper.url,
                    "rsct_similarity": rsct.rsct_similarity,
                    "similarity_score": match.similarity_score,
                    "key_overlaps": rsct.key_overlaps,
                    "rsct_R": cert.get("R"),
                    "rsct_S": cert.get("S"),
                    "rsct_N": cert.get("N"),
                    "rsct_kappa": cert.get("kappa_gate"),
                })

            pdf_reviews = self.pdf_generator.generate_batch(pdf_papers, max_papers=5)
            results["pdfs_generated"] = len(pdf_reviews)

            print(f"  Generated {len(pdf_reviews)} PDF reviews:")
            for review in pdf_reviews:
                status = "PDF" if review.pdf_path else "TEX only"
                print(f"    - {review.title[:50]}... [{status}]")

        print(f"\nPipeline complete: {results['posts_generated']} posts, {results.get('pdfs_generated', 0)} PDFs")
        return results


def main():
    parser = argparse.ArgumentParser(description="Run paper discovery pipeline")
    parser.add_argument("--days", type=int, default=1, help="Days to look back")
    parser.add_argument("--max-papers", type=int, default=50, help="Max papers per source")
    parser.add_argument("--min-score", type=float, default=0.5, help="Min topic similarity score")
    parser.add_argument("--min-rsct-score", type=float, default=0.3, help="Min RSCT relevance score")
    parser.add_argument("--dry-run", action="store_true", help="Don't generate posts")
    parser.add_argument("--no-pdfs", action="store_true", help="Skip PDF generation")
    parser.add_argument("--topics-dir", default="content/topics", help="Topics directory")
    parser.add_argument("--output-dir", default="content/reviews", help="Output directory")
    parser.add_argument("--pdf-output-dir", default="content/pdf-reviews", help="PDF output directory")
    parser.add_argument("--whitepaper", default=None, help="Path to RSCT whitepaper for comparison")
    args = parser.parse_args()

    swarmit_url = os.getenv("SWARMIT_URL", "https://api.swarms.network")

    pipeline = CertifiedPipeline(
        swarmit_url=swarmit_url,
        topics_dir=args.topics_dir,
        output_dir=args.output_dir,
        pdf_output_dir=args.pdf_output_dir,
        whitepaper_path=args.whitepaper,
        min_score=args.min_score,
        min_rsct_score=args.min_rsct_score,
    )

    results = asyncio.run(pipeline.run(
        days=args.days,
        max_papers=args.max_papers,
        dry_run=args.dry_run,
        generate_pdfs=not args.no_pdfs,
    ))

    # Summary
    print("\n" + "=" * 60)
    print("PIPELINE SUMMARY")
    print("=" * 60)
    print(f"Papers fetched:    {results['papers_fetched']}")
    print(f"Papers matched:    {results['papers_matched']}")
    print(f"RSCT ranked:       {results.get('papers_rsct_ranked', 0)}")
    print(f"Posts generated:   {results['posts_generated']}")
    print(f"PDFs generated:    {results.get('pdfs_generated', 0)}")
    print(f"Certifications:    {len(results['certifications'])}")

    if results["errors"]:
        print(f"\nErrors: {results['errors']}")

    # Print certification summary
    if results["certifications"]:
        print("\nCertification Results:")
        for cert in results["certifications"]:
            status = "PASS" if cert["allowed"] else "BLOCK"
            print(f"  [{cert['stage']}] {status} kappa={cert['kappa_gate']:.2f}")

    # Print top papers
    if results.get("top_papers"):
        print("\n" + "-" * 60)
        print("TOP RSCT-RANKED PAPERS")
        print("-" * 60)
        for i, paper in enumerate(results["top_papers"][:5], 1):
            print(f"\n{i}. {paper['title'][:60]}...")
            print(f"   Topic: {paper['topic_score']:.0%} | RSCT: {paper['rsct_score']:.0%} | Combined: {paper['combined_score']:.0%}")
            if paper.get('key_overlaps'):
                print(f"   Key concepts: {', '.join(paper['key_overlaps'][:5])}")


if __name__ == "__main__":
    main()
