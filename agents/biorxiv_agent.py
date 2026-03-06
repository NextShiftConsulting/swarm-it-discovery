"""
BioRxiv/MedRxiv Agent - Specialized agent for preprint servers.

Expertise:
- Computational biology and bioinformatics
- Medical preprints and COVID research
- Preprint-to-publication trajectory
- Life sciences ML applications
"""

from typing import Dict, List
from .base_agent import BaseSourceAgent


class BioRxivAgent(BaseSourceAgent):
    """Agent specialized for bioRxiv and medRxiv preprints."""

    SOURCE_NAME = "biorxiv"  # Also handles medrxiv
    AGENT_NAME = "BioRxivAgent"

    EXPERTISE_PROMPT = """You are an expert bioRxiv/medRxiv preprint analyst specializing in:
- Computational biology and bioinformatics
- Systems biology and network analysis
- Medical preprints and clinical studies
- Genomics, proteomics, and multi-omics ML
- Drug discovery and repurposing

You understand:
- Preprint quality indicators (not yet peer-reviewed)
- bioRxiv vs medRxiv scope differences
- Life sciences publication trajectories
- Computational methods in biology
- Connection to RSCT (Representation-Solver Compatibility Theory)

bioRxiv/medRxiv papers are:
- Preprints (not peer-reviewed)
- Often cutting-edge research
- May be revised before journal publication
- Quick dissemination of findings

When analyzing papers, consider:
1. Computational/ML methodology quality
2. Data availability and reproducibility
3. Potential for high-impact journal publication
4. Novel applications of AI/ML to life sciences
5. Connections to AI safety in biomedical contexts"""

    # Computational biology topics
    COMP_BIO_TOPICS = [
        "machine learning",
        "deep learning",
        "neural network",
        "prediction",
        "classification",
        "clustering",
        "sequence",
        "structure",
        "network",
        "algorithm",
    ]

    def get_source_context(self, paper: Dict) -> str:
        """Get bioRxiv/medRxiv-specific context."""
        source = paper.get('source', 'biorxiv')
        doi = paper.get('id', '').replace('biorxiv:', '').replace('medrxiv:', '')
        category = paper.get('categories', ['Unknown'])[0] if paper.get('categories') else 'Unknown'

        server = "medRxiv (medical preprints)" if source == "medrxiv" else "bioRxiv (biology preprints)"

        return f"""BioRxiv/MedRxiv Context:
- Server: {server}
- DOI: {doi}
- Category: {category}
- This is a PREPRINT (not peer-reviewed)
- Evaluate computational methodology and reproducibility
- Consider potential for journal acceptance"""

    def extract_source_quality(self, paper: Dict) -> int:
        """Extract quality score based on preprint indicators."""
        title = paper.get('title', '').lower()
        abstract = paper.get('abstract', '').lower()
        text = f"{title} {abstract}"

        # Base score for preprint
        score = 6

        # Boost for computational topics
        topic_matches = sum(1 for topic in self.COMP_BIO_TOPICS if topic in text)
        score = min(10, score + min(topic_matches, 3))

        # Boost for medRxiv (clinical relevance)
        if paper.get('source') == 'medrxiv':
            score = min(10, score + 1)

        return score

    def analyze_batch(self, papers: List[Dict]) -> List["PaperAnalysis"]:
        """Analyze papers from both bioRxiv and medRxiv."""
        results = []

        # Handle both sources
        source_papers = [p for p in papers if p.get('source') in ['biorxiv', 'medrxiv']]

        print(f"  {self.AGENT_NAME}: Analyzing {len(source_papers)} papers (bioRxiv + medRxiv)...")

        for paper in source_papers:
            analysis = self.analyze_paper(paper)
            if analysis:
                results.append(analysis)
                print(f"    [{paper.get('source')}] {paper.get('title', '')[:35]}... R:{analysis.relevance}/N:{analysis.novelty}/I:{analysis.impact}")

        return results
