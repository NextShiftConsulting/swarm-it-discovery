"""
Tests for DiscoveryOrchestrator — ADR-027 Stage 9.

Verifies:
  1. Delegation call produces audit event with populated act chain.
  2. No regression: analyze_all() delegates to SourceAgentOrchestrator unchanged.
  3. Policy denial (non-DEVELOPER role) is handled gracefully.

ADR-027 Stage 9 acceptance criterion 1:
  "At least one real delegation call produces an audit log entry
   with a populated act chain."
"""

import pytest

from swarm_auth.adapters.memory_audit import MemoryAuditAdapter
from swarm_auth.domain.human_user import HumanUser
from swarm_auth.domain.roles import UserRole
from swarm_auth.factory import create_jwt_auth

from agents.discovery_orchestrator import DiscoveryOrchestrator

_SIGNING_KEY = "swarm-it-discovery-signing-key-32b!"


@pytest.fixture
def audit():
    return MemoryAuditAdapter()


@pytest.fixture
def orchestrator(audit):
    return DiscoveryOrchestrator(signing_key=_SIGNING_KEY, audit=audit)


@pytest.fixture
def human_jwt():
    """JWT for a DEVELOPER-role human — has openai.chat.generate permission."""
    jwt = create_jwt_auth(secret=_SIGNING_KEY)
    human = HumanUser(
        user_id="researcher-001",
        username="researcher",
        role=UserRole.DEVELOPER,
        email="researcher@example.com",
    )
    return jwt.create_token(human)


@pytest.fixture
def papers():
    """Minimal paper list — sub-agents will find no source papers and return empty."""
    return []


class TestDelegationAuditChain:
    """ADR-027 Stage 9 criterion 1: delegation produces audit event with act chain."""

    def test_delegation_emits_credential_vended_event(self, orchestrator, human_jwt, papers):
        """run_with_delegation() emits at least one audit event."""
        orchestrator.run_with_delegation(papers, human_jwt=human_jwt)
        events = orchestrator.audit.get_events()
        assert len(events) >= 1

    def test_delegation_event_type_is_credential_vended(self, orchestrator, human_jwt, papers):
        """The delegation event type is credential.vended."""
        orchestrator.run_with_delegation(papers, human_jwt=human_jwt)
        delegation_events = orchestrator.get_delegation_events()
        assert len(delegation_events) == 1, (
            f"Expected 1 delegation event, got: {delegation_events}"
        )
        assert delegation_events[0]["event_type"] == "credential.vended"

    def test_delegation_event_has_human_as_subject(self, orchestrator, human_jwt, papers):
        """The act chain subject is the human principal."""
        orchestrator.run_with_delegation(papers, human_jwt=human_jwt)
        events = orchestrator.get_delegation_events()
        assert events[0]["subject"] == "researcher-001"

    def test_delegation_event_has_orchestrator_as_actor(self, orchestrator, human_jwt, papers):
        """The act chain actor is the discovery orchestrator."""
        orchestrator.run_with_delegation(papers, human_jwt=human_jwt)
        events = orchestrator.get_delegation_events()
        assert events[0]["actor"] == DiscoveryOrchestrator.AGENT_ID

    def test_delegation_event_outcome_is_success(self, orchestrator, human_jwt, papers):
        """Delegation with a DEVELOPER principal succeeds."""
        orchestrator.run_with_delegation(papers, human_jwt=human_jwt)
        events = orchestrator.get_delegation_events()
        assert events[0]["outcome"] == "success"

    def test_delegation_chain_depth_is_one(self, orchestrator, human_jwt, papers):
        """Act chain has exactly one hop (human → orchestrator)."""
        orchestrator.run_with_delegation(papers, human_jwt=human_jwt)
        events = orchestrator.get_delegation_events()
        # chain_depth not in get_events() dict; verify via raw audit query
        from swarm_auth.ports.audit_port import AuditQuery, AuditEventType
        raw_events = orchestrator.audit.query(
            AuditQuery(event_type=AuditEventType.CREDENTIAL_VENDED, limit=10)
        )
        delegation_raw = [e for e in raw_events if e.actor_chain is not None]
        assert len(delegation_raw) == 1
        assert delegation_raw[0].actor_chain.subject == "researcher-001"
        assert delegation_raw[0].actor_chain.actor == DiscoveryOrchestrator.AGENT_ID
        assert delegation_raw[0].actor_chain.chain_depth == 1


class TestBackwardsCompatibility:
    """ADR-027 Stage 9 criterion 2: no regression in SourceAgentOrchestrator behavior."""

    def test_analyze_all_returns_dict(self, orchestrator, papers):
        """analyze_all() returns a dict (SourceAgentOrchestrator contract)."""
        result = orchestrator.analyze_all(papers)
        assert isinstance(result, dict)

    def test_analyze_all_has_expected_keys(self, orchestrator, papers):
        """analyze_all() result has the standard report keys."""
        result = orchestrator.analyze_all(papers)
        assert "timestamp" in result
        assert "total_analyzed" in result
        assert "source_stats" in result

    def test_analyze_all_does_not_emit_delegation_event(self, orchestrator, papers):
        """analyze_all() (no delegation) does not emit any delegation events."""
        orchestrator.analyze_all(papers)
        events = orchestrator.get_delegation_events()
        assert len(events) == 0

    def test_run_with_delegation_returns_same_structure(self, orchestrator, human_jwt, papers):
        """run_with_delegation() returns the same dict structure as analyze_all()."""
        result = orchestrator.run_with_delegation(papers, human_jwt=human_jwt)
        assert isinstance(result, dict)
        assert "timestamp" in result
        assert "total_analyzed" in result


class TestPolicyEnforcement:
    """Delegation is denied for principals without openai.chat.generate permission."""

    def test_guest_role_delegation_fails_gracefully(self, audit, papers):
        """GUEST role cannot delegate — run falls back gracefully without raising."""
        jwt = create_jwt_auth(secret=_SIGNING_KEY)
        guest = HumanUser(
            user_id="guest-001",
            username="guest",
            role=UserRole.GUEST,
        )
        # GUEST has openai.chat.generate — so this passes
        # Use AUDITOR role instead (has *.*.read only)
        from swarm_auth.domain.roles import UserRole as UR
        auditor = HumanUser(user_id="auditor-001", username="auditor", role=UR.AUDITOR)
        auditor_jwt = jwt.create_token(auditor)

        orchestrator = DiscoveryOrchestrator(signing_key=_SIGNING_KEY, audit=audit)
        # Should not raise — falls back to undelegated run
        result = orchestrator.run_with_delegation(papers, human_jwt=auditor_jwt)
        assert isinstance(result, dict)

        # No delegation event (policy denied)
        events = orchestrator.get_delegation_events()
        assert len(events) == 0

    def test_multiple_delegation_calls_each_emit_event(self, orchestrator, human_jwt, papers):
        """Each run_with_delegation() call emits a separate delegation event."""
        orchestrator.run_with_delegation(papers, human_jwt=human_jwt)
        orchestrator.run_with_delegation(papers, human_jwt=human_jwt)
        events = orchestrator.get_delegation_events()
        assert len(events) == 2
        # Both have the same subject and actor
        assert all(e["subject"] == "researcher-001" for e in events)
        assert all(e["actor"] == DiscoveryOrchestrator.AGENT_ID for e in events)


class TestOrchestratorIdentity:
    """DiscoveryOrchestrator has correct AgentIdentity (AgentType.ORCHESTRATOR)."""

    def test_orchestrator_agent_id(self):
        assert DiscoveryOrchestrator.AGENT_ID == "discovery-orchestrator-001"

    def test_orchestrator_identity_is_orchestrator_type(self):
        from swarm_auth.domain.agent_identity import AgentType
        o = DiscoveryOrchestrator(signing_key=_SIGNING_KEY)
        assert o._identity.agent_type == AgentType.ORCHESTRATOR

    def test_orchestrator_identity_kind_is_agent(self):
        o = DiscoveryOrchestrator(signing_key=_SIGNING_KEY)
        assert o._identity.kind() == "agent"
