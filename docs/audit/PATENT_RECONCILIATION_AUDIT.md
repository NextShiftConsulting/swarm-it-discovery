# Patent Reconciliation Audit: swarm-it-discovery

**Date:** 2026-04-24 (Re-audit)
**Patent:** US Application 19/575,615 (TUP96543)
**Status:** ADVISORY ONLY -- NO CODE CHANGES

---

## Executive Summary

swarm-it-discovery uses RSCT scoring for paper discovery. **Critical change since initial audit:** Commit `dbe991a` ("fix(C3): close P1 bypass") eliminated the three `allowed:True` bypass paths. Heuristic fallback now labeled `HEURISTIC_UNCERTIFIED`. No-score path returns `allowed:False, decision:UNCERTIFIED`. Error path returns `allowed:False, decision:ERROR`. **Remaining gap:** Publication gate not enforced -- `run.py` does not check `allowed` before blog generation. Gate 4 is structurally unreachable.

### Changes Since Initial Audit

- **P1 bypass CLOSED** for no-score and error paths (commit dbe991a)
- **Heuristic path labeled** `certification_method: "HEURISTIC_UNCERTIFIED"` (line 176)
- **No-score path** changed from `allowed:True, decision:PENDING` to `allowed:False, decision:UNCERTIFIED`
- **Error path** changed from `allowed:True` to `allowed:False, decision:ERROR`

---

## Findings

### CLAIM 1: R+S+N Decomposition

| Mode | Status | Evidence |
|------|--------|----------|
| With sidecar API | **COMPLIANT** | `run.py:218-264` -- real R,S,N from SwarmIt API |
| Heuristic fallback | **PARTIAL** (improved) | `run.py:157-194` -- R=min(0.9,score*1.2), S=min(0.9,score*0.9), N=max(0.1,1-score). R+S+N=1 enforced via normalization (lines 165-166). Now labeled `HEURISTIC_UNCERTIFIED`. Variables still named R,S,N (not r_heuristic). |
| No score available | **COMPLIANT** (FIXED) | `run.py:197-216` -- Returns `allowed:False, decision:UNCERTIFIED`, zeroed values. |

### P1: Certificate-First Bypass

| Path | Status | Evidence | Changed? |
|------|--------|----------|----------|
| No-score path | **FIXED** | `allowed:False, decision:UNCERTIFIED` | YES |
| Error path | **FIXED** | `allowed:False, decision:ERROR` | YES |
| Heuristic path | **IMPROVED** | `allowed` now gated by constraint graph result, labeled HEURISTIC_UNCERTIFIED | YES |
| Publication gate | **GAP** | `run.py:427-473` -- `generate_and_save()` called unconditionally. `allowed` flag not checked. | NEW finding |

### CLAIM 8: Four-Gate Pipeline (RSCTConstraintGraph)

| Gate | Status | Evidence |
|------|--------|----------|
| Gate 1 (N>=0.5 → REJECT) | **COMPLIANT** | `constraint_graph.py:200-209` |
| Gate 2 (sigma>0.5 → BLOCK) | **COMPLIANT** | `constraint_graph.py:237-246` |
| Gate 3 (Oobleck kappa_req) | **COMPLIANT** | `constraint_graph.py:429-434` -- `kappa_req = 0.5 + 0.4 * sigma` |
| Gate 4 (kappa<0.3 → REPAIR) | **STRUCTURALLY UNREACHABLE** | `constraint_graph.py:437-438`. Gate 3 catches all kappa<0.5 when sigma>=0. Gate 4 can only fire if sigma<0 (impossible). |

### P6: Embedding Provider Separation

| Status | Evidence |
|--------|----------|
| **PARTIAL** | SBERT (`all-MiniLM-L6-v2`, 384d) for discovery. Titan (`amazon.titan-embed-text-v1`, 1536d) for topic matching. No dimension guard -- mixed embeddings would silently produce nonsense cosine similarity. |

### P18: Credentials

**4 raw boto3.client() calls remain:**
- `run.py:616` -- boto3.client("s3") in upload_to_s3()
- `run.py:757` -- boto3.client("s3") in save_daily_report()
- `chart_generator.py:172` -- boto3.client("s3")
- `mdx_generator.py:121` -- boto3.client('bedrock-runtime')

`bedrock_matcher.py` is P18-compliant (uses get_aws_credentials()). `rsct_scorer.py` checks P18 first with fallback.

---

## Summary Scorecard

| Claim | Status | Severity | Changed? |
|-------|--------|----------|----------|
| 1 (RSN decomposition, sidecar) | **COMPLIANT** | -- | No |
| 1 (RSN decomposition, heuristic) | **PARTIAL** | MEDIUM -- labeled but still fabricated | Improved (labeled) |
| P1 (Certificate-first bypass) | **SIGNIFICANTLY IMPROVED** | MEDIUM -- publication gate missing | YES (3 bypasses closed) |
| 8 (Four gates) | **PARTIAL** | LOW -- Gate 4 unreachable | No |
| P6 (Embedding separation) | **PARTIAL** | LOW -- no dimension guard | No |
| P18 (Credentials) | **PARTIAL** | MEDIUM -- 4 raw boto3 calls | No |

---

## Priority Actions

1. **Publication gate** -- Add `if not cert["allowed"]: skip` guard before `generate_and_save()` in `run.py:427-473`.
2. **Gate 4 reachability** -- Review Gate 3/4 overlap; either adjust thresholds or document Gate 4 as defense-in-depth.
3. **P18** -- Replace 4 remaining raw boto3.client() calls with swarm_auth.
4. **Heuristic variables** -- Rename R,S,N to r_heuristic,s_heuristic,n_heuristic in fallback path.
