"""
Topic configuration for Paper2SwarmAgent.

Loads research topics from JSON config and provides matching utilities.
Designed for ADK extraction - no external dependencies beyond stdlib.
"""

import json
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class Topic:
    """A research topic for paper matching."""
    id: str
    title: str
    content: str
    keywords: List[str] = field(default_factory=list)

    def matches(self, text: str, threshold: int = 2) -> bool:
        """Check if text matches this topic (at least N keywords)."""
        text_lower = text.lower()
        matches = sum(1 for kw in self.keywords if kw.lower() in text_lower)
        return matches >= threshold

    def relevance_score(self, text: str) -> float:
        """Calculate relevance score (0-1) based on keyword matches."""
        if not self.keywords:
            return 0.0
        text_lower = text.lower()
        matches = sum(1 for kw in self.keywords if kw.lower() in text_lower)
        return min(1.0, matches / max(3, len(self.keywords) * 0.5))


@dataclass
class TopicConfig:
    """
    Configuration for topic-based paper filtering.

    Designed to be serializable and portable for ADK extraction.
    """
    topics: List[Topic] = field(default_factory=list)
    min_relevance: float = 0.3
    require_github: bool = True

    @classmethod
    def from_json(cls, path: str) -> "TopicConfig":
        """Load topics from JSON file."""
        with open(path, "r") as f:
            data = json.load(f)

        topics = [
            Topic(
                id=t["id"],
                title=t["title"],
                content=t.get("content", ""),
                keywords=t.get("keywords", []),
            )
            for t in data.get("topics", [])
        ]

        return cls(topics=topics)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TopicConfig":
        """Load from dictionary (for ADK integration)."""
        topics = [
            Topic(
                id=t["id"],
                title=t["title"],
                content=t.get("content", ""),
                keywords=t.get("keywords", []),
            )
            for t in data.get("topics", [])
        ]

        return cls(
            topics=topics,
            min_relevance=data.get("min_relevance", 0.3),
            require_github=data.get("require_github", True),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Export to dictionary (for ADK serialization)."""
        return {
            "topics": [
                {
                    "id": t.id,
                    "title": t.title,
                    "content": t.content,
                    "keywords": t.keywords,
                }
                for t in self.topics
            ],
            "min_relevance": self.min_relevance,
            "require_github": self.require_github,
        }

    def match_paper(self, title: str, abstract: str) -> Optional[Topic]:
        """Find best matching topic for a paper."""
        text = f"{title} {abstract}"
        best_topic = None
        best_score = 0.0

        for topic in self.topics:
            score = topic.relevance_score(text)
            if score > best_score and score >= self.min_relevance:
                best_score = score
                best_topic = topic

        return best_topic

    def get_topic(self, topic_id: str) -> Optional[Topic]:
        """Get topic by ID."""
        for topic in self.topics:
            if topic.id == topic_id:
                return topic
        return None
