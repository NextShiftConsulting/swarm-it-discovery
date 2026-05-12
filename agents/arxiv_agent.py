"""
ArXiv Agent - Specialized agent for arXiv preprints.

Expertise:
- CS.AI, CS.LG, CS.CL, CS.MA categories
- Preprint quality assessment
- Citation prediction for ML papers
- Connection to RSCT theory
"""

from typing import Dict
from .base_agent import BaseSourceAgent


class ArXivAgent(BaseSourceAgent):
    """Agent specialized for arXiv preprints."""

    SOURCE_NAME = "arxiv"
    AGENT_NAME = "ArXivAgent"

    EXPERTISE_PROMPT = """You are an expert ArXiv research analyst specializing in:
- Machine Learning (cs.LG)
- Artificial Intelligence (cs.AI)
- Computation and Language (cs.CL)
- Multi-Agent Systems (cs.MA)
- Statistical ML (stat.ML)

You understand:
- ArXiv submission patterns and quality indicators
- Citation dynamics for ML preprints
- How papers relate to RSCT (Representation-Solver Compatibility Theory)
- Key concepts: kappa metric, R/S/N decomposition, hallucination detection, multi-agent certification

When analyzing papers, consider:
1. Technical rigor and mathematical foundations
2. Novelty compared to existing arXiv submissions
3. Potential for conference acceptance (NeurIPS, ICML, ICLR, ACL)
4. Connections to safety, alignment, and multi-agent systems"""

    # High-impact arXiv categories
    HIGH_QUALITY_CATEGORIES = {
        "cs.LG": 10,   # Machine Learning
        "cs.AI": 9,    # Artificial Intelligence
        "cs.CL": 9,    # NLP
        "cs.MA": 8,    # Multi-Agent
        "stat.ML": 8,  # Statistical ML
        "cs.CV": 7,    # Computer Vision
        "cs.NE": 7,    # Neural/Evolutionary
    }

    def get_source_context(self, paper: Dict) -> str:
        """Get arXiv-specific context."""
        categories = paper.get('categories', [])
        arxiv_id = paper.get('id', '').replace('arxiv:', '')

        return f"""ArXiv Context:
- ArXiv ID: {arxiv_id}
- Primary categories: {', '.join(categories)}
- This is a preprint (not peer-reviewed)
- Evaluate based on technical quality and novelty
- Consider potential for top ML conference acceptance"""

    def extract_source_quality(self, paper: Dict) -> int:
        """Extract quality score based on arXiv categories."""
        categories = paper.get('categories', [])

        if not categories:
            return 5

        # Score based on best matching category
        max_score = 5
        for cat in categories:
            if cat in self.HIGH_QUALITY_CATEGORIES:
                max_score = max(max_score, self.HIGH_QUALITY_CATEGORIES[cat])

        return max_score

    def analyze_paper(self, paper: Dict) -> "PaperAnalysis":  # noqa: F821
        """Analyze an arXiv paper with additional arXiv-specific insights."""
        analysis = super().analyze_paper(paper)

        if analysis:
            # Add arXiv-specific metadata

            # Boost relevance for certain categories
            categories = paper.get('categories', [])
            if 'cs.MA' in categories or 'cs.AI' in categories:
                analysis.relevance = min(10, analysis.relevance + 1)

        return analysis
