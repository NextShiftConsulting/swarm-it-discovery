#!/usr/bin/env python3
"""
Daily Discovery Pipeline - Complete daily paper discovery and analysis.

This script runs the full pipeline:
1. Fetch papers from all 6 sources
2. Match against research topics
3. Score against RSCT whitepaper
4. Run source-specific SWARM agents
5. Generate and upload posts to S3
6. Save analytics reports

Usage:
    # Run locally
    python scripts/daily_discovery.py

    # With options
    python scripts/daily_discovery.py --days 1 --max-papers 50 --dry-run

    # As Lambda handler
    # The handler() function is called by EventBridge
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "pipeline"))

from pipeline.scanner.sources import fetch_all_sources
from pipeline.analyzer.matcher import SimilarityMatcher
from pipeline.analyzer.rsct_scorer import RSCTScorer
from pipeline.publisher.mdx_generator import MDXGenerator, PaperData
from agents.orchestrator import run_daily_agents


class DailyDiscoveryPipeline:
    """Complete daily discovery pipeline with SWARM agents."""

    def __init__(
        self,
        topics_dir: str = "content/topics",
        output_dir: str = "/tmp/generated-posts",
        whitepaper_path: str = None,
        s3_bucket: str = None,
        s3_prefix: str = None,
        min_score: float = 0.5,
        min_rsct_score: float = 0.1,
    ):
        self.topics_dir = topics_dir
        self.output_dir = output_dir
        self.whitepaper_path = whitepaper_path
        self.s3_bucket = s3_bucket or os.getenv("S3_BUCKET", "swarmit-nextshift-site")
        self.s3_prefix = s3_prefix or os.getenv("S3_PREFIX", "content/reviews")
        self.min_score = min_score
        self.min_rsct_score = min_rsct_score

        # Initialize components
        self.matcher = SimilarityMatcher(topics_dir=topics_dir, threshold=min_score)
        self.rsct_scorer = RSCTScorer(whitepaper_path=whitepaper_path)
        self.generator = MDXGenerator(output_dir=output_dir)

    async def run(
        self,
        days: int = 1,
        max_papers: int = 50,
        dry_run: bool = False,
    ) -> dict:
        """Run the complete daily pipeline."""

        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "papers_fetched": 0,
            "papers_matched": 0,
            "papers_rsct_ranked": 0,
            "posts_generated": 0,
            "source_distribution": {},
            "agent_report": {},
            "s3_uploads": [],
        }

        # Step 1: Fetch papers
        print("\n[1/6] Fetching papers from all sources...")
        papers = await fetch_all_sources(days=days, max_per_source=max_papers)
        results["papers_fetched"] = len(papers)

        # Convert to dicts for processing
        paper_dicts = [
            {
                "id": p.id,
                "title": p.title,
                "abstract": p.abstract,
                "authors": p.authors,
                "source": p.source,
                "url": p.url,
                "pdf_url": p.pdf_url,
                "published_date": p.published_date,
                "categories": p.categories,
            }
            for p in papers
        ]

        # Source distribution
        from collections import Counter
        import math

        source_counts = Counter(p["source"] for p in paper_dicts)
        total = len(paper_dicts)

        sources_info = {}
        for source, count in source_counts.items():
            sources_info[source] = {
                "count": count,
                "percentage": round(count / total * 100, 1) if total > 0 else 0,
            }

        # Diversity score
        if total > 0 and len(source_counts) > 1:
            entropy = -sum((c/total) * math.log2(c/total) for c in source_counts.values() if c > 0)
            max_entropy = math.log2(len(source_counts))
            diversity = round(entropy / max_entropy, 3) if max_entropy > 0 else 0
        else:
            diversity = 0

        results["source_distribution"] = {
            "total_papers": total,
            "sources": sources_info,
            "diversity_score": diversity,
        }

        print(f"  Found {total} papers from {len(source_counts)} sources (diversity: {diversity:.1%})")
        for src, info in sources_info.items():
            print(f"    {src}: {info['count']} ({info['percentage']}%)")

        if not papers:
            print("No papers found")
            return results

        # Step 2: Match against topics
        print("\n[2/6] Matching papers against topics...")
        self.matcher.load_topics()
        matches = self.matcher.match_papers(paper_dicts)

        # Filter by score
        relevant = [(p, m) for p, m in zip(paper_dicts, matches) if m.similarity_score >= self.min_score]
        results["papers_matched"] = len(relevant)
        print(f"  {len(relevant)} papers above {self.min_score:.0%} threshold")

        if not relevant:
            print("No papers matched")
            return results

        # Step 3: RSCT scoring
        print("\n[3/6] Scoring against RSCT whitepaper...")
        rsct_papers = [
            {
                "id": p["id"],
                "title": p["title"],
                "abstract": p["abstract"],
                "similarity_score": m.similarity_score,
            }
            for p, m in relevant
        ]
        rsct_scores = self.rsct_scorer.rank_papers(rsct_papers, min_rsct_score=self.min_rsct_score)
        results["papers_rsct_ranked"] = len(rsct_scores)
        print(f"  {len(rsct_scores)} papers above {self.min_rsct_score:.0%} RSCT threshold")

        # Build lookup
        rsct_lookup = {s.paper_id: s for s in rsct_scores}
        matched_papers = [p for p, m in relevant if p["id"] in rsct_lookup]

        # Step 4: SWARM Agent Analysis
        print("\n[4/6] Running SWARM source agents...")
        agent_report = run_daily_agents(matched_papers, self.s3_bucket if not dry_run else None)
        results["agent_report"] = agent_report

        # Step 5: Generate posts
        print("\n[5/6] Generating blog posts...")

        if dry_run:
            print("  [DRY RUN] Would generate posts for:")
            for p in matched_papers[:5]:
                rsct = rsct_lookup.get(p["id"])
                print(f"    - {p['title'][:50]}... (RSCT: {rsct.rsct_similarity:.0%})")
            return results

        # Convert to PaperData
        paper_data = []
        for paper in matched_papers[:10]:  # Limit to top 10
            rsct = rsct_lookup.get(paper["id"])
            if rsct:
                paper_data.append(PaperData(
                    id=paper["id"],
                    title=paper["title"],
                    abstract=paper["abstract"],
                    authors=paper.get("authors", []),
                    source=paper["source"],
                    url=paper.get("url", ""),
                    pdf_url=paper.get("pdf_url"),
                    published_date=paper.get("published_date", ""),
                    similarity_score=rsct.combined_score,
                    matched_topics=[],
                    categories=paper.get("categories", []),
                ))

        # Generate posts
        saved = self.generator.generate_and_save(paper_data)
        results["posts_generated"] = len(saved)
        print(f"  Generated {len(saved)} posts")

        # Step 6: Upload to S3
        print("\n[6/6] Uploading to S3...")
        uploaded = self._upload_to_s3()
        results["s3_uploads"] = uploaded

        # Save daily report
        self._save_report(results)

        print(f"\n=== Pipeline Complete ===")
        print(f"Papers: {results['papers_fetched']} fetched → {results['papers_matched']} matched → {results['posts_generated']} posts")

        return results

    def _upload_to_s3(self) -> list:
        """Upload posts to S3."""
        import boto3
        from pathlib import Path

        s3 = boto3.client("s3")
        uploaded = []

        output_path = Path(self.output_dir)
        if not output_path.exists():
            return uploaded

        for file in output_path.glob("*.mdx"):
            key = f"{self.s3_prefix}/{file.name}"
            try:
                s3.upload_file(str(file), self.s3_bucket, key, ExtraArgs={"ContentType": "text/markdown"})
                uploaded.append(key)
                print(f"  Uploaded: s3://{self.s3_bucket}/{key}")
            except Exception as e:
                print(f"  Error uploading {file.name}: {e}")

        return uploaded

    def _save_report(self, results: dict) -> None:
        """Save daily report to S3."""
        import boto3

        s3 = boto3.client("s3")
        today = datetime.utcnow().strftime("%Y-%m-%d")

        # Use different analytics path for dev vs prod
        if "dev" in self.s3_prefix:
            key = f"analytics/daily-dev/{today}.json"
        else:
            key = f"analytics/daily/{today}.json"

        try:
            s3.put_object(
                Bucket=self.s3_bucket,
                Key=key,
                Body=json.dumps(results, indent=2, default=str),
                ContentType="application/json",
            )
            print(f"  Report saved: s3://{self.s3_bucket}/{key}")
        except Exception as e:
            print(f"  Error saving report: {e}")


def handler(event, context):
    """AWS Lambda handler for daily execution."""
    days = event.get("days", 1)
    max_papers = event.get("max_papers", 50)
    min_score = event.get("min_score", 0.5)
    min_rsct_score = event.get("min_rsct_score", 0.1)
    dry_run = event.get("dry_run", False)

    # Use bundled whitepaper
    whitepaper_path = os.path.join(os.path.dirname(__file__), "..", "pipeline", "rsct_whitepaper.pdf")
    if not os.path.exists(whitepaper_path):
        whitepaper_path = None

    pipeline = DailyDiscoveryPipeline(
        topics_dir="content/topics",
        output_dir="/tmp/generated-posts",
        whitepaper_path=whitepaper_path,
        s3_bucket=os.getenv("S3_BUCKET"),
        min_score=min_score,
        min_rsct_score=min_rsct_score,
    )

    results = asyncio.run(pipeline.run(
        days=days,
        max_papers=max_papers,
        dry_run=dry_run,
    ))

    return {
        "statusCode": 200,
        "body": json.dumps({
            "papers_fetched": results["papers_fetched"],
            "papers_matched": results["papers_matched"],
            "posts_generated": results["posts_generated"],
            "source_distribution": results["source_distribution"],
            "agent_summary": {
                "total_analyzed": results["agent_report"].get("total_analyzed", 0),
                "avg_relevance": results["agent_report"].get("avg_relevance", 0),
                "top_papers": results["agent_report"].get("top_papers", [])[:3],
            },
        })
    }


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Daily Discovery Pipeline")
    parser.add_argument("--days", type=int, default=1, help="Days to look back")
    parser.add_argument("--max-papers", type=int, default=50, help="Max papers per source")
    parser.add_argument("--min-score", type=float, default=0.5, help="Min topic score")
    parser.add_argument("--min-rsct-score", type=float, default=0.1, help="Min RSCT score")
    parser.add_argument("--dry-run", action="store_true", help="Don't upload to S3")
    parser.add_argument("--topics-dir", default="content/topics", help="Topics directory")
    parser.add_argument("--whitepaper", help="Path to RSCT whitepaper")
    parser.add_argument("--s3-bucket", help="S3 bucket for uploads")
    parser.add_argument("--s3-prefix", default="content/reviews-dev", help="S3 prefix (dev vs prod)")
    args = parser.parse_args()

    pipeline = DailyDiscoveryPipeline(
        topics_dir=args.topics_dir,
        output_dir="/tmp/generated-posts",
        whitepaper_path=args.whitepaper,
        s3_bucket=args.s3_bucket,
        s3_prefix=args.s3_prefix,
        min_score=args.min_score,
        min_rsct_score=args.min_rsct_score,
    )

    results = asyncio.run(pipeline.run(
        days=args.days,
        max_papers=args.max_papers,
        dry_run=args.dry_run,
    ))

    print("\n" + "=" * 60)
    print(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    main()
