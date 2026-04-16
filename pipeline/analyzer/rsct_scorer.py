"""
RSCT Relevance Scorer - Compare papers against base RSCT whitepaper.

Computes semantic similarity between discovered papers and the RSCT
theory paper to identify papers most relevant to our research.

P18 Compliance: All credentials via swarm-it-auth (preferred) or config_manager.
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass

# P18 v3.0 - Unified credential access
from swarm_auth import get_credential

# Optional: sentence-transformers for local embeddings (FREE - check first)
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

# Optional: Bedrock for embeddings (fallback)
try:
    import boto3
    import numpy as np
    HAS_BEDROCK = True  # Check credentials via swarm-it-auth, not env vars
except ImportError:
    HAS_BEDROCK = False


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

    # Key RSCT concepts to look for (aligned with whitepaper terminology)
    RSCT_CONCEPTS = [
        # Core theory terms
        "representation", "solver", "compatibility", "kappa",
        # Three certification axes
        "purity", "alpha", "turbulence", "sigma", "stability",
        # RSN decomposition
        "noise", "superfluous", "relevance", "decomposition", "simplex",
        # Gatekeeper system
        "gatekeeper", "gate", "oobleck", "fano", "threshold",
        # Multi-agent and safety
        "certification", "multi-agent", "swarm", "hallucination",
        "alignment", "safety", "constraint", "adversarial",
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
        self.use_bedrock = False
        self.embed_mode = None
        self.sbert_model = None
        self.openai = None

        # Check for embedding providers (prefer local FREE options first)
        if HAS_SBERT:
            self.embed_mode = "sbert"
            self.sbert_model = SentenceTransformer("all-MiniLM-L6-v2")
            self._compute_whitepaper_embedding_sbert()
            print("RSCT Scorer: Using local embeddings (FREE)")
        elif HAS_OPENAI and get_credential("OPENAI_API_KEY"):
            self.embed_mode = "openai"
            self.openai = OpenAI(api_key=get_credential("OPENAI_API_KEY"))
            self._compute_whitepaper_embedding()
            print("RSCT Scorer: Using OpenAI embeddings")
        elif HAS_BEDROCK and self._has_aws_credentials():
            self.embed_mode = "bedrock"
            self.use_bedrock = True
            self.bedrock_client = self._create_bedrock_client()
            self._compute_whitepaper_embedding_bedrock()
            print("RSCT Scorer: Using Bedrock Titan embeddings")
        else:
            print("Warning: No embedding service configured, using keyword matching only")

    def _has_aws_credentials(self) -> bool:
        """Check if AWS credentials available via P18 gateway or ~/.aws/credentials."""
        if get_credential("AWS_ACCESS_KEY_ID"):
            return True
        # Fall back to ~/.aws/credentials file
        return os.path.exists(os.path.expanduser("~/.aws/credentials"))

    def _create_bedrock_client(self):
        """Create Bedrock client using P18 compliant credentials."""
        aws_key = get_credential("AWS_ACCESS_KEY_ID")
        aws_secret = get_credential("AWS_SECRET_ACCESS_KEY")
        if aws_key and aws_secret:
            session = boto3.Session(
                aws_access_key_id=aws_key,
                aws_secret_access_key=aws_secret,
                region_name="us-east-1"
            )
            return session.client("bedrock-runtime")
        # Fall back to default boto3 chain (~/.aws/credentials)
        return boto3.client("bedrock-runtime", region_name="us-east-1")

    def _load_whitepaper(self, path: str) -> str:
        """Load and clean whitepaper text (supports .tex, .txt, .pdf)."""
        try:
            import re

            if path.endswith('.pdf'):
                # Extract text from PDF
                try:
                    from pypdf import PdfReader
                    reader = PdfReader(path)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                except ImportError:
                    print("pypdf not available, cannot read PDF")
                    return ""
            else:
                with open(path, 'r', encoding='utf-8') as f:
                    text = f.read()

                # Remove LaTeX commands but keep text
                text = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', text)
                text = re.sub(r'\\[a-zA-Z]+', '', text)
                text = re.sub(r'[{}]', '', text)

            text = re.sub(r'\s+', ' ', text)
            return text[:8000]  # Limit for embedding
        except Exception as e:
            print(f"Error loading whitepaper: {e}")
            return ""

    def _whitepaper_cache_path(self, embed_mode: str, model_name: str) -> Path:
        """Path to cached whitepaper embedding. Key: text-hash + mode + model."""
        import hashlib
        cache_dir = Path.home() / ".cache" / "swarm-discovery" / "whitepaper_embed"
        cache_dir.mkdir(parents=True, exist_ok=True)
        text_hash = hashlib.sha256(self.whitepaper_text[:8000].encode("utf-8")).hexdigest()[:16]
        safe_model = model_name.replace("/", "_").replace(":", "_")
        return cache_dir / f"{embed_mode}_{safe_model}_{text_hash}.json"

    def _load_cached_whitepaper_embedding(self, embed_mode: str, model_name: str):
        """Return cached embedding if present, else None."""
        try:
            p = self._whitepaper_cache_path(embed_mode, model_name)
            if p.exists():
                data = json.loads(p.read_text(encoding="utf-8"))
                return data.get("embedding")
        except Exception:
            pass
        return None

    def _save_cached_whitepaper_embedding(self, embed_mode: str, model_name: str):
        """Persist current self.whitepaper_embedding to cache."""
        if self.whitepaper_embedding is None:
            return
        try:
            p = self._whitepaper_cache_path(embed_mode, model_name)
            p.write_text(json.dumps({
                "embedding": self.whitepaper_embedding,
                "embed_mode": embed_mode,
                "model_name": model_name,
            }), encoding="utf-8")
        except Exception as e:
            print(f"Warning: failed to save whitepaper embedding cache: {e}")

    def _compute_whitepaper_embedding_sbert(self):
        """Compute embedding for whitepaper using local SBERT."""
        if not self.sbert_model or not self.whitepaper_text:
            return

        cached = self._load_cached_whitepaper_embedding("sbert", "all-MiniLM-L6-v2")
        if cached is not None:
            self.whitepaper_embedding = cached
            return

        try:
            embedding = self.sbert_model.encode(self.whitepaper_text[:8000])
            self.whitepaper_embedding = embedding.tolist()
            self._save_cached_whitepaper_embedding("sbert", "all-MiniLM-L6-v2")
        except Exception as e:
            print(f"Error computing whitepaper embedding (SBERT): {e}")

    def _compute_whitepaper_embedding(self):
        """Compute embedding for whitepaper using OpenAI."""
        if not self.openai or not self.whitepaper_text:
            return

        cached = self._load_cached_whitepaper_embedding("openai", self.embed_model)
        if cached is not None:
            self.whitepaper_embedding = cached
            return

        try:
            response = self.openai.embeddings.create(
                input=self.whitepaper_text,
                model=self.embed_model,
            )
            self.whitepaper_embedding = response.data[0].embedding
            self._save_cached_whitepaper_embedding("openai", self.embed_model)
        except Exception as e:
            print(f"Error computing whitepaper embedding: {e}")

    def _compute_whitepaper_embedding_bedrock(self):
        """Compute embedding for whitepaper using Bedrock Titan."""
        if not self.whitepaper_text:
            return

        cached = self._load_cached_whitepaper_embedding("bedrock", "amazon.titan-embed-text-v1")
        if cached is not None:
            self.whitepaper_embedding = cached
            return

        try:
            self.whitepaper_embedding = self._embed_bedrock(self.whitepaper_text)
            self._save_cached_whitepaper_embedding("bedrock", "amazon.titan-embed-text-v1")
        except Exception as e:
            print(f"Error computing whitepaper embedding (Bedrock): {e}")

    def _embed_bedrock(self, text: str) -> Optional[List[float]]:
        """Get embedding from Bedrock Titan."""
        if not self.use_bedrock:
            return None

        try:
            response = self.bedrock_client.invoke_model(
                modelId="amazon.titan-embed-text-v1",
                body=json.dumps({"inputText": text[:8000]})
            )
            result = json.loads(response["body"].read())
            return result["embedding"]
        except Exception as e:
            print(f"Bedrock embedding error: {e}")
            return None

    def _embed(self, text: str) -> Optional[List[float]]:
        """Get embedding for text (SBERT, OpenAI, or Bedrock)."""
        if self.embed_mode == "sbert" and self.sbert_model:
            try:
                embedding = self.sbert_model.encode(text[:8000])
                return embedding.tolist()
            except Exception as e:
                print(f"SBERT embedding error: {e}")
                return None
        elif self.embed_mode == "openai" and self.openai:
            try:
                response = self.openai.embeddings.create(
                    input=text[:8000],
                    model=self.embed_model,
                )
                return response.data[0].embedding
            except Exception as e:
                print(f"OpenAI embedding error: {e}")
                return None
        elif self.use_bedrock:
            return self._embed_bedrock(text)
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
