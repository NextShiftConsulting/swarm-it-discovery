# Audience-Conditional RSN: A Research Direction

## The Problem

Current RSCT computes a single RSN decomposition per document, implicitly assuming one "correct" perspective. But for cross-domain papers, R and S are **reader-dependent**:

- What's "superfluous" to an expert is "essential background" to a newcomer
- Cross-domain papers intentionally include high S to build bridges
- Penalizing high S discourages the knowledge transfer we actually want

## The Kindness Principle

> "Kindness is the highest form of wisdom."

High S in cross-domain papers is not waste—it's **generosity**. A paper that explains ML concepts to biologists (or vice versa) is performing a valuable service that single-domain papers don't.

## Proposed Extension: RSN(reader | document)

### Formal Definition

Let $D$ be a document and $r$ be a reader profile (expertise vector across domains).

**Current RSCT:**
$$R + S + N = 1 \quad \text{(single decomposition)}$$

**Proposed:**
$$R(r|D) + S(r|D) + N(D) = 1$$

Where:
- $R(r|D)$ = Content that's new AND useful to reader $r$
- $S(r|D)$ = Content reader $r$ already knows (redundant for them)
- $N(D)$ = Adversarial content (reader-independent—errors are errors)

### Key Insight: N is Absolute, R and S are Relative

Noise (N) doesn't depend on the reader—factual errors, logical inconsistencies, and misleading claims are bad for everyone.

But Relevance (R) and Superfluous (S) depend on **what the reader already knows**:
- Expert: High prior knowledge → More S, less R
- Newcomer: Low prior knowledge → Less S, more R

### Reader Profiles

Define expertise levels per domain:

```python
reader_profiles = {
    "ml_expert": {"machine_learning": 0.9, "neuroscience": 0.2, "statistics": 0.7},
    "neuro_expert": {"machine_learning": 0.3, "neuroscience": 0.9, "statistics": 0.5},
    "phd_student": {"machine_learning": 0.4, "neuroscience": 0.3, "statistics": 0.4},
    "newcomer": {"machine_learning": 0.1, "neuroscience": 0.1, "statistics": 0.1},
}
```

### Computing Conditional RSN

1. **Segment document** into semantic chunks
2. **Classify each chunk** by domain (ML, neuro, methods, etc.)
3. **For each reader profile:**
   - Chunks in domains where reader expertise is HIGH → contribute to S
   - Chunks in domains where reader expertise is LOW → contribute to R
   - Chunks with errors/inconsistencies → contribute to N (always)

### The Bridge Factor

For cross-domain papers, compute a **bridge factor** (β):

$$\beta = \text{Var}(S(r|D)) \text{ across reader profiles}$$

High β means the paper serves diverse audiences differently—it's a **bridge paper**.

- β ≈ 0: Single-audience paper (experts only or newcomers only)
- β > 0.1: Bridge paper (valuable to multiple expertise levels)

## Practical Implementation

### For Discovery Reviews

Instead of:
> "This paper has 40% superfluous content."

Say:
> "**Reader's Guide:**
> - **ML researchers:** Skip §2.1 (background you know). Core contribution in §3-4.
> - **Neuroscientists:** The ML tutorial in §2 is well-written. Focus on §4 for neuro applications.
> - **Students:** Read fully—this is an excellent cross-domain introduction."

### For Quality Assessment

Don't penalize high S when β is high:

```python
def adjusted_quality(kappa, S, bridge_factor):
    """High S is fine if the paper is bridging domains."""
    if bridge_factor > 0.15:
        # This is a bridge paper - don't penalize S
        return kappa
    else:
        # Single-audience paper - S is actually waste
        return kappa * (1 - 0.2 * S)
```

## Research Questions

1. **How do we reliably detect reader expertise level?**
   - User profiles?
   - Reading history?
   - Self-reported?

2. **Can we segment documents by "who this is for"?**
   - Section-level audience detection
   - Automatic skip recommendations

3. **How does conditional RSN affect the 4-gate system?**
   - Gate 1 (N ≥ 0.5) is unchanged—noise is absolute
   - Gates 2-4 may need reader-conditioning

4. **What's the right UI for showing multiple RSN profiles?**
   - Tabs per reader type?
   - Adaptive based on logged-in user?
   - Summary with expandable details?

## Connection to Existing Work

- **Adaptive Learning Systems**: Personalized content based on learner state
- **Expertise Modeling**: Estimating user knowledge from behavior
- **Reading Level Assessment**: Flesch-Kincaid, but for domain expertise
- **Knowledge Graphs**: Mapping prerequisite relationships

## Next Steps

1. **Prototype**: Build a simple conditional RSN scorer
2. **Annotate**: Label a small corpus with multi-reader RSN
3. **Validate**: Check if conditional RSN predicts reading time/comprehension
4. **Integrate**: Add reader profiles to discovery pipeline

---

*This document captures a research direction inspired by the observation that "kindness is the highest form of wisdom" - high S content in cross-domain papers is an act of generosity, not waste.*
