"""Tests for @action detection in the .pyx parser."""

from __future__ import annotations

from textwrap import dedent

import pytest

from pyxle.compiler.exceptions import CompilationError
from pyxle.compiler.parser import ActionDetails, PyxParser


def parse(text: str) -> object:
    return PyxParser().parse_text(dedent(text).strip())


# ---------------------------------------------------------------------------
# Happy-path detection
# ---------------------------------------------------------------------------


def test_detects_single_action() -> None:
    result = parse(
        """
        from pyxle.runtime import action

        @action
        async def save_name(request):
            pass

        import React from 'react';
        export default function Page() { return <div/>; }
        """
    )
    assert len(result.actions) == 1
    a = result.actions[0]
    assert isinstance(a, ActionDetails)
    assert a.name == "save_name"
    assert a.is_async is True
    assert list(a.parameters) == ["request"]


def test_detects_multiple_actions() -> None:
    result = parse(
        """
        from pyxle.runtime import action

        @action
        async def create(request):
            pass

        @action
        async def delete_item(request):
            pass

        import React from 'react';
        export default function Page() { return <div/>; }
        """
    )
    names = [a.name for a in result.actions]
    assert names == ["create", "delete_item"]


def test_action_with_extra_params() -> None:
    result = parse(
        """
        from pyxle.runtime import action

        @action
        async def update(request, extra=None):
            pass

        import React from 'react';
        export default function Page() { return <div/>; }
        """
    )
    assert result.actions[0].name == "update"
    assert "request" in result.actions[0].parameters


def test_action_qualified_decorator() -> None:
    """@runtime.action should also be detected."""
    result = parse(
        """
        import pyxle.runtime as runtime

        @runtime.action
        async def do_thing(request):
            pass

        import React from 'react';
        export default function Page() { return <div/>; }
        """
    )
    assert len(result.actions) == 1
    assert result.actions[0].name == "do_thing"


def test_no_actions_gives_empty_tuple() -> None:
    result = parse(
        """
        import React from 'react';
        export default function Page() { return <div/>; }
        """
    )
    assert result.actions == ()


def test_action_and_loader_coexist() -> None:
    result = parse(
        """
        from pyxle.runtime import server, action

        @server
        async def load(request):
            return {}

        @action
        async def save(request):
            pass

        import React from 'react';
        export default function Page() { return <div/>; }
        """
    )
    assert result.loader is not None
    assert result.loader.name == "load"
    assert len(result.actions) == 1
    assert result.actions[0].name == "save"


def test_action_line_number_mapped() -> None:
    result = parse(
        """
        from pyxle.runtime import action

        @action
        async def save(request):
            pass

        import React from 'react';
        export default function Page() { return <div/>; }
        """
    )
    assert result.actions[0].line_number is not None
    assert isinstance(result.actions[0].line_number, int)


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------


def test_action_sync_raises() -> None:
    with pytest.raises(CompilationError, match="must be declared as async"):
        parse(
            """
            from pyxle.runtime import action

            @action
            def save(request):
                pass

            import React from 'react';
            export default function Page() { return <div/>; }
            """
        )


def test_action_on_class_raises() -> None:
    with pytest.raises(CompilationError, match="can only be applied to functions"):
        parse(
            """
            from pyxle.runtime import action

            @action
            class MyAction:
                pass

            import React from 'react';
            export default function Page() { return <div/>; }
            """
        )


def test_action_and_server_on_same_function_raises() -> None:
    with pytest.raises(CompilationError, match="@action and @server cannot both"):
        parse(
            """
            from pyxle.runtime import server, action

            @server
            @action
            async def load(request):
                pass

            import React from 'react';
            export default function Page() { return <div/>; }
            """
        )


def test_action_missing_request_raises() -> None:
    with pytest.raises(CompilationError, match="must accept a `request` argument"):
        parse(
            """
            from pyxle.runtime import action

            @action
            async def save():
                pass

            import React from 'react';
            export default function Page() { return <div/>; }
            """
        )


def test_action_wrong_first_arg_raises() -> None:
    with pytest.raises(CompilationError, match="must be named 'request'"):
        parse(
            """
            from pyxle.runtime import action

            @action
            async def save(req):
                pass

            import React from 'react';
            export default function Page() { return <div/>; }
            """
        )


def test_duplicate_action_names_raises() -> None:
    with pytest.raises(CompilationError, match="Duplicate @action name"):
        parse(
            """
            from pyxle.runtime import action

            @action
            async def save(request):
                pass

            @action
            async def save(request):
                pass

            import React from 'react';
            export default function Page() { return <div/>; }
            """
        )


def test_nested_action_raises() -> None:
    with pytest.raises(CompilationError, match="module scope"):
        parse(
            """
            from pyxle.runtime import action

            class Wrapper:
                @action
                async def save(request):
                    pass

            import React from 'react';
            export default function Page() { return <div/>; }
            """
        )
