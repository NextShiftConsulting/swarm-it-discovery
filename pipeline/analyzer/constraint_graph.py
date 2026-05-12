"""
RSCT Constraint Graph for Paper Evaluation

Maps solver constraints to a graph structure for richer paper assessment.
Based on YRSN constraint graph architecture.

The graph encodes:
- Thresholds: Numeric boundaries (e.g., N_max = 0.5)
- Collapse types: Failure modes triggered by threshold violations
- Domains: Quality, Reliability, Stability
- Gates: Which gate catches which violations

Usage:
    from analyzer.constraint_graph import RSCTConstraintGraph, evaluate_paper_constraints

    graph = RSCTConstraintGraph()
    result = evaluate_paper_constraints(R=0.4, S=0.3, N=0.3, kappa=0.65)
    print(result.triggered_constraints)
    print(result.gate_diagnosis)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple


# =============================================================================
# Enums and Types
# =============================================================================

class ConstraintDomain(str, Enum):
    """Quality domains for constraint classification."""
    SIGNAL_PURITY = "signal_purity"      # α-related (R, N)
    STABILITY = "stability"               # σ-related (turbulence)
    COMPATIBILITY = "compatibility"       # κ-related (solver fit)
    CONSENSUS = "consensus"               # Multi-agent agreement


class CollapseType(str, Enum):
    """Types of failure modes in paper evaluation."""
    # Signal Purity failures (Gate 1)
    NOISE_SATURATION = "noise_saturation"      # N ≥ 0.5 - adversarial content dominates
    SIGNAL_STARVATION = "signal_starvation"    # R < 0.15 - no useful signal

    # Stability failures (Gate 2, 3)
    TURBULENCE = "turbulence"                  # σ > 0.5 - unstable representation
    PHASOR_CONFLICT = "phasor_conflict"        # Consensus < 0.4 - disagreement

    # Compatibility failures (Gate 3, 4)
    FORMAT_MISMATCH = "format_mismatch"        # κ_H low - high-level incompatibility
    GROUNDING_FAILURE = "grounding_failure"    # κ_L low - low-level health issues

    # Cross-domain (special)
    BRIDGE_PAPER = "bridge_paper"              # High S but intentional (not a failure)


class GateNumber(int, Enum):
    """The 4 RSCT gates."""
    GATE_1_INTEGRITY = 1      # N ≥ 0.5 → REJECT
    GATE_2_CONSENSUS = 2      # c < 0.4 → BLOCK
    GATE_3_ADMISSIBILITY = 3  # κ < κ_req(σ) → RE_ENCODE
    GATE_4_GROUNDING = 4      # κ_L < 0.3 → REPAIR


class RSCTDecision(str, Enum):
    """Gate decisions."""
    EXECUTE = "EXECUTE"       # Passed all gates
    RE_ENCODE = "RE_ENCODE"   # Failed Gate 3
    BLOCK = "BLOCK"           # Failed Gate 2
    REPAIR = "REPAIR"         # Failed Gate 4
    REJECT = "REJECT"         # Failed Gate 1


# =============================================================================
# Constraint Definitions
# =============================================================================

@dataclass
class Threshold:
    """A threshold that triggers a collapse when violated."""
    name: str
    metric: str              # R, S, N, kappa, sigma, alpha
    value: float
    direction: str           # "above" or "below" - violation occurs when metric is above/below threshold
    collapse_type: CollapseType
    domain: ConstraintDomain
    gate: GateNumber
    description: str

    def is_violated(self, metric_value: float) -> bool:
        """Check if this threshold is violated."""
        if self.direction == "above":
            return metric_value >= self.value
        else:
            return metric_value <= self.value

    def violation_margin(self, metric_value: float) -> float:
        """How much the metric exceeds the threshold."""
        if self.direction == "above":
            return max(0, metric_value - self.value)
        else:
            return max(0, self.value - metric_value)


@dataclass
class ConstraintViolation:
    """A detected constraint violation."""
    threshold: Threshold
    actual_value: float
    margin: float
    severity: str  # "fatal", "critical", "warning", "advisory"

    @property
    def message(self) -> str:
        direction_word = "exceeds" if self.threshold.direction == "above" else "below"
        return (
            f"{self.threshold.name}: {self.threshold.metric}={self.actual_value:.2f} "
            f"{direction_word} threshold {self.threshold.value:.2f} "
            f"(margin: {self.margin:.2f}) - {self.threshold.description}"
        )


@dataclass
class EvaluationResult:
    """Result of constraint graph evaluation."""
    # Input metrics
    R: float
    S: float
    N: float
    kappa: float
    sigma: float
    alpha: float  # purity = R/(R+N)

    # Violations detected
    violations: List[ConstraintViolation]

    # Gate analysis
    gate_reached: GateNumber
    decision: RSCTDecision
    blocking_gate: Optional[GateNumber]

    # Domain analysis
    domains_affected: List[ConstraintDomain]
    collapse_types: List[CollapseType]

    # Cross-domain detection
    is_bridge_paper: bool
    bridge_factor: float  # How much "bridging" content (high S but low N)

    # Human-readable diagnosis
    diagnosis: str
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metrics": {
                "R": self.R, "S": self.S, "N": self.N,
                "kappa": self.kappa, "sigma": self.sigma, "alpha": self.alpha,
            },
            "gate_reached": self.gate_reached.value,
            "decision": self.decision.value,
            "blocking_gate": self.blocking_gate.value if self.blocking_gate else None,
            "violations": [v.message for v in self.violations],
            "domains_affected": [d.value for d in self.domains_affected],
            "collapse_types": [c.value for c in self.collapse_types],
            "is_bridge_paper": self.is_bridge_paper,
            "bridge_factor": self.bridge_factor,
            "diagnosis": self.diagnosis,
            "recommendations": self.recommendations,
        }


# =============================================================================
# The Constraint Graph
# =============================================================================

class RSCTConstraintGraph:
    """
    Graph-based constraint evaluation for RSCT.

    Encodes the relationships between:
    - Metrics (R, S, N, κ, σ, α)
    - Thresholds (violation boundaries)
    - Collapse types (failure modes)
    - Gates (enforcement points)
    - Domains (quality categories)
    """

    def __init__(self):
        self.thresholds: Dict[str, Threshold] = {}
        self._build_default_graph()

    def _build_default_graph(self):
        """Build the default RSCT constraint graph."""

        # =====================================================================
        # Gate 1: Integrity Guard (Signal Purity)
        # =====================================================================

        self.add_threshold(Threshold(
            name="noise_saturation",
            metric="N",
            value=0.50,
            direction="above",
            collapse_type=CollapseType.NOISE_SATURATION,
            domain=ConstraintDomain.SIGNAL_PURITY,
            gate=GateNumber.GATE_1_INTEGRITY,
            description="Adversarial noise dominates - no solver can recover correct inference (Fano bound)",
        ))

        self.add_threshold(Threshold(
            name="signal_starvation",
            metric="R",
            value=0.15,
            direction="below",
            collapse_type=CollapseType.SIGNAL_STARVATION,
            domain=ConstraintDomain.SIGNAL_PURITY,
            gate=GateNumber.GATE_1_INTEGRITY,
            description="Insufficient relevant signal - paper lacks substantive content",
        ))

        self.add_threshold(Threshold(
            name="purity_floor",
            metric="alpha",
            value=0.30,
            direction="below",
            collapse_type=CollapseType.NOISE_SATURATION,
            domain=ConstraintDomain.SIGNAL_PURITY,
            gate=GateNumber.GATE_1_INTEGRITY,
            description="Purity α = R/(R+N) too low - information-theoretic ceiling on inference",
        ))

        # =====================================================================
        # Gate 2: Consensus Gate (Stability)
        # =====================================================================

        self.add_threshold(Threshold(
            name="high_turbulence",
            metric="sigma",
            value=0.50,
            direction="above",
            collapse_type=CollapseType.TURBULENCE,
            domain=ConstraintDomain.STABILITY,
            gate=GateNumber.GATE_2_CONSENSUS,
            description="Representational instability - trajectory may diverge",
        ))

        # =====================================================================
        # Gate 3: Admissibility (Compatibility)
        # =====================================================================

        self.add_threshold(Threshold(
            name="kappa_floor",
            metric="kappa",
            value=0.50,
            direction="below",
            collapse_type=CollapseType.FORMAT_MISMATCH,
            domain=ConstraintDomain.COMPATIBILITY,
            gate=GateNumber.GATE_3_ADMISSIBILITY,
            description="Low compatibility - representation doesn't fit solver well",
        ))

        self.add_threshold(Threshold(
            name="kappa_certified",
            metric="kappa",
            value=0.70,
            direction="below",
            collapse_type=CollapseType.FORMAT_MISMATCH,
            domain=ConstraintDomain.COMPATIBILITY,
            gate=GateNumber.GATE_3_ADMISSIBILITY,
            description="Below certification threshold - needs additional context",
        ))

        # =====================================================================
        # Gate 4: Grounding Repair
        # =====================================================================

        self.add_threshold(Threshold(
            name="grounding_floor",
            metric="kappa",
            value=0.30,
            direction="below",
            collapse_type=CollapseType.GROUNDING_FAILURE,
            domain=ConstraintDomain.COMPATIBILITY,
            gate=GateNumber.GATE_4_GROUNDING,
            description="Grounding failure - low-level health below floor",
        ))

        # =====================================================================
        # Advisory thresholds (not blocking, but informative)
        # =====================================================================

        self.add_threshold(Threshold(
            name="noise_warning",
            metric="N",
            value=0.25,
            direction="above",
            collapse_type=CollapseType.NOISE_SATURATION,
            domain=ConstraintDomain.SIGNAL_PURITY,
            gate=GateNumber.GATE_3_ADMISSIBILITY,  # Warning, not blocking
            description="Elevated noise - some content may mislead",
        ))

        self.add_threshold(Threshold(
            name="superfluous_high",
            metric="S",
            value=0.40,
            direction="above",
            collapse_type=CollapseType.BRIDGE_PAPER,  # Not a failure - may be intentional
            domain=ConstraintDomain.SIGNAL_PURITY,
            gate=GateNumber.GATE_3_ADMISSIBILITY,
            description="High background content - may be a bridge paper for multiple audiences",
        ))

    def add_threshold(self, threshold: Threshold):
        """Add a threshold to the graph."""
        self.thresholds[threshold.name] = threshold

    def get_thresholds_for_gate(self, gate: GateNumber) -> List[Threshold]:
        """Get all thresholds enforced at a specific gate."""
        return [t for t in self.thresholds.values() if t.gate == gate]

    def get_thresholds_for_domain(self, domain: ConstraintDomain) -> List[Threshold]:
        """Get all thresholds in a domain."""
        return [t for t in self.thresholds.values() if t.domain == domain]

    def evaluate(
        self,
        R: float,
        S: float,
        N: float,
        kappa: float,
        sigma: float = 0.3,
    ) -> EvaluationResult:
        """
        Evaluate paper metrics against the constraint graph.

        Args:
            R: Relevance (0-1)
            S: Superfluous (0-1)
            N: Noise (0-1)
            kappa: Compatibility score (0-1)
            sigma: Turbulence (0-1), default 0.3

        Returns:
            EvaluationResult with full diagnosis
        """
        # Compute derived metrics
        alpha = R / (R + N) if (R + N) > 0 else 0.5

        metrics = {
            "R": R, "S": S, "N": N,
            "kappa": kappa, "sigma": sigma, "alpha": alpha,
        }

        # Check all thresholds
        violations = []
        for threshold in self.thresholds.values():
            metric_value = metrics.get(threshold.metric, 0)
            if threshold.is_violated(metric_value):
                margin = threshold.violation_margin(metric_value)

                # Determine severity based on gate
                if threshold.gate == GateNumber.GATE_1_INTEGRITY:
                    severity = "fatal"
                elif threshold.gate == GateNumber.GATE_2_CONSENSUS:
                    severity = "critical"
                elif threshold.name in ["kappa_certified", "noise_warning", "superfluous_high"]:
                    severity = "advisory"
                else:
                    severity = "warning"

                violations.append(ConstraintViolation(
                    threshold=threshold,
                    actual_value=metric_value,
                    margin=margin,
                    severity=severity,
                ))

        # Determine gate reached and decision
        gate_reached, decision, blocking_gate = self._determine_gate_decision(violations, metrics)

        # Collect affected domains and collapse types
        domains_affected = list(set(v.threshold.domain for v in violations if v.severity in ["fatal", "critical", "warning"]))
        collapse_types = list(set(v.threshold.collapse_type for v in violations if v.severity in ["fatal", "critical", "warning"]))

        # Detect bridge paper
        is_bridge_paper = S > 0.35 and N < 0.25
        bridge_factor = S * (1 - N) if is_bridge_paper else 0

        # Generate diagnosis and recommendations
        diagnosis = self._generate_diagnosis(violations, decision, is_bridge_paper)
        recommendations = self._generate_recommendations(violations, decision, is_bridge_paper)

        return EvaluationResult(
            R=R, S=S, N=N, kappa=kappa, sigma=sigma, alpha=alpha,
            violations=violations,
            gate_reached=gate_reached,
            decision=decision,
            blocking_gate=blocking_gate,
            domains_affected=domains_affected,
            collapse_types=collapse_types,
            is_bridge_paper=is_bridge_paper,
            bridge_factor=bridge_factor,
            diagnosis=diagnosis,
            recommendations=recommendations,
        )

    def _determine_gate_decision(
        self,
        violations: List[ConstraintViolation],
        metrics: Dict[str, float],
    ) -> Tuple[GateNumber, RSCTDecision, Optional[GateNumber]]:
        """Determine which gate blocks and what decision to make."""

        # Check gates in order (security property)

        # Gate 1: Integrity
        gate1_violations = [v for v in violations if v.threshold.gate == GateNumber.GATE_1_INTEGRITY and v.severity == "fatal"]
        if gate1_violations:
            return GateNumber.GATE_1_INTEGRITY, RSCTDecision.REJECT, GateNumber.GATE_1_INTEGRITY

        # Gate 2: Consensus
        gate2_violations = [v for v in violations if v.threshold.gate == GateNumber.GATE_2_CONSENSUS and v.severity in ["fatal", "critical"]]
        if gate2_violations:
            return GateNumber.GATE_2_CONSENSUS, RSCTDecision.BLOCK, GateNumber.GATE_2_CONSENSUS

        # Gate 3/4: Admissibility + Grounding (Oobleck principle: kappa_req depends on sigma)
        kappa = metrics["kappa"]
        sigma = metrics["sigma"]
        kappa_req = 0.5 + 0.4 * sigma  # Oobleck: higher turbulence demands higher kappa

        if kappa < kappa_req:
            # Gate 4 refines severity within the failure range:
            # kappa < 0.30 is a grounding failure (REPAIR), otherwise admissibility (RE_ENCODE).
            if kappa < 0.30:
                return GateNumber.GATE_4_GROUNDING, RSCTDecision.REPAIR, GateNumber.GATE_4_GROUNDING
            return GateNumber.GATE_3_ADMISSIBILITY, RSCTDecision.RE_ENCODE, GateNumber.GATE_3_ADMISSIBILITY

        # All gates passed
        if kappa >= 0.70:
            return GateNumber.GATE_4_GROUNDING, RSCTDecision.EXECUTE, None
        else:
            # Passed but below certification
            return GateNumber.GATE_4_GROUNDING, RSCTDecision.REPAIR, None

    def _generate_diagnosis(
        self,
        violations: List[ConstraintViolation],
        decision: RSCTDecision,
        is_bridge_paper: bool,
    ) -> str:
        """Generate human-readable diagnosis."""

        if decision == RSCTDecision.EXECUTE:
            if is_bridge_paper:
                return "Certified. This is a bridge paper with high background content for cross-domain readers."
            return "Certified. Paper passes all quality gates."

        if decision == RSCTDecision.REJECT:
            fatal = [v for v in violations if v.severity == "fatal"]
            if fatal:
                return f"Rejected at Gate 1 (Integrity): {fatal[0].threshold.description}"
            return "Rejected due to noise saturation."

        if decision == RSCTDecision.BLOCK:
            return "Blocked at Gate 2 (Consensus): Representational instability or conflicting signals."

        if decision == RSCTDecision.RE_ENCODE:
            return "Needs re-encoding at Gate 3 (Admissibility): Compatibility below required threshold for current turbulence level."

        if decision == RSCTDecision.REPAIR:
            return "Needs repair at Gate 4 (Grounding): Low-level health issues need attention."

        return "Unknown state."

    def _generate_recommendations(
        self,
        violations: List[ConstraintViolation],
        decision: RSCTDecision,
        is_bridge_paper: bool,
    ) -> List[str]:
        """Generate actionable recommendations."""

        recommendations = []

        if decision == RSCTDecision.EXECUTE:
            recommendations.append("Safe to cite and build upon.")
            if is_bridge_paper:
                recommendations.append("Note: High background content serves cross-domain readers - skip sections you already know.")

        elif decision == RSCTDecision.REJECT:
            recommendations.append("Do not cite without independent verification.")
            recommendations.append("Look for alternative sources with lower noise.")
            for v in violations:
                if v.severity == "fatal" and "noise" in v.threshold.name.lower():
                    recommendations.append(f"Noise level {v.actual_value:.0%} exceeds safe threshold.")

        elif decision == RSCTDecision.BLOCK:
            recommendations.append("Wait for consensus to emerge - conflicting signals detected.")
            recommendations.append("Check for follow-up work or errata.")

        elif decision == RSCTDecision.RE_ENCODE:
            recommendations.append("Paper needs additional context to be useful.")
            recommendations.append("Consider reading prerequisite papers first.")
            recommendations.append("Core ideas may be sound but presentation needs work.")

        elif decision == RSCTDecision.REPAIR:
            recommendations.append("Verify key claims independently before citing.")
            recommendations.append("Check experimental methodology carefully.")

        # Add specific recommendations based on violations
        for v in violations:
            if v.severity == "advisory" and "superfluous" in v.threshold.name:
                if is_bridge_paper:
                    recommendations.append(f"Bridge paper: {v.actual_value:.0%} is background for newcomers - experts can skim.")
                else:
                    recommendations.append(f"Consider skimming background sections ({v.actual_value:.0%} context).")

        return recommendations


# =============================================================================
# Convenience Functions
# =============================================================================

# Singleton graph instance
_default_graph: Optional[RSCTConstraintGraph] = None

def get_constraint_graph() -> RSCTConstraintGraph:
    """Get the default constraint graph (singleton)."""
    global _default_graph
    if _default_graph is None:
        _default_graph = RSCTConstraintGraph()
    return _default_graph


def evaluate_paper_constraints(
    R: float,
    S: float,
    N: float,
    kappa: float,
    sigma: float = 0.3,
) -> EvaluationResult:
    """
    Evaluate paper metrics against RSCT constraints.

    Args:
        R: Relevance (0-1)
        S: Superfluous (0-1)
        N: Noise (0-1)
        kappa: Compatibility score (0-1)
        sigma: Turbulence (0-1)

    Returns:
        EvaluationResult with diagnosis and recommendations
    """
    graph = get_constraint_graph()
    return graph.evaluate(R, S, N, kappa, sigma)


def get_gate_diagnosis(result: EvaluationResult) -> str:
    """Get a concise gate diagnosis string."""
    gate_names = {
        GateNumber.GATE_1_INTEGRITY: "Integrity",
        GateNumber.GATE_2_CONSENSUS: "Consensus",
        GateNumber.GATE_3_ADMISSIBILITY: "Admissibility",
        GateNumber.GATE_4_GROUNDING: "Grounding",
    }

    if result.blocking_gate:
        return f"Blocked at Gate {result.blocking_gate.value} ({gate_names[result.blocking_gate]})"
    else:
        return f"Passed all 4 gates → {result.decision.value}"


__all__ = [
    # Enums
    "ConstraintDomain",
    "CollapseType",
    "GateNumber",
    "RSCTDecision",
    # Classes
    "Threshold",
    "ConstraintViolation",
    "EvaluationResult",
    "RSCTConstraintGraph",
    # Functions
    "get_constraint_graph",
    "evaluate_paper_constraints",
    "get_gate_diagnosis",
]
