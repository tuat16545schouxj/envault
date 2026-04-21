"""Tests for envault.alias."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.vault import save_vault
from envault.alias import (
    AliasError,
    set_alias,
    remove_alias,
    resolve_alias,
    list_aliases,
)

PASSWORD = "test-secret"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    path = tmp_path / "vault.enc"
    save_vault(path, PASSWORD, {"variables": {"DB_HOST": "localhost", "DB_PORT": "5432"}})
    return path


def test_set_alias_success(vault_file: Path) -> None:
    set_alias(vault_file, PASSWORD, "db", "DB_HOST")
    assert resolve_alias(vault_file, PASSWORD, "db") == "DB_HOST"


def test_set_alias_missing_key_raises(vault_file: Path) -> None:
    with pytest.raises(AliasError, match="not found in vault"):
        set_alias(vault_file, PASSWORD, "missing", "NONEXISTENT_KEY")


def test_set_alias_overwrites_existing(vault_file: Path) -> None:
    set_alias(vault_file, PASSWORD, "db", "DB_HOST")
    set_alias(vault_file, PASSWORD, "db", "DB_PORT")
    assert resolve_alias(vault_file, PASSWORD, "db") == "DB_PORT"


def test_remove_alias_success(vault_file: Path) -> None:
    set_alias(vault_file, PASSWORD, "host", "DB_HOST")
    remove_alias(vault_file, PASSWORD, "host")
    with pytest.raises(AliasError):
        resolve_alias(vault_file, PASSWORD, "host")


def test_remove_alias_not_found_raises(vault_file: Path) -> None:
    with pytest.raises(AliasError, match="not found"):
        remove_alias(vault_file, PASSWORD, "ghost")


def test_resolve_alias_not_found_raises(vault_file: Path) -> None:
    with pytest.raises(AliasError, match="not found"):
        resolve_alias(vault_file, PASSWORD, "nope")


def test_list_aliases_empty(vault_file: Path) -> None:
    assert list_aliases(vault_file, PASSWORD) == {}


def test_list_aliases_sorted(vault_file: Path) -> None:
    set_alias(vault_file, PASSWORD, "z_alias", "DB_PORT")
    set_alias(vault_file, PASSWORD, "a_alias", "DB_HOST")
    result = list_aliases(vault_file, PASSWORD)
    assert list(result.keys()) == ["a_alias", "z_alias"]
    assert result["a_alias"] == "DB_HOST"
    assert result["z_alias"] == "DB_PORT"


def test_list_aliases_returns_all(vault_file: Path) -> None:
    set_alias(vault_file, PASSWORD, "host", "DB_HOST")
    set_alias(vault_file, PASSWORD, "port", "DB_PORT")
    result = list_aliases(vault_file, PASSWORD)
    assert len(result) == 2
