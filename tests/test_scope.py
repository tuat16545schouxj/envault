"""Tests for envault.scope."""

from __future__ import annotations

import pytest

from envault.scope import (
    ScopeError,
    assign_scope,
    get_keys_for_scope,
    list_scopes,
    remove_scope,
)
from envault.vault import save_vault


@pytest.fixture()
def vault_file(tmp_path):
    path = str(tmp_path / "vault.enc")
    data = {"vars": {"API_KEY": "secret", "DB_URL": "postgres://localhost", "TOKEN": "abc"}}
    save_vault(path, "pass", data)
    return path


def test_assign_scope_success(vault_file):
    assign_scope(vault_file, "pass", "API_KEY", "prod")
    scopes = list_scopes(vault_file, "pass")
    assert "prod" in scopes["API_KEY"]


def test_assign_scope_idempotent(vault_file):
    assign_scope(vault_file, "pass", "API_KEY", "dev")
    assign_scope(vault_file, "pass", "API_KEY", "dev")
    scopes = list_scopes(vault_file, "pass")
    assert scopes["API_KEY"].count("dev") == 1


def test_assign_scope_missing_key_raises(vault_file):
    with pytest.raises(ScopeError, match="does not exist"):
        assign_scope(vault_file, "pass", "MISSING", "dev")


def test_assign_scope_empty_scope_raises(vault_file):
    with pytest.raises(ScopeError, match="must not be empty"):
        assign_scope(vault_file, "pass", "API_KEY", "   ")


def test_assign_scope_normalises_to_lowercase(vault_file):
    assign_scope(vault_file, "pass", "API_KEY", "PROD")
    scopes = list_scopes(vault_file, "pass")
    assert "prod" in scopes["API_KEY"]
    assert "PROD" not in scopes["API_KEY"]


def test_remove_scope_success(vault_file):
    assign_scope(vault_file, "pass", "API_KEY", "staging")
    remove_scope(vault_file, "pass", "API_KEY", "staging")
    scopes = list_scopes(vault_file, "pass")
    assert scopes.get("API_KEY", []) == []


def test_remove_scope_not_assigned_raises(vault_file):
    with pytest.raises(ScopeError, match="not assigned to scope"):
        remove_scope(vault_file, "pass", "API_KEY", "prod")


def test_list_scopes_empty_vault(vault_file):
    assert list_scopes(vault_file, "pass") == {}


def test_list_scopes_multiple_keys(vault_file):
    assign_scope(vault_file, "pass", "API_KEY", "prod")
    assign_scope(vault_file, "pass", "DB_URL", "prod")
    assign_scope(vault_file, "pass", "DB_URL", "staging")
    scopes = list_scopes(vault_file, "pass")
    assert set(scopes.keys()) == {"API_KEY", "DB_URL"}
    assert scopes["DB_URL"] == ["prod", "staging"]


def test_get_keys_for_scope_returns_sorted(vault_file):
    assign_scope(vault_file, "pass", "TOKEN", "dev")
    assign_scope(vault_file, "pass", "API_KEY", "dev")
    keys = get_keys_for_scope(vault_file, "pass", "dev")
    assert keys == ["API_KEY", "TOKEN"]


def test_get_keys_for_scope_empty_when_none(vault_file):
    keys = get_keys_for_scope(vault_file, "pass", "prod")
    assert keys == []
