#!/usr/bin/env python3
"""
PDF Candidate Scanner
=====================

Scans a folder of PDFs for best candidates based on topic matching
and RSCT certification via Swarm-It API.

Usage:
    python scripts/scan_pdf_candidates.py /path/to/pdfs
    python scripts/scan_pdf_candidates.py /path/to/pdfs --threshold 0.3 --top 10
    python scripts/scan_pdf_candidates.py ~/GitHub/ram_pdfs/research_papers --certify

Examples:
    # Quick scan with keyword matching only
    python scripts/scan_pdf_candidates.py ~/GitHub/ram_pdfs/research_papers

    # Full scan with Swarm-It RSCT certification
    python scripts/scan_pdf_candidates.py ~/GitHub/ram_pdfs/research_papers --certify

    # Scan specific category
    python scripts/scan_pdf_candidates.py ~/GitHub/ram_pdfs/model_validation --threshold 0.2
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import re

# PDF extraction
try:
    import fitz  # PyMuPDF - faster and better
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    from pypdf import PdfReader
    HAS_PYPDF = True
except ImportError:
    try:
        from PyPDF2 import PdfReader
        HAS_PYPDF = True
    except ImportError:
        HAS_PYPDF = False

# Swarm-It ADK client
try:
    sys.path.insert(0, os.path.expanduser("~/GitHub/swarm-it-adk/clients/python"))
    from swarm_it.client import SwarmIt
    HAS_SWARMIT = True
except ImportError:
    HAS_SWARMIT = False


@dataclass
class PDFCandidate:
    """A PDF candidate with relevance scores."""
    path: str
    filename: str
    title: str
    text_preview: str
    topic_scores: Dict[str, float] = field(default_factory=dict)
    best_topic: str = ""
    best_topic_score: float = 0.0
    keyword_matches: List[str] = field(default_factory=list)
    rsct_kappa: float = 0.0
    rsct_R: float = 0.0
    rsct_S: float = 0.0
    rsct_N: float = 0.0
    combined_score: float = 0.0
    error: str = ""


class PDFExtractor:
    """Extract text from PDFs using available library."""

    def __init__(self):
        self.backend = "pymupdf" if HAS_PYMUPDF else "pypdf" if HAS_PYPDF else None
        if not self.backend:
            print("WARNING: No PDF library available. Install: pip install pymupdf")

    def extract(self, pdf_path: Path, max_pages: int = 5, max_chars: int = 8000) -> Tuple[str, str]:
        """
        Extract text from PDF.

        Returns:
            Tuple of (title, text_content)
        """
        if not self.backend:
            return "", ""

        try:
            if self.backend == "pymupdf":
                return self._extract_pymupdf(pdf_path, max_pages, max_chars)
            else:
                return self._extract_pypdf(pdf_path, max_pages, max_chars)
        except Exception as e:
            return "", f"ERROR: {e}"

    def _extract_pymupdf(self, pdf_path: Path, max_pages: int, max_chars: int) -> Tuple[str, str]:
        """Extract using PyMuPDF (faster, better quality)."""
        doc = fitz.open(str(pdf_path))

        # Get title from metadata or first page
        title = doc.metadata.get("title", "") or ""

        text_parts = []
        total_chars = 0

        for i, page in enumerate(doc):
            if i >= max_pages or total_chars >= max_chars:
                break

            page_text = page.get_text()
            text_parts.append(page_text)
            total_chars += len(page_text)

            # Try to extract title from first page if not in metadata
            if i == 0 and not title:
                lines = page_text.strip().split('\n')
                for line in lines[:5]:
                    line = line.strip()
                    # Title heuristic: substantial text, not too long
                    if 10 < len(line) < 200 and not line.startswith('arXiv'):
                        title = line
                        break

        doc.close()
        text = '\n'.join(text_parts)[:max_chars]
        return title or pdf_path.stem, text

    def _extract_pypdf(self, pdf_path: Path, max_pages: int, max_chars: int) -> Tuple[str, str]:
        """Extract using pypdf (fallback)."""
        reader = PdfReader(str(pdf_path))

        # Get title from metadata
        title = ""
        if reader.metadata:
            title = reader.metadata.get("/Title", "") or ""

        text_parts = []
        total_chars = 0

        for i, page in enumerate(reader.pages):
            if i >= max_pages or total_chars >= max_chars:
                break

            page_text = page.extract_text() or ""
            text_parts.append(page_text)
            total_chars += len(page_text)

            # Extract title from first page if needed
            if i == 0 and not title:
                lines = page_text.strip().split('\n')
                for line in lines[:5]:
                    line = line.strip()
                    if 10 < len(line) < 200:
                        title = line
                        break

        text = '\n'.join(text_parts)[:max_chars]
        return title or pdf_path.stem, text


class TopicMatcher:
    """Match text against topics using keyword and semantic scoring."""

    def __init__(self, topics_path: str = None):
        self.topics = self._load_topics(topics_path)

    def _load_topics(self, topics_path: str = None) -> List[Dict]:
        """Load topics from JSON file."""
        if topics_path is None:
            # Default path
            base = Path(__file__).parent.parent
            topics_path = base / "content" / "topics" / "topics.json"

        topics_path = Path(topics_path)
        if not topics_path.exists():
            print(f"Topics file not found: {topics_path}")
            return []

        with open(topics_path) as f:
            data = json.load(f)

        return data.get("topics", [])

    def score(self, text: str) -> Dict[str, float]:
        """
        Score text against all topics.

        Returns:
            Dict mapping topic_id -> relevance score (0-1)
        """
        text_lower = text.lower()
        scores = {}

        for topic in self.topics:
            topic_id = topic["id"]
            keywords = topic.get("keywords", [])
            content = topic.get("content", "").lower()

            # Keyword matching
            keyword_matches = sum(1 for kw in keywords if kw.lower() in text_lower)
            keyword_score = min(keyword_matches / max(len(keywords), 1), 1.0)

            # Content word overlap (simple TF similarity)
            content_words = set(content.split())
            text_words = set(text_lower.split())
            overlap = len(content_words & text_words)
            content_score = min(overlap / max(len(content_words), 1), 1.0)

            # Combined score (weight keywords higher)
            scores[topic_id] = 0.7 * keyword_score + 0.3 * content_score

        return scores

    def get_keyword_matches(self, text: str) -> List[str]:
        """Get list of all matching keywords across topics."""
        text_lower = text.lower()
        matches = []

        for topic in self.topics:
            for kw in topic.get("keywords", []):
                if kw.lower() in text_lower and kw not in matches:
                    matches.append(kw)

        return matches


class PDFCandidateScanner:
    """Scan PDFs and find best candidates based on topics and RSCT certification."""

    def __init__(
        self,
        topics_path: str = None,
        swarmit_url: str = None,
        use_certification: bool = False,
    ):
        self.extractor = PDFExtractor()
        self.matcher = TopicMatcher(topics_path)
        self.use_certification = use_certification
        self.swarmit_client = None

        if use_certification and HAS_SWARMIT:
            url = swarmit_url or os.getenv("SWARMIT_URL", "https://api.swarms.network")
            try:
                self.swarmit_client = SwarmIt(url=url)
                print(f"Swarm-It API connected: {url}")
            except Exception as e:
                print(f"WARNING: Could not connect to Swarm-It API: {e}")

    def scan_folder(
        self,
        folder_path: str,
        threshold: float = 0.2,
        top_n: int = 20,
        recursive: bool = False,
    ) -> List[PDFCandidate]:
        """
        Scan all PDFs in a folder and return ranked candidates.

        Args:
            folder_path: Path to folder containing PDFs
            threshold: Minimum topic score to include (0-1)
            top_n: Maximum number of results to return
            recursive: Whether to scan subdirectories

        Returns:
            List of PDFCandidate objects, sorted by combined score
        """
        folder = Path(folder_path)
        if not folder.exists():
            print(f"Folder not found: {folder}")
            return []

        # Find all PDFs
        pattern = "**/*.pdf" if recursive else "*.pdf"
        pdf_files = list(folder.glob(pattern))
        print(f"Found {len(pdf_files)} PDF files in {folder}")

        candidates = []

        for i, pdf_path in enumerate(pdf_files):
            print(f"\r[{i+1}/{len(pdf_files)}] Scanning: {pdf_path.name[:50]}...", end="", flush=True)

            candidate = self._analyze_pdf(pdf_path)

            # Filter by threshold
            if candidate.best_topic_score >= threshold:
                candidates.append(candidate)

        print()  # Newline after progress

        # Sort by combined score
        candidates.sort(key=lambda c: c.combined_score, reverse=True)

        # Apply RSCT certification to top candidates if enabled
        if self.use_certification and self.swarmit_client:
            print(f"\nCertifying top {min(top_n, len(candidates))} candidates via Swarm-It API...")
            for i, candidate in enumerate(candidates[:top_n]):
                print(f"  [{i+1}] Certifying: {candidate.filename[:40]}...", end="", flush=True)
                self._certify_candidate(candidate)
                print(f" kappa={candidate.rsct_kappa:.3f}")

            # Re-sort with RSCT scores
            candidates.sort(key=lambda c: c.combined_score, reverse=True)

        return candidates[:top_n]

    def _analyze_pdf(self, pdf_path: Path) -> PDFCandidate:
        """Analyze a single PDF."""
        candidate = PDFCandidate(
            path=str(pdf_path),
            filename=pdf_path.name,
            title="",
            text_preview="",
        )

        # Extract text
        title, text = self.extractor.extract(pdf_path)

        if text.startswith("ERROR:"):
            candidate.error = text
            return candidate

        candidate.title = title
        candidate.text_preview = text[:500] + "..." if len(text) > 500 else text

        # Score against topics
        candidate.topic_scores = self.matcher.score(text)

        if candidate.topic_scores:
            best = max(candidate.topic_scores.items(), key=lambda x: x[1])
            candidate.best_topic = best[0]
            candidate.best_topic_score = best[1]

        # Get keyword matches
        candidate.keyword_matches = self.matcher.get_keyword_matches(text)

        # Initial combined score (before RSCT)
        candidate.combined_score = candidate.best_topic_score

        return candidate

    def _certify_candidate(self, candidate: PDFCandidate):
        """Get RSCT certification from Swarm-It API."""
        if not self.swarmit_client:
            return

        try:
            # Create prompt from PDF content
            prompt = f"""Analyze this research paper for RSCT certification:

Title: {candidate.title}

Content Preview:
{candidate.text_preview}

Matched Topics: {candidate.best_topic}
Keyword Matches: {', '.join(candidate.keyword_matches[:10])}

Assess the relevance (R), spurious content (S), and noise (N) for research quality."""

            # Call Swarm-It API
            cert = self.swarmit_client.certify(prompt=prompt)

            candidate.rsct_kappa = cert.kappa_gate
            candidate.rsct_R = cert.R
            candidate.rsct_S = cert.S
            candidate.rsct_N = cert.N

            # Update combined score with RSCT weighting
            candidate.combined_score = (
                0.4 * candidate.best_topic_score +
                0.6 * candidate.rsct_kappa
            )

        except Exception as e:
            candidate.error = f"Certification error: {e}"


def print_results(candidates: List[PDFCandidate], output_format: str = "table"):
    """Print results in specified format."""

    if not candidates:
        print("\nNo candidates found above threshold.")
        return

    print(f"\n{'='*80}")
    print(f"  BEST CANDIDATES ({len(candidates)} papers)")
    print(f"{'='*80}\n")

    if output_format == "json":
        results = []
        for c in candidates:
            results.append({
                "filename": c.filename,
                "title": c.title,
                "best_topic": c.best_topic,
                "topic_score": round(c.best_topic_score, 3),
                "rsct_kappa": round(c.rsct_kappa, 3),
                "combined_score": round(c.combined_score, 3),
                "keywords": c.keyword_matches[:5],
            })
        print(json.dumps(results, indent=2))
        return

    # Table format
    print(f"{'#':<3} {'Score':<7} {'Topic':<25} {'Keywords':<20} {'Title':<30}")
    print("-" * 85)

    for i, c in enumerate(candidates, 1):
        topic = c.best_topic[:23] if c.best_topic else "none"
        keywords = ', '.join(c.keyword_matches[:3])[:18] or "-"
        title = c.title[:28] if c.title else c.filename[:28]

        if c.rsct_kappa > 0:
            score = f"{c.combined_score:.2f}*"  # * indicates RSCT certified
        else:
            score = f"{c.combined_score:.2f}"

        print(f"{i:<3} {score:<7} {topic:<25} {keywords:<20} {title}")

    print("-" * 85)
    print("* = RSCT certified (kappa included in score)\n")

    # Show top 3 details
    print("\nTOP 3 DETAILS:\n")
    for i, c in enumerate(candidates[:3], 1):
        print(f"{i}. {c.title}")
        print(f"   File: {c.filename}")
        print(f"   Topic: {c.best_topic} (score: {c.best_topic_score:.3f})")
        if c.rsct_kappa > 0:
            print(f"   RSCT: kappa={c.rsct_kappa:.3f}, R={c.rsct_R:.3f}, S={c.rsct_S:.3f}, N={c.rsct_N:.3f}")
        print(f"   Keywords: {', '.join(c.keyword_matches[:8])}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Scan PDFs for best candidates based on topics and RSCT certification",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s ~/GitHub/ram_pdfs/research_papers
  %(prog)s ~/GitHub/ram_pdfs/research_papers --threshold 0.3 --top 5
  %(prog)s ~/GitHub/ram_pdfs --recursive --certify
        """
    )

    parser.add_argument("folder", help="Path to folder containing PDFs")
    parser.add_argument("--threshold", "-t", type=float, default=0.2,
                       help="Minimum topic score (0-1, default: 0.2)")
    parser.add_argument("--top", "-n", type=int, default=20,
                       help="Number of top results (default: 20)")
    parser.add_argument("--recursive", "-r", action="store_true",
                       help="Scan subdirectories")
    parser.add_argument("--certify", "-c", action="store_true",
                       help="Use Swarm-It API for RSCT certification")
    parser.add_argument("--topics", help="Path to topics.json file")
    parser.add_argument("--format", choices=["table", "json"], default="table",
                       help="Output format (default: table)")
    parser.add_argument("--swarmit-url", help="Swarm-It API URL")

    args = parser.parse_args()

    print(f"\nPDF Candidate Scanner")
    print(f"{'='*40}")
    print(f"Folder: {args.folder}")
    print(f"Threshold: {args.threshold}")
    print(f"Top N: {args.top}")
    print(f"Recursive: {args.recursive}")
    print(f"RSCT Certification: {args.certify}")
    print(f"PDF Backend: {PDFExtractor().backend or 'NONE - install pymupdf!'}")
    print()

    scanner = PDFCandidateScanner(
        topics_path=args.topics,
        swarmit_url=args.swarmit_url,
        use_certification=args.certify,
    )

    candidates = scanner.scan_folder(
        args.folder,
        threshold=args.threshold,
        top_n=args.top,
        recursive=args.recursive,
    )

    print_results(candidates, args.format)

    return 0 if candidates else 1


if __name__ == "__main__":
    sys.exit(main())
