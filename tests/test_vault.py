"""Tests for envault.vault module."""

import os
import pytest

from envault.vault import (
    load_vault,
    save_vault,
    set_var,
    delete_var,
    export_to_env,
    VaultError,
)

PASSWORD = "test-password-123"
SAMPLE_DATA = {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET_KEY": "s3cr3t"}


@pytest.fixture
def vault_file(tmp_path):
    """Return a temporary vault file path."""
    return str(tmp_path / ".envault")


def test_save_and_load_roundtrip(vault_file):
    save_vault(SAMPLE_DATA, PASSWORD, vault_file)
    loaded = load_vault(PASSWORD, vault_file)
    assert loaded == SAMPLE_DATA


def test_load_vault_file_not_found(tmp_path):
    with pytest.raises(VaultError, match="Vault file not found"):
        load_vault(PASSWORD, str(tmp_path / "nonexistent.envault"))


def test_load_vault_wrong_password(vault_file):
    save_vault(SAMPLE_DATA, PASSWORD, vault_file)
    with pytest.raises(VaultError, match="Failed to load vault"):
        load_vault("wrong-password", vault_file)


def test_set_var_creates_vault_if_missing(vault_file):
    set_var("NEW_KEY", "new_value", PASSWORD, vault_file)
    loaded = load_vault(PASSWORD, vault_file)
    assert loaded == {"NEW_KEY": "new_value"}


def test_set_var_updates_existing_key(vault_file):
    save_vault(SAMPLE_DATA, PASSWORD, vault_file)
    set_var("DB_HOST", "remotehost", PASSWORD, vault_file)
    loaded = load_vault(PASSWORD, vault_file)
    assert loaded["DB_HOST"] == "remotehost"
    assert loaded["DB_PORT"] == "5432"  # other keys intact


def test_delete_var_removes_key(vault_file):
    save_vault(SAMPLE_DATA, PASSWORD, vault_file)
    delete_var("DB_PORT", PASSWORD, vault_file)
    loaded = load_vault(PASSWORD, vault_file)
    assert "DB_PORT" not in loaded
    assert "DB_HOST" in loaded


def test_delete_var_missing_key_raises(vault_file):
    save_vault(SAMPLE_DATA, PASSWORD, vault_file)
    with pytest.raises(VaultError, match="not found in vault"):
        delete_var("NONEXISTENT", PASSWORD, vault_file)


def test_export_to_env_sets_os_environ(vault_file):
    save_vault(SAMPLE_DATA, PASSWORD, vault_file)
    exported = export_to_env(PASSWORD, vault_file)
    assert exported == SAMPLE_DATA
    for key, value in SAMPLE_DATA.items():
        assert os.environ.get(key) == value


def test_vault_file_is_not_plaintext(vault_file):
    save_vault(SAMPLE_DATA, PASSWORD, vault_file)
    raw = open(vault_file).read()
    for value in SAMPLE_DATA.values():
        assert value not in raw, "Vault file should not contain plaintext values"
