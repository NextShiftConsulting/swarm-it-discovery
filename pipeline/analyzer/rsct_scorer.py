"""
RSCT Relevance Scorer - Compare papers against base RSCT whitepaper.

Computes semantic similarity between discovered papers and the RSCT
theory paper to identify papers most relevant to our research.
"""

import os
from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass

# Optional: OpenAI for embeddings
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


@dataclass
class RSCTScore:
    """RSCT relevance score for a paper."""
    paper_id: str
    paper_title: str
    rsct_similarity: float  # 0-1, similarity to RSCT whitepaper
    topic_similarity: float  # Original topic match score
    combined_score: float  # Weighted combination
    key_overlaps: List[str]  # Key concepts that overlap


class RSCTScorer:
    """Score papers by relevance to RSCT theory."""

    # Key RSCT concepts to look for
    RSCT_CONCEPTS = [
        "representation", "solver", "compatibility", "kappa",
        "noise", "spurious", "relevance", "decomposition",
        "simplex", "certification", "multi-agent", "swarm",
        "hallucination", "alignment", "safety", "constraint",
    ]

    def __init__(
        self,
        whitepaper_path: str = None,
        embed_model: str = "text-embedding-3-small",
    ):
        self.embed_model = embed_model

        # Load whitepaper
        if whitepaper_path is None:
            whitepaper_path = os.path.expanduser(
                "~/GitHub/yrsn/docs/primary/RSCT_PRIMARY_WHITEPAPER.tex"
            )

        self.whitepaper_text = self._load_whitepaper(whitepaper_path)
        self.whitepaper_embedding = None

        if HAS_OPENAI and os.getenv("OPENAI_API_KEY"):
            self.openai = OpenAI()
            self._compute_whitepaper_embedding()
        else:
            self.openai = None
            print("Warning: OpenAI not configured, using keyword matching only")

    def _load_whitepaper(self, path: str) -> str:
        """Load and clean whitepaper text."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()

            # Remove LaTeX commands but keep text
            import re
            text = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', text)
            text = re.sub(r'\\[a-zA-Z]+', '', text)
            text = re.sub(r'[{}]', '', text)
            text = re.sub(r'\s+', ' ', text)

            return text[:8000]  # Limit for embedding
        except Exception as e:
            print(f"Error loading whitepaper: {e}")
            return ""

    def _compute_whitepaper_embedding(self):
        """Compute embedding for whitepaper."""
        if not self.openai or not self.whitepaper_text:
            return

        try:
            response = self.openai.embeddings.create(
                input=self.whitepaper_text,
                model=self.embed_model,
            )
            self.whitepaper_embedding = response.data[0].embedding
        except Exception as e:
            print(f"Error computing whitepaper embedding: {e}")

    def _embed(self, text: str) -> Optional[List[float]]:
        """Get embedding for text."""
        if not self.openai:
            return None

        try:
            response = self.openai.embeddings.create(
                input=text[:8000],
                model=self.embed_model,
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Embedding error: {e}")
            return None

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Compute cosine similarity."""
        import math
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def _keyword_score(self, text: str) -> Tuple[float, List[str]]:
        """Score by RSCT keyword overlap."""
        text_lower = text.lower()
        matches = [c for c in self.RSCT_CONCEPTS if c in text_lower]
        score = len(matches) / len(self.RSCT_CONCEPTS)
        return score, matches

    def score_paper(
        self,
        paper_id: str,
        title: str,
        abstract: str,
        topic_similarity: float = 0.0,
    ) -> RSCTScore:
        """Score a paper's relevance to RSCT."""
        text = f"{title} {abstract}"

        # Keyword matching
        keyword_score, key_overlaps = self._keyword_score(text)

        # Embedding similarity
        if self.whitepaper_embedding:
            paper_embedding = self._embed(text)
            if paper_embedding:
                embed_score = self._cosine_similarity(
                    paper_embedding, self.whitepaper_embedding
                )
            else:
                embed_score = keyword_score
        else:
            embed_score = keyword_score

        # Combined score (weighted average)
        rsct_similarity = 0.7 * embed_score + 0.3 * keyword_score
        combined_score = 0.6 * rsct_similarity + 0.4 * topic_similarity

        return RSCTScore(
            paper_id=paper_id,
            paper_title=title,
            rsct_similarity=rsct_similarity,
            topic_similarity=topic_similarity,
            combined_score=combined_score,
            key_overlaps=key_overlaps,
        )

    def rank_papers(
        self,
        papers: List[dict],
        min_rsct_score: float = 0.3,
    ) -> List[RSCTScore]:
        """Rank papers by RSCT relevance."""
        scores = []
        for p in papers:
            score = self.score_paper(
                paper_id=p.get('id', ''),
                title=p.get('title', ''),
                abstract=p.get('abstract', ''),
                topic_similarity=p.get('similarity_score', 0.0),
            )
            if score.rsct_similarity >= min_rsct_score:
                scores.append(score)

        # Sort by combined score descending
        scores.sort(key=lambda x: x.combined_score, reverse=True)
        return scores
