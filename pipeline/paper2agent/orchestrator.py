"""
Paper2SwarmAgent Orchestrator - Main entry point for converting papers to agents.

Coordinates the full pipeline: scan → extract → convert.
Designed for ADK extraction with clean interfaces.
"""

import os
import json
import tempfile
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

from .config import TopicConfig, Topic
from .scanner import TutorialScanner, ScanResult
from .extractor import ToolExtractor, ExtractionResult
from .converter import SwarmAgentConverter, AgentDefinition


@dataclass
class ConversionResult:
    """Result of converting a paper to an agent."""
    paper_id: str
    paper_title: str
    github_url: str
    success: bool
    agent: Optional[AgentDefinition] = None
    scan_result: Optional[ScanResult] = None
    extraction_results: List[ExtractionResult] = field(default_factory=list)
    error: Optional[str] = None
    duration_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "paper_id": self.paper_id,
            "paper_title": self.paper_title,
            "github_url": self.github_url,
            "success": self.success,
            "agent": self.agent.to_dict() if self.agent else None,
            "scan_result": self.scan_result.to_dict() if self.scan_result else None,
            "extraction_count": len(self.extraction_results),
            "error": self.error,
            "duration_seconds": self.duration_seconds,
        }


class Paper2SwarmAgent:
    """
    Convert research papers with GitHub repos to swarm-it agents.

    Orchestrates the full pipeline:
    1. Clone repository (if URL provided)
    2. Scan for tutorials
    3. Extract tools from tutorials
    4. Convert to ADK-compatible agent definition

    Usage:
        from pipeline.paper2agent import Paper2SwarmAgent, TopicConfig

        # Load topics
        config = TopicConfig.from_json("content/topics/topics.json")

        # Initialize
        converter = Paper2SwarmAgent(topics=config)

        # Convert a paper
        result = converter.convert(
            paper_id="2401.12345",
            paper_title="My Research Paper",
            github_url="https://github.com/author/repo",
        )

        if result.success:
            result.agent.save("agents/my_agent.json")
    """

    def __init__(
        self,
        topics: Optional[TopicConfig] = None,
        work_dir: Optional[str] = None,
        cleanup: bool = True,
    ):
        """
        Initialize the converter.

        Args:
            topics: Topic configuration for matching
            work_dir: Working directory for cloned repos (default: temp)
            cleanup: Clean up cloned repos after conversion
        """
        self.topics = topics or TopicConfig()
        self.work_dir = work_dir
        self.cleanup = cleanup

        # Initialize components
        self.scanner = TutorialScanner()
        self.extractor = ToolExtractor()
        self.converter = SwarmAgentConverter()

    def convert(
        self,
        paper_id: str,
        paper_title: str,
        github_url: str,
        paper_url: Optional[str] = None,
        topic_id: Optional[str] = None,
        repo_path: Optional[str] = None,
    ) -> ConversionResult:
        """
        Convert a paper to a swarm-it agent.

        Args:
            paper_id: Paper identifier (e.g., arXiv ID)
            paper_title: Paper title
            github_url: GitHub repository URL
            paper_url: Optional paper URL
            topic_id: Optional topic ID (auto-matched if not provided)
            repo_path: Optional local repo path (skips cloning)

        Returns:
            ConversionResult with agent definition
        """
        start_time = datetime.now()

        try:
            # Step 1: Get repository
            if repo_path:
                local_path = repo_path
                should_cleanup = False
            else:
                local_path, should_cleanup = self._clone_repo(github_url)

            if not local_path:
                return ConversionResult(
                    paper_id=paper_id,
                    paper_title=paper_title,
                    github_url=github_url,
                    success=False,
                    error="Failed to clone repository",
                )

            # Step 2: Scan for tutorials
            scan_result = self.scanner.scan(local_path)

            if not scan_result.success:
                return ConversionResult(
                    paper_id=paper_id,
                    paper_title=paper_title,
                    github_url=github_url,
                    success=False,
                    scan_result=scan_result,
                    error=scan_result.error,
                )

            # Step 3: Extract tools from included tutorials
            extraction_results = []
            for tutorial in scan_result.get_included():
                result = self.extractor.extract(tutorial, local_path)
                extraction_results.append(result)

            # Step 4: Match topic
            topic = None
            if topic_id:
                topic = self.topics.get_topic(topic_id)
            elif self.topics.topics:
                topic = self.topics.match_paper(paper_title, "")

            # Step 5: Convert to agent
            agent = self.converter.convert(
                paper_id=paper_id,
                paper_title=paper_title,
                github_url=github_url,
                extraction_results=extraction_results,
                topic=topic,
                paper_url=paper_url,
            )

            # Cleanup
            if should_cleanup and self.cleanup:
                self._cleanup_repo(local_path)

            duration = (datetime.now() - start_time).total_seconds()

            return ConversionResult(
                paper_id=paper_id,
                paper_title=paper_title,
                github_url=github_url,
                success=True,
                agent=agent,
                scan_result=scan_result,
                extraction_results=extraction_results,
                duration_seconds=duration,
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return ConversionResult(
                paper_id=paper_id,
                paper_title=paper_title,
                github_url=github_url,
                success=False,
                error=str(e),
                duration_seconds=duration,
            )

    def convert_batch(
        self,
        papers: List[Dict[str, Any]],
        output_dir: str,
    ) -> List[ConversionResult]:
        """
        Convert multiple papers to agents.

        Args:
            papers: List of paper dicts with id, title, github_url
            output_dir: Directory to save agent definitions

        Returns:
            List of ConversionResults
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        results = []

        for paper in papers:
            paper_id = paper.get("id", "")
            github_url = paper.get("github_url", "")

            if not github_url:
                results.append(ConversionResult(
                    paper_id=paper_id,
                    paper_title=paper.get("title", ""),
                    github_url="",
                    success=False,
                    error="No GitHub URL provided",
                ))
                continue

            result = self.convert(
                paper_id=paper_id,
                paper_title=paper.get("title", "Unknown"),
                github_url=github_url,
                paper_url=paper.get("url"),
                topic_id=paper.get("topic_id"),
            )

            # Save successful agents
            if result.success and result.agent:
                agent_path = output_path / f"{result.agent.id}.json"
                result.agent.save(str(agent_path))

            results.append(result)

        return results

    def _clone_repo(self, github_url: str) -> Tuple[Optional[str], bool]:
        """Clone a GitHub repository."""
        try:
            # Create temp directory if no work_dir
            if self.work_dir:
                base_dir = Path(self.work_dir)
                base_dir.mkdir(parents=True, exist_ok=True)
            else:
                base_dir = Path(tempfile.mkdtemp(prefix="paper2agent_"))

            # Extract repo name
            repo_name = github_url.rstrip("/").split("/")[-1]
            if repo_name.endswith(".git"):
                repo_name = repo_name[:-4]

            local_path = base_dir / repo_name

            # Clone
            result = subprocess.run(
                ["git", "clone", "--depth", "1", github_url, str(local_path)],
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode != 0:
                print(f"Clone failed: {result.stderr}")
                return None, False

            return str(local_path), True

        except subprocess.TimeoutExpired:
            print("Clone timeout")
            return None, False
        except Exception as e:
            print(f"Clone error: {e}")
            return None, False

    def _cleanup_repo(self, repo_path: str) -> None:
        """Clean up a cloned repository."""
        import shutil
        try:
            shutil.rmtree(repo_path)
        except Exception as e:
            print(f"Cleanup error: {e}")


def run_pipeline(
    topics_path: str,
    papers: List[Dict[str, Any]],
    output_dir: str,
) -> Dict[str, Any]:
    """
    Run the full Paper2SwarmAgent pipeline.

    Args:
        topics_path: Path to topics.json
        papers: List of paper dicts with github_url
        output_dir: Directory to save agents

    Returns:
        Summary report dict
    """
    # Load topics
    config = TopicConfig.from_json(topics_path)

    # Initialize
    converter = Paper2SwarmAgent(topics=config)

    # Convert
    results = converter.convert_batch(papers, output_dir)

    # Generate report
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]

    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "total_papers": len(papers),
        "successful": len(successful),
        "failed": len(failed),
        "output_dir": output_dir,
        "agents": [
            {
                "id": r.agent.id,
                "name": r.agent.name,
                "tools": len(r.agent.tools),
                "confidence": r.agent.confidence,
            }
            for r in successful if r.agent
        ],
        "failures": [
            {
                "paper_id": r.paper_id,
                "error": r.error,
            }
            for r in failed
        ],
    }

    # Save report
    report_path = Path(output_dir) / "conversion_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    return report


# CLI entry point
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Paper2SwarmAgent CLI")
    parser.add_argument("--topics", "-t", required=True, help="Path to topics.json")
    parser.add_argument("--papers", "-p", required=True, help="Path to papers.json")
    parser.add_argument("--output", "-o", required=True, help="Output directory")
    args = parser.parse_args()

    # Load papers
    with open(args.papers) as f:
        papers = json.load(f)

    # Run pipeline
    report = run_pipeline(args.topics, papers, args.output)

    print(f"\n=== Paper2SwarmAgent Complete ===")
    print(f"Successful: {report['successful']}/{report['total_papers']}")
    print(f"Agents saved to: {report['output_dir']}")
