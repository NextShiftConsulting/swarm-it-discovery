"""
Paper2SwarmAgent - Convert research papers to Swarm-It agents.

Designed for eventual extraction to swarm-it-adk.

Quick Start:
    from pipeline.paper2agent import Paper2SwarmAgent, TopicConfig

    # Load topics from config
    config = TopicConfig.from_json("content/topics/topics.json")

    # Initialize converter
    converter = Paper2SwarmAgent(topics=config)

    # Convert a paper with GitHub repo
    agent_def = converter.convert(
        paper_url="https://arxiv.org/abs/2401.12345",
        github_url="https://github.com/author/repo"
    )

    # Use with ADK
    from swarm_it import Agent
    agent = Agent.from_definition(agent_def)

Modules:
    - scanner: Scan repos for tutorials and tools (TutorialScanner)
    - extractor: Extract callable functions (ToolExtractor)
    - converter: Convert to swarm-it agent format (SwarmAgentConverter)
    - config: Topic-based filtering (TopicConfig)
"""

__version__ = "0.1.0"

from .config import TopicConfig, Topic
from .scanner import TutorialScanner, TutorialFile, ScanResult
from .extractor import ToolExtractor, ExtractedTool, ExtractionResult
from .converter import SwarmAgentConverter, AgentDefinition
from .orchestrator import Paper2SwarmAgent

__all__ = [
    # Version
    "__version__",

    # Config
    "TopicConfig",
    "Topic",

    # Scanner
    "TutorialScanner",
    "TutorialFile",
    "ScanResult",

    # Extractor
    "ToolExtractor",
    "ExtractedTool",
    "ExtractionResult",

    # Converter
    "SwarmAgentConverter",
    "AgentDefinition",

    # Orchestrator
    "Paper2SwarmAgent",
]
