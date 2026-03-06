"""
Tool Extractor - Extract callable functions from tutorials.

Parses notebooks and scripts to extract reusable tool definitions.
Designed for ADK extraction - uses only stdlib (ast module).
"""

import ast
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

from .scanner import TutorialFile, TutorialType


@dataclass
class Parameter:
    """A function parameter."""
    name: str
    type_hint: Optional[str] = None
    default: Optional[str] = None
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type_hint,
            "default": self.default,
            "description": self.description,
        }


@dataclass
class ExtractedTool:
    """A tool extracted from source code."""
    name: str
    description: str
    source_file: str
    source_code: str
    parameters: List[Parameter] = field(default_factory=list)
    return_type: Optional[str] = None
    return_description: str = ""
    dependencies: List[str] = field(default_factory=list)
    is_async: bool = False
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Export to dictionary (ADK-compatible)."""
        return {
            "name": self.name,
            "description": self.description,
            "source_file": self.source_file,
            "source_code": self.source_code,
            "parameters": [p.to_dict() for p in self.parameters],
            "return_type": self.return_type,
            "return_description": self.return_description,
            "dependencies": self.dependencies,
            "is_async": self.is_async,
            "confidence": self.confidence,
        }

    def to_tool_schema(self) -> Dict[str, Any]:
        """Convert to OpenAI/Anthropic tool schema format."""
        properties = {}
        required = []

        for param in self.parameters:
            prop = {"type": "string", "description": param.description or param.name}

            # Infer type from hint
            if param.type_hint:
                if "int" in param.type_hint.lower():
                    prop["type"] = "integer"
                elif "float" in param.type_hint.lower():
                    prop["type"] = "number"
                elif "bool" in param.type_hint.lower():
                    prop["type"] = "boolean"
                elif "list" in param.type_hint.lower():
                    prop["type"] = "array"
                elif "dict" in param.type_hint.lower():
                    prop["type"] = "object"

            properties[param.name] = prop

            if param.default is None:
                required.append(param.name)

        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }


@dataclass
class ExtractionResult:
    """Result of extracting tools from a tutorial."""
    tutorial_path: str
    tools: List[ExtractedTool] = field(default_factory=list)
    success: bool = True
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tutorial_path": self.tutorial_path,
            "tools": [t.to_dict() for t in self.tools],
            "success": self.success,
            "error": self.error,
        }


class ToolExtractor:
    """
    Extract callable tools from tutorial files.

    Uses AST parsing to extract function definitions with their
    signatures, docstrings, and dependencies.

    Usage:
        extractor = ToolExtractor()
        result = extractor.extract(tutorial_file, repo_path)

        for tool in result.tools:
            print(f"Found: {tool.name} - {tool.description}")
    """

    # Imports that indicate useful tools
    USEFUL_IMPORTS = {
        "numpy", "pandas", "torch", "tensorflow", "sklearn",
        "transformers", "datasets", "scipy", "matplotlib",
        "seaborn", "plotly", "networkx", "openai", "anthropic",
    }

    # Skip functions matching these patterns
    SKIP_FUNCTIONS = {
        "__init__", "__str__", "__repr__", "__eq__", "__hash__",
        "main", "test_", "_test", "setup", "teardown",
    }

    def __init__(self, min_params: int = 1, require_docstring: bool = False):
        """
        Initialize extractor.

        Args:
            min_params: Minimum parameters for a function to be a tool
            require_docstring: Require docstring for inclusion
        """
        self.min_params = min_params
        self.require_docstring = require_docstring

    def extract(
        self, tutorial: TutorialFile, repo_path: str
    ) -> ExtractionResult:
        """
        Extract tools from a tutorial file.

        Args:
            tutorial: Tutorial file metadata
            repo_path: Path to repository root

        Returns:
            ExtractionResult with extracted tools
        """
        file_path = Path(repo_path) / tutorial.path

        if not file_path.exists():
            return ExtractionResult(
                tutorial_path=tutorial.path,
                success=False,
                error=f"File not found: {file_path}",
            )

        try:
            if tutorial.type == TutorialType.NOTEBOOK:
                return self._extract_from_notebook(file_path, tutorial.path)
            elif tutorial.type == TutorialType.MARKDOWN:
                return self._extract_from_markdown(file_path, tutorial.path)
            else:
                return ExtractionResult(
                    tutorial_path=tutorial.path,
                    success=False,
                    error=f"Unsupported type: {tutorial.type}",
                )
        except Exception as e:
            return ExtractionResult(
                tutorial_path=tutorial.path,
                success=False,
                error=str(e),
            )

    def _extract_from_notebook(
        self, file_path: Path, relative_path: str
    ) -> ExtractionResult:
        """Extract tools from a Jupyter notebook."""
        with open(file_path, "r", encoding="utf-8") as f:
            nb = json.load(f)

        tools = []
        all_code = []
        imports = set()

        # Collect all code cells
        for cell in nb.get("cells", []):
            if cell.get("cell_type") == "code":
                source = "".join(cell.get("source", []))
                all_code.append(source)

                # Track imports
                for line in source.split("\n"):
                    if line.startswith("import ") or line.startswith("from "):
                        imports.add(line.strip())

        # Parse combined code
        combined_code = "\n\n".join(all_code)
        extracted = self._extract_from_code(combined_code, relative_path, imports)
        tools.extend(extracted)

        return ExtractionResult(
            tutorial_path=relative_path,
            tools=tools,
            success=True,
        )

    def _extract_from_markdown(
        self, file_path: Path, relative_path: str
    ) -> ExtractionResult:
        """Extract tools from markdown code blocks."""
        content = file_path.read_text(encoding="utf-8")

        # Extract Python code blocks
        code_blocks = re.findall(
            r"```(?:python|py)\n(.*?)```",
            content,
            re.DOTALL | re.IGNORECASE,
        )

        tools = []
        imports = set()

        for block in code_blocks:
            for line in block.split("\n"):
                if line.startswith("import ") or line.startswith("from "):
                    imports.add(line.strip())

        combined_code = "\n\n".join(code_blocks)
        extracted = self._extract_from_code(combined_code, relative_path, imports)
        tools.extend(extracted)

        return ExtractionResult(
            tutorial_path=relative_path,
            tools=tools,
            success=True,
        )

    def _extract_from_code(
        self, code: str, source_file: str, imports: set
    ) -> List[ExtractedTool]:
        """Extract tools from Python code string."""
        tools = []

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return tools

        # Determine dependencies from imports
        dependencies = []
        for imp in imports:
            for useful in self.USEFUL_IMPORTS:
                if useful in imp:
                    dependencies.append(useful)
                    break

        dependencies = list(set(dependencies))

        # Extract function definitions
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                tool = self._extract_function(node, source_file, dependencies, code)
                if tool:
                    tools.append(tool)

        return tools

    def _extract_function(
        self,
        node: ast.FunctionDef,
        source_file: str,
        dependencies: List[str],
        full_code: str,
    ) -> Optional[ExtractedTool]:
        """Extract a single function as a tool."""
        name = node.name

        # Skip internal/test functions
        if name.startswith("_") and not name.startswith("__"):
            return None
        for skip in self.SKIP_FUNCTIONS:
            if name.startswith(skip) or name == skip:
                return None

        # Get docstring
        docstring = ast.get_docstring(node) or ""

        # Require docstring if configured
        if self.require_docstring and not docstring:
            return None

        # Extract parameters
        parameters = self._extract_parameters(node, docstring)

        # Check minimum parameters
        if len(parameters) < self.min_params:
            return None

        # Get return type
        return_type = None
        if node.returns:
            return_type = ast.unparse(node.returns)

        # Extract source code for this function
        try:
            source_code = ast.get_source_segment(full_code, node) or ""
        except:
            # Fallback: reconstruct from AST
            source_code = f"def {name}(...):\n    {docstring[:100]}..."

        # Parse description from docstring
        description = self._parse_description(docstring) or f"Function {name}"

        # Calculate confidence based on quality signals
        confidence = self._calculate_confidence(
            docstring=docstring,
            parameters=parameters,
            has_return_type=return_type is not None,
            dependencies=dependencies,
        )

        return ExtractedTool(
            name=name,
            description=description,
            source_file=source_file,
            source_code=source_code,
            parameters=parameters,
            return_type=return_type,
            return_description=self._parse_returns(docstring),
            dependencies=dependencies,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            confidence=confidence,
        )

    def _extract_parameters(
        self, node: ast.FunctionDef, docstring: str
    ) -> List[Parameter]:
        """Extract parameters from function definition."""
        parameters = []
        args = node.args

        # Get defaults (aligned from the right)
        defaults = [None] * (len(args.args) - len(args.defaults)) + [
            ast.unparse(d) for d in args.defaults
        ]

        for i, arg in enumerate(args.args):
            if arg.arg in ("self", "cls"):
                continue

            type_hint = None
            if arg.annotation:
                type_hint = ast.unparse(arg.annotation)

            # Try to get description from docstring
            description = self._parse_param_description(docstring, arg.arg)

            parameters.append(Parameter(
                name=arg.arg,
                type_hint=type_hint,
                default=defaults[i] if i < len(defaults) else None,
                description=description,
            ))

        return parameters

    def _parse_description(self, docstring: str) -> str:
        """Parse function description from docstring."""
        if not docstring:
            return ""

        lines = docstring.strip().split("\n")
        description_lines = []

        for line in lines:
            line = line.strip()
            # Stop at section headers
            if line.lower().startswith(("args:", "parameters:", "returns:", "raises:", "example")):
                break
            if line:
                description_lines.append(line)

        return " ".join(description_lines)

    def _parse_param_description(self, docstring: str, param_name: str) -> str:
        """Parse parameter description from docstring."""
        if not docstring:
            return ""

        # Look for Google-style: param_name: description
        # or NumPy-style: param_name : type\n    description
        patterns = [
            rf"{param_name}\s*:\s*(.+?)(?:\n|$)",
            rf"{param_name}\s*\(.*?\)\s*:\s*(.+?)(?:\n|$)",
        ]

        for pattern in patterns:
            match = re.search(pattern, docstring, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return ""

    def _parse_returns(self, docstring: str) -> str:
        """Parse returns description from docstring."""
        if not docstring:
            return ""

        match = re.search(
            r"Returns?:\s*\n?\s*(.+?)(?:\n\n|Raises:|Example|$)",
            docstring,
            re.IGNORECASE | re.DOTALL,
        )

        if match:
            return match.group(1).strip().split("\n")[0]

        return ""

    def _calculate_confidence(
        self,
        docstring: str,
        parameters: List[Parameter],
        has_return_type: bool,
        dependencies: List[str],
    ) -> float:
        """Calculate confidence score for extracted tool."""
        score = 0.5  # Base score

        # Docstring quality
        if docstring:
            score += 0.1
            if len(docstring) > 100:
                score += 0.1

        # Parameter documentation
        documented_params = sum(1 for p in parameters if p.description)
        if parameters:
            score += 0.1 * (documented_params / len(parameters))

        # Type hints
        typed_params = sum(1 for p in parameters if p.type_hint)
        if parameters:
            score += 0.1 * (typed_params / len(parameters))

        if has_return_type:
            score += 0.1

        # Dependencies (useful libraries)
        if dependencies:
            score += 0.1

        return min(1.0, score)
