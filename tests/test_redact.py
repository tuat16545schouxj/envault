"""Tests for envault.redact."""

from __future__ import annotations

import json
import os
import pytest

from envault.redact import (
    REDACT_PLACEHOLDER,
    RedactError,
    is_sensitive_key,
    redact_dict,
    redact_value,
    redact_vault,
)
from envault.vault import save_vault


# ---------------------------------------------------------------------------
# is_sensitive_key
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("key", [
    "DB_PASSWORD", "api_key", "SECRET_TOKEN", "PRIVATE_KEY",
    "AUTH_CREDENTIAL", "access_token", "my_secret",
])
def test_is_sensitive_key_true(key):
    assert is_sensitive_key(key) is True


@pytest.mark.parametrize("key", [
    "DATABASE_URL", "APP_ENV", "PORT", "LOG_LEVEL", "FEATURE_FLAG",
])
def test_is_sensitive_key_false(key):
    assert is_sensitive_key(key) is False


# ---------------------------------------------------------------------------
# redact_value
# ---------------------------------------------------------------------------

def test_redact_value_returns_placeholder():
    assert redact_value("super-secret") == REDACT_PLACEHOLDER


def test_redact_value_custom_mask():
    assert redact_value("super-secret", mask="[HIDDEN]") == "[HIDDEN]"


# ---------------------------------------------------------------------------
# redact_dict
# ---------------------------------------------------------------------------

def test_redact_dict_auto_redacts_sensitive_keys():
    variables = {"DB_PASSWORD": "hunter2", "APP_ENV": "production"}
    result = redact_dict(variables)
    assert result["DB_PASSWORD"] == REDACT_PLACEHOLDER
    assert result["APP_ENV"] == "production"


def test_redact_dict_explicit_keys():
    variables = {"APP_ENV": "staging", "CUSTOM": "value"}
    result = redact_dict(variables, keys=["CUSTOM"], auto=False)
    assert result["CUSTOM"] == REDACT_PLACEHOLDER
    assert result["APP_ENV"] == "staging"


def test_redact_dict_explicit_plus_auto():
    variables = {"DB_PASSWORD": "secret", "CUSTOM": "value", "APP_ENV": "dev"}
    result = redact_dict(variables, keys=["CUSTOM"], auto=True)
    assert result["DB_PASSWORD"] == REDACT_PLACEHOLDER
    assert result["CUSTOM"] == REDACT_PLACEHOLDER
    assert result["APP_ENV"] == "dev"


def test_redact_dict_auto_false_no_auto_redaction():
    variables = {"DB_PASSWORD": "secret"}
    result = redact_dict(variables, auto=False)
    assert result["DB_PASSWORD"] == "secret"


def test_redact_dict_empty():
    assert redact_dict({}) == {}


def test_redact_dict_custom_mask():
    variables = {"API_KEY": "abc123"}
    result = redact_dict(variables, mask="<redacted>")
    assert result["API_KEY"] == "<redacted>"


# ---------------------------------------------------------------------------
# redact_vault
# ---------------------------------------------------------------------------

@pytest.fixture()
def vault_file(tmp_path):
    path = str(tmp_path / "vault.enc")
    variables = {"DB_PASSWORD": "s3cr3t", "APP_ENV": "prod", "API_KEY": "key123"}
    save_vault(path, "mypassword", {"variables": variables})
    return path


def test_redact_vault_masks_sensitive(vault_file):
    result = redact_vault(vault_file, "mypassword")
    assert result["DB_PASSWORD"] == REDACT_PLACEHOLDER
    assert result["API_KEY"] == REDACT_PLACEHOLDER
    assert result["APP_ENV"] == "prod"


def test_redact_vault_wrong_password_raises(vault_file):
    with pytest.raises(RedactError):
        redact_vault(vault_file, "wrongpassword")


def test_redact_vault_missing_file_raises(tmp_path):
    with pytest.raises(RedactError):
        redact_vault(str(tmp_path / "nonexistent.enc"), "pass")
