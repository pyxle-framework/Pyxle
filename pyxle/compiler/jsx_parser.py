"""JSX component extraction using Babel AST parsing."""

from __future__ import annotations

import json
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class JSXComponent:
    """Represents a JSX component usage found in code."""

    name: str  # Component name (e.g., "Script", "Image", "Head")
    props: dict[str, Any]  # Props/attributes
    children: str | None  # Text content for container components like <Head>
    self_closing: bool  # Whether it's self-closing
    line: int | None
    column: int | None


@dataclass(frozen=True)
class JSXParseResult:
    """Result of parsing JSX code."""

    components: tuple[JSXComponent, ...]
    error: str | None


def parse_jsx_components(jsx_code: str, *, target_components: set[str] | None = None) -> JSXParseResult:
    """
    Parse JSX code using Babel and extract specific component usages.

    Args:
        jsx_code: The JSX source code to parse
        target_components: Set of component names to extract (e.g., {"Script", "Image", "Head"}).
                          If None, extracts all components.

    Returns:
        JSXParseResult with extracted components or error information.
    """
    if not jsx_code.strip():
        return JSXParseResult(components=(), error=None)

    # Create temporary file for Node.js parser
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsx", delete=False, encoding="utf-8") as temp_file:
        temp_file.write(jsx_code)
        temp_file.flush()
        temp_path = temp_file.name

    try:
        result = _run_babel_parser(temp_path, target_components)
        return result
    finally:
        Path(temp_path).unlink(missing_ok=True)


def _run_babel_parser(source_path: str, target_components: set[str] | None) -> JSXParseResult:
    """Run the Node.js Babel parser script."""
    # Find the parser script in pyxle_langkit
    script_path = Path(__file__).parent.parent / "pyxle_langkit" / "js" / "jsx_component_extractor.mjs"

    if not script_path.exists():
        # Fallback: try relative to package root
        script_path = Path(__file__).parent.parent.parent / "pyxle_langkit" / "js" / "jsx_component_extractor.mjs"

    if not script_path.exists():
        # Fallback: try sibling repo (pyxle-langkit alongside pyxle in workspace)
        script_path = Path(__file__).resolve().parent.parent.parent.parent / "pyxle-langkit" / "pyxle_langkit" / "js" / "jsx_component_extractor.mjs"

    if not script_path.exists():
        return JSXParseResult(
            components=(),
            error="JSX parser script not found. Install pyxle[langkit] dependencies.",
        )

    # Prepare command
    components_arg = json.dumps(list(target_components)) if target_components else "null"
    command = ["node", str(script_path), source_path, components_arg]

    try:
        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except FileNotFoundError:
        return JSXParseResult(
            components=(),
            error="Node.js not found. Install Node.js >=18 to parse JSX components.",
        )
    except subprocess.TimeoutExpired:
        return JSXParseResult(components=(), error="JSX parser timed out.")

    # Parse JSON output
    try:
        payload = json.loads(proc.stdout.strip() or proc.stderr.strip() or "{}")
    except json.JSONDecodeError:
        return JSXParseResult(
            components=(),
            error=f"JSX parser produced invalid output: {proc.stdout[:200]}",
        )

    # Check for errors
    if not payload.get("ok", False):
        error_msg = payload.get("message", "Unknown JSX parsing error")
        return JSXParseResult(components=(), error=error_msg)

    # Convert payload to JSXComponent objects
    components = []
    for comp_data in payload.get("components", []):
        component = JSXComponent(
            name=comp_data.get("name", "unknown"),
            props=comp_data.get("props", {}),
            children=comp_data.get("children"),
            self_closing=comp_data.get("selfClosing", False),
            line=comp_data.get("line"),
            column=comp_data.get("column"),
        )
        components.append(component)

    return JSXParseResult(components=tuple(components), error=None)
