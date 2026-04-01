"""Tests for pyxle.devserver.error_pages — error boundary resolution."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from pyxle.devserver.error_pages import (
    ErrorBoundaryRegistry,
    build_error_boundary_registry,
    is_error_boundary_file,
    is_error_page,
    is_not_found_page,
)


# ---------------------------------------------------------------------------
# Filename classification helpers
# ---------------------------------------------------------------------------


class TestFilenameClassification:
    @pytest.mark.parametrize(
        "path,expected",
        [
            ("error.pyx", True),
            ("not-found.pyx", True),
            ("dashboard/error.pyx", True),
            ("dashboard/not-found.pyx", True),
            ("deep/nested/dir/error.pyx", True),
            ("index.pyx", False),
            ("about.pyx", False),
            ("error.py", False),
            ("error.tsx", False),
            ("my-error.pyx", False),
            ("errors.pyx", False),
        ],
    )
    def test_is_error_boundary_file(self, path: str, expected: bool):
        assert is_error_boundary_file(path) == expected

    @pytest.mark.parametrize(
        "path,expected",
        [
            ("error.pyx", True),
            ("dashboard/error.pyx", True),
            ("not-found.pyx", False),
            ("index.pyx", False),
        ],
    )
    def test_is_error_page(self, path: str, expected: bool):
        assert is_error_page(path) == expected

    @pytest.mark.parametrize(
        "path,expected",
        [
            ("not-found.pyx", True),
            ("dashboard/not-found.pyx", True),
            ("error.pyx", False),
            ("index.pyx", False),
        ],
    )
    def test_is_not_found_page(self, path: str, expected: bool):
        assert is_not_found_page(path) == expected

    def test_case_insensitive(self):
        assert is_error_boundary_file("Error.pyx")
        assert is_error_boundary_file("NOT-FOUND.pyx")
        assert is_error_boundary_file("ERROR.PYX")


# ---------------------------------------------------------------------------
# Stub page route
# ---------------------------------------------------------------------------


def _stub_page(relative_path: str, path: str = "/") -> MagicMock:
    """Create a minimal mock PageRoute for testing the registry."""
    mock = MagicMock()
    mock.source_relative_path = Path(relative_path)
    mock.path = path
    return mock


# ---------------------------------------------------------------------------
# build_error_boundary_registry
# ---------------------------------------------------------------------------


class TestBuildErrorBoundaryRegistry:
    def test_empty_input(self):
        registry = build_error_boundary_registry([])
        assert registry.error_pages == {}
        assert registry.not_found_pages == {}

    def test_root_error_page(self):
        page = _stub_page("error.pyx", "/error")
        registry = build_error_boundary_registry([page])
        assert "." in registry.error_pages
        assert registry.error_pages["."] is page

    def test_root_not_found_page(self):
        page = _stub_page("not-found.pyx", "/not-found")
        registry = build_error_boundary_registry([page])
        assert "." in registry.not_found_pages
        assert registry.not_found_pages["."] is page

    def test_nested_error_page(self):
        page = _stub_page("dashboard/error.pyx", "/dashboard/error")
        registry = build_error_boundary_registry([page])
        assert "dashboard" in registry.error_pages

    def test_deeply_nested(self):
        page = _stub_page("dashboard/settings/error.pyx", "/dashboard/settings/error")
        registry = build_error_boundary_registry([page])
        assert "dashboard/settings" in registry.error_pages

    def test_multiple_boundaries(self):
        root_error = _stub_page("error.pyx", "/error")
        dash_error = _stub_page("dashboard/error.pyx", "/dashboard/error")
        root_nf = _stub_page("not-found.pyx", "/not-found")
        registry = build_error_boundary_registry([root_error, dash_error, root_nf])
        assert len(registry.error_pages) == 2
        assert len(registry.not_found_pages) == 1

    def test_non_boundary_pages_are_ignored(self):
        index = _stub_page("index.pyx", "/")
        about = _stub_page("about.pyx", "/about")
        registry = build_error_boundary_registry([index, about])
        assert not registry.has_error_pages
        assert not registry.has_not_found_pages

    def test_has_error_pages_property(self):
        page = _stub_page("error.pyx", "/error")
        registry = build_error_boundary_registry([page])
        assert registry.has_error_pages
        assert not registry.has_not_found_pages

    def test_has_not_found_pages_property(self):
        page = _stub_page("not-found.pyx", "/not-found")
        registry = build_error_boundary_registry([page])
        assert not registry.has_error_pages
        assert registry.has_not_found_pages


# ---------------------------------------------------------------------------
# Error boundary walk-up resolution
# ---------------------------------------------------------------------------


class TestFindErrorBoundary:
    def _registry(self) -> ErrorBoundaryRegistry:
        """Registry with root + dashboard error pages, root not-found."""
        return ErrorBoundaryRegistry(
            error_pages={
                ".": _stub_page("error.pyx", "/error"),
                "dashboard": _stub_page("dashboard/error.pyx", "/dashboard/error"),
                "dashboard/settings": _stub_page(
                    "dashboard/settings/error.pyx",
                    "/dashboard/settings/error",
                ),
            },
            not_found_pages={
                ".": _stub_page("not-found.pyx", "/not-found"),
                "dashboard": _stub_page("dashboard/not-found.pyx", "/dashboard/not-found"),
            },
        )

    # --- Error boundary tests ---

    def test_root_route_finds_root_error(self):
        reg = self._registry()
        result = reg.find_error_boundary("/")
        assert result is not None
        assert result.source_relative_path == Path("error.pyx")

    def test_dashboard_route_finds_dashboard_error(self):
        reg = self._registry()
        result = reg.find_error_boundary("/dashboard")
        assert result is not None
        assert result.source_relative_path == Path("dashboard/error.pyx")

    def test_dashboard_child_finds_dashboard_error(self):
        reg = self._registry()
        result = reg.find_error_boundary("/dashboard/users")
        assert result is not None
        assert result.source_relative_path == Path("dashboard/error.pyx")

    def test_dashboard_settings_finds_settings_error(self):
        reg = self._registry()
        result = reg.find_error_boundary("/dashboard/settings")
        assert result is not None
        assert result.source_relative_path == Path("dashboard/settings/error.pyx")

    def test_dashboard_settings_child_finds_settings_error(self):
        reg = self._registry()
        result = reg.find_error_boundary("/dashboard/settings/profile")
        assert result is not None
        assert result.source_relative_path == Path("dashboard/settings/error.pyx")

    def test_unrelated_route_falls_back_to_root(self):
        reg = self._registry()
        result = reg.find_error_boundary("/about")
        assert result is not None
        assert result.source_relative_path == Path("error.pyx")

    def test_no_boundary_returns_none(self):
        empty = ErrorBoundaryRegistry(error_pages={}, not_found_pages={})
        assert empty.find_error_boundary("/anything") is None

    # --- Not-found boundary tests ---

    def test_root_route_finds_root_not_found(self):
        reg = self._registry()
        result = reg.find_not_found_boundary("/")
        assert result is not None
        assert result.source_relative_path == Path("not-found.pyx")

    def test_dashboard_route_finds_dashboard_not_found(self):
        reg = self._registry()
        result = reg.find_not_found_boundary("/dashboard/unknown")
        assert result is not None
        assert result.source_relative_path == Path("dashboard/not-found.pyx")

    def test_unrelated_route_finds_root_not_found(self):
        reg = self._registry()
        result = reg.find_not_found_boundary("/blog/missing")
        assert result is not None
        assert result.source_relative_path == Path("not-found.pyx")

    def test_no_not_found_returns_none(self):
        empty = ErrorBoundaryRegistry(error_pages={}, not_found_pages={})
        assert empty.find_not_found_boundary("/anything") is None

    # --- Edge cases ---

    def test_trailing_slash_normalised(self):
        reg = self._registry()
        result = reg.find_error_boundary("/dashboard/")
        assert result is not None
        assert result.source_relative_path == Path("dashboard/error.pyx")

    def test_empty_path_treated_as_root(self):
        reg = self._registry()
        result = reg.find_error_boundary("")
        assert result is not None
        assert result.source_relative_path == Path("error.pyx")

    def test_only_deepest_match_wins(self):
        """When multiple error boundaries exist, the closest one wins."""
        reg = self._registry()
        # /dashboard/settings/profile -> dashboard/settings/error.pyx
        result = reg.find_error_boundary("/dashboard/settings/profile")
        assert result.source_relative_path == Path("dashboard/settings/error.pyx")
        # /dashboard/users -> dashboard/error.pyx (not root)
        result = reg.find_error_boundary("/dashboard/users")
        assert result.source_relative_path == Path("dashboard/error.pyx")
