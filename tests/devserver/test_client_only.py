"""Tests for ClientOnly component generation and behavior."""

from pyxle.devserver.client_files import (
    _render_client_only_component,
    _render_client_only_component_types,
)


class TestClientOnlyComponent:
    """Test ClientOnly component code generation."""

    def test_client_only_component_exists(self):
        """ClientOnly component should be generated."""
        code = _render_client_only_component()
        assert len(code) > 0
        assert "ClientOnly" in code

    def test_client_only_has_fallback_prop(self):
        """ClientOnly should accept fallback prop."""
        code = _render_client_only_component()
        assert "fallback" in code
        assert "children" in code

    def test_client_only_uses_effect_for_hydration(self):
        """ClientOnly should use useEffect to detect client mount."""
        code = _render_client_only_component()
        assert "React.useEffect" in code
        assert "useState" in code

    def test_client_only_returns_fallback_initially(self):
        """ClientOnly should return fallback when isClient is false."""
        code = _render_client_only_component()
        # Check the pattern: if (!isClient) return fallback
        assert "!isClient" in code
        assert "return fallback" in code

    def test_client_only_returns_children_after_mount(self):
        """ClientOnly should return children after client mount."""
        code = _render_client_only_component()
        # After setIsClient(true), should render children
        assert "setIsClient(true)" in code
        assert "return React.createElement(React.Fragment, null, children)" in code

    def test_client_only_has_forward_ref(self):
        """ClientOnly should support ref forwarding."""
        code = _render_client_only_component()
        assert "React.forwardRef" in code
        assert "ref" in code

    def test_client_only_default_fallback(self):
        """ClientOnly should have default fallback when none provided."""
        code = _render_client_only_component()
        # Should use ?? or || for default fallback
        assert "fallback ?? " in code or "fallback || " in code

    def test_client_only_typescript_types(self):
        """ClientOnly TypeScript types should be generated."""
        types = _render_client_only_component_types()
        assert "ClientOnlyProps" in types
        assert "children: React.ReactNode" in types
        assert "fallback?: React.ReactNode" in types
        assert "ClientOnly" in types

    def test_client_only_exports_correctly(self):
        """ClientOnly should export both named and default."""
        code = _render_client_only_component()
        # Should have export default
        assert "export default ClientOnly" in code

    def test_client_only_display_name(self):
        """ClientOnly should have displayName for debugging."""
        code = _render_client_only_component()
        assert "ClientOnly.displayName = 'ClientOnly'" in code
