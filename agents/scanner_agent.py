"""
Scanner Agent - Fetches papers from multiple academic sources.

Uses swarm-it-auth for credentials.
Coordinates parallel fetching from arXiv, PubMed, bioRxiv, Semantic Scholar, OpenAlex.
"""

import sys
import asyncio
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone

# Add swarm-it repos to path
sys.path.insert(0, str(Path.home() / "GitHub" / "swarm-it-auth"))

# Import pipeline scanner
sys.path.insert(0, str(Path(__file__).parent.parent / "pipeline"))
from scanner.sources import fetch_all_sources


@dataclass
class ScanResult:
    """Result from scanning sources."""
    papers: List[Dict]
    source_counts: Dict[str, int]
    total_count: int
    scan_time: float
    errors: List[str] = field(default_factory=list)


class ScannerAgent:
    """
    Agent for fetching papers from academic sources.

    Sources:
    - arXiv: ML/AI preprints
    - PubMed: Biomedical literature
    - bioRxiv/medRxiv: Life sciences preprints
    - Semantic Scholar: Citation-aware search
    - OpenAlex: Comprehensive academic database

    Usage:
        agent = ScannerAgent()
        result = agent.scan(days=7, max_per_source=50)
        print(f"Found {result.total_count} papers")
    """

    SOURCES = ["arxiv", "pubmed", "biorxiv", "medrxiv", "semantic_scholar", "openalex"]

    def __init__(self, sources: Optional[List[str]] = None):
        """
        Initialize scanner agent.

        Args:
            sources: List of sources to scan (default: all)
        """
        self.sources = sources or self.SOURCES
        self._init_time = datetime.now(timezone.utc)

    def scan(
        self,
        days: int = 7,
        max_per_source: int = 50,
        query: Optional[str] = None,
    ) -> ScanResult:
        """
        Scan all sources for papers.

        Args:
            days: Look back N days
            max_per_source: Max papers per source
            query: Optional search query

        Returns:
            ScanResult with papers and metadata
        """
        print("\n=== ScannerAgent: Fetching papers ===")
        print(f"Sources: {', '.join(self.sources)}")
        print(f"Days: {days}, Max per source: {max_per_source}")

        start_time = datetime.now(timezone.utc)
        errors = []

        # Use async fetcher from pipeline
        try:
            papers = asyncio.run(
                fetch_all_sources(
                    days=days,
                    max_per_source=max_per_source,
                )
            )
        except Exception as e:
            errors.append(f"Fetch error: {e}")
            papers = []

        # Convert Paper objects to dicts
        paper_dicts = []
        for p in papers:
            if hasattr(p, '__dict__'):
                paper_dicts.append(p.__dict__ if hasattr(p, '__dict__') else p)
            elif isinstance(p, dict):
                paper_dicts.append(p)

        # Count by source
        source_counts = {}
        for p in paper_dicts:
            source = p.get('source', 'unknown')
            source_counts[source] = source_counts.get(source, 0) + 1

        scan_time = (datetime.now(timezone.utc) - start_time).total_seconds()

        print(f"\n✓ Scan complete in {scan_time:.1f}s")
        for source, count in sorted(source_counts.items()):
            print(f"  {source}: {count} papers")

        return ScanResult(
            papers=paper_dicts,
            source_counts=source_counts,
            total_count=len(paper_dicts),
            scan_time=scan_time,
            errors=errors,
        )

    def scan_source(
        self,
        source: str,
        days: int = 7,
        max_papers: int = 50,
    ) -> List[Dict]:
        """
        Scan a single source.

        Args:
            source: Source name (arxiv, pubmed, etc.)
            days: Look back N days
            max_papers: Max papers to fetch

        Returns:
            List of paper dicts
        """
        print(f"\n=== ScannerAgent: Fetching from {source} ===")

        # Run full scan but filter to source
        result = self.scan(days=days, max_per_source=max_papers)
        return [p for p in result.papers if p.get('source') == source]

    def __repr__(self) -> str:
        return f"ScannerAgent(sources={self.sources})"


# CLI entry point
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scan academic sources for papers")
    parser.add_argument("--days", type=int, default=7, help="Days to look back")
    parser.add_argument("--max", type=int, default=50, help="Max papers per source")
    parser.add_argument("--source", help="Single source to scan")
    parser.add_argument("--output", "-o", help="Output JSON file")
    args = parser.parse_args()

    agent = ScannerAgent()

    if args.source:
        papers = agent.scan_source(args.source, days=args.days, max_papers=args.max)
        result = ScanResult(
            papers=papers,
            source_counts={args.source: len(papers)},
            total_count=len(papers),
            scan_time=0,
        )
    else:
        result = agent.scan(days=args.days, max_per_source=args.max)

    if args.output:
        import json
        with open(args.output, 'w') as f:
            json.dump({
                "papers": result.papers,
                "source_counts": result.source_counts,
                "total_count": result.total_count,
                "scan_time": result.scan_time,
            }, f, indent=2, default=str)
        print(f"\nSaved to {args.output}")
