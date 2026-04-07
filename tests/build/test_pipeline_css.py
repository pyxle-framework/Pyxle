"""Tests for CSS bundle propagation through the build pipeline.

These tests pin the contract that allows hashed CSS bundles to flow from
the Vite manifest into the SSR ``<link rel="stylesheet">`` tag without any
hand-bumped ``?v=N`` workaround:

1. The user imports a stylesheet from a JSX module (e.g.
   ``import './styles/tailwind.css';``).
2. Vite (with PostCSS) compiles the CSS and emits an entry like
   ``"pages/index.jsx": {"file": "...", "css": ["assets/index-abc123.css"]}``
   in ``manifest.json``.
3. ``_build_page_manifest`` reads the Vite manifest and writes the CSS
   asset paths into ``page-manifest.json`` under
   ``<route>.client.css``, prefixed with ``dist/``.
4. ``ssr/template.py`` reads ``page-manifest.json`` and emits
   ``<link rel="stylesheet" href="/client/dist/assets/index-abc123.css" />``
   on every render.

This file owns step 3. Step 1/2 is enforced by
``tests/compiler/test_compile.py::test_compile_passes_through_side_effect_css_imports``,
and step 4 is enforced by
``tests/ssr/test_template.py::test_render_document_uses_manifest_assets_in_production``.
"""

from __future__ import annotations

from pathlib import Path

from pyxle.build.pipeline import _build_page_manifest
from pyxle.devserver.registry import MetadataRegistry, PageRegistryEntry
from pyxle.devserver.settings import DevServerSettings


def _make_page(route_path: str, *, project: Path) -> PageRegistryEntry:
    """Build a minimal ``PageRegistryEntry`` for ``_build_page_manifest`` input."""

    return PageRegistryEntry(
        route_path=route_path,
        alternate_route_paths=(),
        source_relative_path=Path("pages/index.pyx"),
        source_absolute_path=project / "pages" / "index.pyx",
        server_module_path=project / ".pyxle-build" / "server" / "pages" / "index.py",
        client_module_path=project / ".pyxle-build" / "client" / "pages" / "index.jsx",
        metadata_path=project / ".pyxle-build" / "metadata" / "pages" / "index.json",
        client_asset_path="/pages/index.jsx",
        server_asset_path="server/pages/index.py",
        module_key="pyxle.server.pages.index",
        content_hash="hash123",
        loader_name=None,
        loader_line=None,
        head_elements=(),
        head_is_dynamic=False,
    )


def test_build_page_manifest_propagates_hashed_css_assets(tmp_path: Path) -> None:
    """A Vite manifest containing a ``css`` array under a page entry must
    flow into ``page-manifest.json`` as ``client.css`` with the ``dist/``
    prefix the static file middleware expects.
    """

    project = tmp_path / "project"
    project.mkdir()
    settings = DevServerSettings.from_project_root(project)

    registry = MetadataRegistry(pages=[_make_page("/", project=project)], apis=[])
    vite_manifest = {
        "pages/index.jsx": {
            "file": "assets/index-DEADBEEF.js",
            "css": [
                "assets/index-CAFEBABE.css",
                "assets/extra-1234.css",
            ],
        }
    }

    page_manifest = _build_page_manifest(
        settings, registry, vite_manifest=vite_manifest
    )

    assert page_manifest["/"]["client"]["file"] == "dist/assets/index-DEADBEEF.js"
    assert page_manifest["/"]["client"]["css"] == [
        "dist/assets/index-CAFEBABE.css",
        "dist/assets/extra-1234.css",
    ]


def test_build_page_manifest_defaults_css_to_empty_when_vite_omits(tmp_path: Path) -> None:
    """A page with no CSS in its Vite manifest entry should still produce a
    valid ``client.css`` field (empty list) so downstream consumers don't
    need to defensively check for ``None``.
    """

    project = tmp_path / "project"
    project.mkdir()
    settings = DevServerSettings.from_project_root(project)

    registry = MetadataRegistry(pages=[_make_page("/", project=project)], apis=[])
    vite_manifest = {
        "pages/index.jsx": {
            "file": "assets/index-DEADBEEF.js",
            # No "css" key on purpose.
        }
    }

    page_manifest = _build_page_manifest(
        settings, registry, vite_manifest=vite_manifest
    )

    assert page_manifest["/"]["client"]["css"] == []


def test_build_page_manifest_ignores_non_string_css_entries(tmp_path: Path) -> None:
    """Defensive: malformed Vite manifests with non-string CSS entries are
    filtered out rather than crashing the build.
    """

    project = tmp_path / "project"
    project.mkdir()
    settings = DevServerSettings.from_project_root(project)

    registry = MetadataRegistry(pages=[_make_page("/", project=project)], apis=[])
    vite_manifest = {
        "pages/index.jsx": {
            "file": "assets/index.js",
            "css": ["assets/good.css", 42, None, "assets/also-good.css"],
        }
    }

    page_manifest = _build_page_manifest(
        settings, registry, vite_manifest=vite_manifest
    )

    assert page_manifest["/"]["client"]["css"] == [
        "dist/assets/good.css",
        "dist/assets/also-good.css",
    ]


def test_build_page_manifest_handles_missing_vite_manifest(tmp_path: Path) -> None:
    """When no Vite manifest is supplied (e.g. dev mode without a build),
    ``client.css`` is an empty list and ``client.file`` falls back to the
    page's source-relative ``client_asset_path``.
    """

    project = tmp_path / "project"
    project.mkdir()
    settings = DevServerSettings.from_project_root(project)

    registry = MetadataRegistry(pages=[_make_page("/", project=project)], apis=[])

    page_manifest = _build_page_manifest(settings, registry, vite_manifest=None)

    assert page_manifest["/"]["client"]["file"] == "/pages/index.jsx"
    assert page_manifest["/"]["client"]["css"] == []


def test_build_page_manifest_propagates_css_to_aliased_routes(tmp_path: Path) -> None:
    """Pages with alternate route paths (e.g. catch-all routes) must share
    the same CSS asset list as the canonical route.
    """

    project = tmp_path / "project"
    project.mkdir()
    settings = DevServerSettings.from_project_root(project)

    page = PageRegistryEntry(
        route_path="/docs/{slug}",
        alternate_route_paths=("/docs", "/docs/"),
        source_relative_path=Path("pages/docs/[[...slug]].pyx"),
        source_absolute_path=project / "pages" / "docs" / "[[...slug]].pyx",
        server_module_path=project / ".pyxle-build" / "server" / "pages" / "docs.py",
        client_module_path=project / ".pyxle-build" / "client" / "pages" / "docs.jsx",
        metadata_path=project / ".pyxle-build" / "metadata" / "pages" / "docs.json",
        client_asset_path="/pages/docs/[[...slug]].jsx",
        server_asset_path="server/pages/docs.py",
        module_key="pyxle.server.pages.docs",
        content_hash="hash999",
        loader_name=None,
        loader_line=None,
        head_elements=(),
        head_is_dynamic=False,
    )
    registry = MetadataRegistry(pages=[page], apis=[])
    vite_manifest = {
        "pages/docs/[[...slug]].jsx": {
            "file": "assets/docs-FACE0FF.js",
            "css": ["assets/docs-FACE0FF.css"],
        }
    }

    page_manifest = _build_page_manifest(
        settings, registry, vite_manifest=vite_manifest
    )

    canonical_css = page_manifest["/docs/{slug}"]["client"]["css"]
    assert canonical_css == ["dist/assets/docs-FACE0FF.css"]
    # Alternate route paths must share the same entry, including CSS.
    assert page_manifest["/docs"]["client"]["css"] == canonical_css
    assert page_manifest["/docs/"]["client"]["css"] == canonical_css
