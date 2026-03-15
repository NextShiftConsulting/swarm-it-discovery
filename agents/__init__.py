"""
SWARM Discovery Agents - Modular agents for the discovery pipeline.

Architecture:
- Pipeline Agents: ScannerAgent → AnalyzerAgent → PublisherAgent
- Source Agents: ArXiv, PubMed, BioRxiv, SemanticScholar, OpenAlex
- Orchestrator: Coordinates pipeline and source agents

All agents use:
- swarm-it-auth for credentials (MiMoClient, EnvCredentialAdapter)
- swarm-it-adk for RSCT certification
"""

# Pipeline Agents
from .scanner_agent import ScannerAgent, ScanResult
from .analyzer_agent import AnalyzerAgent, AnalysisResult, BatchAnalysisResult
from .publisher_agent import PublisherAgent, PublishResult, BatchPublishResult

# Source Agents
from .base_agent import BaseSourceAgent, PaperAnalysis
from .arxiv_agent import ArXivAgent
from .pubmed_agent import PubMedAgent
from .biorxiv_agent import BioRxivAgent
from .semantic_scholar_agent import SemanticScholarAgent
from .openalex_agent import OpenAlexAgent

# Orchestrator
from .orchestrator import SourceAgentOrchestrator

__all__ = [
    # Pipeline Agents
    "ScannerAgent",
    "ScanResult",
    "AnalyzerAgent",
    "AnalysisResult",
    "BatchAnalysisResult",
    "PublisherAgent",
    "PublishResult",
    "BatchPublishResult",
    # Source Agents
    "BaseSourceAgent",
    "PaperAnalysis",
    "ArXivAgent",
    "PubMedAgent",
    "BioRxivAgent",
    "SemanticScholarAgent",
    "OpenAlexAgent",
    # Orchestrator
    "SourceAgentOrchestrator",
]
