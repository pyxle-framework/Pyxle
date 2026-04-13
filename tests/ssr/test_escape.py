"""Tests for pyxle.ssr._escape — inline-JSON escaping utilities."""

import pytest

from pyxle.ssr._escape import escape_inline_json


class TestEscapeInlineJson:
    """Verify that all known dangerous sequences are neutralised."""

    def test_closes_script_tag(self):
        assert "</script>" not in escape_inline_json('{"x":"</script>"}')
        assert "<\\/script>" in escape_inline_json('{"x":"</script>"}')

    def test_closes_style_tag(self):
        assert "</style>" not in escape_inline_json("body{} </style>")

    def test_html_comment_open(self):
        result = escape_inline_json("<!-- comment -->")
        assert "<!--" not in result
        assert "<\\!--" in result

    def test_html_comment_close(self):
        result = escape_inline_json("<!-- comment -->")
        assert "-->" not in result
        assert "--\\>" in result

    def test_unicode_line_separator(self):
        result = escape_inline_json('{"x":"\u2028"}')
        assert "\u2028" not in result
        assert "\\u2028" in result

    def test_unicode_paragraph_separator(self):
        result = escape_inline_json('{"x":"\u2029"}')
        assert "\u2029" not in result
        assert "\\u2029" in result

    def test_safe_content_unchanged(self):
        safe = '{"name":"Pyxle","version":"1.0"}'
        assert escape_inline_json(safe) == safe

    def test_empty_string(self):
        assert escape_inline_json("") == ""

    def test_multiple_dangerous_sequences(self):
        raw = '</script><!-- -->\u2028\u2029'
        result = escape_inline_json(raw)
        assert "</script>" not in result
        assert "<!--" not in result
        assert "-->" not in result
        assert "\u2028" not in result
        assert "\u2029" not in result

    @pytest.mark.parametrize(
        "input_val,expected_fragment",
        [
            ("</", "<\\/"),
            ("<!--", "<\\!--"),
            ("-->", "--\\>"),
            ("\u2028", "\\u2028"),
            ("\u2029", "\\u2029"),
        ],
    )
    def test_individual_replacements(self, input_val, expected_fragment):
        assert expected_fragment in escape_inline_json(input_val)
