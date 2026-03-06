"""
SWARM Source Agents - Specialized agents for each paper source.

Each agent has domain expertise for analyzing papers from its source.
"""

from .base_agent import BaseSourceAgent
from .arxiv_agent import ArXivAgent
from .pubmed_agent import PubMedAgent
from .biorxiv_agent import BioRxivAgent
from .semantic_scholar_agent import SemanticScholarAgent
from .openalex_agent import OpenAlexAgent
from .orchestrator import SourceAgentOrchestrator

__all__ = [
    "BaseSourceAgent",
    "ArXivAgent",
    "PubMedAgent",
    "BioRxivAgent",
    "SemanticScholarAgent",
    "OpenAlexAgent",
    "SourceAgentOrchestrator",
]
