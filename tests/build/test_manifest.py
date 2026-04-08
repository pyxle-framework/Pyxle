from pathlib import Path

import pytest

from pyxle.build.manifest import build_page_manifest
from pyxle.devserver.registry import MetadataRegistry, PageRegistryEntry


@pytest.fixture
def registry(tmp_path: Path) -> MetadataRegistry:
    metadata_path = tmp_path / "metadata" / "pages" / "index.json"
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text("{}", encoding="utf-8")

    server_path = tmp_path / "server" / "pages" / "index.py"
    server_path.parent.mkdir(parents=True, exist_ok=True)
    server_path.write_text("print('server')\n", encoding="utf-8")

    page_entry = PageRegistryEntry(
        route_path="/",
        alternate_route_paths=(),
        source_relative_path=Path("pages/index.pyx"),
        source_absolute_path=tmp_path / "pages" / "index.pyx",
        server_module_path=server_path,
        client_module_path=tmp_path / "client" / "pages" / "index.jsx",
        metadata_path=metadata_path,
        client_asset_path="/routes/index.jsx",
        server_asset_path="server/pages/index.py",
        module_key="pyxle.server.pages.index",
        content_hash="hash",
        loader_name=None,
        loader_line=None,
        head_elements=(),
        head_is_dynamic=False,
    )

    return MetadataRegistry(pages=[page_entry], apis=[])


def test_build_page_manifest_matches_vite_entries(registry: MetadataRegistry):
    vite_manifest = {
        "routes/index.jsx": {
            "file": "assets/index.js",
            "imports": ["assets/vendor.js"],
            "css": ["assets/index.css"],
        }
    }

    result = build_page_manifest(registry=registry, manifest=vite_manifest)

    assert result == {
        "/": {
            "client": {
                "file": "assets/index.js",
                "imports": ["assets/vendor.js"],
                "css": ["assets/index.css"],
            },
            "metadata": registry.pages[0].metadata_path.as_posix(),
            "server": registry.pages[0].server_module_path.as_posix(),
        }
    }


def test_build_page_manifest_matches_src_field(registry: MetadataRegistry):
    vite_manifest = {
        "assets/index.js": {
            "file": "assets/index.js",
            "src": "routes/index.jsx",
            "imports": [],
        }
    }

    result = build_page_manifest(registry=registry, manifest=vite_manifest)

    assert result["/"]["client"]["file"] == "assets/index.js"
