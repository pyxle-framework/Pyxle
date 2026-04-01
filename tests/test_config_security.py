"""Tests for CORS and CSRF configuration parsing in pyxle.config."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pyxle.config import (
    ConfigError,
    CorsConfig,
    CsrfConfig,
    PyxleConfig,
    load_config,
)


# ---------------------------------------------------------------------------
# CorsConfig defaults
# ---------------------------------------------------------------------------


class TestCorsConfigDefaults:
    def test_default_not_enabled(self):
        config = CorsConfig()
        assert not config.enabled

    def test_enabled_when_origins_set(self):
        config = CorsConfig(origins=("http://localhost:3000",))
        assert config.enabled

    def test_default_methods(self):
        config = CorsConfig()
        assert "GET" in config.methods
        assert "POST" in config.methods

    def test_default_max_age(self):
        assert CorsConfig().max_age == 600


# ---------------------------------------------------------------------------
# CsrfConfig defaults
# ---------------------------------------------------------------------------


class TestCsrfConfigDefaults:
    def test_default_enabled(self):
        assert CsrfConfig().enabled is True

    def test_default_cookie_name(self):
        assert CsrfConfig().cookie_name == "pyxle-csrf"

    def test_default_samesite(self):
        assert CsrfConfig().cookie_samesite == "lax"


# ---------------------------------------------------------------------------
# Config JSON parsing — CORS
# ---------------------------------------------------------------------------


class TestCorsConfigParsing:
    def _load(self, tmp_path: Path, cors_data: dict) -> PyxleConfig:
        config_file = tmp_path / "pyxle.config.json"
        config_file.write_text(json.dumps({"cors": cors_data}))
        return load_config(tmp_path, config_path=config_file)

    def test_basic_origins(self, tmp_path: Path):
        config = self._load(tmp_path, {"origins": ["http://localhost:3000"]})
        assert config.cors.enabled
        assert config.cors.origins == ("http://localhost:3000",)

    def test_multiple_origins(self, tmp_path: Path):
        config = self._load(tmp_path, {
            "origins": ["http://localhost:3000", "https://example.com"]
        })
        assert len(config.cors.origins) == 2

    def test_custom_methods(self, tmp_path: Path):
        config = self._load(tmp_path, {
            "origins": ["*"],
            "methods": ["GET", "POST"],
        })
        assert config.cors.methods == ("GET", "POST")

    def test_credentials_flag(self, tmp_path: Path):
        config = self._load(tmp_path, {
            "origins": ["*"],
            "credentials": True,
        })
        assert config.cors.credentials is True

    def test_custom_max_age(self, tmp_path: Path):
        config = self._load(tmp_path, {
            "origins": ["*"],
            "maxAge": 3600,
        })
        assert config.cors.max_age == 3600

    def test_custom_headers(self, tmp_path: Path):
        config = self._load(tmp_path, {
            "origins": ["*"],
            "headers": ["Authorization", "Content-Type"],
        })
        assert config.cors.headers == ("Authorization", "Content-Type")

    def test_invalid_cors_type_raises(self, tmp_path: Path):
        config_file = tmp_path / "pyxle.config.json"
        config_file.write_text(json.dumps({"cors": "invalid"}))
        with pytest.raises(ConfigError, match="cors"):
            load_config(tmp_path, config_path=config_file)

    def test_invalid_credentials_type_raises(self, tmp_path: Path):
        config_file = tmp_path / "pyxle.config.json"
        config_file.write_text(json.dumps({"cors": {"credentials": "yes"}}))
        with pytest.raises(ConfigError, match="credentials"):
            load_config(tmp_path, config_path=config_file)

    def test_negative_max_age_raises(self, tmp_path: Path):
        config_file = tmp_path / "pyxle.config.json"
        config_file.write_text(json.dumps({"cors": {"maxAge": -1}}))
        with pytest.raises(ConfigError, match="maxAge"):
            load_config(tmp_path, config_path=config_file)

    def test_no_cors_block_returns_defaults(self, tmp_path: Path):
        config_file = tmp_path / "pyxle.config.json"
        config_file.write_text("{}")
        config = load_config(tmp_path, config_path=config_file)
        assert not config.cors.enabled


# ---------------------------------------------------------------------------
# Config JSON parsing — CSRF
# ---------------------------------------------------------------------------


class TestCsrfConfigParsing:
    def _load(self, tmp_path: Path, csrf_data) -> PyxleConfig:
        config_file = tmp_path / "pyxle.config.json"
        config_file.write_text(json.dumps({"csrf": csrf_data}))
        return load_config(tmp_path, config_path=config_file)

    def test_boolean_false_disables(self, tmp_path: Path):
        config = self._load(tmp_path, False)
        assert config.csrf.enabled is False

    def test_boolean_true_enables(self, tmp_path: Path):
        config = self._load(tmp_path, True)
        assert config.csrf.enabled is True

    def test_object_with_enabled_false(self, tmp_path: Path):
        config = self._load(tmp_path, {"enabled": False})
        assert config.csrf.enabled is False

    def test_custom_cookie_name(self, tmp_path: Path):
        config = self._load(tmp_path, {"cookieName": "my-csrf"})
        assert config.csrf.cookie_name == "my-csrf"

    def test_custom_header_name(self, tmp_path: Path):
        config = self._load(tmp_path, {"headerName": "x-my-token"})
        assert config.csrf.header_name == "x-my-token"

    def test_cookie_secure(self, tmp_path: Path):
        config = self._load(tmp_path, {"cookieSecure": True})
        assert config.csrf.cookie_secure is True

    def test_samesite_strict(self, tmp_path: Path):
        config = self._load(tmp_path, {"cookieSameSite": "strict"})
        assert config.csrf.cookie_samesite == "strict"

    def test_samesite_none(self, tmp_path: Path):
        config = self._load(tmp_path, {"cookieSameSite": "None"})
        assert config.csrf.cookie_samesite == "none"

    def test_invalid_samesite_raises(self, tmp_path: Path):
        config_file = tmp_path / "pyxle.config.json"
        config_file.write_text(json.dumps({"csrf": {"cookieSameSite": "invalid"}}))
        with pytest.raises(ConfigError, match="cookieSameSite"):
            load_config(tmp_path, config_path=config_file)

    def test_exempt_paths(self, tmp_path: Path):
        config = self._load(tmp_path, {"exemptPaths": ["/api/webhooks"]})
        assert config.csrf.exempt_paths == ("/api/webhooks",)

    def test_invalid_csrf_type_raises(self, tmp_path: Path):
        config_file = tmp_path / "pyxle.config.json"
        config_file.write_text(json.dumps({"csrf": 42}))
        with pytest.raises(ConfigError, match="csrf"):
            load_config(tmp_path, config_path=config_file)

    def test_invalid_enabled_type_raises(self, tmp_path: Path):
        config_file = tmp_path / "pyxle.config.json"
        config_file.write_text(json.dumps({"csrf": {"enabled": "yes"}}))
        with pytest.raises(ConfigError, match="csrf.enabled"):
            load_config(tmp_path, config_path=config_file)

    def test_empty_cookie_name_raises(self, tmp_path: Path):
        config_file = tmp_path / "pyxle.config.json"
        config_file.write_text(json.dumps({"csrf": {"cookieName": ""}}))
        with pytest.raises(ConfigError, match="cookieName"):
            load_config(tmp_path, config_path=config_file)

    def test_no_csrf_block_returns_defaults(self, tmp_path: Path):
        config_file = tmp_path / "pyxle.config.json"
        config_file.write_text("{}")
        config = load_config(tmp_path, config_path=config_file)
        assert config.csrf.enabled is True


# ---------------------------------------------------------------------------
# Config passes CORS/CSRF to devserver kwargs
# ---------------------------------------------------------------------------


class TestDevserverKwargs:
    def test_to_devserver_kwargs_includes_cors(self):
        config = PyxleConfig(cors=CorsConfig(origins=("*",)))
        kwargs = config.to_devserver_kwargs()
        assert kwargs["cors"].origins == ("*",)

    def test_to_devserver_kwargs_includes_csrf(self):
        config = PyxleConfig(csrf=CsrfConfig(enabled=False))
        kwargs = config.to_devserver_kwargs()
        assert kwargs["csrf"].enabled is False
