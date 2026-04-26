"""Tests for envault.env_validate."""
from __future__ import annotations

import json
import os
import pytest

from envault.vault import save_vault
from envault.env_validate import (
    EnvValidateError,
    ValidationResult,
    list_rules,
    validate_value,
    validate_vault,
)

PASSWORD = "test-secret"


@pytest.fixture()
def vault_file(tmp_path):
    path = str(tmp_path / "vault.env")
    data = {
        "DATABASE_URL": "https://db.example.com/mydb",
        "MAX_RETRIES": "5",
        "DEBUG": "true",
        "API_KEY": "abc123XYZ",
        "CONTACT_EMAIL": "admin@example.com",
        "EMPTY_VAR": "",
    }
    save_vault(path, PASSWORD, data)
    return path


def test_list_rules_returns_sorted_list():
    rules = list_rules()
    assert isinstance(rules, list)
    assert rules == sorted(rules)
    assert "url" in rules
    assert "integer" in rules


def test_validate_value_url_pass():
    passed, _ = validate_value("https://example.com", "url")
    assert passed is True


def test_validate_value_url_fail():
    passed, msg = validate_value("not-a-url", "url")
    assert passed is False
    assert "URL" in msg


def test_validate_value_integer_pass():
    passed, _ = validate_value("-42", "integer")
    assert passed is True


def test_validate_value_integer_fail():
    passed, _ = validate_value("3.14", "integer")
    assert passed is False


def test_validate_value_boolean():
    for val in ("true", "false", "1", "0", "True", "FALSE"):
        passed, _ = validate_value(val, "boolean")
        assert passed is True
    passed, _ = validate_value("yes", "boolean")
    assert passed is False


def test_validate_value_custom_pattern_pass():
    passed, msg = validate_value("v1.2.3", "nonempty", pattern=r"v\d+\.\d+\.\d+")
    assert passed is True


def test_validate_value_custom_pattern_fail():
    passed, msg = validate_value("1.2.3", "nonempty", pattern=r"v\d+\.\d+\.\d+")
    assert passed is False
    assert "pattern" in msg


def test_validate_value_invalid_pattern_raises():
    with pytest.raises(EnvValidateError, match="Invalid regex"):
        validate_value("value", "nonempty", pattern=r"[invalid")


def test_validate_value_unknown_rule_raises():
    with pytest.raises(EnvValidateError, match="Unknown rule"):
        validate_value("value", "nonexistent_rule")


def test_validate_vault_all_pass(vault_file):
    rules = {
        "DATABASE_URL": {"rule": "url"},
        "MAX_RETRIES": {"rule": "integer"},
        "DEBUG": {"rule": "boolean"},
    }
    results = validate_vault(vault_file, PASSWORD, rules)
    assert all(r.passed for r in results)
    assert len(results) == 3


def test_validate_vault_missing_key(vault_file):
    rules = {"MISSING_KEY": {"rule": "nonempty"}}
    results = validate_vault(vault_file, PASSWORD, rules)
    assert len(results) == 1
    assert results[0].passed is False
    assert "not found" in results[0].message


def test_validate_vault_empty_value_fails_nonempty(vault_file):
    rules = {"EMPTY_VAR": {"rule": "nonempty"}}
    results = validate_vault(vault_file, PASSWORD, rules)
    assert results[0].passed is False


def test_validate_vault_custom_pattern(vault_file):
    rules = {"API_KEY": {"rule": "alphanumeric", "pattern": r"[a-zA-Z0-9]{9}"}}
    results = validate_vault(vault_file, PASSWORD, rules)
    assert results[0].passed is True


def test_validate_vault_missing_file_raises(tmp_path):
    with pytest.raises(EnvValidateError, match="Vault not found"):
        validate_vault(str(tmp_path / "no.env"), PASSWORD, {"KEY": {"rule": "nonempty"}})


def test_validation_result_to_dict():
    r = ValidationResult(key="FOO", passed=True, rule="integer", message="ok")
    d = r.to_dict()
    assert d["key"] == "FOO"
    assert d["passed"] is True
    assert d["rule"] == "integer"
    assert d["message"] == "ok"
