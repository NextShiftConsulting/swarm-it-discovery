"""
HuggingFace Papers Agent - Fetches daily curated ML papers from HuggingFace.

Uses the free HuggingFace API (no auth required):
- https://huggingface.co/api/daily_papers

This is the same feed as @_akhaliq's daily papers - most reliable source.
"""

import sys
import httpx
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime

# Add swarm-it repos to path
sys.path.insert(0, str(Path.home() / "GitHub" / "swarm-it-auth"))


@dataclass
class HFPaper:
    """Paper from HuggingFace Daily Papers."""
    arxiv_id: str
    title: str
    authors: List[str]
    summary: str
    url: str
    pdf_url: str
    published_at: str
    upvotes: int = 0
    comments: int = 0


@dataclass
class HFPapersResult:
    """Result from fetching HuggingFace papers."""
    papers: List[HFPaper]
    arxiv_ids: List[str]
    total_count: int
    fetch_time: float


class HuggingFacePapersAgent:
    """
    Agent for fetching daily curated ML papers from HuggingFace.

    This is the same feed as @_akhaliq's daily papers on X/Twitter,
    but accessed directly via API - no rate limits, no auth needed.

    Usage:
        agent = HuggingFacePapersAgent()
        result = agent.fetch_daily_papers()
        print(f"Found {len(result.arxiv_ids)} papers")

        # Feed to academic pipeline
        for arxiv_id in result.arxiv_ids:
            scanner.fetch_paper(f"arxiv:{arxiv_id}")
    """

    AGENT_NAME = "HuggingFacePapersAgent"

    # HuggingFace API endpoints
    DAILY_PAPERS_URL = "https://huggingface.co/api/daily_papers"
    PAPER_DETAIL_URL = "https://huggingface.co/api/papers"

    def __init__(self):
        """Initialize HuggingFace Papers agent."""
        self._http_client = httpx.Client(timeout=30)
        print(f"✓ {self.AGENT_NAME}: Initialized (no auth required)")

    def fetch_daily_papers(self) -> HFPapersResult:
        """
        Fetch today's curated papers from HuggingFace.

        Returns:
            HFPapersResult with papers and arXiv IDs
        """
        print(f"\n=== {self.AGENT_NAME}: Fetching daily papers ===")
        start_time = datetime.utcnow()

        try:
            response = self._http_client.get(self.DAILY_PAPERS_URL)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"  ⚠ API error: {e}")
            return HFPapersResult(
                papers=[],
                arxiv_ids=[],
                total_count=0,
                fetch_time=0,
            )

        papers = []
        arxiv_ids = []

        for item in data:
            paper_data = item.get('paper', {})
            arxiv_id = paper_data.get('id', '')

            if not arxiv_id:
                continue

            arxiv_ids.append(arxiv_id)

            # Extract authors
            authors = []
            for author in paper_data.get('authors', [])[:10]:
                name = author.get('name', '')
                if name:
                    authors.append(name)

            # Build paper object
            paper = HFPaper(
                arxiv_id=arxiv_id,
                title=paper_data.get('title', ''),
                authors=authors,
                summary=paper_data.get('summary', '')[:1000],
                url=f"https://huggingface.co/papers/{arxiv_id}",
                pdf_url=f"https://arxiv.org/pdf/{arxiv_id}.pdf",
                published_at=paper_data.get('publishedAt', ''),
                upvotes=item.get('paper', {}).get('upvotes', 0),
                comments=item.get('numComments', 0),
            )
            papers.append(paper)

        fetch_time = (datetime.utcnow() - start_time).total_seconds()

        print(f"  ✓ Fetched {len(papers)} papers in {fetch_time:.1f}s")

        # Show top papers by upvotes
        top_papers = sorted(papers, key=lambda p: p.upvotes, reverse=True)[:5]
        if top_papers:
            print(f"\n  Top papers by upvotes:")
            for p in top_papers:
                print(f"    [{p.upvotes}↑] {p.title[:60]}...")

        return HFPapersResult(
            papers=papers,
            arxiv_ids=arxiv_ids,
            total_count=len(papers),
            fetch_time=fetch_time,
        )

    def fetch_paper_details(self, arxiv_id: str) -> Optional[Dict]:
        """
        Fetch detailed info for a specific paper.

        Args:
            arxiv_id: arXiv paper ID (e.g., "2603.08258")

        Returns:
            Paper details dict or None
        """
        try:
            url = f"{self.PAPER_DETAIL_URL}/{arxiv_id}"
            response = self._http_client.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"  ⚠ Failed to fetch {arxiv_id}: {e}")
            return None

    def get_arxiv_ids_for_pipeline(self) -> List[str]:
        """
        Get list of arXiv IDs ready for the academic pipeline.

        Returns:
            List of arXiv IDs to fetch via ScannerAgent
        """
        result = self.fetch_daily_papers()
        return result.arxiv_ids

    def to_scanner_format(self, result: HFPapersResult) -> List[Dict]:
        """
        Convert HF papers to format expected by ScannerAgent.

        Args:
            result: HFPapersResult from fetch_daily_papers

        Returns:
            List of paper dicts compatible with pipeline
        """
        papers = []
        for p in result.papers:
            papers.append({
                'id': f"arxiv:{p.arxiv_id}",
                'title': p.title,
                'abstract': p.summary,
                'authors': p.authors,
                'source': 'huggingface',
                'url': f"https://arxiv.org/abs/{p.arxiv_id}",
                'pdf_url': p.pdf_url,
                'published_date': p.published_at[:10] if p.published_at else '',
                'categories': [],
                'upvotes': p.upvotes,
            })
        return papers


# CLI entry point
if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Fetch HuggingFace daily papers")
    parser.add_argument("--output", "-o", help="Output JSON file")
    parser.add_argument("--ids-only", action="store_true", help="Only output arXiv IDs")
    args = parser.parse_args()

    agent = HuggingFacePapersAgent()
    result = agent.fetch_daily_papers()

    if args.ids_only:
        for arxiv_id in result.arxiv_ids:
            print(arxiv_id)
    else:
        print(f"\n=== Summary ===")
        print(f"Total papers: {result.total_count}")
        print(f"Fetch time: {result.fetch_time:.1f}s")

    if args.output:
        with open(args.output, 'w') as f:
            json.dump({
                'arxiv_ids': result.arxiv_ids,
                'papers': [p.__dict__ for p in result.papers],
                'total_count': result.total_count,
            }, f, indent=2, default=str)
        print(f"\nSaved to {args.output}")
