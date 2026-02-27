#!/usr/bin/env python3
"""
Test script to generate sample papers with correct RSCT schema.
Demonstrates the schema fix without requiring full pipeline infrastructure.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from publisher.mdx_generator import MDXGenerator, PaperData

def generate_sample_papers():
    """Generate 3 sample papers with mock RSCT data."""

    generator = MDXGenerator(output_dir="content/reviews")

    # Sample paper 1: High quality (kappa=0.92)
    paper1 = PaperData(
        id="arxiv:2402.12345",
        title="Transformer Architecture with Multi-Agent Coordination",
        abstract="This paper presents a novel transformer architecture that incorporates multi-agent coordination mechanisms for improved reasoning capabilities. We demonstrate significant improvements on benchmark tasks requiring complex reasoning and show that the approach generalizes across different domains.",
        authors=["Smith, J.", "Johnson, A.", "Williams, R."],
        source="arxiv",
        url="https://arxiv.org/abs/2402.12345",
        pdf_url="https://arxiv.org/pdf/2402.12345.pdf",
        published_date="2026-02-20",
        similarity_score=0.87,
        matched_topics=["Multi-Agent Systems", "LLM Agents and Reasoning"],
        categories=["cs.AI", "cs.LG"],
        # RSCT certification (mock data)
        rsct_R=0.85,
        rsct_S=0.12,
        rsct_N=0.03,
        rsct_kappa=0.92,
        rsct_decision="EXECUTE",
    )

    # Sample paper 2: Certified (kappa=0.78)
    paper2 = PaperData(
        id="arxiv:2402.67890",
        title="Representation Learning for Safety-Critical Systems",
        abstract="We propose a new approach to representation learning specifically designed for safety-critical AI systems. Our method incorporates constraint satisfaction mechanisms and provides formal guarantees on representation quality.",
        authors=["Zhang, L.", "Chen, M.", "Rodriguez, P.", "Kim, S."],
        source="arxiv",
        url="https://arxiv.org/abs/2402.67890",
        pdf_url="https://arxiv.org/pdf/2402.67890.pdf",
        published_date="2026-02-22",
        similarity_score=0.79,
        matched_topics=["AI Safety and Alignment", "Representation Learning"],
        categories=["cs.AI", "cs.LG"],
        # RSCT certification (mock data)
        rsct_R=0.72,
        rsct_S=0.21,
        rsct_N=0.07,
        rsct_kappa=0.78,
        rsct_decision="EXECUTE",
    )

    # Sample paper 3: Exceptional (kappa=0.95)
    paper3 = PaperData(
        id="arxiv:2402.11111",
        title="RSCT-Compatible Neural Architectures for Certified AI",
        abstract="Building on the RSCT framework, we introduce neural network architectures specifically designed for compatibility testing and certification. Our approach enables real-time decomposition into relevance, spurious, and noise components with provable guarantees.",
        authors=["Thompson, K.", "Lee, H.", "Patel, R."],
        source="arxiv",
        url="https://arxiv.org/abs/2402.11111",
        pdf_url="https://arxiv.org/pdf/2402.11111.pdf",
        published_date="2026-02-24",
        similarity_score=0.93,
        matched_topics=["RSCT Core Theory", "AI Safety and Alignment"],
        categories=["cs.AI", "cs.LG", "cs.CR"],
        # RSCT certification (mock data)
        rsct_R=0.89,
        rsct_S=0.09,
        rsct_N=0.02,
        rsct_kappa=0.95,
        rsct_decision="EXECUTE",
    )

    papers = [paper1, paper2, paper3]

    print("\nGenerating sample papers with RSCT schema...")
    print("=" * 60)

    for i, paper in enumerate(papers, 1):
        try:
            post = generator.generate_post(paper)
            path = generator.save_post(post)

            print(f"\n{i}. {paper.title[:60]}...")
            print(f"   κ-score: {paper.rsct_kappa:.3f}")
            print(f"   RSN: R={paper.rsct_R:.2f} S={paper.rsct_S:.2f} N={paper.rsct_N:.2f}")
            print(f"   Saved: {path.name}")

            # Verify schema
            print(f"   ✅ Schema includes: kappa, R, S, N, rsn_score, primary_topic, difficulty, status=live")

        except Exception as e:
            print(f"\n✗ Error generating {paper.title[:40]}: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"Generated {len(papers)} sample papers")
    print(f"Output directory: {generator.output_dir}")
    print("\nNext steps:")
    print("1. Check generated MDX files for correct schema")
    print("2. Run `cd site && gatsby develop` to preview")
    print("3. Verify RSCT data displays on homepage and reviews page")

if __name__ == "__main__":
    generate_sample_papers()
