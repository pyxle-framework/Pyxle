"""Tests for dynamic Head component extraction from React trees."""

from pyxle.ssr.renderer import RenderResult


def test_render_result_includes_head_elements(tmp_path):
    """Test that RenderResult can include head elements."""
    result = RenderResult(
        html="<div>Hello</div>",
        inline_styles=(),
        head_elements=("<title>Test Page</title>", "<meta name='description' content='Test'>"),
    )
    
    assert result.html == "<div>Hello</div>"
    assert result.head_elements == ("<title>Test Page</title>", "<meta name='description' content='Test'>")
    assert len(result.head_elements) == 2


def test_render_result_default_head_elements():
    """Test that RenderResult defaults to empty head_elements tuple."""
    result = RenderResult(html="<div>Hello</div>")
    
    assert result.head_elements == ()
