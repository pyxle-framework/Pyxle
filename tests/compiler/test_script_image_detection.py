"""Tests for Script and Image declaration detection in the parser."""

from __future__ import annotations

from pyxle.compiler.parser import PyxParser


class TestScriptDetection:
    """Tests for <Script /> element detection and parsing."""

    def test_detect_simple_script(self) -> None:
        """Verify that a basic <Script /> element is detected."""
        source = """
# --- JavaScript/PSX ---
import { Script } from 'pyxle/client';

export default function Page() {
  return (
    <>
      <Script src="https://example.com/sdk.js" />
      <h1>Hello</h1>
    </>
  );
}
"""
        parser = PyxParser()
        result = parser.parse_text(source)
        assert len(result.script_declarations) == 1
        assert result.script_declarations[0]["src"] == "https://example.com/sdk.js"

    def test_detect_script_with_strategy(self) -> None:
        """Verify strategy attribute is captured."""
        source = """
import { Script } from 'pyxle/client';

export default function Page() {
  return (
    <>
      <Script src="https://example.com/sdk.js" strategy="afterInteractive" />
    </>
  );
}
"""
        parser = PyxParser()
        result = parser.parse_text(source)
        assert len(result.script_declarations) == 1
        assert result.script_declarations[0]["strategy"] == "afterInteractive"

    def test_detect_multiple_scripts(self) -> None:
        """Verify multiple <Script /> elements are detected."""
        source = """
import { Script } from 'pyxle/client';

export default function Page() {
  return (
    <>
      <Script src="https://example.com/sdk1.js" strategy="beforeInteractive" />
      <Script src="https://example.com/sdk2.js" strategy="afterInteractive" />
      <h1>Page</h1>
    </>
  );
}
"""
        parser = PyxParser()
        result = parser.parse_text(source)
        assert len(result.script_declarations) == 2
        assert result.script_declarations[0]["src"] == "https://example.com/sdk1.js"
        assert result.script_declarations[1]["src"] == "https://example.com/sdk2.js"

    def test_detect_script_with_async_defer(self) -> None:
        """Verify async and defer attributes are captured."""
        source = """
import { Script } from 'pyxle/client';

export default function Page() {
  return (
    <Script src="https://example.com/sdk.js" async defer />
  );
}
"""
        parser = PyxParser()
        result = parser.parse_text(source)
        assert len(result.script_declarations) == 1
        assert result.script_declarations[0]["async"] is True
        assert result.script_declarations[0]["defer"] is True

    def test_no_scripts_detected(self) -> None:
        """Verify empty tuple when no scripts are present."""
        source = """
export default function Page() {
  return <h1>No scripts here</h1>;
}
"""
        parser = PyxParser()
        result = parser.parse_text(source)
        assert len(result.script_declarations) == 0


class TestImageDetection:
    """Tests for <Image /> element detection and parsing."""

    def test_detect_simple_image(self) -> None:
        """Verify that a basic <Image /> element is detected."""
        source = """
import { Image } from 'pyxle/client';

export default function Page() {
  return (
    <Image src="/hero.png" width="800" height="400" alt="Hero" />
  );
}
"""
        parser = PyxParser()
        result = parser.parse_text(source)
        assert len(result.image_declarations) == 1
        assert result.image_declarations[0]["src"] == "/hero.png"
        assert result.image_declarations[0]["width"] == "800"
        assert result.image_declarations[0]["height"] == "400"

    def test_detect_image_with_priority(self) -> None:
        """Verify priority attribute is captured."""
        source = """
import { Image } from 'pyxle/client';

export default function Page() {
  return (
    <Image src="/logo.png" width="200" height="100" priority alt="Logo" />
  );
}
"""
        parser = PyxParser()
        result = parser.parse_text(source)
        assert len(result.image_declarations) == 1
        assert result.image_declarations[0]["priority"] is True

    def test_detect_multiple_images(self) -> None:
        """Verify multiple <Image /> elements are detected."""
        source = """
import { Image } from 'pyxle/client';

export default function Page() {
  return (
    <>
      <Image src="/img1.png" width="400" height="300" alt="Image 1" />
      <Image src="/img2.png" width="400" height="300" alt="Image 2" />
    </>
  );
}
"""
        parser = PyxParser()
        result = parser.parse_text(source)
        assert len(result.image_declarations) == 2
        assert result.image_declarations[0]["src"] == "/img1.png"
        assert result.image_declarations[1]["src"] == "/img2.png"

    def test_no_images_detected(self) -> None:
        """Verify empty tuple when no images are present."""
        source = """
export default function Page() {
  return <img src="/fallback.png" alt="Fallback" />;
}
"""
        parser = PyxParser()
        result = parser.parse_text(source)
        assert len(result.image_declarations) == 0


class TestScriptAndImageTogether:
    """Tests for detecting both scripts and images in same file."""

    def test_detect_scripts_and_images(self) -> None:
        """Verify both scripts and images are detected in the same file."""
        source = """
import { Script, Image } from 'pyxle/client';

@server
async def load_page(request):
    return {"title": "Home"}

export default function Page({ data }) {
  return (
    <>
      <Script src="https://example.com/sdk.js" strategy="afterInteractive" />
      <Image src="/hero.png" width="800" height="400" alt="Hero" />
      <h1>{data.title}</h1>
    </>
  );
}
"""
        parser = PyxParser()
        result = parser.parse_text(source)
        assert len(result.script_declarations) == 1
        assert len(result.image_declarations) == 1
        assert result.loader is not None
        assert result.loader.name == "load_page"
