"""
Base Source Agent - Abstract base for all source-specific agents.

Uses swarm-it-auth for credentials and swarm-it-adk for certification.
NEVER uses direct API keys or OpenAI imports.
"""

import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone
from pathlib import Path

# Add swarm-it repos to path
sys.path.insert(0, str(Path.home() / "GitHub" / "swarm-it-adk" / "adk"))
sys.path.insert(0, str(Path.home() / "GitHub" / "swarm-it-auth"))


@dataclass
class PaperAnalysis:
    """Analysis result from a source agent."""
    paper_id: str
    paper_title: str
    source: str

    # Core scores (0-10)
    relevance: int  # How relevant to RSCT/AI safety
    novelty: int    # How novel the approach
    impact: int     # Potential research impact

    # Source-specific scores
    source_quality: int  # Quality indicators from this source
    citation_potential: int  # Expected citation impact

    # Analysis text
    summary: str
    key_findings: List[str]
    rsct_connections: List[str]  # How it connects to RSCT
    suggested_citations: List[str]

    # Metadata
    analyzed_at: str
    agent_name: str
    confidence: float  # 0-1, agent's confidence in analysis

    # RSCT Certificate (from swarm-it-adk)
    rsct_certified: bool = False
    rsct_kappa: Optional[float] = None


class BaseSourceAgent(ABC):
    """
    Abstract base class for source-specific agents.

    Integration:
    - Credentials via swarm_auth.get_credential (P18 v3.0)
    - Certification via swarm-it-adk (certify before LLM calls)
    """

    SOURCE_NAME: str = "base"
    AGENT_NAME: str = "BaseAgent"

    # Source-specific expertise prompt
    EXPERTISE_PROMPT: str = """You are a research paper analysis agent."""

    def __init__(self):
        self._llm_client = None
        self._certifier = None
        self._init_integrations()

    def _init_integrations(self):
        """Initialize swarm-it-auth and swarm-it-adk integrations."""

        # 1. P18 v3.0 credentials available via swarm_auth.get_credential
        try:
            from swarm_auth import get_credential
            print(f"  ✓ {self.AGENT_NAME}: swarm_auth initialized")
        except ImportError as e:
            print(f"  ✗ {self.AGENT_NAME}: swarm_auth not available: {e}")

        # 2. Initialize certifier (swarm-it-adk)
        try:
            from swarm_it import certify, LocalEngine
            self._certifier = LocalEngine()
            print(f"  ✓ {self.AGENT_NAME}: swarm-it-adk initialized")
        except ImportError as e:
            print(f"  ✗ {self.AGENT_NAME}: swarm-it-adk not available: {e}")

        # 3. Initialize LLM client using credentials from auth
        self._init_llm_client()

    def _init_llm_client(self):
        """Initialize LLM client using credentials from swarm-it-auth.

        Priority:
        1. MiMoClient (cost-effective, 99% cheaper)
        2. OpenAI (fallback)
        """
        if not self._credential_adapter:
            return

        # Try MiMoClient first (99% cheaper than OpenAI)
        try:
            from swarm_auth.adapters import MiMoClient
            mimo_key = self._credential_adapter.retrieve("MIMO_API_KEY")

            if mimo_key:
                self._llm_client = MiMoClient()
                self._llm_provider = "mimo"
                print(f"  ✓ {self.AGENT_NAME}: MiMoClient ready (99% cost savings)")
                return
        except Exception as e:
            print(f"  ⚠ {self.AGENT_NAME}: MiMoClient not available: {e}")

        # Fallback to OpenAI
        try:
            api_key = self._credential_adapter.retrieve("OPENAI_API_KEY")

            if api_key:
                from openai import OpenAI
                self._llm_client = OpenAI(api_key=api_key)
                self._llm_provider = "openai"
                print(f"  ✓ {self.AGENT_NAME}: OpenAI client ready (fallback)")
            else:
                print(f"  ✗ {self.AGENT_NAME}: No LLM credentials found")
        except Exception as e:
            print(f"  ✗ {self.AGENT_NAME}: LLM client init failed: {e}")

    @abstractmethod
    def get_source_context(self, paper: Dict) -> str:
        """Get source-specific context for analysis."""
        pass

    @abstractmethod
    def extract_source_quality(self, paper: Dict) -> int:
        """Extract quality indicators specific to this source."""
        pass

    def _certify_prompt(self, prompt: str) -> Tuple[bool, Optional[float]]:
        """
        Certify prompt using swarm-it-adk before LLM call.

        Returns:
            (allowed, kappa) - whether to proceed and the kappa score
        """
        if not self._certifier:
            # No certifier = allow but flag as uncertified
            return True, None

        try:
            cert = self._certifier.certify(prompt)

            # Check RSCT decision
            from swarm_it.local.engine import GateDecision
            allowed = cert.decision in [GateDecision.EXECUTE, GateDecision.REPAIR]

            return allowed, cert.kappa_gate
        except Exception as e:
            print(f"  ⚠ {self.AGENT_NAME}: Certification failed: {e}")
            return True, None  # Fail open for now

    def analyze_paper(self, paper: Dict) -> Optional[PaperAnalysis]:
        """Analyze a paper using this agent's expertise."""
        if not self._llm_client:
            print(f"  ✗ {self.AGENT_NAME}: No LLM client available")
            return None

        source_context = self.get_source_context(paper)
        source_quality = self.extract_source_quality(paper)

        prompt = f"""{self.EXPERTISE_PROMPT}

{source_context}

Analyze this paper:
Title: {paper.get('title', 'Unknown')}
Abstract: {paper.get('abstract', '')[:1500]}
Categories: {', '.join(paper.get('categories', []))}

Provide analysis in JSON format:
{{
    "relevance": <0-10, relevance to RSCT/AI safety/multi-agent systems>,
    "novelty": <0-10, how novel is the approach>,
    "impact": <0-10, potential research impact>,
    "citation_potential": <0-10, expected citation impact>,
    "summary": "<2-3 sentence summary>",
    "key_findings": ["finding1", "finding2", "finding3"],
    "rsct_connections": ["connection to RSCT theory 1", "connection 2"],
    "suggested_citations": ["paper1 to cite", "paper2 to cite"],
    "confidence": <0-1, your confidence in this analysis>
}}"""

        # RSCT Certification before LLM call
        allowed, kappa = self._certify_prompt(prompt)

        if not allowed:
            print(f"  ✗ {self.AGENT_NAME}: Prompt rejected by RSCT (κ={kappa:.3f})")
            return None

        try:
            import json

            # Use appropriate client based on provider
            if hasattr(self, '_llm_provider') and self._llm_provider == "mimo":
                # MiMoClient (cost-effective)
                result = self._llm_client.chat_json(prompt)
            else:
                # OpenAI client (fallback)
                response = self._llm_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500,
                    response_format={"type": "json_object"},
                )
                result = json.loads(response.choices[0].message.content)

            return PaperAnalysis(
                paper_id=paper.get('id', ''),
                paper_title=paper.get('title', ''),
                source=self.SOURCE_NAME,
                relevance=result.get('relevance', 5),
                novelty=result.get('novelty', 5),
                impact=result.get('impact', 5),
                source_quality=source_quality,
                citation_potential=result.get('citation_potential', 5),
                summary=result.get('summary', ''),
                key_findings=result.get('key_findings', []),
                rsct_connections=result.get('rsct_connections', []),
                suggested_citations=result.get('suggested_citations', []),
                analyzed_at=datetime.now(timezone.utc).isoformat(),
                agent_name=self.AGENT_NAME,
                confidence=result.get('confidence', 0.5),
                rsct_certified=kappa is not None,
                rsct_kappa=kappa,
            )
        except Exception as e:
            print(f"  ✗ {self.AGENT_NAME} error: {e}")
            return None

    def analyze_batch(self, papers: List[Dict]) -> List[PaperAnalysis]:
        """Analyze multiple papers from this source."""
        results = []
        source_papers = [p for p in papers if p.get('source') == self.SOURCE_NAME]

        print(f"  {self.AGENT_NAME}: Analyzing {len(source_papers)} papers...")

        for paper in source_papers:
            analysis = self.analyze_paper(paper)
            if analysis:
                results.append(analysis)
                cert_status = f"κ={analysis.rsct_kappa:.2f}" if analysis.rsct_kappa else "uncert"
                print(f"    {paper.get('title', '')[:40]}... R:{analysis.relevance}/N:{analysis.novelty}/I:{analysis.impact} [{cert_status}]")

        return results
