"""
Swarm Agent Converter - Convert extracted tools to swarm-it agent format.

Generates ADK-compatible agent definitions that can be used standalone
or imported into the swarm-it-adk framework.
"""

import json
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any

from .config import Topic
from .extractor import ExtractedTool, ExtractionResult


@dataclass
class AgentDefinition:
    """
    A swarm-it compatible agent definition.

    Can be serialized to JSON and loaded by swarm-it-adk.
    """
    # Core identity
    id: str
    name: str
    description: str
    version: str = "0.1.0"

    # Source metadata
    paper_id: Optional[str] = None
    paper_title: Optional[str] = None
    paper_url: Optional[str] = None
    github_url: Optional[str] = None
    topic_id: Optional[str] = None

    # Tools
    tools: List[Dict[str, Any]] = field(default_factory=list)

    # Agent configuration
    solver_type: str = "llm"
    modality: str = "text"
    system_prompt: str = ""

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    confidence: float = 1.0
    dependencies: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Export to dictionary (ADK-compatible)."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "paper": {
                "id": self.paper_id,
                "title": self.paper_title,
                "url": self.paper_url,
                "github_url": self.github_url,
            },
            "topic_id": self.topic_id,
            "tools": self.tools,
            "config": {
                "solver_type": self.solver_type,
                "modality": self.modality,
                "system_prompt": self.system_prompt,
            },
            "metadata": {
                "created_at": self.created_at,
                "confidence": self.confidence,
                "dependencies": self.dependencies,
            },
        }

    def to_json(self, indent: int = 2) -> str:
        """Export to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def save(self, path: str) -> None:
        """Save to JSON file."""
        with open(path, "w") as f:
            f.write(self.to_json())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentDefinition":
        """Load from dictionary."""
        paper = data.get("paper", {})
        config = data.get("config", {})
        metadata = data.get("metadata", {})

        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            version=data.get("version", "0.1.0"),
            paper_id=paper.get("id"),
            paper_title=paper.get("title"),
            paper_url=paper.get("url"),
            github_url=paper.get("github_url"),
            topic_id=data.get("topic_id"),
            tools=data.get("tools", []),
            solver_type=config.get("solver_type", "llm"),
            modality=config.get("modality", "text"),
            system_prompt=config.get("system_prompt", ""),
            created_at=metadata.get("created_at", datetime.now(timezone.utc).isoformat()),
            confidence=metadata.get("confidence", 1.0),
            dependencies=metadata.get("dependencies", []),
        )

    @classmethod
    def load(cls, path: str) -> "AgentDefinition":
        """Load from JSON file."""
        with open(path, "r") as f:
            return cls.from_dict(json.load(f))

    def to_adk_agent(self) -> Dict[str, Any]:
        """
        Convert to swarm-it-adk Agent format.

        Returns dict compatible with:
            from swarm_it import Agent
            agent = Agent(**agent_def.to_adk_agent())
        """
        return {
            "id": self.id,
            "name": self.name,
            "solver_type": self.solver_type,
            "modality": self.modality,
            "tools": [t["name"] for t in self.tools],
            "metadata": {
                "paper_id": self.paper_id,
                "paper_title": self.paper_title,
                "description": self.description,
            },
        }


class SwarmAgentConverter:
    """
    Convert extracted tools to swarm-it agent definitions.

    Generates ADK-compatible agents with proper tool schemas,
    system prompts, and metadata.

    Usage:
        converter = SwarmAgentConverter()

        agent_def = converter.convert(
            paper_id="2401.12345",
            paper_title="My Paper",
            github_url="https://github.com/author/repo",
            extraction_results=[result1, result2],
            topic=my_topic,
        )

        agent_def.save("agents/my_paper_agent.json")
    """

    def __init__(
        self,
        min_confidence: float = 0.5,
        max_tools: int = 20,
    ):
        """
        Initialize converter.

        Args:
            min_confidence: Minimum tool confidence for inclusion
            max_tools: Maximum tools per agent
        """
        self.min_confidence = min_confidence
        self.max_tools = max_tools

    def convert(
        self,
        paper_id: str,
        paper_title: str,
        github_url: str,
        extraction_results: List[ExtractionResult],
        topic: Optional[Topic] = None,
        paper_url: Optional[str] = None,
    ) -> AgentDefinition:
        """
        Convert extraction results to an agent definition.

        Args:
            paper_id: Paper identifier (e.g., arXiv ID)
            paper_title: Paper title
            github_url: GitHub repository URL
            extraction_results: Results from tool extraction
            topic: Optional matched topic
            paper_url: Optional paper URL

        Returns:
            AgentDefinition ready for use
        """
        # Collect all tools above confidence threshold
        all_tools = []
        all_dependencies = set()

        for result in extraction_results:
            if not result.success:
                continue

            for tool in result.tools:
                if tool.confidence >= self.min_confidence:
                    all_tools.append(tool)
                    all_dependencies.update(tool.dependencies)

        # Sort by confidence and limit
        all_tools.sort(key=lambda t: t.confidence, reverse=True)
        selected_tools = all_tools[: self.max_tools]

        # Convert tools to schema format
        tool_schemas = [
            self._tool_to_schema(tool) for tool in selected_tools
        ]

        # Generate agent ID
        agent_id = self._generate_id(paper_id, github_url)

        # Generate agent name
        agent_name = self._generate_name(paper_title)

        # Generate description
        description = self._generate_description(
            paper_title=paper_title,
            topic=topic,
            tool_count=len(selected_tools),
        )

        # Generate system prompt
        system_prompt = self._generate_system_prompt(
            paper_title=paper_title,
            topic=topic,
            tools=selected_tools,
        )

        # Calculate overall confidence
        if selected_tools:
            avg_confidence = sum(t.confidence for t in selected_tools) / len(selected_tools)
        else:
            avg_confidence = 0.0

        return AgentDefinition(
            id=agent_id,
            name=agent_name,
            description=description,
            paper_id=paper_id,
            paper_title=paper_title,
            paper_url=paper_url,
            github_url=github_url,
            topic_id=topic.id if topic else None,
            tools=tool_schemas,
            system_prompt=system_prompt,
            confidence=avg_confidence,
            dependencies=sorted(all_dependencies),
        )

    def _generate_id(self, paper_id: str, github_url: str) -> str:
        """Generate unique agent ID."""
        # Use hash of paper_id + github_url for uniqueness
        content = f"{paper_id}:{github_url}"
        hash_suffix = hashlib.md5(content.encode()).hexdigest()[:8]
        # Clean paper_id for use in ID
        clean_id = paper_id.replace(".", "_").replace("/", "_").replace(":", "_")
        return f"paper2agent_{clean_id}_{hash_suffix}"

    def _generate_name(self, paper_title: str) -> str:
        """Generate agent name from paper title."""
        # Take first few meaningful words
        words = paper_title.split()[:5]
        name = " ".join(words)
        if len(paper_title) > len(name):
            name += "..."
        return f"{name} Agent"

    def _generate_description(
        self,
        paper_title: str,
        topic: Optional[Topic],
        tool_count: int,
    ) -> str:
        """Generate agent description."""
        parts = [f"AI agent derived from the paper '{paper_title}'."]

        if topic:
            parts.append(f"Specialized in {topic.title}.")

        parts.append(f"Provides {tool_count} callable tools for research tasks.")

        return " ".join(parts)

    def _generate_system_prompt(
        self,
        paper_title: str,
        topic: Optional[Topic],
        tools: List[ExtractedTool],
    ) -> str:
        """Generate system prompt for the agent."""
        prompt_parts = [
            f"You are a research assistant specialized in the methods from '{paper_title}'.",
            "",
            "Your capabilities include:",
        ]

        # Add tool descriptions
        for tool in tools[:10]:  # Limit to top 10 in prompt
            prompt_parts.append(f"- {tool.name}: {tool.description[:100]}")

        if topic:
            prompt_parts.extend([
                "",
                f"Focus area: {topic.title}",
                f"Key concepts: {', '.join(topic.keywords[:5])}",
            ])

        prompt_parts.extend([
            "",
            "When helping users:",
            "1. Explain which tool is appropriate for their task",
            "2. Provide clear parameter requirements",
            "3. Interpret results in context of the paper's methodology",
        ])

        return "\n".join(prompt_parts)

    def _tool_to_schema(self, tool: ExtractedTool) -> Dict[str, Any]:
        """Convert ExtractedTool to schema format."""
        schema = tool.to_tool_schema()
        schema["source_file"] = tool.source_file
        schema["confidence"] = tool.confidence
        schema["dependencies"] = tool.dependencies
        return schema


def batch_convert(
    papers: List[Dict[str, Any]],
    extraction_results: Dict[str, List[ExtractionResult]],
    topics: List[Topic],
    output_dir: str,
) -> List[AgentDefinition]:
    """
    Batch convert multiple papers to agents.

    Args:
        papers: List of paper metadata dicts
        extraction_results: Map of paper_id -> extraction results
        topics: Available topics for matching
        output_dir: Directory to save agent definitions

    Returns:
        List of created AgentDefinitions
    """
    converter = SwarmAgentConverter()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    agents = []

    for paper in papers:
        paper_id = paper.get("id", "")
        if paper_id not in extraction_results:
            continue

        # Find matching topic
        text = f"{paper.get('title', '')} {paper.get('abstract', '')}"
        matching_topic = None
        best_score = 0.0

        for topic in topics:
            score = topic.relevance_score(text)
            if score > best_score:
                best_score = score
                matching_topic = topic

        # Convert
        agent_def = converter.convert(
            paper_id=paper_id,
            paper_title=paper.get("title", "Unknown"),
            github_url=paper.get("github_url", ""),
            extraction_results=extraction_results[paper_id],
            topic=matching_topic,
            paper_url=paper.get("url"),
        )

        # Save
        agent_path = output_path / f"{agent_def.id}.json"
        agent_def.save(str(agent_path))
        agents.append(agent_def)

    return agents
