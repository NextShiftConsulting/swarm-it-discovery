"""
Base Source Agent - Abstract base for all source-specific agents.
"""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class PaperAnalysis:
    """Analysis result from a source agent."""
    paper_id: str
    paper_title: str
    source: str

    # Core scores (0-10)
    relevance: int  # How relevant to RSCT/AI safety
    novelty: int    # How novel the approach
    impact: int     # Potential research impact

    # Source-specific scores
    source_quality: int  # Quality indicators from this source
    citation_potential: int  # Expected citation impact

    # Analysis text
    summary: str
    key_findings: List[str]
    rsct_connections: List[str]  # How it connects to RSCT
    suggested_citations: List[str]

    # Metadata
    analyzed_at: str
    agent_name: str
    confidence: float  # 0-1, agent's confidence in analysis


class BaseSourceAgent(ABC):
    """Abstract base class for source-specific agents."""

    SOURCE_NAME: str = "base"
    AGENT_NAME: str = "BaseAgent"

    # Source-specific expertise prompt
    EXPERTISE_PROMPT: str = """You are a research paper analysis agent."""

    def __init__(self):
        self.openai = None
        self._init_client()

    def _init_client(self):
        """Initialize OpenAI client."""
        try:
            from openai import OpenAI
            if os.getenv("OPENAI_API_KEY"):
                self.openai = OpenAI()
        except ImportError:
            pass

    @abstractmethod
    def get_source_context(self, paper: Dict) -> str:
        """Get source-specific context for analysis."""
        pass

    @abstractmethod
    def extract_source_quality(self, paper: Dict) -> int:
        """Extract quality indicators specific to this source."""
        pass

    def analyze_paper(self, paper: Dict) -> Optional[PaperAnalysis]:
        """Analyze a paper using this agent's expertise."""
        if not self.openai:
            return None

        source_context = self.get_source_context(paper)
        source_quality = self.extract_source_quality(paper)

        prompt = f"""{self.EXPERTISE_PROMPT}

{source_context}

Analyze this paper:
Title: {paper.get('title', 'Unknown')}
Abstract: {paper.get('abstract', '')[:1500]}
Categories: {', '.join(paper.get('categories', []))}

Provide analysis in JSON format:
{{
    "relevance": <0-10, relevance to RSCT/AI safety/multi-agent systems>,
    "novelty": <0-10, how novel is the approach>,
    "impact": <0-10, potential research impact>,
    "citation_potential": <0-10, expected citation impact>,
    "summary": "<2-3 sentence summary>",
    "key_findings": ["finding1", "finding2", "finding3"],
    "rsct_connections": ["connection to RSCT theory 1", "connection 2"],
    "suggested_citations": ["paper1 to cite", "paper2 to cite"],
    "confidence": <0-1, your confidence in this analysis>
}}"""

        try:
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                response_format={"type": "json_object"},
            )

            import json
            result = json.loads(response.choices[0].message.content)

            return PaperAnalysis(
                paper_id=paper.get('id', ''),
                paper_title=paper.get('title', ''),
                source=self.SOURCE_NAME,
                relevance=result.get('relevance', 5),
                novelty=result.get('novelty', 5),
                impact=result.get('impact', 5),
                source_quality=source_quality,
                citation_potential=result.get('citation_potential', 5),
                summary=result.get('summary', ''),
                key_findings=result.get('key_findings', []),
                rsct_connections=result.get('rsct_connections', []),
                suggested_citations=result.get('suggested_citations', []),
                analyzed_at=datetime.utcnow().isoformat(),
                agent_name=self.AGENT_NAME,
                confidence=result.get('confidence', 0.5),
            )
        except Exception as e:
            print(f"  {self.AGENT_NAME} error: {e}")
            return None

    def analyze_batch(self, papers: List[Dict]) -> List[PaperAnalysis]:
        """Analyze multiple papers from this source."""
        results = []
        source_papers = [p for p in papers if p.get('source') == self.SOURCE_NAME]

        print(f"  {self.AGENT_NAME}: Analyzing {len(source_papers)} papers...")

        for paper in source_papers:
            analysis = self.analyze_paper(paper)
            if analysis:
                results.append(analysis)
                print(f"    {paper.get('title', '')[:40]}... R:{analysis.relevance}/N:{analysis.novelty}/I:{analysis.impact}")

        return results
