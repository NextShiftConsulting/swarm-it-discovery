"""
Bedrock Semantic Matcher - Real embedding-based paper matching using AWS Bedrock.

Uses Titan embeddings for semantic similarity between papers and topics.

P18 Compliance: All credentials via swarm-it-auth.
"""

import os
import sys
import json
import boto3
import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

# Add swarm-it-auth to path for credential management (P18)
sys.path.insert(0, str(Path.home() / "GitHub" / "swarm-it-auth"))

# Optional: swarm-it-auth for credentials (P18 compliant)
try:
    from swarm_auth.adapters import EnvCredentialAdapter
    HAS_SWARM_AUTH = True
except ImportError:
    HAS_SWARM_AUTH = False


def _get_aws_credentials():
    """Get AWS credentials via swarm-it-auth (P18 compliant)."""
    if HAS_SWARM_AUTH:
        adapter = EnvCredentialAdapter()
        aws_key = adapter.retrieve("AWS_ACCESS_KEY_ID")
        aws_secret = adapter.retrieve("AWS_SECRET_ACCESS_KEY")
        if aws_key and aws_secret:
            return {"aws_access_key_id": aws_key, "aws_secret_access_key": aws_secret}
    # Fall back to default boto3 credential chain (~/.aws/credentials)
    return {}


@dataclass
class SemanticMatch:
    """Result of semantic matching."""
    paper_id: str
    similarity_score: float
    matched_topics: List[str]
    top_topic: str
    top_topic_score: float


class BedrockMatcher:
    """
    Semantic matcher using AWS Bedrock Titan embeddings.

    Computes cosine similarity between paper abstracts and topic descriptions.

    Usage:
        matcher = BedrockMatcher()
        matcher.load_topics("content/topics/topics.json")
        matches = matcher.match_papers(papers)
    """

    def __init__(
        self,
        region: str = "us-east-1",
        model_id: str = "amazon.titan-embed-text-v1",
        threshold: float = 0.3,
    ):
        """
        Initialize Bedrock matcher.

        Args:
            region: AWS region
            model_id: Bedrock embedding model ID
            threshold: Minimum similarity score
        """
        self.region = region
        self.model_id = model_id
        self.threshold = threshold
        self.topics = []
        self.topic_embeddings = {}

        # Initialize Bedrock client (P18 compliant)
        creds = _get_aws_credentials()
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=region,
            **creds  # Empty dict uses default chain, or explicit creds from swarm-auth
        )

    def _get_embedding(self, text: str) -> np.ndarray:
        """Get embedding from Bedrock Titan."""
        response = self.client.invoke_model(
            modelId=self.model_id,
            body=json.dumps({"inputText": text[:8000]})  # Titan limit
        )
        result = json.loads(response["body"].read())
        return np.array(result["embedding"])

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity."""
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    def load_topics(self, topics_path: str) -> None:
        """
        Load topics and compute embeddings.

        Args:
            topics_path: Path to topics.json
        """
        with open(topics_path, "r") as f:
            data = json.load(f)

        self.topics = data.get("topics", [])
        print(f"  Loading {len(self.topics)} topics with Bedrock embeddings...")

        for topic in self.topics:
            # Combine title, content, and keywords for embedding
            topic_text = f"{topic['title']}. {topic.get('content', '')}. Keywords: {', '.join(topic.get('keywords', []))}"
            self.topic_embeddings[topic["id"]] = self._get_embedding(topic_text)
            print(f"    ✓ {topic['id']}: {topic['title']}")

    def match_paper(self, paper: Dict[str, Any]) -> SemanticMatch:
        """
        Match a single paper against topics.

        Args:
            paper: Paper dict with id, title, abstract

        Returns:
            SemanticMatch result
        """
        # Get paper embedding
        paper_text = f"{paper['title']}. {paper.get('abstract', '')}"
        paper_embedding = self._get_embedding(paper_text)

        # Compute similarity to each topic
        scores = {}
        for topic in self.topics:
            topic_embedding = self.topic_embeddings[topic["id"]]
            score = self._cosine_similarity(paper_embedding, topic_embedding)
            scores[topic["id"]] = score

        # Find matches above threshold
        matched = [(tid, score) for tid, score in scores.items() if score >= self.threshold]
        matched.sort(key=lambda x: x[1], reverse=True)

        # Get best match
        if matched:
            top_topic = matched[0][0]
            top_score = matched[0][1]
            avg_score = sum(s for _, s in matched) / len(matched)
        else:
            top_topic = ""
            top_score = 0.0
            avg_score = max(scores.values()) if scores else 0.0

        return SemanticMatch(
            paper_id=paper["id"],
            similarity_score=avg_score,
            matched_topics=[tid for tid, _ in matched],
            top_topic=top_topic,
            top_topic_score=top_score,
        )

    def match_papers(self, papers: List[Dict[str, Any]]) -> List[SemanticMatch]:
        """
        Match multiple papers against topics.

        Args:
            papers: List of paper dicts

        Returns:
            List of SemanticMatch results
        """
        results = []
        for i, paper in enumerate(papers):
            try:
                match = self.match_paper(paper)
                results.append(match)
                if (i + 1) % 10 == 0:
                    print(f"    Matched {i + 1}/{len(papers)} papers...")
            except Exception as e:
                print(f"    Error matching {paper.get('id', 'unknown')}: {e}")
                results.append(SemanticMatch(
                    paper_id=paper.get("id", "unknown"),
                    similarity_score=0.0,
                    matched_topics=[],
                    top_topic="",
                    top_topic_score=0.0,
                ))
        return results


class BedrockAnalyzer:
    """
    Paper analyzer using Bedrock Claude for summaries and insights.

    Uses Claude for intelligent paper analysis beyond just embeddings.
    """

    def __init__(
        self,
        region: str = "us-east-1",
        model_id: str = "anthropic.claude-3-haiku-20240307-v1:0",
    ):
        self.region = region
        self.model_id = model_id
        # Initialize Bedrock client (P18 compliant)
        creds = _get_aws_credentials()
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=region,
            **creds  # Empty dict uses default chain, or explicit creds from swarm-auth
        )

    def analyze_paper(
        self,
        paper: Dict[str, Any],
        topics: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Analyze a paper using Claude.

        Args:
            paper: Paper dict with title, abstract
            topics: List of topic dicts

        Returns:
            Analysis dict with relevance, insights, connections
        """
        topic_list = "\n".join([f"- {t['title']}: {t.get('content', '')[:100]}" for t in topics])

        prompt = f"""Analyze this research paper for relevance to our research topics.

Paper Title: {paper['title']}

Abstract: {paper.get('abstract', '')[:2000]}

Our Research Topics:
{topic_list}

Provide a JSON response with:
1. relevance_score (0-10): How relevant is this paper to our topics?
2. matched_topics: List of topic IDs that match
3. key_insights: 3 key insights from this paper
4. rsct_connections: How does this relate to RSCT/swarm certification?
5. summary: 2-sentence summary

Respond with valid JSON only."""

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": prompt}],
        })

        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=body
            )
            result = json.loads(response["body"].read())
            content = result["content"][0]["text"]

            # Parse JSON from response
            # Handle potential markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            return json.loads(content)

        except Exception as e:
            print(f"    Analysis error: {e}")
            return {
                "relevance_score": 5,
                "matched_topics": [],
                "key_insights": [],
                "rsct_connections": "Unable to analyze",
                "summary": paper.get("title", "Unknown paper"),
            }

    def analyze_batch(
        self,
        papers: List[Dict[str, Any]],
        topics: List[Dict[str, Any]],
        max_papers: int = 10,
    ) -> List[Dict[str, Any]]:
        """Analyze multiple papers."""
        results = []
        for i, paper in enumerate(papers[:max_papers]):
            print(f"    Analyzing {i + 1}/{min(len(papers), max_papers)}: {paper['title'][:40]}...")
            analysis = self.analyze_paper(paper, topics)
            analysis["paper_id"] = paper.get("id", "")
            analysis["paper_title"] = paper.get("title", "")
            results.append(analysis)
        return results
