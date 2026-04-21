"""Tests for envault.rename."""

from __future__ import annotations

import pytest

from envault.rename import RenameError, rename_var
from envault.vault import VaultError, load_vault, save_vault, set_var


@pytest.fixture()
def vault_file(tmp_path):
    """Return a path to a temporary vault pre-populated with two variables."""
    path = str(tmp_path / "vault.env")
    set_var(path, "secret", "DB_HOST", "localhost")
    set_var(path, "secret", "DB_PORT", "5432")
    return path


def test_rename_key_success(vault_file):
    rename_var(vault_file, "secret", "DB_HOST", "DATABASE_HOST")
    data = load_vault(vault_file, "secret")
    assert "DATABASE_HOST" in data["variables"]
    assert "DB_HOST" not in data["variables"]
    assert data["variables"]["DATABASE_HOST"] == "localhost"


def test_rename_preserves_value(vault_file):
    rename_var(vault_file, "secret", "DB_PORT", "DATABASE_PORT")
    data = load_vault(vault_file, "secret")
    assert data["variables"]["DATABASE_PORT"] == "5432"


def test_rename_preserves_other_keys(vault_file):
    rename_var(vault_file, "secret", "DB_HOST", "DATABASE_HOST")
    data = load_vault(vault_file, "secret")
    assert "DB_PORT" in data["variables"]


def test_rename_missing_key_raises(vault_file):
    with pytest.raises(RenameError, match="not found"):
        rename_var(vault_file, "secret", "NONEXISTENT", "NEW_KEY")


def test_rename_same_key_raises(vault_file):
    with pytest.raises(RenameError, match="identical"):
        rename_var(vault_file, "secret", "DB_HOST", "DB_HOST")


def test_rename_empty_old_key_raises(vault_file):
    with pytest.raises(RenameError, match="old_key must not be empty"):
        rename_var(vault_file, "secret", "", "NEW_KEY")


def test_rename_empty_new_key_raises(vault_file):
    with pytest.raises(RenameError, match="new_key must not be empty"):
        rename_var(vault_file, "secret", "DB_HOST", "")


def test_rename_existing_new_key_raises_without_overwrite(vault_file):
    with pytest.raises(RenameError, match="already exists"):
        rename_var(vault_file, "secret", "DB_HOST", "DB_PORT")


def test_rename_existing_new_key_succeeds_with_overwrite(vault_file):
    rename_var(vault_file, "secret", "DB_HOST", "DB_PORT", overwrite=True)
    data = load_vault(vault_file, "secret")
    assert data["variables"]["DB_PORT"] == "localhost"
    assert "DB_HOST" not in data["variables"]


def test_rename_wrong_password_raises(vault_file):
    with pytest.raises(VaultError):
        rename_var(vault_file, "wrong_password", "DB_HOST", "DATABASE_HOST")
