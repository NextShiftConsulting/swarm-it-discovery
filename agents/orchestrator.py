"""
Source Agent Orchestrator - Coordinates all source-specific agents.

Runs daily to analyze papers from each source with specialized expertise.
"""

import os
import json
from datetime import datetime, timezone
from typing import List, Dict, Optional
from dataclasses import asdict

from .base_agent import PaperAnalysis
from .arxiv_agent import ArXivAgent
from .pubmed_agent import PubMedAgent
from .biorxiv_agent import BioRxivAgent
from .semantic_scholar_agent import SemanticScholarAgent
from .openalex_agent import OpenAlexAgent


class SourceAgentOrchestrator:
    """
    Orchestrates source-specific agents for comprehensive paper analysis.

    Each agent has specialized knowledge for its source:
    - ArXivAgent: ML preprints, conference potential
    - PubMedAgent: Biomedical AI, clinical relevance
    - BioRxivAgent: Computational biology, life sciences ML
    - SemanticScholarAgent: Citation analysis, cross-domain
    - OpenAlexAgent: Comprehensive coverage, concept tagging
    """

    def __init__(self):
        self.agents = {
            "arxiv": ArXivAgent(),
            "semantic_scholar": SemanticScholarAgent(),
            "openalex": OpenAlexAgent(),
            "biorxiv": BioRxivAgent(),  # Also handles medrxiv
            "pubmed": PubMedAgent(),
        }
        self.analyses: List[PaperAnalysis] = []
        self.source_stats: Dict[str, Dict] = {}

    def analyze_all(self, papers: List[Dict]) -> Dict:
        """
        Run all agents on their respective papers.

        Args:
            papers: List of paper dicts with 'source' field

        Returns:
            Dict with analyses and statistics
        """
        print("\n=== SWARM Agent Analysis ===")
        print(f"Total papers: {len(papers)}")

        self.analyses = []
        self.source_stats = {}

        # Group papers by source
        by_source = {}
        for paper in papers:
            source = paper.get('source', 'unknown')
            if source not in by_source:
                by_source[source] = []
            by_source[source].append(paper)

        # Run each agent on its papers
        for source, agent in self.agents.items():
            source_papers = by_source.get(source, [])

            # BioRxivAgent handles both biorxiv and medrxiv
            if source == 'biorxiv':
                source_papers = by_source.get('biorxiv', []) + by_source.get('medrxiv', [])

            if not source_papers:
                self.source_stats[source] = {"papers": 0, "analyzed": 0, "avg_relevance": 0}
                continue

            # Run agent analysis
            agent_analyses = agent.analyze_batch(source_papers)
            self.analyses.extend(agent_analyses)

            # Compute stats
            if agent_analyses:
                avg_relevance = sum(a.relevance for a in agent_analyses) / len(agent_analyses)
                avg_novelty = sum(a.novelty for a in agent_analyses) / len(agent_analyses)
                avg_impact = sum(a.impact for a in agent_analyses) / len(agent_analyses)
            else:
                avg_relevance = avg_novelty = avg_impact = 0

            self.source_stats[source] = {
                "papers": len(source_papers),
                "analyzed": len(agent_analyses),
                "avg_relevance": round(avg_relevance, 2),
                "avg_novelty": round(avg_novelty, 2),
                "avg_impact": round(avg_impact, 2),
            }

        # Sort by combined score
        self.analyses.sort(
            key=lambda a: (a.relevance + a.novelty + a.impact) / 3,
            reverse=True
        )

        return self.get_report()

    def get_top_papers(self, n: int = 10) -> List[PaperAnalysis]:
        """Get top N papers by combined score."""
        return self.analyses[:n]

    def get_report(self) -> Dict:
        """Generate comprehensive analysis report."""
        total_analyzed = len(self.analyses)

        if total_analyzed == 0:
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "total_analyzed": 0,
                "source_stats": self.source_stats,
                "top_papers": [],
                "rsct_connections": [],
            }

        # Aggregate metrics
        avg_relevance = sum(a.relevance for a in self.analyses) / total_analyzed
        avg_novelty = sum(a.novelty for a in self.analyses) / total_analyzed
        avg_impact = sum(a.impact for a in self.analyses) / total_analyzed

        # Get top papers
        top_papers = [
            {
                "paper_id": a.paper_id,
                "title": a.paper_title,
                "source": a.source,
                "relevance": a.relevance,
                "novelty": a.novelty,
                "impact": a.impact,
                "summary": a.summary,
                "key_findings": a.key_findings,
                "rsct_connections": a.rsct_connections,
                "confidence": a.confidence,
            }
            for a in self.get_top_papers(10)
        ]

        # Collect all RSCT connections
        all_rsct = []
        for a in self.analyses:
            for conn in a.rsct_connections:
                all_rsct.append({
                    "paper": a.paper_title[:50],
                    "connection": conn,
                    "relevance": a.relevance,
                })

        # Sort RSCT connections by relevance
        all_rsct.sort(key=lambda x: x["relevance"], reverse=True)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_analyzed": total_analyzed,
            "avg_relevance": round(avg_relevance, 2),
            "avg_novelty": round(avg_novelty, 2),
            "avg_impact": round(avg_impact, 2),
            "source_stats": self.source_stats,
            "top_papers": top_papers,
            "rsct_connections": all_rsct[:20],  # Top 20 connections
        }

    def save_report(self, filepath: str) -> None:
        """Save report to JSON file."""
        report = self.get_report()
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"Report saved: {filepath}")

    def upload_to_s3(self, bucket: str, prefix: str = "analytics/agents") -> str:
        """Upload report to S3."""
        import boto3

        s3 = boto3.client("s3")
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        key = f"{prefix}/{today}-agents.json"

        report = self.get_report()

        try:
            s3.put_object(
                Bucket=bucket,
                Key=key,
                Body=json.dumps(report, indent=2, default=str),
                ContentType="application/json",
            )
            print(f"Uploaded: s3://{bucket}/{key}")
            return key
        except Exception as e:
            print(f"S3 upload error: {e}")
            return ""


def run_daily_agents(papers: List[Dict], s3_bucket: Optional[str] = None) -> Dict:
    """
    Run daily agent analysis pipeline.

    Args:
        papers: List of paper dicts from all sources
        s3_bucket: Optional S3 bucket for saving results

    Returns:
        Analysis report dict
    """
    orchestrator = SourceAgentOrchestrator()
    report = orchestrator.analyze_all(papers)

    # Print summary
    print("\n=== Agent Analysis Summary ===")
    print(f"Papers analyzed: {report['total_analyzed']}")
    print(f"Avg Relevance: {report.get('avg_relevance', 0):.1f}/10")
    print(f"Avg Novelty: {report.get('avg_novelty', 0):.1f}/10")
    print(f"Avg Impact: {report.get('avg_impact', 0):.1f}/10")

    print("\nBy Source:")
    for source, stats in report.get('source_stats', {}).items():
        if stats['papers'] > 0:
            print(f"  {source}: {stats['analyzed']}/{stats['papers']} analyzed, "
                  f"R:{stats['avg_relevance']}/N:{stats['avg_novelty']}/I:{stats['avg_impact']}")

    print("\nTop Papers:")
    for i, paper in enumerate(report.get('top_papers', [])[:5], 1):
        print(f"  {i}. [{paper['source']}] {paper['title'][:45]}...")
        print(f"     R:{paper['relevance']}/N:{paper['novelty']}/I:{paper['impact']} - {paper['summary'][:60]}...")

    # Upload to S3 if bucket provided
    if s3_bucket:
        orchestrator.upload_to_s3(s3_bucket)

    return report


# CLI entry point
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run SWARM source agents")
    parser.add_argument("--input", "-i", help="Input JSON file with papers")
    parser.add_argument("--output", "-o", help="Output JSON file for report")
    parser.add_argument("--s3-bucket", help="S3 bucket for upload")
    args = parser.parse_args()

    if args.input:
        with open(args.input) as f:
            papers = json.load(f)
        report = run_daily_agents(papers, args.s3_bucket)
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2)
    else:
        print("Usage: python -m agents.orchestrator -i papers.json -o report.json")
