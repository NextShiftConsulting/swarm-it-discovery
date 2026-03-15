"""
Analyzer Agent - Scores and analyzes papers using RSCT and topic matching.

Uses swarm-it-auth for credentials and MiMoClient for LLM calls.
Coordinates source-specific agents for deep analysis.
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

# Add swarm-it repos to path
sys.path.insert(0, str(Path.home() / "GitHub" / "swarm-it-auth"))
sys.path.insert(0, str(Path.home() / "GitHub" / "swarm-it-adk" / "adk"))

# Import from swarm-it-auth
try:
    from swarm_auth.adapters import MiMoClient
    HAS_MIMO = True
except ImportError:
    HAS_MIMO = False

# Import pipeline components
sys.path.insert(0, str(Path(__file__).parent.parent / "pipeline"))
try:
    from analyzer.matcher import SimilarityMatcher
    from analyzer.rsct_scorer import RSCTScorer
    HAS_PIPELINE = True
except ImportError:
    HAS_PIPELINE = False


@dataclass
class AnalysisResult:
    """Result from analyzing papers."""
    paper_id: str
    title: str
    source: str

    # Scores
    topic_score: float  # 0-1, relevance to topics
    rsct_score: float   # 0-1, RSCT quality
    combined_score: float

    # Analysis
    summary: str
    key_findings: List[str]
    rsct_connections: List[str]

    # Metadata
    analyzed_at: str
    cost: float = 0.0


@dataclass
class BatchAnalysisResult:
    """Result from analyzing multiple papers."""
    analyses: List[AnalysisResult]
    total_count: int
    passed_count: int  # Papers above threshold
    analysis_time: float
    total_cost: float
    errors: List[str] = field(default_factory=list)


class AnalyzerAgent:
    """
    Agent for analyzing and scoring papers.

    Analysis includes:
    - Topic matching (relevance to research interests)
    - RSCT scoring (quality assessment)
    - LLM analysis (summary, key findings, connections)

    Usage:
        agent = AnalyzerAgent()
        result = agent.analyze(papers, min_score=0.5)
        for a in result.analyses:
            print(f"{a.title}: {a.combined_score:.2f}")
    """

    def __init__(
        self,
        min_topic_score: float = 0.5,
        min_rsct_score: float = 0.3,
        use_mimo: bool = True,
    ):
        """
        Initialize analyzer agent.

        Args:
            min_topic_score: Minimum topic relevance (0-1)
            min_rsct_score: Minimum RSCT score (0-1)
            use_mimo: Use MiMoClient for LLM (cost-effective)
        """
        self.min_topic_score = min_topic_score
        self.min_rsct_score = min_rsct_score
        self.use_mimo = use_mimo

        self._llm = None
        self._matcher = None
        self._scorer = None

        self._init_components()

    def _init_components(self):
        """Initialize analysis components."""
        # LLM client
        if self.use_mimo and HAS_MIMO:
            try:
                self._llm = MiMoClient()
                print("✓ AnalyzerAgent: MiMoClient initialized")
            except Exception as e:
                print(f"✗ AnalyzerAgent: MiMoClient failed: {e}")

        # Topic matcher
        if HAS_PIPELINE:
            try:
                self._matcher = SimilarityMatcher()
                print("✓ AnalyzerAgent: SimilarityMatcher initialized")
            except Exception as e:
                print(f"✗ AnalyzerAgent: SimilarityMatcher failed: {e}")

            try:
                self._scorer = RSCTScorer()
                print("✓ AnalyzerAgent: RSCTScorer initialized")
            except Exception as e:
                print(f"✗ AnalyzerAgent: RSCTScorer failed: {e}")

    def analyze_paper(self, paper: Dict) -> Optional[AnalysisResult]:
        """
        Analyze a single paper.

        Args:
            paper: Paper dict with title, abstract, source

        Returns:
            AnalysisResult or None if below threshold
        """
        title = paper.get('title', 'Unknown')
        abstract = paper.get('abstract', '')[:1500]
        source = paper.get('source', 'unknown')
        paper_id = paper.get('id', '')

        # Topic scoring
        topic_score = 0.5
        if self._matcher:
            try:
                match = self._matcher.match(title + " " + abstract)
                topic_score = match.score if hasattr(match, 'score') else 0.5
            except Exception:
                pass

        # RSCT scoring
        rsct_score = 0.5
        if self._scorer:
            try:
                score = self._scorer.score(title + " " + abstract)
                rsct_score = score.overall if hasattr(score, 'overall') else 0.5
            except Exception:
                pass

        # Combined score
        combined_score = (topic_score * 0.6) + (rsct_score * 0.4)

        # Check thresholds
        if topic_score < self.min_topic_score:
            return None

        # LLM analysis
        summary = ""
        key_findings = []
        rsct_connections = []
        cost = 0.0

        if self._llm:
            try:
                analysis = self._llm.analyze_paper(title, abstract)
                summary = analysis.get('summary', '')
                key_findings = analysis.get('key_findings', [])
                rsct_connections = analysis.get('rsct_connections', [])
                # Cost tracked in MiMoClient
            except Exception as e:
                summary = f"Analysis failed: {e}"

        return AnalysisResult(
            paper_id=paper_id,
            title=title,
            source=source,
            topic_score=topic_score,
            rsct_score=rsct_score,
            combined_score=combined_score,
            summary=summary,
            key_findings=key_findings,
            rsct_connections=rsct_connections,
            analyzed_at=datetime.utcnow().isoformat(),
            cost=cost,
        )

    def analyze(
        self,
        papers: List[Dict],
        max_papers: Optional[int] = None,
    ) -> BatchAnalysisResult:
        """
        Analyze multiple papers.

        Args:
            papers: List of paper dicts
            max_papers: Max papers to analyze (default: all)

        Returns:
            BatchAnalysisResult with all analyses
        """
        print(f"\n=== AnalyzerAgent: Analyzing {len(papers)} papers ===")
        start_time = datetime.utcnow()

        analyses = []
        errors = []
        total_cost = 0.0

        papers_to_analyze = papers[:max_papers] if max_papers else papers

        for i, paper in enumerate(papers_to_analyze):
            try:
                result = self.analyze_paper(paper)
                if result:
                    analyses.append(result)
                    total_cost += result.cost
                    print(f"  [{i+1}/{len(papers_to_analyze)}] {result.title[:50]}... score={result.combined_score:.2f}")
            except Exception as e:
                errors.append(f"Paper {paper.get('id', i)}: {e}")

        # Sort by combined score
        analyses.sort(key=lambda a: a.combined_score, reverse=True)

        analysis_time = (datetime.utcnow() - start_time).total_seconds()

        print(f"\n✓ Analysis complete in {analysis_time:.1f}s")
        print(f"  Analyzed: {len(analyses)}/{len(papers_to_analyze)}")
        print(f"  Total cost: ${total_cost:.4f}")

        return BatchAnalysisResult(
            analyses=analyses,
            total_count=len(papers_to_analyze),
            passed_count=len(analyses),
            analysis_time=analysis_time,
            total_cost=total_cost,
            errors=errors,
        )

    def __repr__(self) -> str:
        return f"AnalyzerAgent(min_topic={self.min_topic_score}, min_rsct={self.min_rsct_score})"


# CLI entry point
if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Analyze papers")
    parser.add_argument("--input", "-i", required=True, help="Input JSON file with papers")
    parser.add_argument("--output", "-o", help="Output JSON file")
    parser.add_argument("--max", type=int, help="Max papers to analyze")
    parser.add_argument("--min-topic", type=float, default=0.5, help="Min topic score")
    parser.add_argument("--min-rsct", type=float, default=0.3, help="Min RSCT score")
    args = parser.parse_args()

    with open(args.input) as f:
        data = json.load(f)
        papers = data.get('papers', data) if isinstance(data, dict) else data

    agent = AnalyzerAgent(
        min_topic_score=args.min_topic,
        min_rsct_score=args.min_rsct,
    )
    result = agent.analyze(papers, max_papers=args.max)

    if args.output:
        with open(args.output, 'w') as f:
            json.dump({
                "analyses": [a.__dict__ for a in result.analyses],
                "total_count": result.total_count,
                "passed_count": result.passed_count,
                "analysis_time": result.analysis_time,
                "total_cost": result.total_cost,
            }, f, indent=2, default=str)
        print(f"\nSaved to {args.output}")
