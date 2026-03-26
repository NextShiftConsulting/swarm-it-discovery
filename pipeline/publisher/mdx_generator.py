"""
MDX Generator - Create blog posts from matched papers.

P18 Compliance: All credentials via swarm-it-auth.
"""

import os
import sys
import re
import yaml
from datetime import datetime
from dateutil import parser as date_parser
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional

# P18 v3.0 - Unified credential access
from swarm_auth import get_credential


def normalize_date(date_str: str, fallback_date: str = None) -> str:
    """
    Normalize date string to YYYY-MM-DD format.

    Handles various input formats:
    - ISO dates: "2026-03-09", "2026-03-09T00:00:00Z"
    - Month names: "2026-Mar-09", "March 9, 2026"
    - Empty strings or None
    - Invalid/future dates (>2 years from now)

    Returns fallback_date or today's date if input is invalid.
    """
    if not date_str or not isinstance(date_str, str) or date_str.strip() == '':
        return fallback_date or datetime.utcnow().strftime("%Y-%m-%d")

    try:
        # Parse with dateutil (handles many formats)
        parsed = date_parser.parse(date_str, fuzzy=True)

        # Reject dates more than 2 years in the future (likely data errors)
        max_future = datetime.utcnow().year + 2
        if parsed.year > max_future:
            print(f"Warning: Future date {date_str} rejected, using fallback")
            return fallback_date or datetime.utcnow().strftime("%Y-%m-%d")

        # Reject dates before 1990 (unlikely for ML papers)
        if parsed.year < 1990:
            print(f"Warning: Old date {date_str} rejected, using fallback")
            return fallback_date or datetime.utcnow().strftime("%Y-%m-%d")

        return parsed.strftime("%Y-%m-%d")
    except (ValueError, TypeError) as e:
        print(f"Warning: Could not parse date '{date_str}': {e}")
        return fallback_date or datetime.utcnow().strftime("%Y-%m-%d")

# Optional: OpenAI for content generation
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

# Optional: Bedrock/Claude for content generation
try:
    import boto3
    HAS_BEDROCK = True
except ImportError:
    HAS_BEDROCK = False


@dataclass
class PaperData:
    """Paper data for blog generation."""
    id: str
    title: str
    abstract: str
    authors: List[str]
    source: str
    url: str
    pdf_url: Optional[str]
    published_date: str
    similarity_score: float
    matched_topics: List[str]
    categories: List[str] = None
    # RSCT certification metrics
    rsct_R: float = None  # Relevance
    rsct_S: float = None  # Spurious/Support
    rsct_N: float = None  # Noise
    rsct_kappa: float = None  # Compatibility score
    rsct_decision: str = None  # EXECUTE, REPAIR, BLOCK, RE_ENCODE, REJECT
    # Graph-based insights (from constraint graph)
    rsct_alpha: float = None  # Purity = R/(R+N)
    rsct_sigma: float = None  # Turbulence
    rsct_diagnosis: str = None  # Human-readable diagnosis
    rsct_recommendations: List[str] = None  # Actionable recommendations
    rsct_is_bridge_paper: bool = False  # Cross-domain paper flag
    rsct_collapse_types: List[str] = None  # Detected failure modes
    rsct_violations: List[str] = None  # Constraint violations


@dataclass
class BlogPost:
    """Generated blog post."""
    slug: str
    filename: str
    content: str
    frontmatter: dict


class MDXGenerator:
    """Generate MDX paper reviews from matched papers."""

    def __init__(self, output_dir: str = "content/reviews", use_bedrock: bool = True):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.llm_provider = None

        # Try Bedrock first (preferred for Claude)
        if use_bedrock and HAS_BEDROCK:
            try:
                self.bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
                self.llm_provider = "bedrock"
                print("Using AWS Bedrock (Claude) for analysis generation")
            except Exception as e:
                print(f"Bedrock not available: {e}")

        # Fall back to OpenAI (P18 compliant)
        openai_key = get_credential("OPENAI_API_KEY")
        if not self.llm_provider and HAS_OPENAI and openai_key:
            self.openai = OpenAI(api_key=openai_key)
            self.llm_provider = "openai"
            print("Using OpenAI for analysis generation")

        if not self.llm_provider:
            print("Warning: No LLM configured, using template-based generation")

    @property
    def use_llm(self) -> bool:
        return self.llm_provider is not None

    def _slugify(self, text: str) -> str:
        """Convert text to URL-friendly slug."""
        slug = text.lower()
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        slug = slug.strip('-')
        return slug[:60]

    def _sanitize_for_mdx(self, text: str) -> str:
        """Remove LaTeX commands and escape special chars for MDX."""
        # Remove LaTeX commands like \textit{...}, \textbf{...}, etc.
        text = re.sub(r'\\text\w+\{([^}]*)\}', r'\1', text)
        text = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', text)
        text = re.sub(r'\\[a-zA-Z]+', '', text)
        # Remove remaining backslashes that could break MDX
        text = text.replace('\\', '')
        # Escape curly braces for JSX
        text = text.replace('{', '\\{').replace('}', '\\}')
        return text

    def _extract_tags(self, paper: PaperData) -> List[str]:
        """Extract tags from paper."""
        tags = set()

        # From categories
        if paper.categories:
            for cat in paper.categories[:3]:
                tags.add(cat.replace(".", "-").lower())

        # From matched topics
        for topic in paper.matched_topics[:2]:
            tags.add(self._slugify(topic))

        # From title keywords
        keywords = ["transformer", "llm", "agent", "safety", "alignment",
                    "representation", "learning", "neural", "diffusion"]
        title_lower = paper.title.lower()
        for kw in keywords:
            if kw in title_lower:
                tags.add(kw)

        return list(tags)[:5]

    def _generate_graph_insights_section(self, paper: PaperData) -> str:
        """Generate the graph-based insights section for the review."""
        sections = []

        # Diagnosis from constraint graph
        if paper.rsct_diagnosis:
            sections.append(f"**Diagnosis:** {paper.rsct_diagnosis}")

        # Bridge paper notice
        if paper.rsct_is_bridge_paper:
            sections.append(
                "\n**Cross-Domain Paper:** This paper bridges multiple fields. "
                "High background content is intentional to help readers from different domains. "
                "Skip sections covering your area of expertise."
            )

        # Recommendations
        if paper.rsct_recommendations and len(paper.rsct_recommendations) > 0:
            rec_items = "\n".join([f"- {r}" for r in paper.rsct_recommendations[:4]])
            sections.append(f"\n**Recommendations:**\n{rec_items}")

        # Constraint violations (if any warnings)
        if paper.rsct_violations and len(paper.rsct_violations) > 0:
            violation_items = "\n".join([f"- {v}" for v in paper.rsct_violations[:3]])
            sections.append(f"\n**Quality Concerns:**\n{violation_items}")

        # Collapse types (failure modes detected)
        if paper.rsct_collapse_types and len(paper.rsct_collapse_types) > 0:
            collapse_str = ", ".join(paper.rsct_collapse_types)
            sections.append(f"\n**Detected Issues:** {collapse_str}")

        if sections:
            return "\n\n### Constraint Analysis\n\n" + "\n".join(sections) + "\n"
        return ""

    def _generate_analysis_llm(self, paper: PaperData) -> str:
        """Use LLM to generate paper analysis."""
        # Build RSCT context
        rsct_context = ""
        if paper.rsct_kappa is not None:
            r_val = f"{paper.rsct_R:.3f}" if paper.rsct_R else "N/A"
            s_val = f"{paper.rsct_S:.3f}" if paper.rsct_S else "N/A"
            n_val = f"{paper.rsct_N:.3f}" if paper.rsct_N else "N/A"
            rsct_context = f"""
RSCT Certification Metrics:
- κ-gate (compatibility): {paper.rsct_kappa:.3f}
- R (Relevant signal): {r_val}
- S (Superfluous content): {s_val}
- N (Adversarial noise): {n_val}
- α (Purity = R/(R+N)): {float(paper.rsct_R or 0) / (float(paper.rsct_R or 0) + float(paper.rsct_N or 0.01)):.3f}
- Decision: {paper.rsct_decision or 'PENDING'}
"""

        # Determine RSCT gate interpretation
        kappa = paper.rsct_kappa or 0
        if kappa >= 0.7:
            gate_interp = "passes the κ-gate (≥0.7), qualifying for EXECUTE - direct integration into research workflows"
        elif kappa >= 0.5:
            gate_interp = "reaches Gate 4 but doesn't pass κ-gate (<0.7), suggesting REPAIR - valuable with additional context"
        elif kappa >= 0.3:
            gate_interp = "flags at the stability gate, suggesting DELEGATE - needs expert review before integration"
        else:
            gate_interp = "flags early in the pipeline, suggesting careful evaluation before use"

        # Calculate metrics for the prompt
        R_val = float(paper.rsct_R or 0.5)
        S_val = float(paper.rsct_S or 0.3)
        N_val = float(paper.rsct_N or 0.1)
        purity = R_val / (R_val + N_val) if (R_val + N_val) > 0 else 0.5

        # Detect cross-domain papers (multiple topics or high S)
        is_cross_domain = len(paper.matched_topics or []) > 1 or S_val > 0.35

        # Determine trust level based on scores
        if kappa >= 0.85 and N_val < 0.15:
            trust_level = "HIGH - Core claims well-supported, safe to build on"
            read_time = "Worth deep reading (2-3 hours)"
        elif kappa >= 0.7 and N_val < 0.25:
            trust_level = "MODERATE - Solid work, verify key results before building on"
            read_time = "Worth reading (1-2 hours), skim supplementary"
        elif kappa >= 0.5:
            trust_level = "CAUTIOUS - Interesting ideas, but validate independently"
            read_time = "Skim first (30 min), deep read only if directly relevant"
        else:
            trust_level = "LOW - Treat as preliminary/speculative"
            read_time = "Quick skim only (15 min), wait for follow-up work"

        # Cross-domain guidance
        cross_domain_note = ""
        if is_cross_domain:
            cross_domain_note = f"""
**Cross-Domain Paper Detected ({S_val:.0%} background/context content):**
This paper bridges multiple fields. High background content is a FEATURE, not a bug—it helps readers from different domains understand the work. When reviewing:
- Identify which sections are "background for X experts" vs "background for Y experts"
- Help readers know what they can skip based on their expertise
- Don't penalize the paper for being accessible to multiple audiences
"""

        prompt = f"""You are a research advisor helping PhD students decide what papers to read and how to use them. Write a practical, actionable review.

**Paper:**
Title: {paper.title}
Abstract: {paper.abstract}
Topics: {', '.join(paper.matched_topics) if paper.matched_topics else 'General ML'}

**Quality Signals (from automated analysis):**
- Signal strength: {R_val:.0%} of content directly supports claims
- Background/context: {S_val:.0%} supporting material for readers from other fields
- Noise level: {N_val:.0%} potentially misleading content
- Overall reliability: {kappa:.0%}
- Trust level: {trust_level}
- Suggested time investment: {read_time}
{cross_domain_note}
**Write a review (700-900 words) with these sections:**

## One-Sentence Summary
What this paper does, in plain English. No jargon.

## Key Innovation
What's actually NEW here vs. incremental improvement? Be honest - many papers oversell novelty.

## Should You Read This?
**If you work on [X]**: Yes/No/Maybe, because...
**If you work on [Y]**: Yes/No/Maybe, because...
(Pick 2-3 relevant research areas based on the paper's topics)

## The Good
- What parts are solid and trustworthy?
- What can you cite without verification?
- Where does the paper excel?

## The Gaps
- What assumptions does the paper make that might not hold?
- What's missing from the evaluation?
- Where should you be skeptical?
- What would you need to verify before building on this?

## How to Read This Paper
Practical reading guide tailored to your background:
- **If you're from [Domain A]**: Which sections can you skip? What's new for you?
- **If you're from [Domain B]**: Which background sections help you? What's the core for you?
- **Must read (everyone)**: Which sections contain the core contribution?
- **Verify**: Which claims need independent validation?
(Identify the relevant domains from the paper's topics and give specific section guidance)

## Bottom Line
One paragraph: What's the actionable takeaway? How might this change what you do in your research?

**Style Guidelines:**
- Write for a busy PhD student who reads 10+ papers/week
- Be direct and practical - they need to make decisions
- Avoid vague praise ("interesting", "promising", "novel approach")
- Give specific, actionable guidance
- It's OK to say "this paper is not worth your time" if that's true
- Don't pad with generic observations - every sentence should add value

Write the review now:"""

        if self.llm_provider == "bedrock":
            return self._call_bedrock(prompt)
        else:
            return self._call_openai(prompt)

    def _call_bedrock(self, prompt: str) -> str:
        """Call Claude via AWS Bedrock."""
        import json
        response = self.bedrock.invoke_model(
            modelId="anthropic.claude-3-haiku-20240307-v1:0",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "messages": [{"role": "user", "content": prompt}]
            })
        )
        result = json.loads(response['body'].read())
        return result['content'][0]['text']

    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API."""
        response = self.openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
        )
        return response.choices[0].message.content

    def _generate_analysis_template(self, paper: PaperData) -> str:
        """Template-based analysis when LLM unavailable."""
        abstract = paper.abstract or ""
        first_sentence = abstract.split('.')[0] + '.' if '.' in abstract else abstract[:200]
        topics = ', '.join(paper.matched_topics) if paper.matched_topics else 'machine learning'

        # Calculate scores
        kappa = paper.rsct_kappa or 0.5
        R = paper.rsct_R or 0.5
        N = paper.rsct_N or 0.2

        # Generate practical guidance based on scores
        if kappa >= 0.8 and N < 0.15:
            trust = "HIGH"
            guidance = "Core claims appear well-supported. Safe to cite and build upon."
            time_rec = "Worth a deep read (1-2 hours)"
        elif kappa >= 0.7:
            trust = "MODERATE"
            guidance = "Solid work overall. Verify key experimental results before building on this."
            time_rec = "Worth reading (1 hour), focus on methods and results"
        elif kappa >= 0.5:
            trust = "CAUTIOUS"
            guidance = "Interesting direction but validate claims independently before citing."
            time_rec = "Skim first (30 min), deep read only if directly relevant"
        else:
            trust = "LOW"
            guidance = "Treat as preliminary work. Wait for replication or follow-up studies."
            time_rec = "Quick scan only (15 min)"

        return f"""## One-Sentence Summary

{first_sentence}

## Should You Read This?

**Time investment:** {time_rec}

**If you work on {topics}:** This paper may be relevant to your research. The abstract suggests contributions in this area.

**Trust level:** {trust} - {guidance}

## What We Know From Automated Analysis

- **{R:.0%} signal strength** - Proportion of content directly supporting claims
- **{N:.0%} noise detected** - Content that may need verification
- **Reliability:** {kappa:.0%}

## The Abstract

{abstract}

## Reading Recommendation

Based on automated quality analysis, we recommend:
- **Read carefully:** Methods section (verify the approach)
- **Check:** Experimental setup and baselines
- **Verify:** Any claims that seem too good to be true

*This is an automated assessment. For nuanced analysis, consult the full paper and related work.*"""

    def generate_post(self, paper: PaperData) -> BlogPost:
        """Generate a blog post from paper data."""
        today = datetime.utcnow()
        slug = f"{today.strftime('%Y-%m-%d')}-{self._slugify(paper.title)}"

        # Generate analysis
        if self.use_llm:
            try:
                analysis = self._generate_analysis_llm(paper)
            except Exception as e:
                print(f"LLM error: {e}")
                analysis = self._generate_analysis_template(paper)
        else:
            analysis = self._generate_analysis_template(paper)

        # Infer difficulty from kappa score
        if paper.rsct_kappa:
            if paper.rsct_kappa >= 0.9:
                difficulty = "advanced"
            elif paper.rsct_kappa >= 0.75:
                difficulty = "intermediate"
            else:
                difficulty = "beginner"
        else:
            difficulty = "intermediate"  # Default when no RSCT data

        # Build frontmatter with frontend-expected schema
        frontmatter = {
            # Core metadata
            "title": paper.title,
            "arxiv_id": paper.id.replace("arxiv:", "") if paper.id.startswith("arxiv:") else paper.id,
            "authors": paper.authors[:5],
            "published_date": normalize_date(paper.published_date, today.strftime("%Y-%m-%d")),
            "go_live_date": today.strftime("%Y-%m-%d"),  # Go live today

            # RSCT Certification (top-level fields for frontend)
            # Use actual values or estimate from similarity_score
            "kappa": round(paper.rsct_kappa, 3) if paper.rsct_kappa is not None else round(paper.similarity_score * 0.8, 3),
            "R": round(paper.rsct_R, 3) if paper.rsct_R is not None else round(paper.similarity_score * 0.5, 3),
            "S": round(paper.rsct_S, 3) if paper.rsct_S is not None else round(paper.similarity_score * 0.4, 3),
            "N": round(paper.rsct_N, 3) if paper.rsct_N is not None else round(max(0.1, 1.0 - paper.similarity_score) * 0.3, 3),
            "rsn_score": f"{paper.rsct_R or paper.similarity_score * 0.5:.2f}/{paper.rsct_S or paper.similarity_score * 0.4:.2f}/{paper.rsct_N or max(0.1, 1.0 - paper.similarity_score) * 0.3:.2f}",

            # Classification
            "tags": self._extract_tags(paper),
            "primary_topic": paper.matched_topics[0] if paper.matched_topics else "General ML",
            "difficulty": difficulty,

            # Content metadata
            "abstract": paper.abstract,
            "tldr": self._sanitize_for_mdx(paper.abstract[:200].replace("\n", " ")) + "...",

            # Links
            "arxiv_url": paper.url,
            "pdf_url": paper.pdf_url,

            # Status
            "status": "live",  # Changed from staging to live
            "featured": False,

            # Legacy fields (backward compatibility)
            "date": today.strftime("%Y-%m-%d"),
            "source": paper.source,
            "arxivId": paper.id.replace("arxiv:", "") if paper.id.startswith("arxiv:") else None,
            "paperUrl": paper.url,
            "pdfUrl": paper.pdf_url,
            "similarityScore": round(paper.similarity_score, 3),
            "matchedTopics": paper.matched_topics,
            "excerpt": self._sanitize_for_mdx(paper.abstract[:200].replace("\n", " ")) + "...",
        }

        # Build MDX content with proper YAML frontmatter
        # Remove None values for cleaner YAML
        frontmatter_clean = {k: v for k, v in frontmatter.items() if v is not None}

        frontmatter_yaml = yaml.safe_dump(
            frontmatter_clean,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False
        )

        # RSCT quality tier for display
        kappa = paper.rsct_kappa or 0.0
        R = paper.rsct_R or 0.0
        S = paper.rsct_S or 0.0
        N = paper.rsct_N or 0.0

        quality_tier = "exceptional" if kappa >= 0.9 else \
                       "high-quality" if kappa >= 0.8 else \
                       "certified" if kappa >= 0.7 else "pending"

        # Detect cross-domain papers and frame S positively
        is_bridge_paper = len(paper.matched_topics or []) > 1 or S > 0.35
        s_description = (
            f"Background material for readers from other fields (this is a **bridge paper** - high context is a feature!)"
            if is_bridge_paper else
            "Background material, not critical to evaluate"
        )

        content = f"""---
{frontmatter_yaml.strip()}
---

# {paper.title}

**RSCT Certification:** κ={kappa:.3f} ({quality_tier}) | **RSN:** {frontmatter['rsn_score']} | **Topics:** {', '.join(paper.matched_topics) if paper.matched_topics else 'General'}

## Overview

{analysis}

## Quality Assessment

**Trust Level:** {
    'HIGH - Safe to build on' if kappa >= 0.85 and N < 0.15 else
    'MODERATE - Verify key results first' if kappa >= 0.7 else
    'CAUTIOUS - Validate independently' if kappa >= 0.5 else
    'LOW - Treat as preliminary'
}

**What the scores mean:**
- **{R:.0%} signal** - This much of the paper directly supports its claims
- **{S:.0%} context** - {s_description}
- **{N:.0%} noise** - Content that may mislead if taken at face value{' ⚠️ Higher than ideal' if N > 0.25 else ''}

**Reliability score:** {kappa:.0%} ({quality_tier})

**Practical interpretation:**
{
    f"Core methodology appears solid. Safe to cite the main results. Verify edge cases before extending." if kappa >= 0.8 else
    f"Good foundation but some gaps. Read critically and verify key claims before building on this work." if kappa >= 0.7 else
    f"Interesting direction but needs validation. Wait for replication or verify independently before citing heavily." if kappa >= 0.5 else
    f"Early-stage work. Treat claims as hypotheses rather than established results."
}

{self._generate_graph_insights_section(paper)}

## Paper Details

- **Authors:** {', '.join(paper.authors[:5]) if paper.authors else 'Unknown'}{' et al.' if paper.authors and len(paper.authors) > 5 else ''}
- **Published:** {paper.published_date or 'Unknown'}
- **Source:** [{paper.source}]({paper.url})
{f'- **PDF:** [Download]({paper.pdf_url})' if paper.pdf_url else ''}
- **Primary Topic:** {frontmatter['primary_topic']}
- **Difficulty:** {frontmatter['difficulty'].title()}

## Abstract

> {self._sanitize_for_mdx(paper.abstract)}

---

*This analysis was automatically generated and certified by the Swarm-It RSCT pipeline.
κ-gate score: {kappa:.3f} | Quality tier: {quality_tier}*
"""

        return BlogPost(
            slug=slug,
            filename=f"{slug}.mdx",
            content=content,
            frontmatter=frontmatter,
        )

    def save_post(self, post: BlogPost) -> Path:
        """Save blog post to disk."""
        filepath = self.output_dir / post.filename
        filepath.write_text(post.content)
        return filepath

    def generate_and_save(self, papers: List[PaperData]) -> List[Path]:
        """Generate and save posts for multiple papers."""
        saved = []

        for paper in papers:
            try:
                post = self.generate_post(paper)
                path = self.save_post(post)
                saved.append(path)
                print(f"Generated: {post.filename}")
            except Exception as e:
                print(f"Error generating post for {paper.title}: {e}")

        return saved
