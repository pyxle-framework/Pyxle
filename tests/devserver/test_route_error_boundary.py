"""Tests for error boundary pages being separated from the regular route table."""

from __future__ import annotations

from pathlib import Path


from pyxle.devserver.registry import MetadataRegistry, PageRegistryEntry
from pyxle.devserver.routes import build_route_table


def _page_entry(
    relative_path: str,
    route_path: str,
    *,
    loader_name: str | None = None,
    actions: tuple[dict, ...] = (),
) -> PageRegistryEntry:
    """Create a minimal PageRegistryEntry for testing."""
    return PageRegistryEntry(
        route_path=route_path,
        alternate_route_paths=(),
        source_relative_path=Path(relative_path),
        source_absolute_path=Path("/project/pages") / relative_path,
        server_module_path=Path("/build/server/pages") / Path(relative_path).with_suffix(".py"),
        client_module_path=Path("/build/client") / Path(relative_path).with_suffix(".jsx"),
        metadata_path=Path("/build/metadata/pages") / Path(relative_path).with_suffix(".json"),
        client_asset_path=f"/{Path(relative_path).stem}.jsx",
        server_asset_path=f"pages/{Path(relative_path).stem}",
        module_key=f"pyxle.server.pages.{Path(relative_path).stem}",
        content_hash="abc123",
        loader_name=loader_name,
        loader_line=1 if loader_name else None,
        head_elements=(),
        head_is_dynamic=False,
        actions=actions,
    )


class TestRouteTableErrorBoundaryFiltering:
    def test_error_pyx_excluded_from_pages(self):
        registry = MetadataRegistry(
            pages=[
                _page_entry("index.pyx", "/"),
                _page_entry("error.pyx", "/error"),
            ],
            apis=[],
        )
        table = build_route_table(registry)

        page_paths = [p.path for p in table.pages]
        assert "/" in page_paths
        assert "/error" not in page_paths

    def test_not_found_pyx_excluded_from_pages(self):
        registry = MetadataRegistry(
            pages=[
                _page_entry("index.pyx", "/"),
                _page_entry("not-found.pyx", "/not-found"),
            ],
            apis=[],
        )
        table = build_route_table(registry)

        page_paths = [p.path for p in table.pages]
        assert "/" in page_paths
        assert "/not-found" not in page_paths

    def test_nested_error_pages_excluded(self):
        registry = MetadataRegistry(
            pages=[
                _page_entry("index.pyx", "/"),
                _page_entry("dashboard/index.pyx", "/dashboard"),
                _page_entry("dashboard/error.pyx", "/dashboard/error"),
                _page_entry("dashboard/not-found.pyx", "/dashboard/not-found"),
            ],
            apis=[],
        )
        table = build_route_table(registry)

        page_paths = [p.path for p in table.pages]
        assert "/" in page_paths
        assert "/dashboard" in page_paths
        assert "/dashboard/error" not in page_paths
        assert "/dashboard/not-found" not in page_paths

    def test_error_pages_appear_in_error_boundary_pages(self):
        registry = MetadataRegistry(
            pages=[
                _page_entry("index.pyx", "/"),
                _page_entry("error.pyx", "/error"),
                _page_entry("not-found.pyx", "/not-found"),
                _page_entry("dashboard/error.pyx", "/dashboard/error"),
            ],
            apis=[],
        )
        table = build_route_table(registry)

        boundary_sources = [
            p.source_relative_path.as_posix() for p in table.error_boundary_pages
        ]
        assert "error.pyx" in boundary_sources
        assert "not-found.pyx" in boundary_sources
        assert "dashboard/error.pyx" in boundary_sources

    def test_actions_from_error_pages_excluded(self):
        """@action functions in error.pyx should not be routed."""
        registry = MetadataRegistry(
            pages=[
                _page_entry("index.pyx", "/", actions=({"name": "submit"},)),
                _page_entry("error.pyx", "/error", actions=({"name": "report_error"},)),
            ],
            apis=[],
        )
        table = build_route_table(registry)

        action_paths = [a.path for a in table.actions]
        assert any("submit" in p for p in action_paths)
        assert not any("report_error" in p for p in action_paths)

    def test_empty_registry(self):
        registry = MetadataRegistry(pages=[], apis=[])
        table = build_route_table(registry)
        assert table.pages == []
        assert table.error_boundary_pages == []
        assert table.actions == []

    def test_route_table_find_methods_unaffected(self):
        """Existing find_page/find_api/find_action still work correctly."""
        registry = MetadataRegistry(
            pages=[
                _page_entry("index.pyx", "/"),
                _page_entry("error.pyx", "/error"),
            ],
            apis=[],
        )
        table = build_route_table(registry)

        assert table.find_page("/") is not None
        assert table.find_page("/error") is None  # filtered out
