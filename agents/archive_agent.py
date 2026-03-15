"""
Archive Agent - Stores research papers in tiered archive based on RSCT metrics.

Tier 1 (PUBLISH):  κ ≥ 0.5, RSCT ≥ 30%, Topic ≥ 50% → Full MDX + archive
Tier 2 (ARCHIVE):  κ ≥ 0.3, RSCT ≥ 15%, Topic ≥ 25% → JSON archive only
Tier 3 (LOG):      Any scanned paper → Basic metadata log

Uses swarm-it-auth for credentials.
"""

import sys
import json
import os
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime

# Add swarm-it repos to path
sys.path.insert(0, str(Path.home() / "GitHub" / "swarm-it-auth"))


@dataclass
class ArchiveThresholds:
    """RSCT-based thresholds for archive tiers."""
    # Tier 1: PUBLISH
    t1_kappa: float = 0.5
    t1_rsct: float = 0.30
    t1_topic: float = 0.50

    # Tier 2: ARCHIVE
    t2_kappa: float = 0.3
    t2_rsct: float = 0.15
    t2_topic: float = 0.25

    # Tier 3: LOG (no thresholds - logs everything)


@dataclass
class ArchivedPaper:
    """Paper stored in archive."""
    paper_id: str
    title: str
    source: str
    url: str
    abstract: str
    authors: List[str]
    published_date: str

    # RSCT Metrics
    kappa: float
    rsct_score: float
    topic_score: float
    combined_score: float

    # Classification
    tier: int  # 1, 2, or 3
    topics_matched: List[str]

    # Metadata
    archived_at: str
    scan_date: str

    # Optional
    pdf_url: Optional[str] = None
    github_url: Optional[str] = None
    key_findings: List[str] = field(default_factory=list)
    rsct_connections: List[str] = field(default_factory=list)


@dataclass
class ArchiveResult:
    """Result from archiving papers."""
    tier1_count: int
    tier2_count: int
    tier3_count: int
    total_archived: int
    archive_date: str
    files_created: List[str]


class ArchiveAgent:
    """
    Agent for archiving research papers based on RSCT metrics.

    Papers are classified into tiers based on their κ, RSCT, and topic scores,
    then stored in the appropriate archive directory.

    Usage:
        agent = ArchiveAgent()
        result = agent.archive_papers(papers, analyses)
        print(f"Archived {result.total_archived} papers")
    """

    AGENT_NAME = "ArchiveAgent"
    DATA_DIR = Path.home() / "GitHub" / "swarm-it-discovery" / "data"

    def __init__(self, thresholds: Optional[ArchiveThresholds] = None):
        """
        Initialize archive agent.

        Args:
            thresholds: Custom thresholds (default: standard RSCT thresholds)
        """
        self.thresholds = thresholds or ArchiveThresholds()
        self._ensure_directories()

    def _ensure_directories(self):
        """Create archive directories if they don't exist."""
        for tier_dir in ["tier1-publish", "tier2-archive", "tier3-log", "transcripts", "pdfs"]:
            (self.DATA_DIR / tier_dir).mkdir(parents=True, exist_ok=True)

    def classify_tier(self, kappa: float, rsct: float, topic: float) -> int:
        """
        Classify paper into archive tier based on RSCT metrics.

        Args:
            kappa: κ certification score (0-1)
            rsct: RSCT similarity score (0-1)
            topic: Topic relevance score (0-1)

        Returns:
            Tier number (1, 2, or 3)
        """
        t = self.thresholds

        # Tier 1: Publish quality
        if kappa >= t.t1_kappa and rsct >= t.t1_rsct and topic >= t.t1_topic:
            return 1

        # Tier 2: Archive quality
        if kappa >= t.t2_kappa and rsct >= t.t2_rsct and topic >= t.t2_topic:
            return 2

        # Tier 3: Log everything else
        return 3

    def archive_paper(self, paper: Dict, analysis: Optional[Dict] = None) -> ArchivedPaper:
        """
        Archive a single paper with its analysis.

        Args:
            paper: Paper metadata dict
            analysis: Optional analysis results

        Returns:
            ArchivedPaper record
        """
        # Extract metrics
        kappa = 0.0
        rsct_score = 0.0
        topic_score = 0.0
        combined_score = 0.0
        topics_matched = []
        key_findings = []
        rsct_connections = []

        if analysis:
            kappa = analysis.get("kappa", analysis.get("rsct_kappa", 0.0)) or 0.0
            rsct_score = analysis.get("rsct_score", analysis.get("rsct_similarity", 0.0)) or 0.0
            topic_score = analysis.get("topic_score", analysis.get("similarity_score", 0.0)) or 0.0
            combined_score = analysis.get("combined_score", 0.0) or 0.0
            topics_matched = analysis.get("topics_matched", analysis.get("matched_topics", [])) or []
            key_findings = analysis.get("key_findings", []) or []
            rsct_connections = analysis.get("rsct_connections", []) or []

        # Classify tier
        tier = self.classify_tier(kappa, rsct_score, topic_score)

        # Create archive record
        archived = ArchivedPaper(
            paper_id=paper.get("id", paper.get("paper_id", "unknown")),
            title=paper.get("title", "Unknown"),
            source=paper.get("source", "unknown"),
            url=paper.get("url", ""),
            abstract=paper.get("abstract", "")[:2000],  # Truncate long abstracts
            authors=paper.get("authors", [])[:10],  # Limit authors
            published_date=paper.get("published_date", ""),
            kappa=round(kappa, 4),
            rsct_score=round(rsct_score, 4),
            topic_score=round(topic_score, 4),
            combined_score=round(combined_score, 4),
            tier=tier,
            topics_matched=topics_matched[:5],  # Limit topics
            archived_at=datetime.utcnow().isoformat(),
            scan_date=datetime.utcnow().strftime("%Y-%m-%d"),
            pdf_url=paper.get("pdf_url"),
            github_url=paper.get("github_url"),
            key_findings=key_findings[:5],
            rsct_connections=rsct_connections[:5],
        )

        return archived

    def save_to_tier(self, archived: ArchivedPaper) -> str:
        """
        Save archived paper to appropriate tier directory.

        Args:
            archived: ArchivedPaper record

        Returns:
            Path to saved file
        """
        tier_dir = self.DATA_DIR / f"tier{archived.tier}-{'publish' if archived.tier == 1 else 'archive' if archived.tier == 2 else 'log'}"
        date_dir = tier_dir / archived.scan_date
        date_dir.mkdir(parents=True, exist_ok=True)

        # Create filename from paper_id
        safe_id = archived.paper_id.replace("/", "_").replace(":", "_")
        filepath = date_dir / f"{safe_id}.json"

        # Save as JSON
        with open(filepath, 'w') as f:
            json.dump(asdict(archived), f, indent=2, default=str)

        return str(filepath)

    def archive_papers(
        self,
        papers: List[Dict],
        analyses: Optional[List[Dict]] = None
    ) -> ArchiveResult:
        """
        Archive multiple papers.

        Args:
            papers: List of paper metadata dicts
            analyses: Optional list of analysis results (matched by index or paper_id)

        Returns:
            ArchiveResult with counts and file paths
        """
        print(f"\n=== {self.AGENT_NAME}: Archiving {len(papers)} papers ===")

        # Build analysis lookup
        analysis_lookup = {}
        if analyses:
            for a in analyses:
                pid = a.get("paper_id", a.get("id", ""))
                if pid:
                    analysis_lookup[pid] = a

        tier_counts = {1: 0, 2: 0, 3: 0}
        files_created = []

        for i, paper in enumerate(papers):
            paper_id = paper.get("id", paper.get("paper_id", f"unknown_{i}"))

            # Get matching analysis
            analysis = analysis_lookup.get(paper_id)
            if not analysis and analyses and i < len(analyses):
                analysis = analyses[i]

            # Archive paper
            archived = self.archive_paper(paper, analysis)
            filepath = self.save_to_tier(archived)

            tier_counts[archived.tier] += 1
            files_created.append(filepath)

        # Summary
        print(f"  Tier 1 (PUBLISH): {tier_counts[1]} papers")
        print(f"  Tier 2 (ARCHIVE): {tier_counts[2]} papers")
        print(f"  Tier 3 (LOG):     {tier_counts[3]} papers")
        print(f"  Total: {sum(tier_counts.values())} papers archived")

        return ArchiveResult(
            tier1_count=tier_counts[1],
            tier2_count=tier_counts[2],
            tier3_count=tier_counts[3],
            total_archived=sum(tier_counts.values()),
            archive_date=datetime.utcnow().strftime("%Y-%m-%d"),
            files_created=files_created,
        )

    def save_transcript(self, video_id: str, transcript: str, channel: str = "unknown") -> str:
        """
        Save YouTube transcript for future processing.

        Args:
            video_id: YouTube video ID
            transcript: Full transcript text
            channel: Channel name

        Returns:
            Path to saved file
        """
        transcript_dir = self.DATA_DIR / "transcripts" / channel
        transcript_dir.mkdir(parents=True, exist_ok=True)

        filepath = transcript_dir / f"{video_id}.txt"
        with open(filepath, 'w') as f:
            f.write(transcript)

        return str(filepath)

    def get_archive_stats(self) -> Dict[str, Any]:
        """
        Get statistics on archived papers.

        Returns:
            Dict with counts per tier and date
        """
        stats = {"tier1": 0, "tier2": 0, "tier3": 0, "by_date": {}}

        for tier in [1, 2, 3]:
            tier_name = "publish" if tier == 1 else "archive" if tier == 2 else "log"
            tier_dir = self.DATA_DIR / f"tier{tier}-{tier_name}"

            if tier_dir.exists():
                for date_dir in tier_dir.iterdir():
                    if date_dir.is_dir():
                        count = len(list(date_dir.glob("*.json")))
                        stats[f"tier{tier}"] += count

                        date_str = date_dir.name
                        if date_str not in stats["by_date"]:
                            stats["by_date"][date_str] = {"tier1": 0, "tier2": 0, "tier3": 0}
                        stats["by_date"][date_str][f"tier{tier}"] = count

        stats["total"] = stats["tier1"] + stats["tier2"] + stats["tier3"]
        return stats


# CLI entry point
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Archive research papers")
    parser.add_argument("--stats", action="store_true", help="Show archive statistics")
    parser.add_argument("--input", "-i", help="Input JSON file with papers")
    args = parser.parse_args()

    agent = ArchiveAgent()

    if args.stats:
        stats = agent.get_archive_stats()
        print(f"\n=== Archive Statistics ===")
        print(f"Tier 1 (Publish): {stats['tier1']}")
        print(f"Tier 2 (Archive): {stats['tier2']}")
        print(f"Tier 3 (Log):     {stats['tier3']}")
        print(f"Total:            {stats['total']}")

    elif args.input:
        with open(args.input) as f:
            data = json.load(f)
        papers = data.get("papers", data)
        result = agent.archive_papers(papers)
        print(f"\nArchived {result.total_archived} papers")
