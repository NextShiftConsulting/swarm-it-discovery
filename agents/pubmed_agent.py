"""
PubMed Agent - Specialized agent for PubMed/NCBI papers.

Expertise:
- Biomedical AI and ML applications
- Clinical relevance assessment
- MeSH term analysis
- FDA/regulatory implications
"""

from typing import Dict
from .base_agent import BaseSourceAgent


class PubMedAgent(BaseSourceAgent):
    """Agent specialized for PubMed/NCBI papers."""

    SOURCE_NAME = "pubmed"
    AGENT_NAME = "PubMedAgent"

    EXPERTISE_PROMPT = """You are an expert PubMed/biomedical research analyst specializing in:
- AI/ML applications in medicine and healthcare
- Clinical decision support systems
- Medical imaging AI
- Drug discovery ML
- Biomedical NLP

You understand:
- PubMed indexing and MeSH terms
- Clinical trial phases and evidence levels
- FDA approval implications for AI/ML tools
- HIPAA and medical data privacy
- Connection to RSCT (Representation-Solver Compatibility Theory)

PubMed papers are:
- Peer-reviewed in medical journals
- Often have clinical validation
- Subject to medical ethics review
- May have regulatory implications

When analyzing papers, consider:
1. Clinical applicability and patient impact
2. Regulatory pathway (FDA, CE marking)
3. Evidence level (RCT, cohort, case study)
4. Safety implications for medical AI
5. Connections to AI safety and alignment in healthcare"""

    # High-impact medical AI topics
    HIGH_IMPACT_TOPICS = [
        "machine learning",
        "deep learning",
        "artificial intelligence",
        "neural network",
        "clinical decision",
        "medical imaging",
        "drug discovery",
        "diagnosis",
        "prognosis",
    ]

    def get_source_context(self, paper: Dict) -> str:
        """Get PubMed-specific context."""
        pmid = paper.get('id', '').replace('pubmed:', '')
        pub_date = paper.get('published_date', 'Unknown')

        return f"""PubMed Context:
- PMID: {pmid}
- Published: {pub_date}
- This is a peer-reviewed biomedical publication
- Indexed in MEDLINE/PubMed database
- Consider clinical relevance and regulatory implications
- Evaluate evidence quality and patient safety aspects"""

    def extract_source_quality(self, paper: Dict) -> int:
        """Extract quality score based on PubMed indicators."""
        title = paper.get('title', '').lower()
        abstract = paper.get('abstract', '').lower()
        text = f"{title} {abstract}"

        # Base score for peer-reviewed
        score = 7

        # Boost for AI/ML topics
        topic_matches = sum(1 for topic in self.HIGH_IMPACT_TOPICS if topic in text)
        score = min(10, score + min(topic_matches, 3))

        return score

    def analyze_paper(self, paper: Dict) -> "PaperAnalysis":  # noqa: F821
        """Analyze a PubMed paper with biomedical-focused insights."""
        analysis = super().analyze_paper(paper)

        if analysis:
            # Add clinical relevance context
            abstract = paper.get('abstract', '').lower()

            # Boost impact for clinical studies
            if 'clinical trial' in abstract or 'patient' in abstract:
                analysis.impact = min(10, analysis.impact + 1)

            # Boost relevance for AI safety in healthcare
            if 'safety' in abstract or 'adverse' in abstract:
                analysis.relevance = min(10, analysis.relevance + 1)

        return analysis
