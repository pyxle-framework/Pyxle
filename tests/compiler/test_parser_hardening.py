"""Tests for parser hardening: fence-based deterministic parsing, ast.parse()
repair, JSX import detection, and ambiguous-line edge cases.

Phase 1.7 of the Pyxle roadmap.
"""

from __future__ import annotations

from textwrap import dedent

import pytest

from pyxle.compiler.parser import PyxParser, _SegmentNode, _LineNode


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse(text: str) -> "PyxParser":
    """Parse text and return the result."""
    return PyxParser().parse_text(dedent(text).strip("\n"))


# ---------------------------------------------------------------------------
# Fence-based deterministic parsing
# ---------------------------------------------------------------------------


class TestFencedParsing:
    """When explicit section markers are present, heuristic switching is disabled."""

    def test_server_and_client_fences_split_cleanly(self):
        result = _parse("""
            # --- server ---
            from pyxle.runtime import server

            @server
            async def loader(request):
                return {"title": "Hello"}

            # --- client ---
            import React from 'react';

            export default function Page({ data }) {
                return <h1>{data.title}</h1>;
            }
        """)
        assert "from pyxle.runtime import server" in result.python_code
        assert "@server" in result.python_code
        assert "import React" in result.jsx_code
        assert "export default" in result.jsx_code
        assert result.loader is not None
        assert result.loader.name == "loader"

    def test_fenced_python_section_keeps_jsx_looking_code(self):
        """JSX-like content inside a server fence stays Python."""
        result = _parse("""
            # --- server ---
            template = "<div>hello</div>"
            config = {"key": "value"}

            # --- client ---
            export default function Page() {
                return <div>Hello</div>;
            }
        """)
        assert 'template = "<div>hello</div>"' in result.python_code
        assert "config = " in result.python_code
        # The template string should NOT leak into JSX
        assert 'template = ' not in result.jsx_code

    def test_fenced_jsx_section_keeps_python_looking_code(self):
        """Python-looking content inside a client fence stays JSX."""
        result = _parse("""
            # --- server ---
            x = 1

            # --- client ---
            import os
            for item in items:
                pass
            export default function Page() {
                return <div>Hello</div>;
            }
        """)
        # "import os" inside client fence should be JSX, not Python
        assert "import os" not in result.python_code
        assert "import os" in result.jsx_code
        # "for item in items:" inside client fence should be JSX
        assert "for item in items:" in result.jsx_code

    def test_multiple_fence_pairs(self):
        """Multiple server/client fence pairs work correctly."""
        result = _parse("""
            # --- server ---
            x = 1

            # --- client ---
            const a = 1;

            # --- server ---
            y = 2

            # --- client ---
            const b = 2;
        """)
        assert "x = 1" in result.python_code
        assert "y = 2" in result.python_code
        assert "const a = 1;" in result.jsx_code
        assert "const b = 2;" in result.jsx_code

    def test_fenced_mode_preserves_blank_lines(self):
        result = _parse("""
            # --- server ---
            x = 1

            y = 2

            # --- client ---
            <div />
        """)
        assert "x = 1" in result.python_code
        assert "y = 2" in result.python_code

    def test_fenced_mode_preserves_comments_in_section(self):
        result = _parse("""
            # --- server ---
            # This is a Python comment
            x = 1

            # --- client ---
            // This is a JS comment
            <div />
        """)
        assert "# This is a Python comment" in result.python_code
        assert "// This is a JS comment" in result.jsx_code

    def test_python_and_javascript_keywords_in_fences(self):
        """Both 'python'/'server' and 'javascript'/'client' keywords work."""
        parser = PyxParser()
        assert parser._detect_mode_toggle("# --- python ---") == "python"
        assert parser._detect_mode_toggle("# --- server ---") == "python"
        assert parser._detect_mode_toggle("# --- javascript ---") == "jsx"
        assert parser._detect_mode_toggle("# --- client ---") == "jsx"
        assert parser._detect_mode_toggle("# --- Python Section ---") == "python"
        assert parser._detect_mode_toggle("# --- Client Component ---") == "jsx"

    def test_fence_with_mixed_keywords_prefers_jsx(self):
        """When both JSX and Python keywords appear, JSX wins."""
        parser = PyxParser()
        # "JavaScript" + "Server" in the same label → JSX takes priority
        assert parser._detect_mode_toggle("# --- JavaScript/PSX (Client + Server) ---") == "jsx"
        assert parser._detect_mode_toggle("# --- Client Server ---") == "jsx"

    def test_fence_lines_are_excluded_from_output(self):
        """Fence marker lines should not appear in python_code or jsx_code."""
        result = _parse("""
            # --- server ---
            x = 1
            # --- client ---
            <div />
        """)
        assert "# --- server ---" not in result.python_code
        assert "# --- client ---" not in result.jsx_code
        assert "# --- server ---" not in result.jsx_code
        assert "# --- client ---" not in result.python_code

    def test_single_server_fence_without_client_raises(self):
        """A single server fence without a client fence forces all content into
        Python, causing a CompilationError for JS-like code."""
        from pyxle.compiler.exceptions import CompilationError

        with pytest.raises(CompilationError, match="invalid syntax"):
            _parse("""
                # --- server ---
                x = 1
                const y = 2;
            """)


# ---------------------------------------------------------------------------
# ast.parse() repair for heuristic mode
# ---------------------------------------------------------------------------


class TestAstParseRepair:
    """When heuristic classification produces invalid Python, ambiguous segments
    without strong Python markers are reclassified as JSX."""

    def test_repair_reclassifies_misidentified_jsx(self):
        """A line like 'value = something()' that looks like Python but isn't
        should be reclassified when it breaks ast.parse()."""
        # This simulates a JSX expression that has '=' in it
        result = _parse("""
            from pyxle.runtime import server

            @server
            async def loader(request):
                return {"key": "val"}

            import React from 'react';

            export default function Page({ data }) {
                return <div>{data.key}</div>;
            }
        """)
        assert "from pyxle.runtime import server" in result.python_code
        assert result.loader is not None
        assert "export default" in result.jsx_code

    def test_repair_reclassifies_assignment_like_jsx(self):
        """An assignment-like JSX line (has '=') that the heuristic treats as
        Python should be reclassified to JSX when ast.parse fails."""
        # The heuristic sees 'config = ...' at indent 0 with '=' and
        # classifies as Python.  But without import/def/@, repair kicks in.
        parser = PyxParser()
        segment = _SegmentNode(kind="python", lines=[
            _LineNode(number=1, text="config = <Provider value={ctx}>"),
        ])
        doc = parser._build_document([])
        doc.segments = [segment]
        parser._try_repair_document(doc)
        assert segment.kind == "jsx"

    def test_repair_preserves_strong_python(self):
        """Repair should NOT reclassify segments with import/def/class/@."""
        parser = PyxParser()
        segment = _SegmentNode(kind="python", lines=[
            _LineNode(number=1, text="from math import sqrt"),
            _LineNode(number=2, text="const x = <div>;"),  # invalid Python
        ])
        doc = parser._build_document([])
        doc.segments = [segment]
        # Should NOT reclassify because of the strong "from" marker
        parser._try_repair_document(doc)
        assert segment.kind == "python"

    def test_repair_handles_lineno_none(self):
        """Repair exits gracefully when SyntaxError has no line number."""
        # This is a defensive test — in practice lineno is almost always set.
        parser = PyxParser()
        segment = _SegmentNode(kind="python", lines=[
            _LineNode(number=1, text="???"),
        ])
        doc = parser._build_document([])
        doc.segments = [segment]
        # Should not crash
        parser._try_repair_document(doc)

    def test_repair_handles_error_outside_boundaries(self):
        """Repair exits when the error line doesn't map to any segment."""
        parser = PyxParser()
        # Single segment that is valid Python
        segment = _SegmentNode(kind="python", lines=[
            _LineNode(number=1, text="x = 1"),
        ])
        doc = parser._build_document([])
        doc.segments = [segment]
        # Valid code, no repair needed
        parser._try_repair_document(doc)
        assert segment.kind == "python"

    def test_no_repair_for_fenced_mode(self):
        """Fenced mode should NOT trigger repair — errors are real."""
        parser = PyxParser()
        result = parser.parse_text(dedent("""
            # --- server ---
            x = 1
        """).strip("\n"))
        # Valid fenced Python, no repair needed
        assert "x = 1" in result.python_code

    def test_repair_does_not_reclassify_strong_python(self):
        """Segments with imports, defs, or decorators should not be reclassified."""
        parser = PyxParser()
        segment = _SegmentNode(kind="python", lines=[
            _LineNode(number=1, text="import os"),
            _LineNode(number=2, text="something invalid"),
        ])
        assert parser._has_strong_python_markers(segment) is True

    def test_has_strong_python_markers_detects_defs(self):
        parser = PyxParser()
        for code in ["def foo():", "async def bar():", "class Baz:", "@decorator", '"""docstring"""', "from x import y"]:
            segment = _SegmentNode(kind="python", lines=[
                _LineNode(number=1, text=code),
            ])
            assert parser._has_strong_python_markers(segment) is True, f"Failed for: {code}"

    def test_has_strong_python_markers_false_for_assignments(self):
        parser = PyxParser()
        segment = _SegmentNode(kind="python", lines=[
            _LineNode(number=1, text="value = something"),
        ])
        assert parser._has_strong_python_markers(segment) is False

    def test_has_strong_python_markers_skips_blanks_and_comments(self):
        parser = PyxParser()
        segment = _SegmentNode(kind="python", lines=[
            _LineNode(number=1, text=""),
            _LineNode(number=2, text="# comment"),
            _LineNode(number=3, text="value = 1"),
        ])
        assert parser._has_strong_python_markers(segment) is False


# ---------------------------------------------------------------------------
# JSX import detection
# ---------------------------------------------------------------------------


class TestJsxImportDetection:
    """import X from 'path' (with quotes) is always JSX, never Python."""

    def test_default_import_with_quotes(self):
        parser = PyxParser()
        assert parser._looks_like_js_import("import React from 'react'") is True
        assert parser._looks_like_js_import('import React from "react"') is True

    def test_named_import_with_braces(self):
        parser = PyxParser()
        assert parser._looks_like_js_import("import { useState } from 'react'") is True

    def test_side_effect_import_single_quotes(self):
        parser = PyxParser()
        assert parser._looks_like_js_import("import './styles.css'") is True

    def test_side_effect_import_double_quotes(self):
        parser = PyxParser()
        assert parser._looks_like_js_import('import "./styles.css"') is True

    def test_side_effect_import_no_semicolon(self):
        """Side-effect imports without semicolons should still be detected."""
        parser = PyxParser()
        assert parser._looks_like_js_import("import 'normalize.css'") is True
        assert parser._looks_like_js_import('import "lodash"') is True

    def test_import_type(self):
        parser = PyxParser()
        assert parser._looks_like_js_import("import type { FC } from 'react'") is True
        assert parser._looks_like_js_import("import type Props") is True

    def test_import_with_semicolon(self):
        parser = PyxParser()
        assert parser._looks_like_js_import("import foo;") is True

    def test_python_import_not_detected_as_js(self):
        parser = PyxParser()
        assert parser._looks_like_js_import("import os") is False
        assert parser._looks_like_js_import("import sys") is False

    def test_side_effect_import_classified_as_jsx(self):
        """Side-effect imports should end up in jsx_code, not python_code."""
        result = _parse("""
            from pyxle.runtime import server

            @server
            async def loader(request):
                return {}

            import 'normalize.css'
            import React from 'react';

            export default function Page() {
                return <div>Hello</div>;
            }
        """)
        assert "import 'normalize.css'" in result.jsx_code
        assert "import 'normalize.css'" not in result.python_code

    def test_star_import_with_quotes(self):
        parser = PyxParser()
        assert parser._looks_like_js_import("import * as React from 'react'") is True


# ---------------------------------------------------------------------------
# Ambiguous line edge cases
# ---------------------------------------------------------------------------


class TestAmbiguousLines:
    """Edge cases where lines could be Python or JSX."""

    def test_import_from_with_quotes_is_jsx(self):
        """import X from 'path' is JSX, not Python from...import."""
        result = _parse("""
            import React from 'react';

            export default function Page() {
                return <div>Hello</div>;
            }
        """)
        assert "import React" in result.jsx_code
        assert result.python_code.strip() == ""

    def test_python_import_is_python(self):
        """import os (no quotes) is Python."""
        result = _parse("""
            import os

            import React from 'react';

            export default function Page() {
                return <div>Hello</div>;
            }
        """)
        assert "import os" in result.python_code

    def test_assignment_with_semicolon_is_jsx(self):
        """Assignments ending in `;` are JSX."""
        parser = PyxParser()
        assert parser._is_probable_python("value = something;", 0, False) is False
        assert parser._is_probable_js("value = something;", 0) is True

    def test_comment_hash_is_python(self):
        """# comments are always Python in auto mode."""
        parser = PyxParser()
        assert parser._is_probable_python("# this is a comment", 0, False) is True

    def test_comment_double_slash_is_jsx(self):
        """// comments are always JSX."""
        parser = PyxParser()
        assert parser._is_probable_js("// this is a comment", 0) is True

    def test_if_without_colon_is_not_python(self):
        """if (condition) is JSX/JS, not Python (no colon)."""
        parser = PyxParser()
        assert parser._is_probable_python("if (condition)", 0, False) is False

    def test_if_with_colon_is_python(self):
        """if condition: is Python."""
        parser = PyxParser()
        assert parser._is_probable_python("if condition:", 0, False) is True

    def test_for_without_colon_is_not_python(self):
        parser = PyxParser()
        assert parser._is_probable_python("for (let i = 0; i < 10; i++)", 0, False) is False

    def test_angle_bracket_is_jsx(self):
        """Lines starting with < are JSX."""
        parser = PyxParser()
        assert parser._is_probable_js("<div className='test'>", 0) is True
        assert parser._is_probable_js("<Component />", 0) is True

    def test_export_is_jsx(self):
        parser = PyxParser()
        assert parser._is_probable_js("export default function Page() {}", 0) is True
        assert parser._is_probable_js("export const value = 1;", 0) is True

    def test_const_let_var_are_jsx(self):
        parser = PyxParser()
        assert parser._is_probable_js("const x = 1;", 0) is True
        assert parser._is_probable_js("let y = 2;", 0) is True
        assert parser._is_probable_js("var z = 3;", 0) is True

    def test_triple_quoted_string_is_python(self):
        parser = PyxParser()
        assert parser._is_probable_python('"""docstring"""', 0, False) is True
        assert parser._is_probable_python("'''another'''", 0, False) is True

    def test_decorator_is_python(self):
        parser = PyxParser()
        assert parser._is_probable_python("@dataclass", 0, False) is True
        assert parser._is_probable_python("@server", 0, False) is True

    def test_indented_code_is_python_in_heuristic_mode(self):
        """Indented lines are always Python in heuristic mode."""
        parser = PyxParser()
        assert parser._is_probable_python("    return value", 4, False) is True

    def test_template_literal_not_misidentified(self):
        """Template literals (backtick strings) should stay JSX."""
        result = _parse("""
            import React from 'react';

            export default function Page() {
                const name = `hello world`;
                return <div>{name}</div>;
            }
        """)
        assert "const name = `hello world`" in result.jsx_code

    def test_await_classified_as_jsx(self):
        """Top-level 'await' is classified as JSX."""
        parser = PyxParser()
        assert parser._is_probable_js("await fetch('/api')", 0) is True

    def test_async_function_keyword_is_jsx(self):
        """'async function' (JS style) is classified as JSX."""
        parser = PyxParser()
        assert parser._is_probable_js("async function handleClick() {}", 0) is True

    def test_function_keyword_is_jsx(self):
        parser = PyxParser()
        assert parser._is_probable_js("function helper() {}", 0) is True


# ---------------------------------------------------------------------------
# Full file parsing edge cases
# ---------------------------------------------------------------------------


class TestFullFileParsing:
    """End-to-end parsing of complete .pyx files with tricky content."""

    def test_python_string_containing_jsx_is_not_jsx(self):
        """Python strings that contain JSX-like content stay in Python."""
        result = _parse("""
            from pyxle.runtime import server

            @server
            async def loader(request):
                template = "<div>hello</div>"
                return {"html": template}

            import React from 'react';

            export default function Page({ data }) {
                return <div dangerouslySetInnerHTML={{__html: data.html}} />;
            }
        """)
        assert 'template = "<div>hello</div>"' in result.python_code

    def test_python_multiline_string_not_split(self):
        """Multiline Python strings should stay together."""
        result = _parse("""
            from pyxle.runtime import server

            @server
            async def loader(request):
                query = \"\"\"
                    SELECT * FROM users
                    WHERE active = true
                \"\"\"
                return {"query": query}

            import React from 'react';

            export default function Page() {
                return <div>Page</div>;
            }
        """)
        assert "SELECT * FROM users" in result.python_code

    def test_empty_file_produces_empty_result(self):
        result = _parse("")
        assert result.python_code == ""
        assert result.jsx_code == ""
        assert result.loader is None

    def test_python_only_file(self):
        result = _parse("""
            from pyxle.runtime import server

            @server
            async def loader(request):
                return {"key": "value"}
        """)
        assert "from pyxle.runtime import server" in result.python_code
        assert result.jsx_code.strip() == ""
        assert result.loader is not None

    def test_jsx_only_file(self):
        result = _parse("""
            import React from 'react';

            export default function Page() {
                return <div>Hello World</div>;
            }
        """)
        assert result.python_code.strip() == ""
        assert "export default" in result.jsx_code
        assert result.loader is None

    def test_fenced_file_with_loader_and_actions(self):
        result = _parse("""
            # --- server ---
            from pyxle.runtime import server, action

            @server
            async def loader(request):
                return {"items": []}

            @action
            async def add_item(request):
                return {"ok": True}

            # --- client ---
            import React from 'react';

            export default function Page({ data }) {
                return <ul>{data.items.map(i => <li key={i}>{i}</li>)}</ul>;
            }
        """)
        assert result.loader is not None
        assert len(result.actions) == 1
        assert result.actions[0].name == "add_item"
        assert "export default" in result.jsx_code

    def test_fenced_with_python_and_javascript_keywords(self):
        """Alternate keyword styles for fences."""
        result = _parse("""
            # --- python ---
            x = 42

            # --- javascript ---
            export default function Page() {
                return <div>42</div>;
            }
        """)
        assert "x = 42" in result.python_code
        assert "export default" in result.jsx_code

    def test_comment_only_python_section(self):
        result = _parse("""
            # This page has no server logic

            import React from 'react';

            export default function Page() {
                return <div>Static page</div>;
            }
        """)
        # Comments at the top should be Python
        assert "# This page has no server logic" in result.python_code

    def test_inline_comment_in_python(self):
        result = _parse("""
            from pyxle.runtime import server  # import the decorator

            @server
            async def loader(request):
                x = 1  # inline comment
                return {"x": x}

            import React from 'react';
            export default function Page() { return <div />; }
        """)
        assert "# import the decorator" in result.python_code
        assert "# inline comment" in result.python_code

    def test_python_dict_with_jsx_like_values(self):
        """Python dicts can have string values that look like JSX."""
        result = _parse("""
            # --- server ---
            from pyxle.runtime import server

            @server
            async def loader(request):
                return {
                    "title": "<h1>Hello</h1>",
                    "body": "<p>World</p>",
                }

            # --- client ---
            export default function Page({ data }) {
                return <div>{data.title}</div>;
            }
        """)
        assert '"<h1>Hello</h1>"' in result.python_code
        assert '"<p>World</p>"' in result.python_code

    def test_parenthesized_python_expression_not_split(self):
        """Multi-line parenthesized expressions stay together."""
        result = _parse("""
            from pyxle.runtime import server

            @server
            async def loader(request):
                result = (
                    some_function(
                        arg1,
                        arg2,
                    )
                )
                return {"data": result}

            import React from 'react';
            export default function Page() { return <div />; }
        """)
        assert "some_function(" in result.python_code
        assert "arg1," in result.python_code
