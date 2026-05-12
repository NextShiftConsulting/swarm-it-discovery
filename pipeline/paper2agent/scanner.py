"""
Tutorial Scanner - Scan repositories for convertible tutorials.

Adapted from Paper2Agent's tutorial-scanner for swarm-it integration.
Designed for ADK extraction - minimal dependencies.
"""

import re
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any
from enum import Enum


class TutorialType(str, Enum):
    """Type of tutorial file."""
    NOTEBOOK = "notebook"
    MARKDOWN = "markdown"
    SCRIPT = "script"
    DOCUMENTATION = "documentation"


@dataclass
class TutorialFile:
    """A discovered tutorial file."""
    path: str
    title: str
    description: str
    type: TutorialType
    include_in_tools: bool
    reason: str
    code_blocks: int = 0
    estimated_functions: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Export to dictionary."""
        return {
            "path": self.path,
            "title": self.title,
            "description": self.description,
            "type": self.type.value,
            "include_in_tools": self.include_in_tools,
            "reason": self.reason,
            "code_blocks": self.code_blocks,
            "estimated_functions": self.estimated_functions,
        }


@dataclass
class ScanResult:
    """Result of scanning a repository."""
    repo_name: str
    repo_path: str
    total_scanned: int
    total_included: int
    tutorials: List[TutorialFile] = field(default_factory=list)
    success: bool = True
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Export to dictionary."""
        return {
            "scan_metadata": {
                "github_repo_name": self.repo_name,
                "total_files_scanned": self.total_scanned,
                "total_files_included_in_tools": self.total_included,
                "success": self.success,
                "error": self.error,
            },
            "tutorials": [t.to_dict() for t in self.tutorials],
        }

    def get_included(self) -> List[TutorialFile]:
        """Get tutorials marked for inclusion."""
        return [t for t in self.tutorials if t.include_in_tools]


class TutorialScanner:
    """
    Scan repositories for tutorials that can be converted to tools.

    Follows Paper2Agent patterns but simplified for swarm-it use.

    Usage:
        scanner = TutorialScanner()
        result = scanner.scan("/path/to/repo")

        for tutorial in result.get_included():
            print(f"Found: {tutorial.title}")
    """

    # File patterns to scan (in priority order)
    PATTERNS = [
        ("docs/**/*.ipynb", TutorialType.NOTEBOOK),
        ("docs/**/*.md", TutorialType.MARKDOWN),
        ("tutorials/**/*.ipynb", TutorialType.NOTEBOOK),
        ("examples/**/*.ipynb", TutorialType.NOTEBOOK),
        ("notebooks/**/*.ipynb", TutorialType.NOTEBOOK),
        ("**/*.ipynb", TutorialType.NOTEBOOK),
    ]

    # Directories to skip
    SKIP_DIRS = {
        ".git", "__pycache__", "node_modules", ".venv", "venv",
        "build", "dist", ".tox", ".pytest_cache", "templates",
    }

    # Files to skip (patterns)
    SKIP_PATTERNS = [
        r"test_.*\.py$",
        r".*_test\.py$",
        r"conftest\.py$",
        r"setup\.py$",
        r"__init__\.py$",
        r".*legacy.*",
        r".*deprecated.*",
        r".*old.*",
    ]

    def __init__(self, min_code_blocks: int = 3, min_functions: int = 1):
        """
        Initialize scanner.

        Args:
            min_code_blocks: Minimum code blocks to include a notebook
            min_functions: Minimum extractable functions to include
        """
        self.min_code_blocks = min_code_blocks
        self.min_functions = min_functions

    def scan(self, repo_path: str) -> ScanResult:
        """
        Scan a repository for tutorials.

        Args:
            repo_path: Path to cloned repository

        Returns:
            ScanResult with discovered tutorials
        """
        repo_path = Path(repo_path)
        repo_name = repo_path.name

        if not repo_path.exists():
            return ScanResult(
                repo_name=repo_name,
                repo_path=str(repo_path),
                total_scanned=0,
                total_included=0,
                success=False,
                error=f"Repository path not found: {repo_path}",
            )

        tutorials = []
        scanned_paths = set()

        # Scan in priority order
        for pattern, file_type in self.PATTERNS:
            for file_path in repo_path.glob(pattern):
                if str(file_path) in scanned_paths:
                    continue
                if self._should_skip(file_path):
                    continue

                scanned_paths.add(str(file_path))
                tutorial = self._analyze_file(file_path, file_type, repo_path)
                if tutorial:
                    tutorials.append(tutorial)

        # Count included
        included = [t for t in tutorials if t.include_in_tools]

        return ScanResult(
            repo_name=repo_name,
            repo_path=str(repo_path),
            total_scanned=len(scanned_paths),
            total_included=len(included),
            tutorials=tutorials,
            success=True,
        )

    def _should_skip(self, file_path: Path) -> bool:
        """Check if file should be skipped."""
        # Check directory
        for part in file_path.parts:
            if part in self.SKIP_DIRS:
                return True

        # Check file patterns
        filename = file_path.name
        for pattern in self.SKIP_PATTERNS:
            if re.match(pattern, filename, re.IGNORECASE):
                return True

        return False

    def _analyze_file(
        self, file_path: Path, file_type: TutorialType, repo_root: Path
    ) -> Optional[TutorialFile]:
        """Analyze a file to determine if it should be included."""
        try:
            relative_path = str(file_path.relative_to(repo_root))

            if file_type == TutorialType.NOTEBOOK:
                return self._analyze_notebook(file_path, relative_path)
            elif file_type == TutorialType.MARKDOWN:
                return self._analyze_markdown(file_path, relative_path)
            else:
                return None

        except Exception as e:
            return TutorialFile(
                path=str(file_path),
                title=file_path.stem,
                description=f"Error analyzing: {e}",
                type=file_type,
                include_in_tools=False,
                reason=f"Analysis error: {e}",
            )

    def _analyze_notebook(
        self, file_path: Path, relative_path: str
    ) -> Optional[TutorialFile]:
        """Analyze a Jupyter notebook."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                nb = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None

        cells = nb.get("cells", [])
        code_cells = [c for c in cells if c.get("cell_type") == "code"]
        markdown_cells = [c for c in cells if c.get("cell_type") == "markdown"]

        # Extract title from first markdown cell
        title = file_path.stem.replace("_", " ").replace("-", " ").title()
        if markdown_cells:
            first_md = "".join(markdown_cells[0].get("source", []))
            if first_md.startswith("#"):
                title = first_md.split("\n")[0].lstrip("#").strip()

        # Count code blocks and estimate functions
        code_blocks = len(code_cells)
        estimated_functions = self._estimate_functions(code_cells)

        # Build description from markdown
        description = self._extract_description(markdown_cells)

        # Determine inclusion
        include = (
            code_blocks >= self.min_code_blocks
            and estimated_functions >= self.min_functions
        )

        if include:
            reason = f"Contains {code_blocks} code cells with ~{estimated_functions} extractable functions"
        else:
            reason = f"Insufficient content: {code_blocks} code cells, ~{estimated_functions} functions"

        return TutorialFile(
            path=relative_path,
            title=title,
            description=description,
            type=TutorialType.NOTEBOOK,
            include_in_tools=include,
            reason=reason,
            code_blocks=code_blocks,
            estimated_functions=estimated_functions,
        )

    def _analyze_markdown(
        self, file_path: Path, relative_path: str
    ) -> Optional[TutorialFile]:
        """Analyze a markdown file."""
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return None

        # Extract title
        title = file_path.stem.replace("_", " ").replace("-", " ").title()
        lines = content.split("\n")
        for line in lines:
            if line.startswith("# "):
                title = line[2:].strip()
                break

        # Count code blocks
        code_blocks = len(re.findall(r"```(?:python|py)", content, re.IGNORECASE))
        estimated_functions = self._estimate_functions_from_markdown(content)

        # Build description
        description = self._extract_description_from_markdown(content)

        # Markdown files with code are lower priority
        include = code_blocks >= 5 and estimated_functions >= 2

        if include:
            reason = f"Contains {code_blocks} Python code blocks with ~{estimated_functions} functions"
        else:
            reason = f"Insufficient code: {code_blocks} blocks, ~{estimated_functions} functions"

        return TutorialFile(
            path=relative_path,
            title=title,
            description=description,
            type=TutorialType.MARKDOWN,
            include_in_tools=include,
            reason=reason,
            code_blocks=code_blocks,
            estimated_functions=estimated_functions,
        )

    def _estimate_functions(self, code_cells: List[Dict]) -> int:
        """Estimate number of extractable functions from code cells."""
        count = 0
        for cell in code_cells:
            source = "".join(cell.get("source", []))
            # Count function definitions
            count += len(re.findall(r"^\s*def\s+\w+\s*\(", source, re.MULTILINE))
            # Count class definitions
            count += len(re.findall(r"^\s*class\s+\w+", source, re.MULTILINE))
        return count

    def _estimate_functions_from_markdown(self, content: str) -> int:
        """Estimate functions from markdown code blocks."""
        code_blocks = re.findall(
            r"```(?:python|py)\n(.*?)```", content, re.DOTALL | re.IGNORECASE
        )
        count = 0
        for block in code_blocks:
            count += len(re.findall(r"^\s*def\s+\w+\s*\(", block, re.MULTILINE))
        return count

    def _extract_description(self, markdown_cells: List[Dict]) -> str:
        """Extract description from markdown cells."""
        for cell in markdown_cells[:3]:  # First 3 markdown cells
            text = "".join(cell.get("source", []))
            # Skip title lines
            lines = [line for line in text.split("\n") if not line.startswith("#")]
            text = " ".join(lines).strip()
            if len(text) > 50:
                return text[:200] + "..." if len(text) > 200 else text
        return "No description available"

    def _extract_description_from_markdown(self, content: str) -> str:
        """Extract description from markdown content."""
        lines = content.split("\n")
        description_lines = []
        for line in lines:
            if line.startswith("#"):
                continue
            if line.startswith("```"):
                break
            line = line.strip()
            if line:
                description_lines.append(line)
            if len(" ".join(description_lines)) > 200:
                break
        text = " ".join(description_lines)
        return text[:200] + "..." if len(text) > 200 else text
