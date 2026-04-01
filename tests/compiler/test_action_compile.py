"""Integration tests for ArtifactWriter with @action pages."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from pyxle.compiler.parser import PyxParser
from pyxle.compiler.writers import ArtifactWriter


def _make_writer(tmp_path: Path) -> ArtifactWriter:
    build_root = tmp_path / ".pyxle-build"
    return ArtifactWriter(
        build_root=build_root,
        client_root=build_root / "client",
        server_root=build_root / "server",
        metadata_root=build_root / "metadata",
    )


def test_writer_action_only_page(tmp_path: Path) -> None:
    """Page with @action (no @server loader) gets ensure_action_import."""
    source = tmp_path / "pages" / "form.pyx"
    source.parent.mkdir(parents=True)
    source.write_text(
        dedent(
            """
            from pyxle.runtime import action

            @action
            async def submit(request):
                return {"ok": True}

            import React from 'react';
            export default function Page() { return <form/>; }
            """
        ).strip() + "\n",
        encoding="utf-8",
    )

    writer = _make_writer(tmp_path)
    parse_result = PyxParser().parse(source)
    result = writer.write(
        source_path=source,
        page_relative_path=Path("form.pyx"),
        route_path="/form",
        alternate_route_paths=None,
        parse_result=parse_result,
    )

    server_code = result.server_output.read_text()
    # action import should be present
    assert "from pyxle.runtime import action" in server_code
    # metadata should list the action
    assert len(result.metadata.actions) == 1
    assert result.metadata.actions[0].name == "submit"


def test_writer_loader_and_action_page(tmp_path: Path) -> None:
    """Page with both @server and @action gets the combined import."""
    source = tmp_path / "pages" / "settings.pyx"
    source.parent.mkdir(parents=True)
    source.write_text(
        dedent(
            """
            @server
            async def load(request):
                return {}

            @action
            async def save(request):
                return {"saved": True}

            import React from 'react';
            export default function Page() { return <div/>; }
            """
        ).strip() + "\n",
        encoding="utf-8",
    )

    writer = _make_writer(tmp_path)
    parse_result = PyxParser().parse(source)
    result = writer.write(
        source_path=source,
        page_relative_path=Path("settings.pyx"),
        route_path="/settings",
        alternate_route_paths=None,
        parse_result=parse_result,
    )

    server_code = result.server_output.read_text()
    # Both imports should be satisfied
    assert "server" in server_code
    assert "action" in server_code
    assert len(result.metadata.actions) == 1
    assert result.metadata.actions[0].name == "save"
    assert result.metadata.loader_name == "load"


def test_writer_multiple_actions_in_metadata_json(tmp_path: Path) -> None:
    source = tmp_path / "pages" / "multi.pyx"
    source.parent.mkdir(parents=True)
    source.write_text(
        dedent(
            """
            from pyxle.runtime import action

            @action
            async def create(request):
                return {}

            @action
            async def remove(request):
                return {}

            import React from 'react';
            export default function Page() { return <div/>; }
            """
        ).strip() + "\n",
        encoding="utf-8",
    )

    import json

    writer = _make_writer(tmp_path)
    parse_result = PyxParser().parse(source)
    result = writer.write(
        source_path=source,
        page_relative_path=Path("multi.pyx"),
        route_path="/multi",
        alternate_route_paths=None,
        parse_result=parse_result,
    )

    metadata_json = json.loads(result.metadata_output.read_text())
    assert len(metadata_json["actions"]) == 2
    names = [a["name"] for a in metadata_json["actions"]]
    assert "create" in names
    assert "remove" in names
