"""Tests for action-related import helpers in writers.py."""

from __future__ import annotations

from textwrap import dedent

from pyxle.compiler.writers import (
    ensure_action_import,
    ensure_server_action_import,
)


class TestEnsureActionImport:
    def test_adds_import_when_missing(self) -> None:
        source = "async def save(request):\n    pass\n"
        result = ensure_action_import(source)
        assert "from pyxle.runtime import action" in result

    def test_no_duplicate_when_already_present(self) -> None:
        source = "from pyxle.runtime import action\nasync def save(request):\n    pass\n"
        result = ensure_action_import(source)
        assert result.count("from pyxle.runtime import action") == 1

    def test_empty_source_unchanged(self) -> None:
        result = ensure_action_import("")
        assert result == ""

    def test_preserves_trailing_newline(self) -> None:
        source = "async def save(request):\n    pass\n"
        result = ensure_action_import(source)
        assert result.endswith("\n")

    def test_no_trailing_newline_preserved(self) -> None:
        source = "async def save(request):\n    pass"
        result = ensure_action_import(source)
        assert not result.endswith("\n")

    def test_no_import_when_action_defined_locally(self) -> None:
        source = "def action(fn):\n    return fn\nasync def save(request):\n    pass\n"
        result = ensure_action_import(source)
        assert result.count("import action") == 0

    def test_no_import_when_action_assigned(self) -> None:
        source = "action = lambda fn: fn\nasync def save(request):\n    pass\n"
        result = ensure_action_import(source)
        assert result.count("import action") == 0

    def test_no_import_when_action_annotated_assigned(self) -> None:
        source = "action: object = lambda fn: fn\nasync def save(request):\n    pass\n"
        result = ensure_action_import(source)
        assert result.count("import action") == 0

    def test_no_import_when_action_bare_imported(self) -> None:
        source = "import action\nasync def save(request):\n    pass\n"
        result = ensure_action_import(source)
        assert result.count("import action") == 1  # the bare import, not a new one

    def test_adds_import_when_different_module_imported(self) -> None:
        """import os should not satisfy the action import requirement."""
        source = "import os\nasync def save(request):\n    pass\n"
        result = ensure_action_import(source)
        assert "from pyxle.runtime import action" in result

    def test_adds_import_with_tuple_assignment_target(self) -> None:
        """Tuple unpacking assignment should not suppress the action import."""
        source = "x, y = 1, 2\nasync def save(request):\n    pass\n"
        result = ensure_action_import(source)
        assert "from pyxle.runtime import action" in result

    def test_adds_import_after_docstring_only_module(self) -> None:
        """Module with only a docstring should get the import inserted after it."""
        source = '"""Module docstring."""\nasync def save(request):\n    pass\n'
        result = ensure_action_import(source)
        assert "from pyxle.runtime import action" in result


class TestEnsureServerActionImport:
    def test_combined_import_when_both_missing(self) -> None:
        source = dedent(
            """
            @server
            async def load(request):
                return {}

            @action
            async def save(request):
                pass
            """
        ).strip() + "\n"
        result = ensure_server_action_import(source)
        assert "from pyxle.runtime import server, action" in result

    def test_only_server_when_action_present(self) -> None:
        source = dedent(
            """
            from pyxle.runtime import action

            @server
            async def load(request):
                return {}
            """
        ).strip() + "\n"
        result = ensure_server_action_import(source)
        assert "from pyxle.runtime import server" in result
        # Should not add combined import
        assert result.count("from pyxle.runtime import server, action") == 0

    def test_only_action_when_server_present(self) -> None:
        source = dedent(
            """
            from pyxle.runtime import server

            @action
            async def save(request):
                pass
            """
        ).strip() + "\n"
        result = ensure_server_action_import(source)
        assert "from pyxle.runtime import action" in result

    def test_no_change_when_both_present(self) -> None:
        source = dedent(
            """
            from pyxle.runtime import server, action

            @server
            async def load(request):
                return {}

            @action
            async def save(request):
                pass
            """
        ).strip() + "\n"
        result = ensure_server_action_import(source)
        assert result == source

    def test_empty_source_unchanged(self) -> None:
        result = ensure_server_action_import("")
        assert result == ""

    def test_no_trailing_newline_preserved(self) -> None:
        source = "async def save(request):\n    pass"
        result = ensure_server_action_import(source)
        assert not result.endswith("\n")
