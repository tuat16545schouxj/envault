"""Tests for envault.schema."""
from __future__ import annotations

import pytest

from envault.schema import SchemaError, SchemaRule, SchemaViolation, validate_schema
from envault.vault import save_vault


@pytest.fixture()
def vault_file(tmp_path):
    path = str(tmp_path / "vault.env")
    data = {
        "variables": {
            "DATABASE_URL": "postgres://localhost/mydb",
            "SECRET_KEY": "supersecret123",
            "ENV": "production",
            "PORT": "8080",
        }
    }
    save_vault(path, "password", data)
    return path


def test_no_violations_when_all_rules_pass(vault_file):
    rules = [
        SchemaRule(key="DATABASE_URL"),
        SchemaRule(key="SECRET_KEY"),
    ]
    violations = validate_schema(vault_file, "password", rules)
    assert violations == []


def test_required_key_missing_raises_violation(vault_file):
    rules = [SchemaRule(key="MISSING_KEY", required=True)]
    violations = validate_schema(vault_file, "password", rules)
    assert len(violations) == 1
    v = violations[0]
    assert v.key == "MISSING_KEY"
    assert v.rule == "required"


def test_optional_missing_key_no_violation(vault_file):
    rules = [SchemaRule(key="MISSING_KEY", required=False)]
    violations = validate_schema(vault_file, "password", rules)
    assert violations == []


def test_min_length_violation(vault_file):
    rules = [SchemaRule(key="PORT", min_length=10)]
    violations = validate_schema(vault_file, "password", rules)
    assert len(violations) == 1
    assert violations[0].rule == "min_length"
    assert "PORT" in violations[0].message


def test_max_length_violation(vault_file):
    rules = [SchemaRule(key="DATABASE_URL", max_length=5)]
    violations = validate_schema(vault_file, "password", rules)
    assert len(violations) == 1
    assert violations[0].rule == "max_length"


def test_pattern_violation(vault_file):
    rules = [SchemaRule(key="PORT", pattern=r"[a-z]+")]
    violations = validate_schema(vault_file, "password", rules)
    assert len(violations) == 1
    assert violations[0].rule == "pattern"


def test_pattern_passes(vault_file):
    rules = [SchemaRule(key="PORT", pattern=r"\d+")]
    violations = validate_schema(vault_file, "password", rules)
    assert violations == []


def test_allowed_values_violation(vault_file):
    rules = [SchemaRule(key="ENV", allowed_values=["staging", "development"])]
    violations = validate_schema(vault_file, "password", rules)
    assert len(violations) == 1
    assert violations[0].rule == "allowed_values"


def test_allowed_values_passes(vault_file):
    rules = [SchemaRule(key="ENV", allowed_values=["production", "staging"])]
    violations = validate_schema(vault_file, "password", rules)
    assert violations == []


def test_multiple_violations_same_key(vault_file):
    rules = [SchemaRule(key="PORT", min_length=10, pattern=r"[a-z]+")]
    violations = validate_schema(vault_file, "password", rules)
    assert len(violations) == 2
    rules_hit = {v.rule for v in violations}
    assert rules_hit == {"min_length", "pattern"}


def test_wrong_password_raises_schema_error(vault_file):
    rules = [SchemaRule(key="DATABASE_URL")]
    with pytest.raises(SchemaError, match="Could not load vault"):
        validate_schema(vault_file, "wrongpassword", rules)


def test_to_dict_schema_violation():
    v = SchemaViolation(key="FOO", rule="required", message="FOO is required.")
    d = v.to_dict()
    assert d == {"key": "FOO", "rule": "required", "message": "FOO is required."}


def test_to_dict_schema_rule():
    rule = SchemaRule(key="FOO", required=True, pattern=r"\w+", min_length=2)
    d = rule.to_dict()
    assert d["key"] == "FOO"
    assert d["pattern"] == r"\w+"
    assert d["min_length"] == 2
    assert d["allowed_values"] is None
