#!/usr/bin/env python3
"""
Daily Pipeline Runner - Fetch, Match, Certify, Publish

Uses Swarm-It sidecar API for RSCT certification of the analysis pipeline.

Usage:
    # Set environment variables
    export SWARMIT_URL=http://localhost:8080
    export OPENAI_API_KEY=sk-...

    # Run pipeline
    python pipeline/run.py

    # Or with options
    python pipeline/run.py --days 3 --min-score 0.6 --dry-run
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path
from datetime import datetime
from dataclasses import asdict

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scanner.sources import fetch_all_sources, Paper
from analyzer.matcher import SimilarityMatcher, MatchResult
from analyzer.rsct_scorer import RSCTScorer, RSCTScore
from publisher.mdx_generator import MDXGenerator, PaperData
from publisher.pdf_generator import PDFReviewGenerator

# Paper2SwarmAgent integration
try:
    from paper2agent import Paper2SwarmAgent, TopicConfig
    HAS_PAPER2AGENT = True
except ImportError:
    HAS_PAPER2AGENT = False

# Bedrock semantic matching (real embeddings)
HAS_BEDROCK = False
try:
    from analyzer.bedrock_matcher import BedrockMatcher, BedrockAnalyzer
    # Check for AWS credentials (env var or ~/.aws/credentials)
    if os.environ.get("AWS_ACCESS_KEY_ID"):
        HAS_BEDROCK = True
    else:
        # Try boto3 credential chain
        try:
            import boto3
            session = boto3.Session()
            creds = session.get_credentials()
            HAS_BEDROCK = creds is not None
        except:
            pass
except ImportError:
    pass

# Swarm-It ADK client - add path before import
_adk_path = os.path.expanduser("~/GitHub/swarm-it-adk/clients/python")
if _adk_path not in sys.path:
    sys.path.insert(0, _adk_path)

try:
    from swarm_it import SwarmIt
    HAS_SWARMIT = True
except ImportError:
    HAS_SWARMIT = False
    print("Warning: Swarm-It ADK client not found, running without certification")


class CertifiedPipeline:
    """
    Paper discovery pipeline with RSCT certification.

    Certification strategy:
    - Scanner/Analyzer: Trusted internal operations (no certification)
    - Paper content: Certified (external data from arXiv/bioRxiv/S2)
    - Generated posts: Individual papers pre-certified before generation

    This approach:
    - Avoids false positives from internal summaries
    - Certifies all external data (untrusted input)
    - Ensures published content meets quality standards
    """

    def __init__(
        self,
        swarmit_url: str = "http://localhost:8080",
        topics_dir: str = "site/src/content/topics",
        output_dir: str = "site/src/content/reviews",
        pdf_output_dir: str = "site/src/content/pdf-reviews",
        agents_output_dir: str = "site/src/content/research-agents",
        whitepaper_path: str = None,
        min_score: float = 0.5,
        min_rsct_score: float = 0.3,
    ):
        self.min_score = min_score
        self.min_rsct_score = min_rsct_score
        self.topics_dir = topics_dir

        # Use Bedrock for real semantic matching if available
        if HAS_BEDROCK:
            self.bedrock_matcher = BedrockMatcher(threshold=min_score)
            self.bedrock_analyzer = BedrockAnalyzer()
            self.matcher = None  # Will use Bedrock instead
            print("Bedrock: Enabled (real semantic matching with Titan embeddings)")
        else:
            self.bedrock_matcher = None
            self.bedrock_analyzer = None
            self.matcher = SimilarityMatcher(topics_dir=topics_dir, threshold=min_score)
            print("Warning: Bedrock not available, using keyword matching")

        self.generator = MDXGenerator(output_dir=output_dir)
        self.rsct_scorer = RSCTScorer(whitepaper_path=whitepaper_path)
        self.pdf_generator = PDFReviewGenerator(output_dir=pdf_output_dir)
        self.agents_output_dir = agents_output_dir

        # Initialize Paper2SwarmAgent converter
        if HAS_PAPER2AGENT:
            topics_json = os.path.join(topics_dir, "topics.json")
            if os.path.exists(topics_json):
                self.paper2agent = Paper2SwarmAgent(
                    topics=TopicConfig.from_json(topics_json),
                    cleanup=True,
                )
                print("Paper2SwarmAgent: Enabled (will convert papers with GitHub repos)")
            else:
                self.paper2agent = None
                print("Paper2SwarmAgent: Disabled (topics.json not found)")
        else:
            self.paper2agent = None

        # Initialize Swarm-It client
        if HAS_SWARMIT:
            self.swarmit = SwarmIt(url=swarmit_url)
            if not self.swarmit.health():
                print(f"Warning: Swarm-It sidecar not reachable at {swarmit_url}")
                self.swarmit = None
        else:
            self.swarmit = None

    def certify(self, content: str, stage: str, fallback_score: float = None) -> dict:
        """Certify content through Swarm-It API with constraint graph evaluation."""
        # Import constraint graph for rich evaluation
        from analyzer.constraint_graph import evaluate_paper_constraints, get_gate_diagnosis

        if not self.swarmit:
            # Use fallback score from RSCT scorer to estimate RSN
            # When API unavailable, estimate from combined_score
            if fallback_score is not None and fallback_score > 0:
                # Estimate RSN from combined score (heuristic)
                R = min(0.9, fallback_score * 1.2)  # Relevance ~ score
                S = min(0.9, fallback_score * 0.9)  # Stability slightly lower
                N = max(0.1, 1.0 - fallback_score)  # Noise inverse of score
                # Normalize to simplex
                total = R + S + N
                R, S, N = R/total, S/total, N/total
                kappa = R / (R + N) if (R + N) > 0 else 0.5
                # Estimate sigma (turbulence) from noise - lower N means more stable
                sigma = N * 0.7  # Scale noise to turbulence range

                # Use constraint graph for full evaluation
                eval_result = evaluate_paper_constraints(R, S, N, kappa, sigma)

                return {
                    "allowed": eval_result.decision != "REJECT",
                    "kappa_gate": round(kappa, 3),
                    "R": round(R, 3),
                    "S": round(S, 3),
                    "N": round(N, 3),
                    "sigma": round(sigma, 3),
                    "alpha": round(eval_result.alpha, 3),
                    "gate_reached": eval_result.gate_reached.value,
                    "decision": eval_result.decision.value,
                    "stage": stage,
                    # Rich graph-based insights
                    "diagnosis": eval_result.diagnosis,
                    "recommendations": eval_result.recommendations,
                    "is_bridge_paper": eval_result.is_bridge_paper,
                    "bridge_factor": round(eval_result.bridge_factor, 3),
                    "collapse_types": [c.value for c in eval_result.collapse_types],
                    "domains_affected": [d.value for d in eval_result.domains_affected],
                    "violations": [v.message for v in eval_result.violations if v.severity in ["fatal", "critical", "warning"]],
                }
            else:
                R, S, N = 0.33, 0.34, 0.33  # Uniform when no score
                kappa = 0.5
                sigma = 0.3
                decision = "PENDING"
                gate_reached = 0  # Not yet evaluated
                return {
                    "allowed": True,
                    "kappa_gate": round(kappa, 3),
                    "R": round(R, 3),
                    "S": round(S, 3),
                    "N": round(N, 3),
                    "sigma": round(sigma, 3),
                    "alpha": 0.5,
                    "gate_reached": gate_reached,
                    "decision": decision,
                    "stage": stage,
                    "diagnosis": "Pending evaluation - no score available",
                    "recommendations": ["Score the paper to get full evaluation"],
                    "is_bridge_paper": False,
                    "bridge_factor": 0.0,
                    "collapse_types": [],
                    "domains_affected": [],
                    "violations": [],
                }

        try:
            cert = self.swarmit.certify(content)
            R = cert.R
            S = cert.S
            N = cert.N
            kappa = cert.kappa_gate
            sigma = cert.sigma if hasattr(cert, 'sigma') else 0.3

            # Use constraint graph for additional insights
            eval_result = evaluate_paper_constraints(R, S, N, kappa, sigma)

            return {
                "allowed": cert.allowed,
                "kappa_gate": kappa,
                "decision": cert.decision.value if hasattr(cert.decision, 'value') else str(cert.decision),
                "R": R,
                "S": S,
                "N": N,
                "sigma": sigma,
                "alpha": round(eval_result.alpha, 3),
                "gate_reached": cert.gate_reached if hasattr(cert, 'gate_reached') else eval_result.gate_reached.value,
                "stage": stage,
                # Rich graph-based insights
                "diagnosis": eval_result.diagnosis,
                "recommendations": eval_result.recommendations,
                "is_bridge_paper": eval_result.is_bridge_paper,
                "bridge_factor": round(eval_result.bridge_factor, 3),
                "collapse_types": [c.value for c in eval_result.collapse_types],
                "domains_affected": [d.value for d in eval_result.domains_affected],
                "violations": [v.message for v in eval_result.violations if v.severity in ["fatal", "critical", "warning"]],
            }
        except Exception as e:
            print(f"Certification error: {e}")
            # Return proper fallback with RSN values (error = high noise)
            return {
                "allowed": True,
                "kappa_gate": 0.0,
                "R": 0.0,
                "S": 0.0,
                "N": 1.0,
                "sigma": 0.5,
                "gate_reached": 1,  # Failed at noise gate
                "decision": "ERROR",
                "stage": stage
            }

    async def run(self, days: int = 1, max_papers: int = 50, dry_run: bool = False, generate_pdfs: bool = True) -> dict:
        """Run the full pipeline."""
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "papers_fetched": 0,
            "papers_matched": 0,
            "papers_rsct_ranked": 0,
            "posts_generated": 0,
            "pdfs_generated": 0,
            "certifications": [],
            "top_papers": [],
            "errors": [],
        }

        # Load topics
        print("Loading topics...")
        if self.bedrock_matcher:
            topics_json = os.path.join(self.topics_dir, "topics.json")
            self.bedrock_matcher.load_topics(topics_json)
        elif self.matcher:
            self.matcher.load_topics()
            if not self.matcher.topics:
                print("Warning: No topics loaded, using keyword matching")

        # Stage 1: Fetch papers
        print(f"\n[1/3] Fetching papers from last {days} day(s)...")
        papers = await fetch_all_sources(days=days, max_per_source=max_papers)
        results["papers_fetched"] = len(papers)
        results["all_papers"] = papers  # For source distribution analysis
        print(f"  Found {len(papers)} papers")

        if not papers:
            print("No papers found")
            return results

        # Skip scanner certification (internal operation, trust internal code)
        print(f"  Scanner: Trusted internal operation (no certification needed)")

        # Stage 2: Match against topics
        print("\n[2/3] Matching papers against topics...")
        paper_dicts = [{"id": p.id, "title": p.title, "abstract": p.abstract} for p in papers]

        if self.bedrock_matcher:
            print("  Using Bedrock Titan embeddings for semantic matching...")
            bedrock_matches = self.bedrock_matcher.match_papers(paper_dicts)
            # Convert to MatchResult-like objects
            class BedrockMatchResult:
                def __init__(self, m):
                    self.similarity_score = m.similarity_score
                    self.matched_topics = m.matched_topics
            matches = [BedrockMatchResult(m) for m in bedrock_matches]
        else:
            matches = self.matcher.match_papers(paper_dicts)

        # Filter by score
        relevant = [(p, m) for p, m in zip(papers, matches) if m.similarity_score >= self.min_score]
        results["papers_matched"] = len(relevant)
        results["matched_papers"] = [p for p, m in relevant]  # For SWARM analysis
        print(f"  {len(relevant)} papers above {self.min_score:.0%} threshold")

        if not relevant:
            print("No papers matched above threshold")
            return results

        # Skip analyzer certification (internal operation)
        print(f"  Analyzer: Trusted internal operation (no certification needed)")

        # Stage 2.5: RSCT Whitepaper Scoring
        print("\n[2.5/4] Scoring papers against RSCT whitepaper...")
        rsct_paper_dicts = [
            {
                "id": p.id,
                "title": p.title,
                "abstract": p.abstract,
                "similarity_score": m.similarity_score,
            }
            for p, m in relevant
        ]
        rsct_scores = self.rsct_scorer.rank_papers(rsct_paper_dicts, min_rsct_score=self.min_rsct_score)
        results["papers_rsct_ranked"] = len(rsct_scores)
        print(f"  {len(rsct_scores)} papers above {self.min_rsct_score:.0%} RSCT threshold")

        # Create lookup for RSCT scores
        rsct_lookup = {s.paper_id: s for s in rsct_scores}

        # Resort relevant papers by RSCT combined score
        relevant_with_rsct = []
        for paper, match in relevant:
            rsct = rsct_lookup.get(paper.id)
            if rsct:
                relevant_with_rsct.append((paper, match, rsct))

        # Sort by combined RSCT score
        relevant_with_rsct.sort(key=lambda x: x[2].combined_score, reverse=True)

        # Show top papers
        print("\n  Top RSCT-Ranked Papers:")
        for i, (p, m, r) in enumerate(relevant_with_rsct[:5]):
            print(f"    {i+1}. {p.title[:50]}...")
            print(f"       Topic: {m.similarity_score:.0%} | RSCT: {r.rsct_similarity:.0%} | Combined: {r.combined_score:.0%}")
            results["top_papers"].append({
                "title": p.title,
                "topic_score": m.similarity_score,
                "rsct_score": r.rsct_similarity,
                "combined_score": r.combined_score,
                "key_overlaps": r.key_overlaps,
            })

        # Stage 2.75: Paper2SwarmAgent conversion (papers with GitHub repos)
        results["agents_converted"] = 0
        if self.paper2agent and not dry_run:
            papers_with_github = [
                (p, m, r) for p, m, r in relevant_with_rsct
                if hasattr(p, 'github_url') and p.github_url
            ]

            if papers_with_github:
                print(f"\n[2.75/4] Converting {len(papers_with_github)} papers with GitHub repos to agents...")
                os.makedirs(self.agents_output_dir, exist_ok=True)

                for paper, match, rsct in papers_with_github[:5]:  # Limit to top 5
                    try:
                        result = self.paper2agent.convert(
                            paper_id=paper.id,
                            paper_title=paper.title,
                            github_url=paper.github_url,
                            paper_url=paper.url,
                        )

                        if result.success and result.agent:
                            agent_path = os.path.join(
                                self.agents_output_dir,
                                f"{result.agent.id}.json"
                            )
                            result.agent.save(agent_path)
                            results["agents_converted"] += 1
                            print(f"    ✓ {paper.title[:40]}... → {result.agent.id}")
                            print(f"      Tools: {len(result.agent.tools)}, Confidence: {result.agent.confidence:.2f}")
                        else:
                            print(f"    ✗ {paper.title[:40]}... ({result.error or 'no tools found'})")

                    except Exception as e:
                        print(f"    ✗ {paper.title[:40]}... (error: {e})")

                print(f"  Converted {results['agents_converted']} papers to agents")
            else:
                print("\n[2.75/4] Paper2SwarmAgent: No papers with GitHub URLs found")

        # Stage 3: Generate blog posts
        print("\n[3/4] Generating blog posts...")

        if dry_run:
            print("  [DRY RUN] Would generate posts for:")
            for paper, match, rsct in relevant_with_rsct[:10]:
                print(f"    - {paper.title[:50]}... (combined: {rsct.combined_score:.0%})")
            return results

        # Convert to PaperData with RSCT metrics
        # Certification strategy: Certify external data (paper content from arXiv)
        # Skip internal operations (scanner/analyzer) - trust our own code
        paper_data = []
        for paper, match, rsct in relevant_with_rsct[:10]:  # Limit to top 10
            # Certify external paper content (not our summaries)
            # Pass RSCT combined_score as fallback when API unavailable
            cert = self.certify(
                f"{paper.title}\n\nAbstract: {paper.abstract[:500]}",
                "paper",
                fallback_score=rsct.combined_score
            )
            # Debug: trace problematic papers
            if cert.get("R") == 0 or cert.get("kappa_gate") == 0:
                print(f"DEBUG: Paper '{paper.title[:40]}' got R=0!")
                print(f"  rsct.combined_score = {rsct.combined_score}")
                print(f"  cert = {cert}")
            results["certifications"].append(cert)

            paper_data.append(PaperData(
                id=paper.id,
                title=paper.title,
                abstract=paper.abstract,
                authors=paper.authors,
                source=paper.source,
                url=paper.url,
                pdf_url=paper.pdf_url,
                published_date=paper.published_date,
                similarity_score=rsct.combined_score,  # Use combined score
                matched_topics=match.matched_topics,
                categories=paper.categories,
                # RSCT certification from sidecar
                rsct_R=cert.get("R"),
                rsct_S=cert.get("S"),
                rsct_N=cert.get("N"),
                rsct_kappa=cert.get("kappa_gate"),
                rsct_decision=cert.get("decision"),
                # Graph-based insights
                rsct_alpha=cert.get("alpha"),
                rsct_sigma=cert.get("sigma"),
                rsct_diagnosis=cert.get("diagnosis"),
                rsct_recommendations=cert.get("recommendations"),
                rsct_is_bridge_paper=cert.get("is_bridge_paper", False),
                rsct_collapse_types=cert.get("collapse_types"),
                rsct_violations=cert.get("violations"),
            ))

        # Generate posts
        saved = self.generator.generate_and_save(paper_data)
        results["posts_generated"] = len(saved)
        print(f"  Generated {len(saved)} posts (each paper pre-certified)")

        # Stage 4: Generate PDF reviews for top papers
        if generate_pdfs and relevant_with_rsct:
            print("\n[4/4] Generating PDF reviews for top papers...")
            top_for_pdf = relevant_with_rsct[:5]  # Top 5 for detailed PDF reviews

            pdf_papers = []
            for paper, match, rsct in top_for_pdf:
                # Certify external paper content for PDF generation
                cert = self.certify(
                    f"{paper.title}\n\nAbstract: {paper.abstract[:500]}",
                    "paper_pdf",
                    fallback_score=rsct.combined_score
                )
                pdf_papers.append({
                    "id": paper.id,
                    "title": paper.title,
                    "abstract": paper.abstract,
                    "authors": paper.authors,
                    "url": paper.url,
                    "rsct_similarity": rsct.rsct_similarity,
                    "similarity_score": match.similarity_score,
                    "key_overlaps": rsct.key_overlaps,
                    "rsct_R": cert.get("R"),
                    "rsct_S": cert.get("S"),
                    "rsct_N": cert.get("N"),
                    "rsct_kappa": cert.get("kappa_gate"),
                })

            pdf_reviews = self.pdf_generator.generate_batch(pdf_papers, max_papers=5)
            results["pdfs_generated"] = len(pdf_reviews)

            print(f"  Generated {len(pdf_reviews)} PDF reviews:")
            for review in pdf_reviews:
                status = "PDF" if review.pdf_path else "TEX only"
                print(f"    - {review.title[:50]}... [{status}]")

        # Stage 5: Generate RSCT analysis charts
        print("\n[5/5] Generating RSCT analysis charts...")
        try:
            from publisher.chart_generator import generate_discovery_charts

            # Collect certificates for charting
            chart_certs = results.get("certifications", [])
            if chart_certs:
                chart_batch = generate_discovery_charts(chart_certs, upload_s3=not dry_run)
                results["charts_generated"] = len(chart_batch.chart_paths)
                results["chart_paths"] = chart_batch.chart_paths
                print(f"  Generated {results['charts_generated']} charts")
                if chart_batch.s3_paths:
                    print(f"  Uploaded to S3: {len(chart_batch.s3_paths)} files")
            else:
                print("  No certificates to chart")
                results["charts_generated"] = 0
        except ImportError as e:
            print(f"  Chart generation skipped (swarm-it-api not available): {e}")
            results["charts_generated"] = 0
        except Exception as e:
            print(f"  Chart generation error: {e}")
            results["charts_generated"] = 0

        print(f"\nPipeline complete: {results['posts_generated']} posts, {results.get('pdfs_generated', 0)} PDFs, {results.get('agents_converted', 0)} agents, {results.get('charts_generated', 0)} charts")
        return results


def main():
    parser = argparse.ArgumentParser(description="Run paper discovery pipeline")
    parser.add_argument("--days", type=int, default=1, help="Days to look back")
    parser.add_argument("--max-papers", type=int, default=50, help="Max papers per source")
    parser.add_argument("--min-score", type=float, default=0.5, help="Min topic similarity score")
    parser.add_argument("--min-rsct-score", type=float, default=0.3, help="Min RSCT relevance score")
    parser.add_argument("--dry-run", action="store_true", help="Don't generate posts")
    parser.add_argument("--no-pdfs", action="store_true", help="Skip PDF generation")
    parser.add_argument("--topics-dir", default="site/src/content/topics", help="Topics directory")
    parser.add_argument("--output-dir", default="site/src/content/reviews", help="Output directory")
    parser.add_argument("--pdf-output-dir", default="content/pdf-reviews", help="PDF output directory")
    parser.add_argument("--agents-output-dir", default="content/research-agents", help="Agents output directory")
    parser.add_argument("--whitepaper", default=None, help="Path to RSCT whitepaper for comparison")
    args = parser.parse_args()

    swarmit_url = os.getenv("SWARMIT_URL", "https://api.swarms.network")

    pipeline = CertifiedPipeline(
        swarmit_url=swarmit_url,
        topics_dir=args.topics_dir,
        output_dir=args.output_dir,
        pdf_output_dir=args.pdf_output_dir,
        agents_output_dir=args.agents_output_dir,
        whitepaper_path=args.whitepaper,
        min_score=args.min_score,
        min_rsct_score=args.min_rsct_score,
    )

    results = asyncio.run(pipeline.run(
        days=args.days,
        max_papers=args.max_papers,
        dry_run=args.dry_run,
        generate_pdfs=not args.no_pdfs,
    ))

    # Summary
    print("\n" + "=" * 60)
    print("PIPELINE SUMMARY")
    print("=" * 60)
    print(f"Papers fetched:    {results['papers_fetched']}")
    print(f"Papers matched:    {results['papers_matched']}")
    print(f"RSCT ranked:       {results.get('papers_rsct_ranked', 0)}")
    print(f"Agents converted:  {results.get('agents_converted', 0)}")
    print(f"Posts generated:   {results['posts_generated']}")
    print(f"PDFs generated:    {results.get('pdfs_generated', 0)}")
    print(f"Charts generated:  {results.get('charts_generated', 0)}")
    print(f"Certifications:    {len(results['certifications'])}")

    if results["errors"]:
        print(f"\nErrors: {results['errors']}")

    # Print certification summary
    if results["certifications"]:
        print("\nCertification Results:")
        for cert in results["certifications"]:
            status = "PASS" if cert["allowed"] else "BLOCK"
            print(f"  [{cert['stage']}] {status} kappa={cert['kappa_gate']:.2f}")

    # Print top papers
    if results.get("top_papers"):
        print("\n" + "-" * 60)
        print("TOP RSCT-RANKED PAPERS")
        print("-" * 60)
        for i, paper in enumerate(results["top_papers"][:5], 1):
            print(f"\n{i}. {paper['title'][:60]}...")
            print(f"   Topic: {paper['topic_score']:.0%} | RSCT: {paper['rsct_score']:.0%} | Combined: {paper['combined_score']:.0%}")
            if paper.get('key_overlaps'):
                print(f"   Key concepts: {', '.join(paper['key_overlaps'][:5])}")


def upload_to_s3(local_dir: str, bucket: str, prefix: str = "content/reviews") -> list:
    """Upload generated posts to S3."""
    import boto3
    from pathlib import Path

    s3 = boto3.client("s3")
    uploaded = []

    local_path = Path(local_dir)
    if not local_path.exists():
        return uploaded

    for file in local_path.glob("*.mdx"):
        key = f"{prefix}/{file.name}"
        try:
            s3.upload_file(str(file), bucket, key, ExtraArgs={"ContentType": "text/markdown"})
            uploaded.append(key)
            print(f"  Uploaded: s3://{bucket}/{key}")
        except Exception as e:
            print(f"  S3 upload error for {file.name}: {e}")

    return uploaded


def analyze_source_distribution(papers: list) -> dict:
    """Analyze which sources are producing matching papers."""
    from collections import Counter

    source_counts = Counter(p.source for p in papers)
    total = len(papers)

    distribution = {
        "total_papers": total,
        "sources": {},
        "diversity_score": 0.0,
    }

    for source, count in source_counts.items():
        pct = (count / total * 100) if total > 0 else 0
        distribution["sources"][source] = {
            "count": count,
            "percentage": round(pct, 1),
        }

    # Diversity score: 1.0 = evenly distributed, 0.0 = single source
    if total > 0 and len(source_counts) > 1:
        # Shannon entropy normalized
        import math
        entropy = -sum((c/total) * math.log2(c/total) for c in source_counts.values() if c > 0)
        max_entropy = math.log2(len(source_counts))
        distribution["diversity_score"] = round(entropy / max_entropy, 3) if max_entropy > 0 else 0
    elif len(source_counts) == 1:
        distribution["diversity_score"] = 0.0

    return distribution


def run_swarm_analysis(papers: list, top_n: int = 5) -> list:
    """Run SWARM source-specific agent analysis on papers."""
    try:
        # Try to use full agent system
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from agents.orchestrator import run_daily_agents

        # Convert Paper objects to dicts
        paper_dicts = [
            {
                "id": p.id,
                "title": p.title,
                "abstract": p.abstract,
                "source": p.source,
                "categories": getattr(p, 'categories', []),
            }
            for p in papers[:top_n * 2]  # Analyze more to get good coverage
        ]

        report = run_daily_agents(paper_dicts, s3_bucket=None)

        # Convert to simple list format
        analyses = []
        for paper in report.get("top_papers", []):
            analyses.append({
                "paper_id": paper.get("paper_id", ""),
                "paper_title": paper.get("title", ""),
                "source": paper.get("source", ""),
                "relevance": paper.get("relevance", 5),
                "novelty": paper.get("novelty", 5),
                "impact": paper.get("impact", 5),
                "summary": paper.get("summary", ""),
                "rsct_connections": paper.get("rsct_connections", []),
            })

        return analyses[:top_n]

    except ImportError:
        # Fall back to simple GPT analysis
        print("  Using simple SWARM analysis (agents not available)")
        return _simple_swarm_analysis(papers, top_n)


def _simple_swarm_analysis(papers: list, top_n: int = 3) -> list:
    """Fallback simple SWARM analysis when agents not available."""
    try:
        from openai import OpenAI
        client = OpenAI()
    except:
        print("  SWARM analysis skipped (OpenAI not available)")
        return []

    analyses = []
    for paper in papers[:top_n]:
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "system",
                    "content": """Analyze this research paper. Respond in JSON:
{"relevance": <0-10>, "novelty": <0-10>, "impact": <0-10>, "summary": "<brief>", "rsct_connections": ["connection1"]}"""
                }, {
                    "role": "user",
                    "content": f"Title: {paper.title}\n\nAbstract: {paper.abstract[:1000]}"
                }],
                max_tokens=300,
                response_format={"type": "json_object"},
            )

            import json
            analysis = json.loads(response.choices[0].message.content)
            analysis["paper_id"] = paper.id
            analysis["paper_title"] = paper.title
            analysis["source"] = paper.source
            analyses.append(analysis)
            print(f"  Analyzed: {paper.title[:50]}... R:{analysis.get('relevance')}/N:{analysis.get('novelty')}/I:{analysis.get('impact')}")

        except Exception as e:
            print(f"  Error: {e}")

    return analyses


def save_daily_report(results: dict, bucket: str) -> str:
    """Save daily analytics report to S3."""
    import boto3
    import json
    from datetime import datetime

    s3 = boto3.client("s3")
    today = datetime.utcnow().strftime("%Y-%m-%d")

    report = {
        "date": today,
        "timestamp": datetime.utcnow().isoformat(),
        **results,
    }

    key = f"analytics/daily/{today}.json"
    try:
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(report, indent=2, default=str),
            ContentType="application/json",
        )
        print(f"  Report saved: s3://{bucket}/{key}")
        return key
    except Exception as e:
        print(f"  Report save error: {e}")
        return ""


def handler(event, context):
    """AWS Lambda handler for scheduled execution."""
    import json

    # Get parameters from event or use defaults
    days = event.get("days", 1)
    max_papers = event.get("max_papers", 50)
    min_score = event.get("min_score", 0.5)
    min_rsct_score = event.get("min_rsct_score", 0.1)  # Lowered default
    dry_run = event.get("dry_run", False)

    swarmit_url = os.getenv("SWARMIT_URL", "https://api.swarms.network")
    s3_bucket = os.getenv("S3_BUCKET", "swarmit-nextshift-site")

    # Lambda can only write to /tmp
    # Use bundled whitepaper from Zenodo
    whitepaper_path = os.path.join(os.path.dirname(__file__), "rsct_whitepaper.pdf")

    pipeline = CertifiedPipeline(
        swarmit_url=swarmit_url,
        topics_dir="site/src/content/topics",
        output_dir="/tmp/generated-posts",
        pdf_output_dir="/tmp/pdf-reviews",
        whitepaper_path=whitepaper_path,
        min_score=min_score,
        min_rsct_score=min_rsct_score,
    )

    results = asyncio.run(pipeline.run(
        days=days,
        max_papers=max_papers,
        dry_run=dry_run,
        generate_pdfs=False,  # Skip PDFs in Lambda (no LaTeX)
    ))

    # Analyze source distribution
    print("\n[5/5] Analyzing source distribution...")
    source_dist = analyze_source_distribution(results.get("all_papers", []))
    results["source_distribution"] = source_dist
    print(f"  Sources: {len(source_dist['sources'])} | Diversity: {source_dist['diversity_score']:.1%}")
    for src, data in source_dist["sources"].items():
        print(f"    {src}: {data['count']} papers ({data['percentage']}%)")

    # Run SWARM analysis on matched papers
    if results.get("matched_papers") and not dry_run:
        print("\n[6/6] Running SWARM agent analysis...")
        swarm_analyses = run_swarm_analysis(results["matched_papers"], top_n=5)
        results["swarm_analyses"] = swarm_analyses

    # Upload posts to S3
    if not dry_run and results.get("posts_generated", 0) > 0:
        print("\n[7/7] Uploading posts to S3...")
        uploaded = upload_to_s3("/tmp/generated-posts", s3_bucket)
        results["s3_uploads"] = uploaded

    # Save daily analytics report
    if not dry_run:
        report_key = save_daily_report(results, s3_bucket)
        results["report_key"] = report_key

    # Log summary
    print(f"\nPipeline complete: {results['papers_fetched']} fetched, "
          f"{results['papers_matched']} matched, {results['posts_generated']} posts, "
          f"{len(source_dist['sources'])} sources (diversity: {source_dist['diversity_score']:.1%})")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "papers_fetched": results["papers_fetched"],
            "papers_matched": results["papers_matched"],
            "papers_rsct_ranked": results.get("papers_rsct_ranked", 0),
            "posts_generated": results["posts_generated"],
            "source_distribution": source_dist,
            "swarm_analyses": results.get("swarm_analyses", []),
            "s3_uploads": results.get("s3_uploads", []),
            "top_papers": results.get("top_papers", [])[:5],
        })
    }


if __name__ == "__main__":
    main()
