"""
PDF Review Generator - Create detailed LaTeX reviews for top papers.

Generates academic-style PDF reviews for papers most relevant to RSCT,
including detailed analysis, R/S/N breakdown, and research implications.
"""

import os
import subprocess
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional

# Optional: OpenAI for content generation
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


@dataclass
class PDFReview:
    """Generated PDF review."""
    paper_id: str
    title: str
    tex_path: str
    pdf_path: Optional[str]
    rsct_score: float


class PDFReviewGenerator:
    """Generate detailed PDF reviews for top papers."""

    def __init__(
        self,
        output_dir: str = "content/pdf-reviews",
        template_path: str = None,
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if HAS_OPENAI and os.getenv("OPENAI_API_KEY"):
            self.openai = OpenAI()
        else:
            self.openai = None

    def _escape_latex(self, text: str) -> str:
        """Escape special LaTeX characters."""
        replacements = {
            '&': r'\&',
            '%': r'\%',
            '$': r'\$',
            '#': r'\#',
            '_': r'\_',
            '{': r'\{',
            '}': r'\}',
            '~': r'\textasciitilde{}',
            '^': r'\textasciicircum{}',
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text

    def _generate_analysis(
        self,
        title: str,
        abstract: str,
        rsct_score: float,
        key_overlaps: List[str],
    ) -> str:
        """Generate detailed analysis using LLM."""
        if not self.openai:
            return self._template_analysis(title, abstract, rsct_score, key_overlaps)

        prompt = f"""Write a detailed academic review of this paper from an RSCT (Representation-Solver Compatibility Testing) perspective.

Paper Title: {title}

Abstract: {abstract}

RSCT Relevance Score: {rsct_score:.2%}
Key RSCT Concepts Found: {', '.join(key_overlaps) if key_overlaps else 'None identified'}

Write 3-4 paragraphs covering:

1. **Summary**: What the paper does and its main contributions

2. **RSCT Analysis**: How this work relates to Representation-Solver Compatibility Testing theory:
   - Does it address representation quality (R)?
   - Does it handle spurious correlations (S)?
   - Does it deal with noise/uncertainty (N)?
   - Any implications for the kappa compatibility metric?

3. **Technical Depth**: Key methodological contributions and their significance

4. **Research Implications**: How this could inform or be informed by RSCT-based approaches to AI safety and multi-agent certification

Use academic tone. Be specific about connections to RSCT theory."""

        try:
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"LLM error: {e}")
            return self._template_analysis(title, abstract, rsct_score, key_overlaps)

    def _template_analysis(
        self,
        title: str,
        abstract: str,
        rsct_score: float,
        key_overlaps: List[str],
    ) -> str:
        """Template-based analysis when LLM unavailable."""
        overlaps_text = ', '.join(key_overlaps) if key_overlaps else 'general machine learning'
        return f"""This paper presents research with {rsct_score:.0%} relevance to RSCT theory.

\\textbf{{Abstract Summary:}} {abstract[:500]}{'...' if len(abstract) > 500 else ''}

\\textbf{{RSCT Relevance:}} The work touches on concepts related to {overlaps_text}, which have connections to the Representation-Solver Compatibility Testing framework.

\\textbf{{Further Analysis:}} A detailed manual review is recommended to fully assess the implications for RSCT-based certification approaches."""

    def generate_review(
        self,
        paper_id: str,
        title: str,
        abstract: str,
        authors: List[str],
        url: str,
        rsct_score: float,
        topic_similarity: float,
        key_overlaps: List[str],
        rsct_R: float = None,
        rsct_S: float = None,
        rsct_N: float = None,
        rsct_kappa: float = None,
    ) -> PDFReview:
        """Generate a PDF review for a paper."""
        # Generate analysis
        analysis = self._generate_analysis(title, abstract, rsct_score, key_overlaps)

        # Create LaTeX document
        safe_title = self._escape_latex(title)
        safe_abstract = self._escape_latex(abstract)
        safe_analysis = analysis  # Already escaped or generated

        authors_str = ', '.join(authors[:5])
        if len(authors) > 5:
            authors_str += ' et al.'

        # RSCT metrics section
        if rsct_kappa is not None:
            rsct_metrics = f"""
\\subsection*{{RSCT Certification Metrics}}
\\begin{{tabular}}{{ll}}
\\textbf{{Relevance (R):}} & {rsct_R:.3f} \\\\
\\textbf{{Spurious (S):}} & {rsct_S:.3f} \\\\
\\textbf{{Noise (N):}} & {rsct_N:.3f} \\\\
\\textbf{{Kappa ($\\kappa$):}} & {rsct_kappa:.3f} \\\\
\\end{{tabular}}

The kappa score of {rsct_kappa:.3f} indicates {'high' if rsct_kappa > 0.7 else 'moderate' if rsct_kappa > 0.5 else 'limited'} representation-solver compatibility.
"""
        else:
            rsct_metrics = ""

        tex_content = f"""\\documentclass[11pt,a4paper]{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage[margin=1in]{{geometry}}
\\usepackage{{hyperref}}
\\usepackage{{graphicx}}
\\usepackage{{amsmath}}
\\usepackage{{booktabs}}

\\title{{RSCT Review: {safe_title}}}
\\author{{Swarm-It Research Discovery\\\\\\small Automated RSCT-Based Analysis}}
\\date{{{datetime.utcnow().strftime('%B %d, %Y')}}}

\\begin{{document}}
\\maketitle

\\begin{{abstract}}
This document provides an automated review of the paper ``{safe_title}'' from an RSCT (Representation-Solver Compatibility Testing) perspective. The paper achieved an RSCT relevance score of {rsct_score:.1%} and topic similarity of {topic_similarity:.1%}.
\\end{{abstract}}

\\section{{Paper Information}}
\\begin{{itemize}}
\\item \\textbf{{Title:}} {safe_title}
\\item \\textbf{{Authors:}} {self._escape_latex(authors_str)}
\\item \\textbf{{Source:}} \\url{{{url}}}
\\item \\textbf{{RSCT Relevance:}} {rsct_score:.1%}
\\item \\textbf{{Topic Match:}} {topic_similarity:.1%}
\\item \\textbf{{Key Concepts:}} {', '.join(key_overlaps) if key_overlaps else 'N/A'}
\\end{{itemize}}

\\section{{Original Abstract}}
{safe_abstract}

\\section{{RSCT Analysis}}
{safe_analysis}

{rsct_metrics}

\\section{{Relevance to Swarm-It}}
This paper was identified by the Swarm-It research discovery pipeline as potentially relevant to RSCT-based AI certification. The combined score of {(0.6 * rsct_score + 0.4 * topic_similarity):.1%} places it in the {'top tier' if rsct_score > 0.5 else 'moderate relevance' if rsct_score > 0.3 else 'exploratory'} category for further investigation.

\\vspace{{1em}}
\\hrule
\\vspace{{0.5em}}
\\small{{Generated by Swarm-It Research Discovery | \\url{{https://swarms.network}} | RSCT Certified}}

\\end{{document}}
"""

        # Write LaTeX file
        slug = paper_id.replace(':', '-').replace('/', '-')[:50]
        tex_path = self.output_dir / f"{slug}.tex"
        with open(tex_path, 'w', encoding='utf-8') as f:
            f.write(tex_content)

        # Try to compile PDF
        pdf_path = None
        try:
            result = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', '-output-directory', str(self.output_dir), str(tex_path)],
                capture_output=True,
                timeout=60,
            )
            if result.returncode == 0:
                pdf_path = str(self.output_dir / f"{slug}.pdf")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass  # pdflatex not available or timed out

        return PDFReview(
            paper_id=paper_id,
            title=title,
            tex_path=str(tex_path),
            pdf_path=pdf_path,
            rsct_score=rsct_score,
        )

    def generate_batch(
        self,
        papers: List[dict],
        max_papers: int = 10,
    ) -> List[PDFReview]:
        """Generate PDF reviews for top papers."""
        reviews = []
        for paper in papers[:max_papers]:
            review = self.generate_review(
                paper_id=paper.get('id', ''),
                title=paper.get('title', ''),
                abstract=paper.get('abstract', ''),
                authors=paper.get('authors', []),
                url=paper.get('url', ''),
                rsct_score=paper.get('rsct_similarity', 0.0),
                topic_similarity=paper.get('similarity_score', 0.0),
                key_overlaps=paper.get('key_overlaps', []),
                rsct_R=paper.get('rsct_R'),
                rsct_S=paper.get('rsct_S'),
                rsct_N=paper.get('rsct_N'),
                rsct_kappa=paper.get('rsct_kappa'),
            )
            reviews.append(review)
            print(f"Generated: {review.tex_path}")

        return reviews
