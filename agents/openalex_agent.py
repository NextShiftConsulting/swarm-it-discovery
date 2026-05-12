"""
OpenAlex Agent - Specialized agent for OpenAlex papers.

Expertise:
- Comprehensive academic coverage
- Concept-based paper discovery
- Institution and funding analysis
- Cross-disciplinary research
"""

from typing import Dict
from .base_agent import BaseSourceAgent


class OpenAlexAgent(BaseSourceAgent):
    """Agent specialized for OpenAlex papers."""

    SOURCE_NAME = "openalex"
    AGENT_NAME = "OpenAlexAgent"

    EXPERTISE_PROMPT = """You are an expert OpenAlex research analyst specializing in:
- Comprehensive academic paper analysis
- Concept-based knowledge graphs
- Institution and funding patterns
- Cross-disciplinary research identification
- Open access and data availability

You understand:
- OpenAlex concept tagging system
- Academic institution rankings and output
- Funding agency patterns
- Open access status implications
- Connection to RSCT (Representation-Solver Compatibility Theory)

OpenAlex provides:
- Comprehensive coverage across disciplines
- Concept-based paper tagging
- Institution affiliations
- Open access status
- Citation relationships

When analyzing papers, consider:
1. Concept alignment with AI/ML research
2. Institution credibility and track record
3. Cross-disciplinary potential
4. Open access and reproducibility
5. Connections to safety, alignment, and multi-agent systems"""

    # OpenAlex concept IDs for AI/ML
    AI_CONCEPTS = [
        "Machine Learning",
        "Artificial Intelligence",
        "Deep Learning",
        "Neural Network",
        "Natural Language Processing",
        "Computer Vision",
        "Reinforcement Learning",
    ]

    def get_source_context(self, paper: Dict) -> str:
        """Get OpenAlex-specific context."""
        oa_id = paper.get('id', '').replace('openalex:', '')
        concepts = paper.get('categories', [])[:5]

        return f"""OpenAlex Context:
- OpenAlex ID: {oa_id}
- Concepts: {', '.join(concepts) if concepts else 'Unknown'}
- OpenAlex provides comprehensive academic coverage
- Concepts are AI-tagged from knowledge graph
- Consider cross-disciplinary applications"""

    def extract_source_quality(self, paper: Dict) -> int:
        """Extract quality score based on OpenAlex indicators."""
        concepts = paper.get('categories', [])

        # Base score
        score = 6

        # Boost for AI/ML concepts
        ai_matches = sum(1 for concept in concepts if any(ai in concept for ai in self.AI_CONCEPTS))
        score = min(10, score + min(ai_matches * 2, 4))

        return score

    def analyze_paper(self, paper: Dict) -> "PaperAnalysis":  # noqa: F821
        """Analyze an OpenAlex paper with concept-focused insights."""
        analysis = super().analyze_paper(paper)

        if analysis:
            # Add concept-based insights
            concepts = paper.get('categories', [])

            # Boost for multi-disciplinary
            if len(concepts) >= 3:
                analysis.novelty = min(10, analysis.novelty + 1)

        return analysis
