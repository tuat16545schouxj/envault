"""Tests for envault.namespace module."""

from __future__ import annotations

import pytest

from envault.namespace import (
    NamespaceError,
    delete_namespace,
    get_namespace_vars,
    list_namespaces,
    move_to_namespace,
)
from envault.vault import save_vault

PASSWORD = "testpassword"


@pytest.fixture()
def vault_file(tmp_path):
    path = str(tmp_path / "vault.env")
    data = {
        "variables": {
            "DB_HOST": "localhost",
            "DB_PORT": "5432",
            "APP__SECRET": "abc123",
            "APP__DEBUG": "true",
            "PLAIN_KEY": "plain_value",
        }
    }
    save_vault(path, PASSWORD, data)
    return path


def test_list_namespaces_returns_sorted(vault_file):
    ns = list_namespaces(vault_file, PASSWORD)
    assert ns == ["APP"]


def test_list_namespaces_empty_vault(tmp_path):
    path = str(tmp_path / "empty.env")
    save_vault(path, PASSWORD, {"variables": {}})
    ns = list_namespaces(path, PASSWORD)
    assert ns == []


def test_list_namespaces_multiple(tmp_path):
    path = str(tmp_path / "vault.env")
    save_vault(path, PASSWORD, {
        "variables": {
            "PROD__KEY": "v1",
            "DEV__KEY": "v2",
            "DEV__OTHER": "v3",
        }
    })
    ns = list_namespaces(path, PASSWORD)
    assert ns == ["DEV", "PROD"]


def test_get_namespace_vars_returns_stripped_keys(vault_file):
    result = get_namespace_vars(vault_file, PASSWORD, "APP")
    assert result == {"SECRET": "abc123", "DEBUG": "true"}


def test_get_namespace_vars_empty_for_unknown_ns(vault_file):
    result = get_namespace_vars(vault_file, PASSWORD, "UNKNOWN")
    assert result == {}


def test_move_to_namespace_specific_keys(vault_file):
    moved = move_to_namespace(vault_file, PASSWORD, "DB", keys=["DB_HOST", "DB_PORT"])
    assert sorted(moved) == ["DB__DB_HOST", "DB__DB_PORT"]
    result = get_namespace_vars(vault_file, PASSWORD, "DB")
    assert result == {"DB_HOST": "localhost", "DB_PORT": "5432"}


def test_move_to_namespace_all_plain_keys(vault_file):
    moved = move_to_namespace(vault_file, PASSWORD, "NS")
    # Only keys without "__" are moved: DB_HOST, DB_PORT, PLAIN_KEY
    assert len(moved) == 3
    assert all(k.startswith("NS__") for k in moved)


def test_move_to_namespace_missing_key_raises(vault_file):
    with pytest.raises(NamespaceError, match="not found"):
        move_to_namespace(vault_file, PASSWORD, "X", keys=["MISSING_KEY"])


def test_move_to_namespace_overwrite_false_raises(vault_file):
    # APP__SECRET already exists
    with pytest.raises(NamespaceError, match="already exists"):
        move_to_namespace(vault_file, PASSWORD, "APP", keys=["SECRET"], overwrite=False)


def test_delete_namespace_removes_keys(vault_file):
    count = delete_namespace(vault_file, PASSWORD, "APP")
    assert count == 2
    remaining = get_namespace_vars(vault_file, PASSWORD, "APP")
    assert remaining == {}


def test_delete_namespace_unknown_returns_zero(vault_file):
    count = delete_namespace(vault_file, PASSWORD, "NOPE")
    assert count == 0


def test_empty_namespace_name_raises():
    with pytest.raises(NamespaceError, match="empty"):
        get_namespace_vars("any", PASSWORD, "")
