"""
Publisher Agent - Generates and publishes content from analyzed papers.

Generates MDX posts, PDFs, and uploads to S3.
Uses swarm-it-auth for AWS credentials.
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone

# Add swarm-it repos to path
sys.path.insert(0, str(Path.home() / "GitHub" / "swarm-it-auth"))

# Import pipeline components
sys.path.insert(0, str(Path(__file__).parent.parent / "pipeline"))
try:
    from publisher.mdx_generator import MDXGenerator
    HAS_MDX = True
except ImportError:
    HAS_MDX = False

try:
    from publisher.pdf_generator import PDFGenerator
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

# AWS S3
try:
    import boto3
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False


@dataclass
class PublishResult:
    """Result from publishing content."""
    paper_id: str
    title: str

    # Generated files
    mdx_path: Optional[str] = None
    pdf_path: Optional[str] = None

    # S3 uploads
    s3_mdx_key: Optional[str] = None
    s3_pdf_key: Optional[str] = None

    # Status
    success: bool = False
    error: Optional[str] = None


@dataclass
class BatchPublishResult:
    """Result from publishing multiple papers."""
    results: List[PublishResult]
    total_count: int
    success_count: int
    publish_time: float
    s3_bucket: Optional[str] = None
    errors: List[str] = field(default_factory=list)


class PublisherAgent:
    """
    Agent for generating and publishing paper content.

    Outputs:
    - MDX posts for Gatsby site
    - PDF summaries
    - S3 uploads

    Usage:
        agent = PublisherAgent(s3_bucket="my-bucket")
        result = agent.publish(analyses, output_dir="./content")
    """

    DEFAULT_BUCKET = "swarmit-nextshift-site"
    DEFAULT_PREFIX = "content/reviews"

    def __init__(
        self,
        s3_bucket: Optional[str] = None,
        s3_prefix: Optional[str] = None,
        output_dir: Optional[str] = None,
        dry_run: bool = False,
    ):
        """
        Initialize publisher agent.

        Args:
            s3_bucket: S3 bucket for uploads
            s3_prefix: S3 key prefix
            output_dir: Local output directory
            dry_run: If True, don't actually upload
        """
        self.s3_bucket = s3_bucket or self.DEFAULT_BUCKET
        self.s3_prefix = s3_prefix or self.DEFAULT_PREFIX
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parent.parent / "content" / "reviews"
        self.dry_run = dry_run

        self._mdx_gen = None
        self._pdf_gen = None
        self._s3 = None

        self._init_components()

    def _init_components(self):
        """Initialize publishing components."""
        # MDX generator
        if HAS_MDX:
            try:
                self._mdx_gen = MDXGenerator()
                print("✓ PublisherAgent: MDXGenerator initialized")
            except Exception as e:
                print(f"✗ PublisherAgent: MDXGenerator failed: {e}")

        # PDF generator
        if HAS_PDF:
            try:
                self._pdf_gen = PDFGenerator()
                print("✓ PublisherAgent: PDFGenerator initialized")
            except Exception as e:
                print(f"✗ PublisherAgent: PDFGenerator failed: {e}")

        # S3 client
        if HAS_BOTO and not self.dry_run:
            try:
                self._s3 = boto3.client('s3')
                print(f"✓ PublisherAgent: S3 client initialized (bucket={self.s3_bucket})")
            except Exception as e:
                print(f"✗ PublisherAgent: S3 client failed: {e}")

    def _generate_mdx(self, analysis: Dict) -> Optional[str]:
        """Generate MDX content for a paper analysis."""
        title = analysis.get('title', 'Untitled')
        summary = analysis.get('summary', '')
        key_findings = analysis.get('key_findings', [])
        rsct_connections = analysis.get('rsct_connections', [])
        source = analysis.get('source', 'unknown')
        topic_score = analysis.get('topic_score', 0)
        rsct_score = analysis.get('rsct_score', 0)
        combined_score = analysis.get('combined_score', 0)

        # Generate slug
        slug = title.lower()
        for char in [' ', ':', ',', '.', '?', '!', '"', "'"]:
            slug = slug.replace(char, '-')
        slug = '-'.join(filter(None, slug.split('-')))[:50]

        date = datetime.now(timezone.utc).strftime('%Y-%m-%d')

        # Build MDX content
        findings_md = '\n'.join([f"- {f}" for f in key_findings]) if key_findings else "- No key findings extracted"
        connections_md = '\n'.join([f"- {c}" for c in rsct_connections]) if rsct_connections else "- No RSCT connections identified"

        mdx = f"""---
title: "{title}"
date: "{date}"
source: "{source}"
topic_score: {topic_score:.2f}
rsct_score: {rsct_score:.2f}
combined_score: {combined_score:.2f}
tags: ["research", "{source}", "ai-discovery"]
---

## Summary

{summary}

## Key Findings

{findings_md}

## RSCT Connections

{connections_md}

## Scores

| Metric | Score |
|--------|-------|
| Topic Relevance | {topic_score:.2f} |
| RSCT Quality | {rsct_score:.2f} |
| Combined | {combined_score:.2f} |

---

*Discovered by Swarm-It Discovery Pipeline*
"""
        return mdx, slug

    def publish_paper(self, analysis: Dict) -> PublishResult:
        """
        Publish a single paper analysis.

        Args:
            analysis: Analysis dict from AnalyzerAgent

        Returns:
            PublishResult with paths and status
        """
        title = analysis.get('title', 'Untitled')
        paper_id = analysis.get('paper_id', '')

        result = PublishResult(
            paper_id=paper_id,
            title=title,
        )

        try:
            # Generate MDX
            mdx_content, slug = self._generate_mdx(analysis)

            # Ensure output directory exists
            self.output_dir.mkdir(parents=True, exist_ok=True)

            # Write MDX file
            date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            mdx_filename = f"{date}-{slug}.mdx"
            mdx_path = self.output_dir / mdx_filename

            mdx_path.write_text(mdx_content)
            result.mdx_path = str(mdx_path)

            # Upload to S3
            if self._s3 and not self.dry_run:
                s3_key = f"{self.s3_prefix}/{mdx_filename}"
                self._s3.put_object(
                    Bucket=self.s3_bucket,
                    Key=s3_key,
                    Body=mdx_content,
                    ContentType='text/markdown',
                )
                result.s3_mdx_key = s3_key

            result.success = True

        except Exception as e:
            result.error = str(e)
            result.success = False

        return result

    def publish(
        self,
        analyses: List[Dict],
        max_papers: Optional[int] = None,
    ) -> BatchPublishResult:
        """
        Publish multiple paper analyses.

        Args:
            analyses: List of analysis dicts
            max_papers: Max papers to publish

        Returns:
            BatchPublishResult with all results
        """
        print(f"\n=== PublisherAgent: Publishing {len(analyses)} papers ===")
        print(f"Output: {self.output_dir}")
        print(f"S3: s3://{self.s3_bucket}/{self.s3_prefix}/")
        if self.dry_run:
            print("MODE: DRY RUN (no S3 uploads)")

        start_time = datetime.now(timezone.utc)

        results = []
        errors = []

        analyses_to_publish = analyses[:max_papers] if max_papers else analyses

        for i, analysis in enumerate(analyses_to_publish):
            # Handle both AnalysisResult objects and dicts
            if hasattr(analysis, '__dict__'):
                analysis_dict = analysis.__dict__
            else:
                analysis_dict = analysis

            result = self.publish_paper(analysis_dict)
            results.append(result)

            status = "✓" if result.success else "✗"
            print(f"  [{i+1}/{len(analyses_to_publish)}] {status} {result.title[:50]}...")

            if result.error:
                errors.append(f"{result.title}: {result.error}")

        publish_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        success_count = sum(1 for r in results if r.success)

        print(f"\n✓ Publish complete in {publish_time:.1f}s")
        print(f"  Published: {success_count}/{len(analyses_to_publish)}")

        return BatchPublishResult(
            results=results,
            total_count=len(analyses_to_publish),
            success_count=success_count,
            publish_time=publish_time,
            s3_bucket=self.s3_bucket if not self.dry_run else None,
            errors=errors,
        )

    def __repr__(self) -> str:
        return f"PublisherAgent(bucket={self.s3_bucket}, dry_run={self.dry_run})"


# CLI entry point
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Publish paper analyses")
    parser.add_argument("--input", "-i", required=True, help="Input JSON file with analyses")
    parser.add_argument("--output", "-o", help="Output directory")
    parser.add_argument("--bucket", help="S3 bucket")
    parser.add_argument("--prefix", help="S3 prefix")
    parser.add_argument("--max", type=int, help="Max papers to publish")
    parser.add_argument("--dry-run", action="store_true", help="Don't upload to S3")
    args = parser.parse_args()

    with open(args.input) as f:
        data = json.load(f)
        analyses = data.get('analyses', data) if isinstance(data, dict) else data

    agent = PublisherAgent(
        s3_bucket=args.bucket,
        s3_prefix=args.prefix,
        output_dir=args.output,
        dry_run=args.dry_run,
    )
    result = agent.publish(analyses, max_papers=args.max)

    print(f"\nResults: {result.success_count}/{result.total_count} published")
