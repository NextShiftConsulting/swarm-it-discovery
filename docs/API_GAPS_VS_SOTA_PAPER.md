# API Gaps vs. SOTA Paper (RSCT Framework)

**Date**: February 27, 2026
**SOTA Paper**: "Intelligence as Representation-Solver Compatibility"
**Current API**: https://api.swarms.network

---

## Executive Summary

The current API implements a **simplified subset** of the full RSCT framework defined in the SOTA paper. While it provides core R/S/N decomposition and basic certification, it's **missing several critical components** required for full RSCT compliance, SR 11-7 regulatory compliance, and multi-modal AI systems.

**Status**: 🟡 Partial implementation (~60% complete)

---

## What the API Currently Returns

Based on testing (from `API_TEST_RESULTS.md`):

```json
{
  "id": "d60441e2afe47752",
  "timestamp": "2026-02-27T16:46:53.594730Z",
  "R": 0.374,
  "S": 0.3181,
  "N": 0.3079,
  "kappa_gate": 0.5485,
  "sigma": 0.0581,
  "decision": "REPAIR",
  "gate_reached": 4,
  "reason": "Low compatibility: kappa=0.55 < 0.7",
  "allowed": true,
  "pattern_flags": [],
  "pre_screen_rejection": false
}
```

---

## What the SOTA Paper Specifies

### Full Certificate Tuple (from Section Appendix, SR 11-7 Compliance)

The paper defines the complete logging tuple as:

```
𝓛 = (α, ω, α_ω, κ_gate, σ, gate_reached, outcome, t_stamp)
```

**Plus modal health breakdown:**
- `κ_H` - High-level modal health (text/symbolic)
- `κ_L` - Low-level modal health (vision/signal)
- `κ_interface` - Interface compatibility

**Plus diagnostic simplex (post-hoc):**
- `κ_A` - Algorithmic compatibility
- `κ_E` - Encoding efficiency
- `κ_T` - Tractability

**Plus multi-agent coordination:**
- `c` - Consensus coherence (phasor magnitude)

---

## Gap Analysis

### ✅ Currently Implemented

| Component | In API? | Notes |
|-----------|---------|-------|
| **R** (Relevance) | ✅ Yes | Core YRSN component |
| **S** (Superfluous) | ✅ Yes | Returned as `S` |
| **N** (Noise) | ✅ Yes | Core gating metric |
| **κ_gate** | ✅ Yes | Primary execution score |
| **σ** (Turbulence) | ✅ Yes | Stability metric |
| **decision** | ✅ Yes | Gate outcome |
| **gate_reached** | ✅ Yes | Which gate was reached |
| **timestamp** | ✅ Yes | ISO format |
| **pattern_flags** | ✅ Yes | Attack detection |

### ❌ Missing Components

| Component | Symbol | Definition | Why It Matters |
|-----------|--------|------------|----------------|
| **Purity** | α | `R/(R+N)` | Information-theoretic measure grounded in Fano's inequality |
| **OOD Confidence** | ω | `∈ [0,1]` | **CRITICAL**: Distributional reliability - is input in-distribution? |
| **Weighted Quality** | α_ω | `ω·α + (1-ω)·α_base` | Reliability-weighted purity with fallback |
| **Consensus Coherence** | c | `∈ [0,1]` | **Gate 2 requirement**: Multi-agent phasor alignment |
| **Modal Health - High** | κ_H | `∈ [0,1]` | Text/symbolic processing health |
| **Modal Health - Low** | κ_L | `∈ [0,1]` | Vision/signal processing health (Gate 4) |
| **Modal Health - Interface** | κ_interface | `∈ [0,1]` | Cross-modal alignment |
| **Diagnostic Simplex** | (κ_A, κ_E, κ_T) | Simplex constraint | Post-hoc root cause: Algorithmic/Encoding/Tractability |

---

## Gate Implementation Gaps

### SOTA Paper: 4 Gates (Canonical Order)

**Non-negotiable ordering** (security property, not heuristic):

1. **Gate 1 - Integrity Guard**: `N ≥ 0.5` → **REJECT**
2. **Gate 2 - Consensus Gate**: `c < 0.4` → **BLOCK**
3. **Gate 3 - Admissibility Gate (Oobleck)**: `κ_gate < κ_req(σ)` → **RE_ENCODE**
4. **Gate 4 - Grounding Repair**: `κ_L < 0.3` → **REPAIR**

**Pass all gates** → **EXECUTE**

### Current API: Decision Mapping

| SOTA Decision | Current API | Correct? |
|---------------|-------------|----------|
| **EXECUTE** | EXECUTE | ✅ Yes |
| **REJECT** | REJECT | ✅ Yes |
| **BLOCK** | BLOCK | ✅ Yes (but Gate 2 not implemented?) |
| **RE_ENCODE** | ❌ Missing | ❌ No - Maps to REPAIR instead |
| **REPAIR** | REPAIR | ⚠️ Partial - Used for both RE_ENCODE and REPAIR |
| N/A | DELEGATE | ⚠️ Extra - Not in SOTA spec |

**Issue**: The API appears to collapse **RE_ENCODE** (Gate 3) and **REPAIR** (Gate 4) into a single `REPAIR` decision. These should be distinct because:
- **RE_ENCODE**: Representation is incompatible → change encoding
- **REPAIR**: Low-level modal health issue → fix grounding/vision/signal

---

## Missing Gate 2: Consensus Coherence

**Not implemented in current API!**

```python
# Gate 2: Consensus Gate (MISSING)
if c < 0.4:
    return "BLOCK", "Phasor conflict: c={c}"
```

**Why it matters:**
- **Multi-agent systems**: Detects when sub-agents produce contradictory outputs
- **Failure mode 3.2**: "Phasor Conflict" - high confidence but contradictory answers
- **Example**: Financial compliance where LLM and rule engine disagree on classification

**Required inputs:**
- Consensus coherence `c` (phasor magnitude from multiple model outputs)
- Only relevant for multi-agent/multi-modal systems

---

## Missing Gate 4: Grounding Repair

**Partially implemented** - API returns `decision=REPAIR` but doesn't expose `κ_L`:

```python
# Gate 4: Grounding Repair (PARTIAL)
if κ_L < 0.3:
    return "REPAIR", κ_L
```

**Why it matters:**
- **Vision/signal processing health**: Detects low-level encoding failures
- **Example**: Image preprocessing corrupted, audio features malformed
- **Current issue**: API says "REPAIR" but doesn't tell you WHAT needs repair

**Required:**
- Return `κ_L` (low-level modal health) in response
- Distinguish from `κ_H` (high-level) and `κ_interface`

---

## Missing: Oobleck Principle (Gate 3)

**Partially implemented** - Gate 3 uses dynamic threshold but may not implement Landauer buffer:

```python
# Gate 3: Admissibility Gate (Oobleck)
κ_req(σ) = κ_base + λ·σ  # Default: 0.5 + 0.4·σ

# Landauer buffer [κ_req - 0.05, κ_req)
if κ_gate < κ_req - 0.05:
    return "RE_ENCODE", κ_req - κ_gate
elif κ_gate < κ_req:  # Gray zone
    if σ > 0.5:
        return "RE_ENCODE", "Turbulent gray zone"
    # else: cautiously proceed
```

**Current API behavior:**
- Uses `kappa_gate < 0.7` threshold (static)
- Paper specifies **dynamic threshold** that increases with turbulence
- Missing: Landauer tolerance buffer for measurement noise

---

## Missing: ω (Distributional Reliability)

**Critical for OOD detection** - Not returned by API:

```python
ω ∈ [0,1]  # OOD confidence: how confident are we the input is in-distribution?

α_ω = ω·α + (1-ω)·α_base  # Weighted purity with fallback
# Default: α_base = 0.5
```

**Why it matters:**
- **Failure mode 3.4**: "OOD Fabrication" - wild extrapolation outside training data
- **Financial compliance**: SR 11-7 requires distributional coverage documentation
- **Example**: CECL model trained on 2010-2020 data, deployed during 2023 rate spike

**Proxy estimators** (from paper Appendix):
- Softmax entropy (with calibration)
- Conformal non-conformity score
- MC Dropout variance

**Current gap**: API has no `omega` field in response

---

## Missing: Modal Health Breakdown

**Not exposed by API** - `κ_gate` is returned but not the components:

```python
κ_gate = min(κ_H, κ_L, κ_interface)
```

**Why the breakdown matters:**
- **Root cause diagnosis**: Which modality is the bottleneck?
- **κ_H low**: Text/symbolic encoding issue
- **κ_L low**: Vision/signal encoding issue (triggers Gate 4)
- **κ_interface low**: Modalities don't align (e.g., image caption mismatch)

**Example use case:**
- RAG system: `κ_H=0.85` (good retrieval), `κ_L=0.40` (poor table parsing), `κ_interface=0.72`
- **Diagnosis**: Fix table extraction, not retrieval

**Current gap**: API only returns `kappa_gate` (the min), not the individual components

---

## Missing: SR 11-7 Compliance Logging

**Required for regulatory compliance** (from SOTA paper Section Appendix):

> This tuple directly satisfies SR 11-7 Section 4(c) requirements: α and ω document data quality and distributional coverage; κ_gate and σ satisfy sensitivity analysis and stability monitoring; gate_reached and outcome provide timestamped documentation of model override decisions.

**Full logging tuple:**
```python
𝓛 = (
    α,              # Purity (data quality)
    ω,              # Distributional reliability
    α_ω,            # Weighted quality
    κ_gate,         # Execution score
    σ,              # Turbulence
    gate_reached,   # Which gate was reached
    outcome,        # Decision (EXECUTE/REJECT/BLOCK/RE_ENCODE/REPAIR)
    t_stamp         # ISO timestamp
)
```

**Current API response:**
- Has: `kappa_gate`, `sigma`, `gate_reached`, `decision`, `timestamp`
- Missing: `alpha`, `omega`, `alpha_omega`
- Missing: SR 11-7 export format in `/audit` endpoint

---

## Proxy Estimator Gaps

**From SOTA Paper Appendix B.1** - Proxy heuristics for real-time estimation:

### α (Purity) - Partially Implemented

✅ API computes R, S, N (can derive `α = R/(R+N)`)

Suggested proxies from paper:
- Perplexity ratio (language)
- Embedding coherence (multimodal)
- Imputation precision (structured data)

**Gap**: API doesn't explicitly return `alpha` (though client can compute it)

### κ (Compatibility) - Partial

✅ API returns `kappa_gate`
❌ API doesn't return modal breakdown `(κ_H, κ_L, κ_interface)`

Suggested proxies from paper:
- Retrieval precision@k (text/RAG)
- Schema coverage (tabular)
- Cross-modal alignment
- Graph edge integrity (AML)

### σ (Turbulence) - Implemented

✅ API returns `sigma`

Suggested proxies from paper:
- Softmax entropy
- Conformal non-conformity score
- MC Dropout variance
- Looped model exit count

### ω (OOD Confidence) - NOT Implemented

❌ API doesn't return `omega`

Suggested proxies from paper:
- Conformal prediction sets
- Distance to nearest training example
- Mahalanobis distance in embedding space

---

## Decision Naming Mismatch

### SOTA Paper Decisions

1. **EXECUTE** - Pass all gates, high quality
2. **REJECT** - Gate 1 fail (N ≥ 0.5)
3. **BLOCK** - Gate 2 fail (c < 0.4)
4. **RE_ENCODE** - Gate 3 fail (κ_gate < κ_req(σ))
5. **REPAIR** - Gate 4 fail (κ_L < 0.3)

### Current API Decisions

From testing:
1. **EXECUTE** - High quality ✅
2. **REPAIR** - Low quality but allowed ⚠️ (conflates RE_ENCODE and REPAIR)
3. **DELEGATE** - Human review needed ❓ (not in SOTA spec)
4. **BLOCK** - Policy violation ✅
5. **REJECT** - Security threat ✅

**Issue**:
- `REPAIR` is overloaded (used for both Gate 3 and Gate 4)
- `DELEGATE` not defined in SOTA paper
- Missing distinct `RE_ENCODE` decision

---

## Priority Gaps (Critical)

### 🔴 P0 - Breaks Core Theory

1. **Missing ω (OOD confidence)**
   - Required for Failure Mode 3.4 (OOD Fabrication)
   - Required for SR 11-7 distributional coverage
   - **Impact**: Can't detect out-of-distribution inputs

2. **Missing consensus coherence (c)**
   - Gate 2 not implemented
   - Required for multi-agent systems
   - **Impact**: Can't detect phasor conflicts (contradictory outputs)

3. **RE_ENCODE vs REPAIR conflation**
   - Two different failure modes mapped to same decision
   - **Impact**: Client can't distinguish encoding issue from grounding issue

### 🟡 P1 - Limits Usability

4. **Missing modal health breakdown (κ_H, κ_L, κ_interface)**
   - Only returns `kappa_gate` (min)
   - **Impact**: Can't diagnose which modality failed

5. **Missing α (purity) in response**
   - Computed internally but not returned
   - **Impact**: Client must recompute from R/N

6. **Missing α_ω (weighted quality)**
   - Requires ω to compute
   - **Impact**: Can't implement reliability-weighted decisions

### 🟢 P2 - Nice to Have

7. **Missing diagnostic simplex (κ_A, κ_E, κ_T)**
   - Post-hoc root cause analysis
   - **Impact**: Less detailed failure attribution

8. **Missing SR 11-7 export format**
   - `/audit` endpoint exists but format unclear
   - **Impact**: May need custom formatting for compliance

---

## Implementation Recommendations

### Phase 1: Critical Additions

1. **Add ω (OOD confidence) to response**
   ```json
   {
     "omega": 0.85,
     "alpha": 0.374,
     "alpha_omega": 0.361
   }
   ```

2. **Add consensus coherence (c) for multi-agent**
   ```json
   {
     "consensus_coherence": 0.92,
     "phasor_conflict": false
   }
   ```

3. **Split REPAIR into RE_ENCODE and REPAIR**
   ```json
   {
     "decision": "RE_ENCODE",  // Gate 3 failure
     "reason": "Low compatibility: kappa=0.62 < kappa_req(0.54)=0.716"
   }
   ```
   vs
   ```json
   {
     "decision": "REPAIR",  // Gate 4 failure
     "reason": "Low-level modal health: kappa_L=0.25 < 0.3",
     "kappa_L": 0.25
   }
   ```

### Phase 2: Modal Health Breakdown

4. **Return modal health components**
   ```json
   {
     "kappa_gate": 0.65,
     "kappa_H": 0.78,
     "kappa_L": 0.65,
     "kappa_interface": 0.71,
     "bottleneck": "kappa_L"
   }
   ```

### Phase 3: SR 11-7 Compliance

5. **Full certificate logging tuple**
   ```json
   {
     "certificate": {
       "alpha": 0.374,
       "omega": 0.85,
       "alpha_omega": 0.361,
       "kappa_gate": 0.65,
       "sigma": 0.38,
       "gate_reached": 1,
       "outcome": "REJECT",
       "timestamp": "2026-02-27T16:46:53.594730Z"
     }
   }
   ```

6. **SR 11-7 audit export**
   - Add `/api/v1/audit` format option: `format=SR-11-7`
   - Include full certificate tuple for each execution
   - Aggregate distributional stats (α, ω) over time windows

---

## Testing Gaps

### What We Tested
- ✅ R/S/N decomposition (benign vs attack)
- ✅ Pattern detection (injection, jailbreak, gibberish)
- ✅ Basic kappa_gate threshold
- ✅ Sigma (turbulence) presence

### What We Didn't Test
- ❌ OOD confidence (ω) - not in response
- ❌ Consensus coherence (c) - Gate 2
- ❌ Modal health breakdown (κ_H, κ_L, κ_interface)
- ❌ Oobleck dynamic threshold: κ_req(σ) = 0.5 + 0.4·σ
- ❌ Landauer gray zone behavior
- ❌ RE_ENCODE vs REPAIR distinction
- ❌ Multi-agent phasor conflict detection

---

## Comparison Table

| Feature | SOTA Paper | Current API | Gap |
|---------|-----------|-------------|-----|
| R, S, N decomposition | Required | ✅ Present | None |
| α (purity) | `R/(R+N)` | ⚠️ Computable | Should return explicitly |
| ω (OOD confidence) | Required | ❌ Missing | **Critical** |
| α_ω (weighted quality) | Required | ❌ Missing | **Critical** |
| κ_gate | `min(κ_H, κ_L, κ_interface)` | ✅ Present | Modal breakdown missing |
| σ (turbulence) | Required | ✅ Present | None |
| c (consensus) | Required (Gate 2) | ❌ Missing | **Critical** for multi-agent |
| Gate 1 (Integrity) | N ≥ 0.5 → REJECT | ✅ Working | None |
| Gate 2 (Consensus) | c < 0.4 → BLOCK | ❌ Missing | **Critical** |
| Gate 3 (Oobleck) | κ < κ_req(σ) → RE_ENCODE | ⚠️ Partial | Static threshold, no RE_ENCODE |
| Gate 4 (Grounding) | κ_L < 0.3 → REPAIR | ⚠️ Partial | κ_L not returned |
| Decision: EXECUTE | Pass all gates | ✅ Working | None |
| Decision: REJECT | Gate 1 fail | ✅ Working | None |
| Decision: BLOCK | Gate 2 fail | ⚠️ Exists | Gate 2 not implemented |
| Decision: RE_ENCODE | Gate 3 fail | ❌ Missing | **Critical** |
| Decision: REPAIR | Gate 4 fail | ⚠️ Overloaded | Conflated with RE_ENCODE |
| Decision: DELEGATE | N/A | ⚠️ Extra | Not in SOTA spec |
| SR 11-7 logging | Full tuple | ⚠️ Partial | Missing α, ω, α_ω |

---

## Questions for API Team

1. **Is ω (OOD confidence) computed internally but not returned?**
   - If yes: Just expose it in response
   - If no: Need to implement OOD detection

2. **Is consensus coherence (c) relevant for single-model deployments?**
   - If single model only: Gate 2 can be skipped
   - If multi-agent planned: Gate 2 critical

3. **Why is DELEGATE in the decision set?**
   - Not in SOTA paper
   - Is this a business requirement or implementation artifact?

4. **Is Oobleck dynamic threshold implemented?**
   - Test: Does threshold change with σ?
   - Current testing suggests static threshold (0.7)

5. **What's the roadmap for SR 11-7 full compliance?**
   - Need: Full certificate tuple in audit exports
   - Need: Distributional coverage documentation

---

## Next Steps

### Immediate (Can Do Now)

1. **Expose α (purity) in API response**
   - Already computed: `alpha = R / (R + N)`
   - Add to JSON response

2. **Document decision mapping**
   - Clarify REPAIR vs RE_ENCODE vs DELEGATE
   - Update API docs with SOTA paper terminology

3. **Test Oobleck behavior**
   - Vary σ (turbulence) in inputs
   - Check if threshold adapts: κ_req(σ) = 0.5 + 0.4·σ

### Short-Term (Next Sprint)

4. **Implement ω (OOD confidence)**
   - Choose proxy: conformal prediction, Mahalanobis distance, etc.
   - Add to response: `omega`, `alpha_omega`

5. **Add modal health breakdown**
   - Return: `kappa_H`, `kappa_L`, `kappa_interface`
   - Identify bottleneck

6. **Split RE_ENCODE and REPAIR**
   - Gate 3 fail → `RE_ENCODE`
   - Gate 4 fail → `REPAIR`

### Long-Term (Roadmap)

7. **Implement Gate 2 (Consensus)**
   - For multi-agent/multi-modal systems
   - Return: `consensus_coherence`, decision `BLOCK`

8. **SR 11-7 full compliance**
   - Full certificate tuple export
   - Audit format: `format=SR-11-7`

9. **Post-hoc diagnostic simplex**
   - Root cause attribution: `(κ_A, κ_E, κ_T)`
   - Requires solver execution feedback

---

## Conclusion

The current API implements **~60% of the full RSCT framework**:

✅ **Strong foundation**: R/S/N decomposition, pattern detection, basic gating
⚠️ **Missing critical components**: ω (OOD), c (consensus), modal health, RE_ENCODE decision
❌ **SR 11-7 gaps**: Incomplete certificate tuple, no distributional coverage

**Recommendation**: Prioritize **ω (OOD confidence)** and **modal health breakdown** to reach ~80% compliance with SOTA paper.

---

## Related Documents

- [API_TEST_RESULTS.md](API_TEST_RESULTS.md) - Current API testing
- [PIPELINE_CERTIFICATION_STRATEGY.md](PIPELINE_CERTIFICATION_STRATEGY.md) - How we use the API
- SOTA Paper: "Intelligence as Representation-Solver Compatibility"

---

**Date**: February 27, 2026
**Status**: Analysis complete, awaiting API team review
