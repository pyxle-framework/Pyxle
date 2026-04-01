"""
.env file loading for Pyxle projects.

Files are loaded in order of **increasing** precedence — later files override earlier ones.
Variables already present in ``os.environ`` are **never** overwritten (the shell always wins).

Loading order:
  1. ``.env``                      — base defaults, committed to source control
  2. ``.env.<mode>``               — mode-specific defaults (e.g. ``.env.development``)
  3. ``.env.local``                — local overrides, **not** committed to source control
  4. ``.env.<mode>.local``         — local mode-specific overrides

Environment variable conventions:
  * Any variable is available server-side via ``os.environ``.
  * Variables prefixed with ``PYXLE_PUBLIC_`` may be safely injected into client bundles
    at build time (the build pipeline reads them when assembling JSX).
  * All other variables are server-only — the framework never serialises them into
    client-visible code or HTML.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


class EnvFileError(Exception):
    """Raised when a .env file cannot be read or contains a syntax error."""


@dataclass(frozen=True, slots=True)
class EnvLoadResult:
    """Summary of which variables were loaded from which files."""

    loaded: tuple[tuple[str, str], ...]
    """All ``(key, value)`` pairs that were applied to ``os.environ``."""

    skipped: tuple[str, ...]
    """Keys that were present in the files but already set in the environment."""

    files_read: tuple[Path, ...]
    """Absolute paths of the ``.env`` files that were successfully read (in load order)."""

    @property
    def loaded_count(self) -> int:
        """Number of variables applied to the environment."""
        return len(self.loaded)

    @property
    def public_keys(self) -> tuple[str, ...]:
        """Keys that carry the ``PYXLE_PUBLIC_`` prefix (safe for client injection)."""
        return tuple(k for k, _ in self.loaded if k.startswith("PYXLE_PUBLIC_"))


def load_env_files(
    project_root: Path,
    *,
    mode: str = "development",
) -> EnvLoadResult:
    """Load ``.env`` files from *project_root* into ``os.environ``.

    Variables already present in the environment are left untouched — the
    shell (or CI system) always has higher precedence than ``.env`` files.

    Args:
        project_root: Directory that contains the ``.env`` files.
        mode: Deployment mode — typically ``"development"`` or ``"production"``.
              Determines which mode-specific files are loaded.

    Returns:
        An :class:`EnvLoadResult` summarising what was loaded.
    """
    root = Path(project_root).expanduser().resolve()
    mode = mode.strip().lower()

    # Ordered from lowest to highest precedence.
    candidates: tuple[Path, ...] = (
        root / ".env",
        root / f".env.{mode}",
        root / ".env.local",
        root / f".env.{mode}.local",
    )

    all_pairs: dict[str, str] = {}
    files_read: list[Path] = []

    for candidate in candidates:
        if not candidate.is_file():
            continue
        try:
            text = candidate.read_text(encoding="utf-8")
        except OSError as exc:
            raise EnvFileError(f"Cannot read '{candidate}': {exc}") from exc

        pairs = parse_env_file(text)
        all_pairs.update(pairs)
        files_read.append(candidate)

    loaded: list[tuple[str, str]] = []
    skipped: list[str] = []

    for key, value in all_pairs.items():
        if key in os.environ:
            skipped.append(key)
        else:
            os.environ[key] = value
            loaded.append((key, value))

    return EnvLoadResult(
        loaded=tuple(loaded),
        skipped=tuple(skipped),
        files_read=tuple(files_read),
    )


def parse_env_file(text: str) -> dict[str, str]:
    """Parse a ``.env`` file and return a ``{key: value}`` mapping.

    Handles:
    * ``KEY=value`` — bare value
    * ``KEY="double quoted"`` — double quotes with escape sequences
    * ``KEY='single quoted'`` — single quotes (no escape processing)
    * ``export KEY=value`` — optional ``export`` prefix
    * ``# comment`` — full-line and inline comments
    * Blank lines are ignored

    Args:
        text: Raw contents of a ``.env`` file.

    Returns:
        A dict mapping variable names to their parsed string values.
    """
    result: dict[str, str] = {}

    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()

        # Skip blank lines and comment lines.
        if not line or line.startswith("#"):
            continue

        # Strip optional leading 'export'.
        if line.startswith("export ") or line.startswith("export\t"):
            line = line[6:].strip()

        # Must contain an '=' to be a valid assignment.
        if "=" not in line:
            continue

        key, _, raw_value = line.partition("=")
        key = key.strip()

        if not key:
            continue

        if not _is_valid_key(key):
            raise EnvFileError(
                f"Invalid variable name '{key}' on line {lineno}: "
                "names must match [A-Za-z_][A-Za-z0-9_]*"
            )

        result[key] = _parse_value(raw_value)

    return result


def _is_valid_key(key: str) -> bool:
    """Return True if *key* is a legal shell variable name."""
    if not key:
        return False
    if not (key[0].isalpha() or key[0] == "_"):
        return False
    return all(c.isalnum() or c == "_" for c in key)


def _parse_value(raw: str) -> str:
    """Parse a raw value string from a ``.env`` line.

    Strips surrounding quotes and processes escape sequences in double-quoted
    strings.  Inline ``#`` comments are removed from unquoted values.
    """
    raw = raw.strip()

    # Double-quoted value: process common escape sequences.
    if len(raw) >= 2 and raw[0] == '"' and raw[-1] == '"':
        inner = raw[1:-1]
        return (
            inner
            .replace('\\"', '"')
            .replace("\\n", "\n")
            .replace("\\r", "\r")
            .replace("\\t", "\t")
            .replace("\\\\", "\\")
        )

    # Single-quoted value: literal, no escaping.
    if len(raw) >= 2 and raw[0] == "'" and raw[-1] == "'":
        return raw[1:-1]

    # Unquoted value: strip trailing inline comment.
    if "#" in raw:
        raw = raw[: raw.index("#")].rstrip()

    return raw


def get_public_env_vars() -> dict[str, str]:
    """Return all ``PYXLE_PUBLIC_*`` variables from the current environment.

    These are the only variables that the build pipeline may safely embed in
    client-side JavaScript bundles.
    """
    prefix = "PYXLE_PUBLIC_"
    return {k: v for k, v in os.environ.items() if k.startswith(prefix)}


__all__ = [
    "EnvFileError",
    "EnvLoadResult",
    "load_env_files",
    "parse_env_file",
    "get_public_env_vars",
]
