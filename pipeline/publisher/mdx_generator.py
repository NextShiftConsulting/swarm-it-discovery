"""
MDX Generator - Create blog posts from matched papers.
"""

import os
import re
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional

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


@dataclass
class BlogPost:
    """Generated blog post."""
    slug: str
    filename: str
    content: str
    frontmatter: dict


class MDXGenerator:
    """Generate MDX blog posts from papers."""

    def __init__(self, output_dir: str = "content/generated-posts"):
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

        # Build frontmatter
        frontmatter = {
            "title": paper.title,
            "date": today.strftime("%Y-%m-%d"),
            "source": paper.source,
            "arxivId": paper.id.replace("arxiv:", "") if paper.id.startswith("arxiv:") else None,
            "paperUrl": paper.url,
            "pdfUrl": paper.pdf_url,
            "authors": paper.authors[:5],
            "similarityScore": round(paper.similarity_score, 3),
            "matchedTopics": paper.matched_topics,
            "tags": self._extract_tags(paper),
            "excerpt": paper.abstract[:200].replace("\n", " ") + "...",
        }

        # Build MDX content
        content = f"""---
title: "{paper.title.replace('"', '\\"')}"
date: "{frontmatter['date']}"
source: "{paper.source}"
{f'arxivId: "{frontmatter["arxivId"]}"' if frontmatter["arxivId"] else ''}
paperUrl: "{paper.url}"
{f'pdfUrl: "{paper.pdf_url}"' if paper.pdf_url else ''}
authors: {frontmatter['authors']}
similarityScore: {frontmatter['similarityScore']}
matchedTopics: {frontmatter['matchedTopics']}
tags: {frontmatter['tags']}
excerpt: "{frontmatter['excerpt'].replace('"', '\\"')}"
---

import {{ PaperAnalysis }} from '@components/PaperAnalysis'

# {paper.title}

<PaperAnalysis
  score={{{paper.similarity_score}}}
  topics={{{paper.matched_topics}}}
  source="{paper.source}"
/>

## Overview

{analysis}

## Paper Details

- **Authors:** {', '.join(paper.authors[:5])}{' et al.' if len(paper.authors) > 5 else ''}
- **Published:** {paper.published_date}
- **Source:** [{paper.source}]({paper.url})
{f'- **PDF:** [Download]({paper.pdf_url})' if paper.pdf_url else ''}

## Abstract

> {paper.abstract}

---

*This analysis was automatically generated by the Swarm-It research discovery pipeline.
Similarity score: {paper.similarity_score:.0%} match to our research topics.*
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
