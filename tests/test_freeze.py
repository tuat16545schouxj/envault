"""Tests for envault.freeze."""

from __future__ import annotations

import pytest

from envault.vault import save_vault
from envault.freeze import (
    FreezeError,
    assert_not_frozen,
    freeze_var,
    is_frozen,
    list_frozen,
    unfreeze_var,
)

PASSWORD = "test-secret"


@pytest.fixture()
def vault_file(tmp_path):
    path = str(tmp_path / "vault.enc")
    save_vault(path, PASSWORD, {"variables": {"API_KEY": "abc", "DB_URL": "postgres://"}})
    return path


def test_freeze_var_success(vault_file):
    freeze_var(vault_file, PASSWORD, "API_KEY")
    assert is_frozen(vault_file, PASSWORD, "API_KEY")


def test_freeze_var_missing_key_raises(vault_file):
    with pytest.raises(FreezeError, match="does not exist"):
        freeze_var(vault_file, PASSWORD, "NONEXISTENT")


def test_freeze_var_idempotent(vault_file):
    freeze_var(vault_file, PASSWORD, "API_KEY")
    freeze_var(vault_file, PASSWORD, "API_KEY")  # should not raise
    assert list_frozen(vault_file, PASSWORD) == ["API_KEY"]


def test_unfreeze_var_success(vault_file):
    freeze_var(vault_file, PASSWORD, "API_KEY")
    unfreeze_var(vault_file, PASSWORD, "API_KEY")
    assert not is_frozen(vault_file, PASSWORD, "API_KEY")


def test_unfreeze_var_not_frozen_raises(vault_file):
    with pytest.raises(FreezeError, match="is not frozen"):
        unfreeze_var(vault_file, PASSWORD, "API_KEY")


def test_list_frozen_empty(vault_file):
    assert list_frozen(vault_file, PASSWORD) == []


def test_list_frozen_returns_sorted(vault_file):
    freeze_var(vault_file, PASSWORD, "DB_URL")
    freeze_var(vault_file, PASSWORD, "API_KEY")
    assert list_frozen(vault_file, PASSWORD) == ["API_KEY", "DB_URL"]


def test_is_frozen_false_before_freeze(vault_file):
    assert not is_frozen(vault_file, PASSWORD, "API_KEY")


def test_is_frozen_true_after_freeze(vault_file):
    freeze_var(vault_file, PASSWORD, "DB_URL")
    assert is_frozen(vault_file, PASSWORD, "DB_URL")
    assert not is_frozen(vault_file, PASSWORD, "API_KEY")


def test_assert_not_frozen_raises_when_frozen(vault_file):
    freeze_var(vault_file, PASSWORD, "API_KEY")
    with pytest.raises(FreezeError, match="frozen"):
        assert_not_frozen(vault_file, PASSWORD, "API_KEY")


def test_assert_not_frozen_passes_when_not_frozen(vault_file):
    assert_not_frozen(vault_file, PASSWORD, "API_KEY")  # should not raise
