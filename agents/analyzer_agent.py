"""
Analyzer Agent - Scores and analyzes papers using RSCT and topic matching.

Uses swarm-it-auth for credentials and MiMoClient for LLM calls.
Coordinates source-specific agents for deep analysis.
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone

# Add swarm-it repos to path
sys.path.insert(0, str(Path.home() / "github" / "yrsn" / "src"))
sys.path.insert(0, str(Path.home() / "github" / "swarm-it-adk" / "adk"))

# Import MIMOClient from yrsn SERG module
try:
    from yrsn.framework.api.serg.mimo_swarm import MIMOClient as MiMoClient
    HAS_MIMO = True
except ImportError:
    # Fallback: try swarm-it-adk provider
    try:
        from swarm_it.providers.mimo import MIMOProvider as MiMoClient
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


class MiMoClientWrapper:
    """Wrapper to adapt MIMOClient to expected analyze_paper interface."""

    # Key file locations (check both repos)
    KEY_PATHS = [
        Path.home() / "github" / "swarm-it-auth" / "keys" / "4-openrouter.md",
        Path.home() / "github" / "yrsn" / "keys" / "4-openrouter.md",
        Path.home() / "github" / "yrsn" / "keys" / "xiao_nsc_20260217.txt",
    ]

    def __init__(self):
        """Initialize with OpenRouter or direct MiMo client."""
        self._client = None
        self._api_key = None
        self._base_url = None
        self._model = None

        # Try to load API key from files
        self._load_credentials()

        # Initialize OpenAI-compatible client
        if self._api_key:
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self._api_key,
                    base_url=self._base_url
                )
                print(f"[OK] MiMoClientWrapper: Using {self._base_url} with model {self._model}")
            except Exception as e:
                print(f"[FAIL] MiMoClientWrapper: OpenAI client init failed: {e}")

    def _load_credentials(self):
        """Load API credentials from key files."""
        for key_path in self.KEY_PATHS:
            if key_path.exists():
                try:
                    content = key_path.read_text().strip()

                    # OpenRouter key file format: api_key="sk-or-..."
                    if "openrouter" in str(key_path).lower():
                        import re
                        match = re.search(r'api_key="([^"]+)"', content)
                        if match:
                            self._api_key = match.group(1)
                            self._base_url = "https://openrouter.ai/api/v1"
                            self._model = "xiaomi/mimo-v2-flash"  # Fast, cost-effective
                            return

                    # Direct Xiaomi key file format: sk-...
                    if "xiao" in str(key_path).lower():
                        lines = content.split('\n')
                        for line in lines:
                            if line.startswith('sk-'):
                                self._api_key = line.strip()
                                self._base_url = "https://api.xiaomimimo.com/v1"
                                self._model = "mimo-v2-flash"
                                return
                except Exception as e:
                    print(f"[FAIL] Failed to read {key_path}: {e}")

    def analyze_paper(self, title: str, abstract: str) -> Dict[str, Any]:
        """
        Analyze a paper using MIMO LLM via OpenRouter or direct API.

        Args:
            title: Paper title
            abstract: Paper abstract

        Returns:
            Dict with summary, key_findings, rsct_connections
        """
        if self._client is None:
            return {"summary": "MIMO client not available", "key_findings": [], "rsct_connections": []}

        prompt = f"""Analyze this academic paper and provide:
1. A brief summary (2-3 sentences)
2. Key findings (3-5 bullet points)
3. Connections to RSCT theory (Representation-Solver Compatibility Theory)

Title: {title}

Abstract: {abstract}

Respond in JSON format:
{{"summary": "...", "key_findings": ["...", "..."], "rsct_connections": ["...", "..."]}}"""

        try:
            # Use OpenAI-compatible chat completion
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1024,
            )

            content = response.choices[0].message.content

            # Parse JSON from response
            import json
            try:
                # Find JSON in response
                start = content.find('{')
                end = content.rfind('}') + 1
                if start >= 0 and end > start:
                    return json.loads(content[start:end])
            except json.JSONDecodeError:
                pass

            return {"summary": content[:500], "key_findings": [], "rsct_connections": []}

        except Exception as e:
            return {"summary": f"Analysis error: {e}", "key_findings": [], "rsct_connections": []}


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
        # LLM client (using wrapper for analyze_paper interface)
        if self.use_mimo and HAS_MIMO:
            try:
                self._llm = MiMoClientWrapper()
                print("[OK] AnalyzerAgent: MiMoClientWrapper initialized")
            except Exception as e:
                print(f"[FAIL] AnalyzerAgent: MiMoClientWrapper failed: {e}")

        # Topic matcher
        if HAS_PIPELINE:
            try:
                self._matcher = SimilarityMatcher()
                print("[OK] AnalyzerAgent: SimilarityMatcher initialized")
            except Exception as e:
                print(f"[FAIL] AnalyzerAgent: SimilarityMatcher failed: {e}")

            try:
                self._scorer = RSCTScorer()
                print("[OK] AnalyzerAgent: RSCTScorer initialized")
            except Exception as e:
                print(f"[FAIL] AnalyzerAgent: RSCTScorer failed: {e}")

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
            analyzed_at=datetime.now(timezone.utc).isoformat(),
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
        start_time = datetime.now(timezone.utc)

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

        analysis_time = (datetime.now(timezone.utc) - start_time).total_seconds()

        print(f"\n[OK] Analysis complete in {analysis_time:.1f}s")
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
