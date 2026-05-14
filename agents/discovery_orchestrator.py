"""
DiscoveryOrchestrator — ACP-integrated wrapper for SourceAgentOrchestrator.

ADR-027 Stage 9: migrates flat delegation to ACPOrchestrator.

Before: SourceAgentOrchestrator ran sub-agents directly with no delegation chain.
        Each sub-agent obtained LLM credentials via P18 AccessScript independently,
        with no record of which human principal authorized the work.

After:  DiscoveryOrchestrator establishes an RFC 8693 act chain
        (human → discovery-orchestrator-001) before delegating to sub-agents.
        The chain is recorded in the audit log via ACPOrchestrator.

Standards:
  - RFC 8693 §4.1: act claim (delegation chain)
  - ADR-027 Stage 9: first production ACP consumer
  - ADR-028 SD-1: principal_kind discriminator (human | agent)
  - ADR-026 Rule 6: all credential material via CredentialBrokerPort

Sub-agent LLM credentials continue to flow through the existing P18 AccessScript
triage (get_credential → ADK provider factory). This class adds the delegation
audit layer on top of the existing path without replacing it.

Usage:
    from agents.discovery_orchestrator import DiscoveryOrchestrator

    orchestrator = DiscoveryOrchestrator(signing_key="...", audit=LoggingAuditAdapter())

    # With delegation chain (human is the authorizing principal):
    human_jwt = jwt_adapter.create_token(human_user)
    report = orchestrator.run_with_delegation(papers, human_jwt=human_jwt)

    # Without delegation (backwards-compatible, no act chain):
    report = orchestrator.analyze_all(papers)
"""

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from swarm_auth.acp.orchestrator import ACPOrchestrator, DelegatedCredentialRequest
from swarm_auth.adapters.memory_audit import MemoryAuditAdapter
from swarm_auth.adapters.rbac_policy import RBACPolicyAdapter
from swarm_auth.adapters.rfc8693_token_exchange import RFC8693TokenExchangeAdapter
from swarm_auth.domain.agent_identity import AgentIdentity, AgentType
from swarm_auth.domain.principal import Principal
from swarm_auth.domain.roles import UserRole
from swarm_auth.factory import create_jwt_auth
from swarm_auth.ports.audit_port import AuditPort
from swarm_auth.ports.credential_broker_port import (
    CredentialBrokerPort,
    ProviderCredential,
    ProviderType,
    ToolRequest,
)

from agents.orchestrator import SourceAgentOrchestrator  # direct module import — avoids agents/__init__.py eager-loading optional deps

logger = logging.getLogger(__name__)

_ORCHESTRATOR_ID = "discovery-orchestrator-001"
_ORCHESTRATOR_TEAM = "swarm-it-discovery"

# ToolRequest action for delegation audit (provider-native format: resource_type.verb)
# provider is ProviderType.OPENAI; action maps to "openai.chat.generate" in RBAC
_DELEGATION_ACTION = "chat.generate"
_DELEGATION_RESOURCE = "swarm-it-discovery/analysis-pipeline"
_DELEGATION_HTU = "https://api.swarms.network/discovery/analyze"


class _DelegationContextBroker(CredentialBrokerPort):
    """
    Pass-through broker that records delegation context for audit purposes.

    Sub-agents in swarm-it-discovery get their LLM credentials via the
    existing P18 AccessScript path (get_credential / ADK provider factory).
    This broker is wired into ACPOrchestrator solely to satisfy ADR-026
    Rule 6 and emit the delegation audit event. It does not gate the
    actual LLM calls.

    The returned ProviderCredential carries delegation metadata
    (orchestrator ID, original principal) so downstream systems can
    trace the chain without re-parsing the JWT.
    """

    def vend_credential(
        self,
        principal: Principal,
        tool_request: ToolRequest,
    ) -> ProviderCredential:
        return ProviderCredential(
            provider=ProviderType.OPENAI,
            credential_type="delegation_context",
            credentials={
                "delegation_granted": True,
                "orchestrator_id": _ORCHESTRATOR_ID,
                "originating_principal": principal.user_id,
            },
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            scope=tool_request.action,
            issued_to=principal.user_id,
            issued_at=datetime.now(timezone.utc),
            request_id=tool_request.request_id or str(uuid.uuid4()),
        )

    def revoke_credential(self, credential_id: str) -> bool:
        return True

    def list_active_credentials(
        self,
        principal: Principal,
        provider: Optional[ProviderType] = None,
    ) -> List[ProviderCredential]:
        return []

    def validate_credential(self, credential: ProviderCredential) -> bool:
        return not credential.is_expired()

    def refresh_credential(self, credential: ProviderCredential) -> ProviderCredential:
        raise NotImplementedError(
            "Delegation context credentials cannot be refreshed. "
            "Request a new credential via vend_credential()."
        )


class DiscoveryOrchestrator:
    """
    ACP-integrated orchestrator for the swarm-it-discovery pipeline.

    Wraps SourceAgentOrchestrator with RFC 8693 delegation tracking.
    When run_with_delegation() is called with a human JWT, the orchestrator
    establishes an act chain and records it in the audit log before
    delegating work to SourceAgentOrchestrator and its sub-agents.

    ADR-027 Stage 9 acceptance criteria:
      1. At least one delegation call produces an audit event with act chain.
         => run_with_delegation() calls ACPOrchestrator.request_credential(),
            which emits CREDENTIAL_VENDED with actor = discovery-orchestrator-001.
      2. No regression in SourceAgentOrchestrator behavior.
         => analyze_all() delegates to SourceAgentOrchestrator unchanged.
      3. Migration documented as ADR-027 change-control entry.
         => See ADR-027-implementation-plan.md Stage 9.

    Args:
        signing_key: HS256 signing key for JWT creation and verification.
                     Should come from swarm_auth.get_credential('SWARM_AUTH_SECRET').
                     Defaults to a development key — do not use in production.
        audit:       AuditPort implementation. Defaults to MemoryAuditAdapter
                     (suitable for tests). Use LoggingAuditAdapter in production.
    """

    AGENT_ID: str = _ORCHESTRATOR_ID
    _DEFAULT_SIGNING_KEY: str = "swarm-it-discovery-signing-key-32b!"

    def __init__(
        self,
        signing_key: Optional[str] = None,
        audit: Optional[AuditPort] = None,
    ) -> None:
        self._signing_key = signing_key or self._DEFAULT_SIGNING_KEY
        self._audit = audit or MemoryAuditAdapter()

        # This orchestrator's own identity (AgentType.ORCHESTRATOR)
        self._identity = AgentIdentity(
            user_id=self.AGENT_ID,
            username="discovery-orchestrator",
            role=UserRole.SERVICE,
            agent_type=AgentType.ORCHESTRATOR,
            owning_team=_ORCHESTRATOR_TEAM,
        )

        # JWT adapter for minting and verifying tokens
        self._jwt = create_jwt_auth(secret=self._signing_key)

        # Build the ACP pipeline
        # - RBACPolicyAdapter: enforces role-capability matrix
        #   (UserRole.DEVELOPER has openai.chat.generate)
        # - RFC8693TokenExchangeAdapter: builds act claim from subject + actor tokens
        # - _DelegationContextBroker: satisfies ADR-026 Rule 6 and emits audit event
        # - require_dpop_for_delegation=False: DPoP not yet deployed in discovery
        rbac = RBACPolicyAdapter()
        exchange = RFC8693TokenExchangeAdapter(
            signing_key=self._signing_key,
            issuer=_ORCHESTRATOR_TEAM,
        )
        self._acp = ACPOrchestrator(
            broker=_DelegationContextBroker(),
            policy_pipeline=[rbac],
            audit=self._audit,
            signing_key=self._signing_key,
            token_exchange=exchange,
            require_dpop_for_delegation=False,
        )

        # Inner orchestrator — unchanged by this wrapper
        self._inner = SourceAgentOrchestrator()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def run_with_delegation(
        self,
        papers: List[Dict],
        human_jwt: str,
    ) -> Dict:
        """
        Run paper analysis with explicit RFC 8693 delegation chain.

        Establishes act chain (human → discovery-orchestrator-001) by calling
        ACPOrchestrator.request_credential() with the human's JWT as subject and
        the orchestrator's JWT as actor. On success, the audit log records
        a CREDENTIAL_VENDED event with actor_chain populated.

        Sub-agent LLM credentials continue to flow through the existing
        P18 AccessScript path — this method adds the delegation audit layer,
        it does not replace the credential path.

        Args:
            papers:    List of paper dicts with 'source' field.
            human_jwt: JWT for the requesting human principal. Must be signed
                       with the same signing_key as this orchestrator.
                       Subject principal must have a role that allows
                       openai.chat.generate (e.g. UserRole.DEVELOPER).

        Returns:
            Analysis report dict identical to SourceAgentOrchestrator.analyze_all().
        """
        # Mint actor token for this orchestrator
        actor_token = self._jwt.create_token(self._identity)

        # Request delegation credential — establishes and audits the act chain
        tool_request = ToolRequest(
            tool_name="discovery_analysis",
            provider=ProviderType.OPENAI,
            action=_DELEGATION_ACTION,
            resource=_DELEGATION_RESOURCE,
            request_id=str(uuid.uuid4()),
        )

        response = self._acp.request_credential(
            DelegatedCredentialRequest(
                tool_request=tool_request,
                subject_token=human_jwt,
                actor_token=actor_token,
                expected_htu=_DELEGATION_HTU,
            )
        )

        if response.error:
            logger.warning(
                "ACP delegation failed (%s): %s — proceeding without delegation chain",
                response.error,
                response.error_description,
            )
        else:
            logger.info(
                "Delegation established: human=%s → orchestrator=%s",
                response.credential.issued_to if response.credential else "?",
                self.AGENT_ID,
            )

        # Delegate work to inner orchestrator (existing P18 credential path unchanged)
        return self._inner.analyze_all(papers)

    def analyze_all(self, papers: List[Dict]) -> Dict:
        """
        Run paper analysis without a delegation chain.

        Backwards-compatible entry point. Sub-agents obtain LLM credentials
        via P18 AccessScript triage. No act chain is recorded.

        Args:
            papers: List of paper dicts with 'source' field.

        Returns:
            Analysis report dict.
        """
        return self._inner.analyze_all(papers)

    # ------------------------------------------------------------------
    # Introspection (testing / monitoring)
    # ------------------------------------------------------------------

    @property
    def audit(self) -> AuditPort:
        """The audit adapter wired into this orchestrator."""
        return self._audit

    def get_delegation_events(self) -> List[Dict]:
        """
        Return CREDENTIAL_VENDED audit events that contain an act chain.

        Useful for tests and monitoring to verify delegation was established.
        Returns a list of SIEM-compatible dicts from MemoryAuditAdapter.get_events().
        """
        if not hasattr(self._audit, "get_events"):
            return []
        return [
            e for e in self._audit.get_events()
            if e.get("event_type") == "credential.vended"
            and e.get("actor") is not None
        ]
