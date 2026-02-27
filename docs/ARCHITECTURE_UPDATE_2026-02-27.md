# Architecture Update - February 27, 2026

## Summary

Updated repository structure and documentation to reflect the **3-repo ecosystem** after repository renames:
- `swarm-it` → `swarm-it-adk` (Agent Development Kit)
- `swarmit-site` → `swarm-it-api` (RSCT API backend)

## Changes Implemented

### 1. Fixed Import Path ✅
**File**: `pipeline/run.py`

**Before**:
```python
sys.path.insert(0, os.path.expanduser("~/GitHub/swarm-it/clients/python"))
```

**After**:
```python
sys.path.insert(0, os.path.expanduser("~/GitHub/swarm-it-adk/clients/python"))
```

**Impact**: Pipeline can now find the ADK client library at its new location.

---

### 2. Created Architecture Documentation ✅
**File**: `docs/ARCHITECTURE.md` (new, 400+ lines)

**Contents**:
- Complete 3-repo ecosystem explanation
- Dependency chain: `discovery → ADK → API`
- What each repo does and where it's deployed
- Infrastructure clarification (what `infra/` means)
- Deployment models and cross-repo coordination
- Environment variables and security practices

**Purpose**: Single source of truth for multi-repo architecture.

---

### 3. Added ADK Hybrid Runner ✅
**File**: `pipeline/run_adk.py` (new, 380+ lines)

**What It Does**:
- Wraps existing pipeline functions as agent tasks
- Uses ADK for orchestration, logging, coordination
- **Automatic fallback** to `run.py` if ADK not installed
- Same underlying logic, just agent-orchestrated

**Agents Created**:
- `ScannerAgent` - Wraps paper fetching
- `AnalystAgent` - Wraps topic matching + RSCT scoring
- `WriterAgent` - Wraps MDX generation
- `PublisherAgent` - Wraps deployment preparation

**Why Hybrid**:
- Safe dogfooding (no full rewrite)
- Keeps legacy runner as fallback
- Enables gradual migration to full autonomy
- Marketing credibility ("built with our own ADK")

**Usage**:
```bash
# ADK-orchestrated (falls back automatically if ADK not found)
python pipeline/run_adk.py

# Legacy procedural (always works)
python pipeline/run.py
```

---

### 4. Updated README ✅
**File**: `README.md`

**Changes**:
- Replaced old single-repo architecture diagram
- Added 3-repo ecosystem overview
- Updated Prerequisites (swarm-it-adk instead of swarm-it)
- Documented both runners (legacy vs ADK)
- Linked to full architecture docs

**New Section**:
```markdown
## Architecture

This repo is part of a **3-repo ecosystem**:

┌─────────────────────────────────────────────────────────────┐
│ swarm-it-adk         → Agent Development Kit (framework)    │
│ swarm-it-api         → RSCT API (api.swarms.network)        │
│ swarm-it-discovery   → THIS REPO (paper discovery site)     │
└─────────────────────────────────────────────────────────────┘
```

---

### 5. Clarified infra/ Status ✅
**File**: `infra/README.md`

**Added Warning**:
```markdown
⚠️ **IMPORTANT: This directory contains PROTOTYPE code only.**

**Actual production infrastructure is deployed from the `swarm-it-api` repository.**

This `infra/` directory was used for early planning and exploration. It is kept
for reference but should **NOT** be deployed. No `terraform.tfstate` exists here,
and the actual running infrastructure (ALB + ECS, not API Gateway + Lambda) is
managed elsewhere.
```

**Why This Matters**:
- Prevents confusion about why infrastructure code exists but isn't deployed
- Clarifies that production API is in different repo
- Saves future developers from running `terraform apply` in wrong place

---

## The 3-Repo Ecosystem (Clear Now)

### swarm-it-adk
- **What**: Agent Development Kit (framework + primitives)
- **Location**: `~/GitHub/swarm-it-adk`
- **Used By**: This repo's pipeline + customer applications
- **Deployment**: N/A (library, not service)

### swarm-it-api
- **What**: RSCT Certification API (FastAPI backend)
- **Deployed**: https://api.swarms.network
- **Infrastructure**: ALB + ECS/Fargate
- **Purpose**: Certify content with R/S/N decomposition + κ-scores

### swarm-it-discovery (this repo)
- **What**: Research paper discovery site
- **Deployed**: https://swarmit.nextshiftconsulting.com
- **Infrastructure**: S3 + CloudFront (GitHub Actions)
- **Purpose**: Automated paper discovery + review generation

---

## Benefits of This Update

### 1. Clarity
- ✅ No more confusion about which repo does what
- ✅ Clear dependency chain documented
- ✅ infra/ prototype status explicit

### 2. Dogfooding Strategy
- ✅ Hybrid ADK wrapper enables safe integration
- ✅ Legacy fallback prevents pipeline fragility
- ✅ Can showcase "built with our own ADK"

### 3. Developer Experience
- ✅ New developers understand architecture immediately
- ✅ Clear where to make changes (which repo)
- ✅ Deployment models documented

### 4. Marketing
- ✅ Reference implementation for ADK usage
- ✅ Credibility: "Our discovery site runs on ADK"
- ✅ Working example for customers to learn from

---

## Testing Checklist

### ADK Runner
- [ ] Install swarm-it-adk at `~/GitHub/swarm-it-adk`
- [ ] Run `python pipeline/run_adk.py --dry-run`
- [ ] Verify agents execute in sequence
- [ ] Check logs show agent coordination
- [ ] Test fallback: Rename ADK dir, verify falls back to legacy

### Legacy Runner (Baseline)
- [ ] Run `python pipeline/run.py --dry-run`
- [ ] Verify existing functionality unchanged
- [ ] Check import path finds ADK client

### Documentation
- [ ] Read `docs/ARCHITECTURE.md` - comprehensible?
- [ ] README architecture section makes sense?
- [ ] infra/README.md warning clear?

---

## What We Learned Today

### 1. Code ≠ Deployed Infrastructure
- Found Terraform code but no `.tfstate` file
- Assumed nothing was deployed
- Reality: Both api.swarms.network and swarms.network ARE running
- Infrastructure deployed from different repo

### 2. Repository Renames Clarified Everything
- `swarm-it` → `swarm-it-adk` (signals it's a framework)
- `swarmit-site` → `swarm-it-api` (stops "site vs backend" confusion)
- `nsc-swarmit` → conceptually `swarm-it-discovery` (what it does)

### 3. Hybrid Approach is Right
- Don't rewrite everything to use ADK immediately
- Wrap existing functions as agent tasks
- Keep legacy runner as fallback
- Migrate gradually to full autonomy

### 4. Dogfooding Adds Credibility
- "Our paper discovery runs on our own ADK" is powerful
- Finds ADK issues before customers do
- Provides working reference implementation

---

## Next Steps

### Immediate (Optional)
- [ ] Install swarm-it-adk and test `run_adk.py`
- [ ] Verify ADK client library works at new path
- [ ] Run pipeline to regenerate papers with fixed schema

### Short-Term (When ADK Stable)
- [ ] Add autonomous agent behaviors (adaptive thresholds)
- [ ] Implement retry logic in agents
- [ ] Add structured logging
- [ ] Multi-agent coordination (agents negotiate)

### Long-Term
- [ ] Full agent autonomy (agents make decisions)
- [ ] Real-time coordination (agents collaborate)
- [ ] Self-improving pipeline (agents learn from outcomes)

---

## Commit Details

**Commit**: `47235e7`
**Date**: February 27, 2026
**Files Changed**: 5
**Lines Added**: 818
**Lines Removed**: 15

**Files Modified**:
- `README.md` - Architecture section updated
- `pipeline/run.py` - Import path fixed
- `infra/README.md` - Prototype warning added
- `docs/ARCHITECTURE.md` - Created (400+ lines)
- `pipeline/run_adk.py` - Created (380+ lines)

---

## Related Documents

- [ARCHITECTURE.md](ARCHITECTURE.md) - Full 3-repo architecture
- [SWARM_ANALYSIS_FIXES.md](SWARM_ANALYSIS_FIXES.md) - 10-agent analysis results
- [NAVIGATION_INTEGRATION_PROPOSAL.md](NAVIGATION_INTEGRATION_PROPOSAL.md) - Multi-site nav
- [SITE_PRINCIPLES.md](../SITE_PRINCIPLES.md) - Why separate from nsc-main-gatsby

---

**Status**: Complete ✅
**Impact**: Documentation + code organization (no infrastructure changes)
**Risk**: Low (fallback to legacy runner if issues)
