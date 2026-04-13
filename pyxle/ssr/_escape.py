"""Unified escaping for values injected into inline ``<script>`` blocks.

Browser HTML tokenizers can be tricked by sequences inside ``<script>``
elements — ``</script>`` closes the tag, ``<!--`` opens an HTML comment in
legacy parsing modes, and the Unicode line terminators U+2028/U+2029 are
newline characters in JavaScript but not in JSON.  This module provides a
single ``escape_inline_json`` helper that neutralises all known sequences
so that ``json.dumps`` output can be safely placed inside ``<script>``
tags, ``<style>`` tags, or ``<script type="application/json">`` blocks.
"""

from __future__ import annotations


def escape_inline_json(value: str) -> str:
    """Escape *value* for safe inclusion inside an HTML ``<script>`` block.

    The following replacements are applied:

    * ``</``    → ``<\\/``   — prevents premature ``</script>`` close
    * ``<!--``  → ``<\\!--`` — prevents HTML comment opening
    * ``-->``   → ``--\\>``  — prevents HTML comment closing
    * U+2028    → ``\\u2028``— JS line separator (not valid in JSON strings)
    * U+2029    → ``\\u2029``— JS paragraph separator

    The input is expected to be the return value of :func:`json.dumps` or
    raw CSS text — **not** arbitrary HTML.
    """
    return (
        value
        .replace("</", "<\\/")
        .replace("<!--", "<\\!--")
        .replace("-->", "--\\>")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


__all__ = ["escape_inline_json"]
