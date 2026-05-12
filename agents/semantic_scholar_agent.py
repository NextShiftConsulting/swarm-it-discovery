"""
Semantic Scholar Agent - Specialized agent for Semantic Scholar papers.

Expertise:
- Citation analysis and impact prediction
- Influential citations vs regular citations
- Author impact (h-index, publication history)
- Cross-domain paper discovery
"""

from typing import Dict
from .base_agent import BaseSourceAgent


class SemanticScholarAgent(BaseSourceAgent):
    """Agent specialized for Semantic Scholar papers."""

    SOURCE_NAME = "semantic_scholar"
    AGENT_NAME = "SemanticScholarAgent"

    EXPERTISE_PROMPT = """You are an expert Semantic Scholar research analyst specializing in:
- Citation network analysis
- Influential vs incidental citations
- Author impact assessment
- Cross-domain paper discovery
- Identifying highly-cited potential papers

You understand:
- Semantic Scholar's citation velocity metrics
- How to identify papers likely to become influential
- The difference between breadth citations and depth citations
- Connection to RSCT (Representation-Solver Compatibility Theory)

Semantic Scholar provides:
- Highly influential citations count
- Citation velocity (citations per year)
- Author productivity metrics
- Related paper recommendations

When analyzing papers, consider:
1. Citation potential based on topic and authors
2. Cross-domain applicability
3. Whether this extends or challenges existing work
4. Connections to safety, alignment, and multi-agent systems"""

    # Fields of study quality weights
    FIELD_QUALITY = {
        "Computer Science": 9,
        "Artificial Intelligence": 10,
        "Machine Learning": 10,
        "Natural Language Processing": 9,
        "Mathematics": 8,
        "Statistics": 8,
        "Engineering": 7,
    }

    def get_source_context(self, paper: Dict) -> str:
        """Get Semantic Scholar-specific context."""
        fields = paper.get('categories', [])  # fieldsOfStudy
        s2_id = paper.get('id', '').replace('s2:', '')

        # Check for citation data if available
        citations = paper.get('citation_count', 'unknown')
        influential = paper.get('influential_citations', 'unknown')

        return f"""Semantic Scholar Context:
- S2 Paper ID: {s2_id}
- Fields of Study: {', '.join(fields) if fields else 'Unknown'}
- Citation Count: {citations}
- Influential Citations: {influential}
- This paper was indexed by Semantic Scholar's AI-powered system
- Consider cross-domain impact and citation velocity potential"""

    def extract_source_quality(self, paper: Dict) -> int:
        """Extract quality score based on fields and citations."""
        fields = paper.get('categories', [])

        base_score = 5
        for field in fields:
            if field in self.FIELD_QUALITY:
                base_score = max(base_score, self.FIELD_QUALITY[field])

        # Boost for papers with citation data
        if paper.get('citation_count', 0) > 10:
            base_score = min(10, base_score + 1)

        return base_score

    def analyze_paper(self, paper: Dict) -> "PaperAnalysis":  # noqa: F821
        """Analyze a Semantic Scholar paper with citation-focused insights."""
        analysis = super().analyze_paper(paper)

        if analysis:
            # Add citation prediction insights
            fields = paper.get('categories', [])
            if 'Artificial Intelligence' in fields or 'Machine Learning' in fields:
                analysis.citation_potential = min(10, analysis.citation_potential + 1)

        return analysis
