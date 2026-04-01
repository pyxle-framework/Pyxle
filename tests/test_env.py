"""Tests for pyxle.env — .env file loading."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from pyxle.env import (
    EnvFileError,
    EnvLoadResult,
    get_public_env_vars,
    load_env_files,
    parse_env_file,
)


# ---------------------------------------------------------------------------
# parse_env_file — unit tests
# ---------------------------------------------------------------------------


class TestParseEnvFile:
    def test_basic_key_value(self):
        result = parse_env_file("FOO=bar\nBAZ=qux\n")
        assert result == {"FOO": "bar", "BAZ": "qux"}

    def test_empty_string_is_empty_dict(self):
        assert parse_env_file("") == {}

    def test_blank_lines_ignored(self):
        result = parse_env_file("\n\n\nFOO=1\n\n")
        assert result == {"FOO": "1"}

    def test_comment_lines_ignored(self):
        result = parse_env_file("# this is a comment\nFOO=bar")
        assert result == {"FOO": "bar"}

    def test_inline_comment_stripped_from_unquoted(self):
        result = parse_env_file("FOO=bar # inline comment")
        assert result == {"FOO": "bar"}

    def test_inline_comment_not_stripped_from_double_quoted(self):
        result = parse_env_file('FOO="bar # not a comment"')
        assert result == {"FOO": "bar # not a comment"}

    def test_inline_comment_not_stripped_from_single_quoted(self):
        result = parse_env_file("FOO='bar # not a comment'")
        assert result == {"FOO": "bar # not a comment"}

    def test_double_quoted_value(self):
        result = parse_env_file('KEY="hello world"')
        assert result == {"KEY": "hello world"}

    def test_single_quoted_value(self):
        result = parse_env_file("KEY='hello world'")
        assert result == {"KEY": "hello world"}

    def test_double_quote_escape_sequences(self):
        result = parse_env_file(r'KEY="line1\nline2\ttab\\"')
        assert result == {"KEY": "line1\nline2\ttab\\"}

    def test_double_quote_escaped_quote(self):
        result = parse_env_file(r'KEY="say \"hello\""')
        assert result == {"KEY": 'say "hello"'}

    def test_single_quoted_no_escape_processing(self):
        result = parse_env_file(r"KEY='no\nescape'")
        assert result == {"KEY": r"no\nescape"}

    def test_export_prefix_stripped(self):
        result = parse_env_file("export FOO=bar")
        assert result == {"FOO": "bar"}

    def test_export_tab_prefix_stripped(self):
        result = parse_env_file("export\tFOO=bar")
        assert result == {"FOO": "bar"}

    def test_lines_without_equals_sign_ignored(self):
        result = parse_env_file("NOT_AN_ASSIGNMENT\nFOO=bar")
        assert result == {"FOO": "bar"}

    def test_empty_value(self):
        result = parse_env_file("FOO=")
        assert result == {"FOO": ""}

    def test_value_with_equals_sign(self):
        result = parse_env_file("DATABASE_URL=postgres://user:pass@host/db?param=1")
        assert result == {"DATABASE_URL": "postgres://user:pass@host/db?param=1"}

    def test_underscore_key(self):
        result = parse_env_file("_PRIVATE=secret")
        assert result == {"_PRIVATE": "secret"}

    def test_whitespace_around_key_stripped(self):
        result = parse_env_file("  FOO  =bar")
        assert result == {"FOO": "bar"}

    def test_whitespace_around_unquoted_value_stripped(self):
        result = parse_env_file("FOO=  bar  ")
        assert result == {"FOO": "bar"}

    def test_multiple_assignments_last_wins(self):
        result = parse_env_file("KEY=first\nKEY=second")
        assert result == {"KEY": "second"}

    def test_invalid_key_raises(self):
        with pytest.raises(EnvFileError, match="Invalid variable name"):
            parse_env_file("123INVALID=value")

    def test_key_with_spaces_raises(self):
        with pytest.raises(EnvFileError, match="Invalid variable name"):
            parse_env_file("KEY WITH SPACES=value")

    def test_empty_key_after_export_is_skipped(self):
        # Line "export =value" has empty key after stripping 'export' — skipped
        result = parse_env_file("export =value\nGOOD=ok")
        assert result == {"GOOD": "ok"}

    def test_lineno_in_error_message(self):
        text = "GOOD=ok\n\n123BAD=value"
        with pytest.raises(EnvFileError, match="line 3"):
            parse_env_file(text)

    def test_carriage_return_escape(self):
        result = parse_env_file(r'KEY="a\rb"')
        assert result == {"KEY": "a\rb"}


# ---------------------------------------------------------------------------
# load_env_files — integration tests using tmp_path
# ---------------------------------------------------------------------------


class TestLoadEnvFiles:
    def _write(self, root: Path, name: str, content: str) -> None:
        (root / name).write_text(content, encoding="utf-8")

    def test_loads_base_dot_env(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("BASE_VAR", raising=False)
        self._write(tmp_path, ".env", "BASE_VAR=from_base\n")

        result = load_env_files(tmp_path, mode="development")

        assert os.environ["BASE_VAR"] == "from_base"
        assert ("BASE_VAR", "from_base") in result.loaded
        assert tmp_path / ".env" in result.files_read

    def test_mode_specific_overrides_base(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("PYXLE_MODE_VAR", raising=False)
        self._write(tmp_path, ".env", "PYXLE_MODE_VAR=base\n")
        self._write(tmp_path, ".env.development", "PYXLE_MODE_VAR=dev\n")

        load_env_files(tmp_path, mode="development")

        assert os.environ["PYXLE_MODE_VAR"] == "dev"

    def test_local_overrides_mode(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("PYXLE_LOCAL_VAR", raising=False)
        self._write(tmp_path, ".env", "PYXLE_LOCAL_VAR=base\n")
        self._write(tmp_path, ".env.development", "PYXLE_LOCAL_VAR=dev\n")
        self._write(tmp_path, ".env.local", "PYXLE_LOCAL_VAR=local\n")

        load_env_files(tmp_path, mode="development")

        assert os.environ["PYXLE_LOCAL_VAR"] == "local"

    def test_mode_local_overrides_all(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("PYXLE_PREC_VAR", raising=False)
        self._write(tmp_path, ".env", "PYXLE_PREC_VAR=base\n")
        self._write(tmp_path, ".env.development", "PYXLE_PREC_VAR=dev\n")
        self._write(tmp_path, ".env.local", "PYXLE_PREC_VAR=local\n")
        self._write(tmp_path, ".env.development.local", "PYXLE_PREC_VAR=dev_local\n")

        load_env_files(tmp_path, mode="development")

        assert os.environ["PYXLE_PREC_VAR"] == "dev_local"

    def test_system_env_never_overwritten(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("EXISTING_VAR", "system_value")
        self._write(tmp_path, ".env", "EXISTING_VAR=dotenv_value\n")

        result = load_env_files(tmp_path, mode="development")

        assert os.environ["EXISTING_VAR"] == "system_value"
        assert "EXISTING_VAR" in result.skipped

    def test_missing_all_files_returns_empty_result(self, tmp_path: Path):
        result = load_env_files(tmp_path, mode="development")
        assert result.loaded_count == 0
        assert result.files_read == ()
        assert result.skipped == ()

    def test_only_existing_files_are_read(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("ONLY_BASE", raising=False)
        self._write(tmp_path, ".env", "ONLY_BASE=yes\n")

        result = load_env_files(tmp_path, mode="development")

        # Only .env should be in files_read; the others don't exist
        assert len(result.files_read) == 1
        assert result.files_read[0].name == ".env"

    def test_production_mode_loads_production_files(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("PYXLE_ENV_MODE", raising=False)
        self._write(tmp_path, ".env.production", "PYXLE_ENV_MODE=production\n")

        load_env_files(tmp_path, mode="production")

        assert os.environ["PYXLE_ENV_MODE"] == "production"

    def test_files_read_order_is_precedence_order(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("PYXLE_ORD_VAR", raising=False)
        self._write(tmp_path, ".env", "PYXLE_ORD_VAR=base\n")
        self._write(tmp_path, ".env.development", "PYXLE_ORD_VAR=dev\n")
        self._write(tmp_path, ".env.local", "PYXLE_ORD_VAR=local\n")

        result = load_env_files(tmp_path, mode="development")

        names = [f.name for f in result.files_read]
        assert names == [".env", ".env.development", ".env.local"]

    def test_env_file_io_error_raises_env_file_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        env_file = tmp_path / ".env"
        env_file.write_text("GOOD=ok")

        original_read = Path.read_text

        def mock_read(self, *args, **kwargs):
            if self.name == ".env":
                raise OSError("Permission denied")
            return original_read(self, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", mock_read)
        with pytest.raises(EnvFileError, match="Cannot read"):
            load_env_files(tmp_path, mode="development")

    def test_mode_is_lowercased(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("PYXLE_CASE_VAR", raising=False)
        self._write(tmp_path, ".env.development", "PYXLE_CASE_VAR=lower\n")

        # Passing uppercase mode should still work
        load_env_files(tmp_path, mode="DEVELOPMENT")

        assert os.environ["PYXLE_CASE_VAR"] == "lower"

    def test_tilde_in_project_root_expanded(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("PYXLE_TILDE_VAR", raising=False)
        self._write(tmp_path, ".env", "PYXLE_TILDE_VAR=expanded\n")

        # Replace ~ with the actual tmp_path prefix to test expansion
        monkeypatch.setenv("HOME", str(tmp_path))
        load_env_files(Path("~"), mode="development")

        assert os.environ["PYXLE_TILDE_VAR"] == "expanded"

    def test_result_loaded_count(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("PYXLE_A", raising=False)
        monkeypatch.delenv("PYXLE_B", raising=False)
        self._write(tmp_path, ".env", "PYXLE_A=1\nPYXLE_B=2\n")

        result = load_env_files(tmp_path, mode="development")

        assert result.loaded_count == 2

    def test_result_public_keys(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("PYXLE_PUBLIC_API_URL", raising=False)
        monkeypatch.delenv("PYXLE_SECRET_KEY", raising=False)
        self._write(tmp_path, ".env", "PYXLE_PUBLIC_API_URL=https://api.example.com\nPYXLE_SECRET_KEY=secret\n")

        result = load_env_files(tmp_path, mode="development")

        assert result.public_keys == ("PYXLE_PUBLIC_API_URL",)


# ---------------------------------------------------------------------------
# get_public_env_vars
# ---------------------------------------------------------------------------


class TestGetPublicEnvVars:
    def test_returns_only_public_prefixed(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("PYXLE_PUBLIC_URL", "https://example.com")
        monkeypatch.setenv("PYXLE_SECRET", "nope")
        monkeypatch.setenv("SOME_OTHER_VAR", "also_nope")

        public = get_public_env_vars()

        assert "PYXLE_PUBLIC_URL" in public
        assert "PYXLE_SECRET" not in public
        assert "SOME_OTHER_VAR" not in public

    def test_returns_empty_when_no_public_vars(self, monkeypatch: pytest.MonkeyPatch):
        # Clear any PYXLE_PUBLIC_ vars from the env for isolation
        for k in list(os.environ):
            if k.startswith("PYXLE_PUBLIC_"):
                monkeypatch.delenv(k)

        assert get_public_env_vars() == {}

    def test_values_match_current_env(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("PYXLE_PUBLIC_FOO", "bar")

        public = get_public_env_vars()

        assert public["PYXLE_PUBLIC_FOO"] == "bar"


# ---------------------------------------------------------------------------
# EnvLoadResult — dataclass properties
# ---------------------------------------------------------------------------


class TestEnvLoadResult:
    def test_loaded_count(self):
        r = EnvLoadResult(
            loaded=(("A", "1"), ("B", "2")),
            skipped=(),
            files_read=(),
        )
        assert r.loaded_count == 2

    def test_public_keys_filtered(self):
        r = EnvLoadResult(
            loaded=(("PYXLE_PUBLIC_URL", "x"), ("SECRET", "y"), ("PYXLE_PUBLIC_KEY", "z")),
            skipped=(),
            files_read=(),
        )
        assert set(r.public_keys) == {"PYXLE_PUBLIC_URL", "PYXLE_PUBLIC_KEY"}

    def test_empty_result(self):
        r = EnvLoadResult(loaded=(), skipped=(), files_read=())
        assert r.loaded_count == 0
        assert r.public_keys == ()
