"""Tests for pyxle.devserver._security — shared security utilities."""

import pytest

from pyxle.devserver._security import (
    SAFE_IDENTIFIER_RE,
    redact_sensitive_patterns,
    validate_python_module_path,
)


class TestSafeIdentifierRe:
    """SAFE_IDENTIFIER_RE accepts valid Python/JS identifiers only."""

    @pytest.mark.parametrize(
        "name",
        [
            "foo",
            "_bar",
            "PYXLE_PUBLIC_API_URL",
            "a1",
            "_",
            "CamelCase",
            "x" * 200,
        ],
    )
    def test_valid_identifiers(self, name: str):
        assert SAFE_IDENTIFIER_RE.match(name)

    @pytest.mark.parametrize(
        "name",
        [
            "",
            "1starts_with_digit",
            "has-hyphen",
            "has.dot",
            "has space",
            "has/slash",
            "a'inject",
            "a+b",
            "PYXLE_PUBLIC_X'+console.log(1)+'",
        ],
    )
    def test_invalid_identifiers(self, name: str):
        assert not SAFE_IDENTIFIER_RE.match(name)


class TestValidatePythonModulePath:
    """validate_python_module_path accepts dotted Python import paths."""

    @pytest.mark.parametrize(
        "spec",
        [
            "mypackage",
            "my_package.middleware",
            "a.b.c.d.e",
            "starlette.middleware.cors",
            "_private.module",
        ],
    )
    def test_valid_paths(self, spec: str):
        assert validate_python_module_path(spec) is True

    @pytest.mark.parametrize(
        "spec",
        [
            "",
            ".",
            ".leading_dot",
            "trailing_dot.",
            "double..dot",
            "has/slash",
            "has-hyphen",
            "1digit_start",
            "has space",
            "os;import('evil')",
            "../etc/passwd",
        ],
    )
    def test_invalid_paths(self, spec: str):
        assert validate_python_module_path(spec) is False


class TestRedactSensitivePatterns:
    """redact_sensitive_patterns masks common secret patterns."""

    def test_postgres_dsn(self):
        text = "DSN=postgres://user:secretpass@db.host:5432/mydb"
        result = redact_sensitive_patterns(text)
        assert "secretpass" not in result
        assert "[REDACTED_DSN]" in result

    def test_mysql_dsn(self):
        text = "mysql://root:password123@localhost/app"
        result = redact_sensitive_patterns(text)
        assert "password123" not in result
        assert "[REDACTED_DSN]" in result

    def test_mongodb_dsn(self):
        text = "Error: mongodb://admin:p4ss@cluster0.mongodb.net/test"
        result = redact_sensitive_patterns(text)
        assert "p4ss" not in result

    def test_redis_dsn(self):
        text = "redis://default:mytoken@redis-host:6379"
        result = redact_sensitive_patterns(text)
        assert "mytoken" not in result

    def test_password_equals(self):
        text = "Connection failed: password=hunter2 host=db"
        result = redact_sensitive_patterns(text)
        assert "hunter2" not in result
        assert "password=[REDACTED]" in result

    def test_password_colon(self):
        text = "password: s3cret123"
        result = redact_sensitive_patterns(text)
        assert "s3cret123" not in result

    def test_bearer_token(self):
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.payload.sig"
        result = redact_sensitive_patterns(text)
        assert "eyJhbGciOiJIUzI1NiJ9" not in result
        assert "Bearer [REDACTED]" in result

    def test_aws_secret_key(self):
        text = "AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        result = redact_sensitive_patterns(text)
        assert "wJalrXUtnFEMI" not in result
        assert "[REDACTED_AWS]" in result

    def test_generic_secret(self):
        text = "secret=abc123def456"
        result = redact_sensitive_patterns(text)
        assert "abc123def456" not in result

    def test_generic_api_key(self):
        text = "api_key=sk-proj-abcdef123456"
        result = redact_sensitive_patterns(text)
        assert "sk-proj-abcdef123456" not in result

    def test_safe_text_unchanged(self):
        text = "Component 'Button' failed to render: missing prop 'label'"
        assert redact_sensitive_patterns(text) == text

    def test_empty_string(self):
        assert redact_sensitive_patterns("") == ""

    def test_multiple_patterns(self):
        text = (
            "Error: postgres://u:p@h/db failed. "
            "Bearer tok123 rejected. password=x"
        )
        result = redact_sensitive_patterns(text)
        assert "p@h/db" not in result
        assert "tok123" not in result
        assert "password=x" not in result

    def test_case_insensitive(self):
        text = "PASSWORD=secret123"
        result = redact_sensitive_patterns(text)
        assert "secret123" not in result
