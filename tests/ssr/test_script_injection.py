"""Tests for script injection in SSR templates."""


from pyxle.devserver.routes import PageRoute
from pyxle.devserver.settings import DevServerSettings
from pyxle.ssr.template import (
    _render_before_interactive_scripts,
    _serialize_scripts_metadata,
    build_document_shell,
)


class TestBeforeInteractiveScripts:
    """Test beforeInteractive script rendering."""

    def test_empty_scripts(self):
        """Should return empty string for no scripts."""
        result = _render_before_interactive_scripts(tuple(), "")
        assert result == ""

    def test_single_before_interactive_script(self):
        """Should render single beforeInteractive script."""
        scripts = ({"src": "https://example.com/script.js", "strategy": "beforeInteractive"},)
        result = _render_before_interactive_scripts(scripts, "")
        assert '<script src="https://example.com/script.js"></script>' in result

    def test_filters_non_before_interactive(self):
        """Should only render beforeInteractive scripts."""
        scripts = (
            {"src": "https://example.com/before.js", "strategy": "beforeInteractive"},
            {"src": "https://example.com/after.js", "strategy": "afterInteractive"},
            {"src": "https://example.com/lazy.js", "strategy": "lazyOnload"},
        )
        result = _render_before_interactive_scripts(scripts, "")
        assert "before.js" in result
        assert "after.js" not in result
        assert "lazy.js" not in result

    def test_async_defer_attributes(self):
        """Should include async and defer attributes."""
        scripts = (
            {
                "src": "https://example.com/async.js",
                "strategy": "beforeInteractive",
                "async": True,
            },
            {
                "src": "https://example.com/defer.js",
                "strategy": "beforeInteractive",
                "defer": True,
            },
        )
        result = _render_before_interactive_scripts(scripts, "")
        assert "async" in result
        assert "defer" in result

    def test_module_type(self):
        """Should include type=module for module scripts."""
        scripts = (
            {
                "src": "https://example.com/module.js",
                "strategy": "beforeInteractive",
                "module": True,
            },
        )
        result = _render_before_interactive_scripts(scripts, "")
        assert 'type="module"' in result

    def test_nomodule_attribute(self):
        """Should include nomodule attribute."""
        scripts = (
            {
                "src": "https://example.com/legacy.js",
                "strategy": "beforeInteractive",
                "noModule": True,
            },
        )
        result = _render_before_interactive_scripts(scripts, "")
        assert "nomodule" in result

    def test_nonce_attribute(self):
        """Should include nonce attribute."""
        scripts = ({"src": "https://example.com/script.js", "strategy": "beforeInteractive"},)
        result = _render_before_interactive_scripts(scripts, ' nonce="test123"')
        assert 'nonce="test123"' in result


class TestScriptsMetadataSerialization:
    """Test scripts metadata serialization for client."""

    def test_empty_scripts(self):
        """Should return empty array JSON for no scripts."""
        result = _serialize_scripts_metadata(tuple())
        assert result == "[]"

    def test_filters_before_interactive(self):
        """Should exclude beforeInteractive scripts from client metadata."""
        scripts = (
            {"src": "https://example.com/before.js", "strategy": "beforeInteractive"},
            {"src": "https://example.com/after.js", "strategy": "afterInteractive"},
        )
        result = _serialize_scripts_metadata(scripts)
        assert "before.js" not in result
        assert "after.js" in result

    def test_includes_lazy_onload(self):
        """Should include lazyOnload scripts in client metadata."""
        scripts = ({"src": "https://example.com/lazy.js", "strategy": "lazyOnload"},)
        result = _serialize_scripts_metadata(scripts)
        assert "lazy.js" in result
        assert "lazyOnload" in result

    def test_json_format(self):
        """Should produce valid JSON."""
        import json

        scripts = (
            {"src": "https://example.com/after.js", "strategy": "afterInteractive"},
            {"src": "https://example.com/lazy.js", "strategy": "lazyOnload"},
        )
        result = _serialize_scripts_metadata(scripts)
        parsed = json.loads(result)
        assert len(parsed) == 2
        assert parsed[0]["src"] == "https://example.com/after.js"
        assert parsed[1]["strategy"] == "lazyOnload"


class TestDocumentShellWithScripts:
    """Test full document shell generation with scripts."""

    def test_dev_mode_includes_scripts_metadata(self, tmp_path):
        """Should include scripts metadata in dev mode."""
        settings = DevServerSettings.from_project_root(tmp_path)
        
        page = PageRoute(
            path="/test",
            source_relative_path=tmp_path / "test.pyxl",
            source_absolute_path=tmp_path / "pages/test.pyxl",
            server_module_path=tmp_path / ".pyxle-build/server/pages/test.py",
            client_module_path=tmp_path / ".pyxle-build/client/pages/test.jsx",
            metadata_path=tmp_path / ".pyxle-build/metadata/pages/test.json",
            module_key="pyxle.server.pages.test",
            client_asset_path="/pages/test.jsx",
            server_asset_path="/pages/test.py",
            content_hash="abc123",
            loader_name=None,
            loader_line=None,
            head_elements=tuple(),
            head_is_dynamic=False,
            scripts=(
                {"src": "https://example.com/before.js", "strategy": "beforeInteractive"},
                {"src": "https://example.com/after.js", "strategy": "afterInteractive"},
            ),
            images=tuple(),
        )
        
        shell = build_document_shell(
            settings=settings,
            page=page,
            props={},
            script_nonce="",
            head_elements=tuple(),
        )
        
        # beforeInteractive should be in head
        assert "before.js" in shell.prefix
        
        # Scripts metadata should be in suffix for client
        assert "__PYXLE_SCRIPTS__" in shell.suffix
        assert "after.js" in shell.suffix

    def test_before_interactive_in_head(self, tmp_path):
        """Should inject beforeInteractive scripts in head."""
        settings = DevServerSettings.from_project_root(tmp_path)
        
        page = PageRoute(
            path="/test",
            source_relative_path=tmp_path / "test.pyxl",
            source_absolute_path=tmp_path / "pages/test.pyxl",
            server_module_path=tmp_path / ".pyxle-build/server/pages/test.py",
            client_module_path=tmp_path / ".pyxle-build/client/pages/test.jsx",
            metadata_path=tmp_path / ".pyxle-build/metadata/pages/test.json",
            module_key="pyxle.server.pages.test",
            client_asset_path="/pages/test.jsx",
            server_asset_path="/pages/test.py",
            content_hash="abc123",
            loader_name=None,
            loader_line=None,
            head_elements=tuple(),
            head_is_dynamic=False,
            scripts=(
                {"src": "https://cdn.example.com/critical.js", "strategy": "beforeInteractive"},
            ),
            images=tuple(),
        )
        
        shell = build_document_shell(
            settings=settings,
            page=page,
            props={},
            script_nonce="",
            head_elements=tuple(),
        )
        
        # Script should appear before </head>
        assert '<script src="https://cdn.example.com/critical.js"></script>' in shell.prefix
        assert "</head>" in shell.prefix
        
        # Verify it's in head, not body
        head_end_idx = shell.prefix.index("</head>")
        script_idx = shell.prefix.index("critical.js")
        assert script_idx < head_end_idx
