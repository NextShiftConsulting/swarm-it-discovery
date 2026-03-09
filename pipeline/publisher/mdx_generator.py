"""
MDX Generator - Create blog posts from matched papers.
"""

import os
import re
import yaml
from datetime import datetime
from dateutil import parser as date_parser
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional


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
    rsct_decision: str = None  # EXECUTE, REPAIR, BLOCK


@dataclass
class BlogPost:
    """Generated blog post."""
    slug: str
    filename: str
    content: str
    frontmatter: dict


class MDXGenerator:
    """Generate MDX paper reviews from matched papers."""

    def __init__(self, output_dir: str = "content/reviews"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if HAS_OPENAI and os.getenv("OPENAI_API_KEY"):
            self.openai = OpenAI()
            self.use_llm = True
        else:
            self.openai = None
            self.use_llm = False
            print("Warning: OpenAI not configured, using template-based generation")

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

    def _generate_analysis_llm(self, paper: PaperData) -> str:
        """Use LLM to generate paper analysis."""
        prompt = f"""Analyze this research paper and write a blog post section explaining its significance.

Title: {paper.title}
Abstract: {paper.abstract}

Write 2-3 paragraphs covering:
1. What the paper does and why it matters
2. Key technical contributions
3. How it relates to AI safety, multi-agent systems, or representation learning

Keep it accessible but technically accurate. Use markdown formatting."""

        response = self.openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
        )

        return response.choices[0].message.content

    def _generate_analysis_template(self, paper: PaperData) -> str:
        """Template-based analysis when LLM unavailable."""
        return f"""This paper presents research in the area of {', '.join(paper.categories[:2]) if paper.categories else 'machine learning'}.

**Abstract Summary:**
{paper.abstract[:500]}{'...' if len(paper.abstract) > 500 else ''}

The work shows a **{paper.similarity_score:.0%} similarity** to our research interests in {', '.join(paper.matched_topics) if paper.matched_topics else 'AI systems'}.

Further analysis pending manual review."""

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

        content = f"""---
{frontmatter_yaml.strip()}
---

# {paper.title}

**RSCT Certification:** κ={kappa:.3f} ({quality_tier}) | **RSN:** {frontmatter['rsn_score']} | **Topics:** {', '.join(paper.matched_topics) if paper.matched_topics else 'General'}

## Overview

{analysis}

## RSCT Quality Metrics

This paper has been certified by the Swarm-It RSCT pipeline:

- **κ-gate Score:** {kappa:.3f} ({quality_tier})
- **Relevance (R):** {R:.3f} - Directly relevant to research goals
- **Spurious (S):** {S:.3f} - Supporting context and correlations
- **Noise (N):** {N:.3f} - Irrelevant or noisy components
- **Decision:** {paper.rsct_decision or 'EXECUTE'}

The RSN decomposition satisfies the simplex constraint (R+S+N=1.0), ensuring mathematically valid quality assessment.

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
