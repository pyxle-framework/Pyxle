"""Shared security utilities for the Pyxle dev server.

Provides input-validation helpers and sensitive-data redaction used across
the dev server, action dispatch, and middleware loading subsystems.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Identifier validation
# ---------------------------------------------------------------------------

#: Matches a valid Python/JS identifier: starts with a letter or underscore,
#: followed by letters, digits, or underscores.  Used to validate action names
#: and ``PYXLE_PUBLIC_*`` environment variable keys before they are
#: interpolated into generated code.
SAFE_IDENTIFIER_RE: re.Pattern[str] = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# ---------------------------------------------------------------------------
# Python module-path validation
# ---------------------------------------------------------------------------

#: Each dotted segment of a Python import path must be a valid identifier.
_DOTTED_MODULE_RE: re.Pattern[str] = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*$"
)


def validate_python_module_path(spec: str) -> bool:
    """Return ``True`` if *spec* looks like a valid dotted Python module path.

    Rejects empty strings, paths with slashes or other non-identifier
    characters, and paths that start or end with a dot.
    """
    if not spec:
        return False
    return _DOTTED_MODULE_RE.match(spec) is not None


# ---------------------------------------------------------------------------
# Sensitive-pattern redaction
# ---------------------------------------------------------------------------

#: Compiled patterns that match common secret/credential fragments in error
#: messages.  Each tuple is ``(pattern, replacement_label)``.
_SENSITIVE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    # Database DSN strings: postgres://user:pass@host/db, mysql://…
    (re.compile(r"(?i)(?:postgres|mysql|sqlite|mongodb|redis)(?:ql)?://\S+"), "[REDACTED_DSN]"),
    # Generic password= key-value (URL params, config strings)
    (re.compile(r"(?i)password\s*[=:]\s*\S+"), "password=[REDACTED]"),
    # Bearer tokens
    (re.compile(r"(?i)Bearer\s+\S+"), "Bearer [REDACTED]"),
    # AWS-style credential env vars with values
    (re.compile(r"(?i)(?:AWS_SECRET_ACCESS_KEY|AWS_SESSION_TOKEN)\s*[=:]\s*\S+"), "[REDACTED_AWS]"),
    # Generic secret/token/key assignments
    (re.compile(r"(?i)(?:secret|token|api_?key|private_?key)\s*[=:]\s*\S+"), "[REDACTED_SECRET]"),
)


def redact_sensitive_patterns(text: str) -> str:
    """Replace common secret/credential patterns in *text* with placeholders.

    Intended for developer-facing error messages shown in the dev overlay
    or browser.  This is a best-effort heuristic — it does not guarantee
    that all secrets are caught, but it prevents the most common leaks
    (database DSNs, bearer tokens, AWS keys, generic ``password=`` values).
    """
    for pattern, replacement in _SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


__all__ = [
    "SAFE_IDENTIFIER_RE",
    "redact_sensitive_patterns",
    "validate_python_module_path",
]
