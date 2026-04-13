"""Integration tests for Script and Image compilation."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from pyxle.compiler.core import compile_file


@pytest.fixture
def temp_project() -> Path:
    """Create a temporary project structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        pages_dir = project_root / "pages"
        pages_dir.mkdir()
        yield project_root


class TestScriptImageIntegration:
    """Integration tests for Script/Image compilation and metadata."""

    def test_compile_page_with_scripts_and_images(self, temp_project: Path) -> None:
        """Verify scripts and images are compiled and stored in metadata."""
        source_file = temp_project / "pages" / "index.pyxl"
        source_file.write_text(
            """
from pyxle import server

@server
async def load_home(request):
    return {"title": "Home"}

# --- JavaScript/PSX ---
import { Script, Image } from 'pyxle/client';

export default function Page({ data }) {
  return (
    <>
      <Script src="https://analytics.example.com/tracker.js" strategy="afterInteractive" />
      <Image src="/hero.png" width={800} height={400} alt="Hero" />
      <h1>{data.title}</h1>
    </>
  );
}
"""
        )

        build_root = temp_project / ".pyxle-build"
        result = compile_file(source_file, build_root=build_root)

        # Verify metadata was written
        assert result.metadata_output.exists()
        metadata_json = json.loads(result.metadata_output.read_text())

        # Verify scripts are in metadata
        assert "scripts" in metadata_json
        assert len(metadata_json["scripts"]) == 1
        assert metadata_json["scripts"][0]["src"] == "https://analytics.example.com/tracker.js"
        assert metadata_json["scripts"][0]["strategy"] == "afterInteractive"

        # Verify images are in metadata
        assert "images" in metadata_json
        assert len(metadata_json["images"]) == 1
        assert metadata_json["images"][0]["src"] == "/hero.png"
        assert metadata_json["images"][0]["width"] == 800
        assert metadata_json["images"][0]["height"] == 400

        # Verify client output contains the components
        client_code = result.client_output.read_text()
        assert "Script" in client_code
        assert "Image" in client_code
        assert "Hero" in client_code

    def test_compile_page_with_multiple_scripts(self, temp_project: Path) -> None:
        """Verify multiple scripts are tracked independently."""
        source_file = temp_project / "pages" / "dashboard.pyxl"
        source_file.write_text(
            """
# --- JavaScript/PSX ---
import { Script } from 'pyxle/client';

export default function Dashboard() {
  return (
    <>
      <Script src="https://example.com/charts.js" strategy="beforeInteractive" />
      <Script src="https://example.com/analytics.js" strategy="afterInteractive" async />
      <Script src="https://example.com/editor.js" strategy="lazyOnload" />
      <h1>Dashboard</h1>
    </>
  );
}
"""
        )

        build_root = temp_project / ".pyxle-build"
        result = compile_file(source_file, build_root=build_root)
        metadata_json = json.loads(result.metadata_output.read_text())

        # Verify all three scripts are captured with correct properties
        assert len(metadata_json["scripts"]) == 3
        assert metadata_json["scripts"][0]["strategy"] == "beforeInteractive"
        assert metadata_json["scripts"][1]["strategy"] == "afterInteractive"
        assert metadata_json["scripts"][1]["async"] is True
        assert metadata_json["scripts"][2]["strategy"] == "lazyOnload"

    def test_compile_page_with_images_preserves_priority(self, temp_project: Path) -> None:
        """Verify image priority attribute is captured."""
        source_file = temp_project / "pages" / "gallery.pyxl"
        source_file.write_text(
            """
# --- JavaScript/PSX ---
import { Image } from 'pyxle/client';

export default function Gallery() {
  return (
    <>
      <Image src="/hero.png" width={1200} height={600} alt="Hero" priority />
      <Image src="/thumb1.png" width={400} height={300} alt="Thumbnail 1" />
      <Image src="/thumb2.png" width={400} height={300} alt="Thumbnail 2" lazy={false} />
    </>
  );
}
"""
        )

        build_root = temp_project / ".pyxle-build"
        result = compile_file(source_file, build_root=build_root)
        metadata_json = json.loads(result.metadata_output.read_text())

        assert len(metadata_json["images"]) == 3
        assert metadata_json["images"][0]["priority"] is True
        assert metadata_json["images"][0]["lazy"] is True
        assert metadata_json["images"][1]["lazy"] is True
        assert metadata_json["images"][2]["lazy"] is False

    def test_compile_preserves_existing_head(self, temp_project: Path) -> None:
        """Verify HEAD variable and scripts/images coexist."""
        source_file = temp_project / "pages" / "about.pyxl"
        source_file.write_text(
            """
HEAD = "<title>About</title>"

# --- JavaScript/PSX ---
import { Script } from 'pyxle/client';

export default function About() {
  return (
    <>
      <Script src="https://example.com/analytics.js" />
      <h1>About Us</h1>
    </>
  );
}
"""
        )

        build_root = temp_project / ".pyxle-build"
        result = compile_file(source_file, build_root=build_root)
        metadata_json = json.loads(result.metadata_output.read_text())

        # Verify both HEAD and scripts are present
        assert len(metadata_json["head"]) == 1
        assert "<title>About</title>" in metadata_json["head"]
        assert len(metadata_json["scripts"]) == 1
        assert metadata_json["scripts"][0]["src"] == "https://example.com/analytics.js"
