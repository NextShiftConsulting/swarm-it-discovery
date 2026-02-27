"""
Similarity Matcher - Match papers against topic PDFs using embeddings.
"""

import os
import json
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import numpy as np

# Optional: sentence-transformers for local embeddings
try:
    from sentence_transformers import SentenceTransformer
    HAS_SBERT = True
except ImportError:
    HAS_SBERT = False

# Optional: OpenAI for embeddings
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


@dataclass
class TopicDocument:
    """A topic document (from your curated PDFs)."""
    id: str
    title: str
    content: str
    embedding: Optional[np.ndarray] = None
    keywords: List[str] = None


@dataclass
class MatchResult:
    """Result of matching a paper against topics."""
    paper_id: str
    paper_title: str
    similarity_score: float
    matched_topics: List[str]
    top_keywords: List[str]
    explanation: str


class SimilarityMatcher:
    """Match papers against topic documents using semantic similarity."""

    def __init__(
        self,
        topics_dir: str = "content/topics",
        model_name: str = "all-MiniLM-L6-v2",
        threshold: float = 0.6,
    ):
        self.topics_dir = Path(topics_dir)
        self.threshold = threshold
        self.topics: List[TopicDocument] = []
        self.topic_embeddings: Optional[np.ndarray] = None

        # Initialize embedding model
        if HAS_OPENAI and os.getenv("OPENAI_API_KEY"):
            self.embed_mode = "openai"
            self.openai = OpenAI()
        elif HAS_SBERT:
            self.embed_mode = "sbert"
            self.model = SentenceTransformer(model_name)
        else:
            self.embed_mode = "keyword"
            print("Warning: No embedding model available, using keyword matching")

    def load_topics(self) -> None:
        """Load topic documents from JSON or extracted PDFs."""
        topics_file = self.topics_dir / "topics.json"

        if topics_file.exists():
            with open(topics_file) as f:
                data = json.load(f)

            for item in data.get("topics", []):
                self.topics.append(TopicDocument(
                    id=item["id"],
                    title=item["title"],
                    content=item["content"],
                    keywords=item.get("keywords", []),
                ))
        else:
            # Load from individual files
            for f in self.topics_dir.glob("*.txt"):
                content = f.read_text()
                self.topics.append(TopicDocument(
                    id=f.stem,
                    title=f.stem.replace("_", " ").title(),
                    content=content,
                ))

        if self.topics:
            self._compute_topic_embeddings()

    def _compute_topic_embeddings(self) -> None:
        """Compute embeddings for all topics."""
        if not self.topics:
            return

        texts = [f"{t.title}\n{t.content[:2000]}" for t in self.topics]
        embeddings = self._embed(texts)

        if embeddings is not None:
            self.topic_embeddings = embeddings
            for i, topic in enumerate(self.topics):
                topic.embedding = embeddings[i]

    def _embed(self, texts: List[str]) -> Optional[np.ndarray]:
        """Generate embeddings for texts."""
        if self.embed_mode == "openai":
            response = self.openai.embeddings.create(
                model="text-embedding-3-small",
                input=texts,
            )
            return np.array([e.embedding for e in response.data])

        elif self.embed_mode == "sbert":
            return self.model.encode(texts, convert_to_numpy=True)

        return None

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between vectors."""
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    def _keyword_match(self, text: str) -> Tuple[float, List[str]]:
        """Fallback keyword matching when no embeddings available."""
        text_lower = text.lower()

        # Core keywords from RSCT theory
        keywords = {
            "representation": 0.15,
            "solver": 0.15,
            "compatibility": 0.15,
            "kappa": 0.1,
            "certification": 0.1,
            "multi-agent": 0.1,
            "hallucination": 0.08,
            "grounding": 0.08,
            "safety": 0.05,
            "alignment": 0.05,
        }

        score = 0.0
        matched = []

        for kw, weight in keywords.items():
            if kw in text_lower:
                score += weight
                matched.append(kw)

        return min(score, 1.0), matched

    def match_paper(self, paper_title: str, paper_abstract: str) -> MatchResult:
        """Match a paper against loaded topics."""
        combined_text = f"{paper_title}\n{paper_abstract}"

        if self.embed_mode == "keyword" or self.topic_embeddings is None:
            # Fallback to keyword matching
            score, keywords = self._keyword_match(combined_text)
            return MatchResult(
                paper_id="",
                paper_title=paper_title,
                similarity_score=score,
                matched_topics=[],
                top_keywords=keywords,
                explanation=f"Keyword match: {', '.join(keywords)}" if keywords else "No keyword matches",
            )

        # Compute paper embedding
        paper_embedding = self._embed([combined_text])[0]

        # Compare to all topics
        similarities = []
        for i, topic in enumerate(self.topics):
            sim = self._cosine_similarity(paper_embedding, topic.embedding)
            similarities.append((topic.id, topic.title, sim))

        # Sort by similarity
        similarities.sort(key=lambda x: x[2], reverse=True)

        # Get best match
        best_score = similarities[0][2] if similarities else 0.0
        matched_topics = [t[1] for t in similarities if t[2] >= self.threshold]

        return MatchResult(
            paper_id="",
            paper_title=paper_title,
            similarity_score=best_score,
            matched_topics=matched_topics[:3],
            top_keywords=[],
            explanation=f"Best match: {similarities[0][1]} ({similarities[0][2]:.2f})" if similarities else "",
        )

    def match_papers(self, papers: List[Dict]) -> List[MatchResult]:
        """Match multiple papers against topics."""
        results = []

        for paper in papers:
            result = self.match_paper(paper["title"], paper["abstract"])
            result.paper_id = paper.get("id", "")
            results.append(result)

        # Sort by similarity score
        results.sort(key=lambda x: x.similarity_score, reverse=True)

        return results

    def filter_relevant(self, papers: List[Dict], min_score: float = 0.5) -> List[Tuple[Dict, MatchResult]]:
        """Filter papers to only those above threshold."""
        results = self.match_papers(papers)

        relevant = []
        for paper, result in zip(papers, results):
            if result.similarity_score >= min_score:
                relevant.append((paper, result))

        return relevant
