"""Tests for envault.group."""

from __future__ import annotations

import pytest

from envault.group import (
    GroupError,
    add_to_group,
    create_group,
    delete_group,
    get_group_keys,
    list_groups,
    remove_from_group,
)
from envault.vault import save_vault


PASSWORD = "test-pass"


@pytest.fixture()
def vault_file(tmp_path):
    path = str(tmp_path / "vault.enc")
    save_vault(path, PASSWORD, {"DB_HOST": "localhost", "DB_PORT": "5432", "API_KEY": "secret"})
    return path


def test_create_group_new(vault_file):
    create_group(vault_file, PASSWORD, "database")
    assert "database" in list_groups(vault_file, PASSWORD)


def test_create_group_idempotent(vault_file):
    create_group(vault_file, PASSWORD, "database")
    create_group(vault_file, PASSWORD, "database")  # should not raise
    assert list_groups(vault_file, PASSWORD).count("database") == 1


def test_list_groups_empty(vault_file):
    assert list_groups(vault_file, PASSWORD) == []


def test_list_groups_sorted(vault_file):
    create_group(vault_file, PASSWORD, "zebra")
    create_group(vault_file, PASSWORD, "alpha")
    assert list_groups(vault_file, PASSWORD) == ["alpha", "zebra"]


def test_add_to_group_success(vault_file):
    add_to_group(vault_file, PASSWORD, "database", "DB_HOST")
    assert "DB_HOST" in get_group_keys(vault_file, PASSWORD, "database")


def test_add_to_group_creates_group_implicitly(vault_file):
    add_to_group(vault_file, PASSWORD, "newgroup", "API_KEY")
    assert "newgroup" in list_groups(vault_file, PASSWORD)


def test_add_to_group_missing_key_raises(vault_file):
    with pytest.raises(GroupError, match="not found"):
        add_to_group(vault_file, PASSWORD, "database", "NONEXISTENT")


def test_add_to_group_idempotent(vault_file):
    add_to_group(vault_file, PASSWORD, "database", "DB_HOST")
    add_to_group(vault_file, PASSWORD, "database", "DB_HOST")
    assert get_group_keys(vault_file, PASSWORD, "database").count("DB_HOST") == 1


def test_get_group_keys_sorted(vault_file):
    add_to_group(vault_file, PASSWORD, "database", "DB_PORT")
    add_to_group(vault_file, PASSWORD, "database", "DB_HOST")
    assert get_group_keys(vault_file, PASSWORD, "database") == ["DB_HOST", "DB_PORT"]


def test_get_group_keys_missing_group_raises(vault_file):
    with pytest.raises(GroupError, match="does not exist"):
        get_group_keys(vault_file, PASSWORD, "ghost")


def test_remove_from_group_success(vault_file):
    add_to_group(vault_file, PASSWORD, "database", "DB_HOST")
    remove_from_group(vault_file, PASSWORD, "database", "DB_HOST")
    assert get_group_keys(vault_file, PASSWORD, "database") == []


def test_remove_from_group_missing_group_raises(vault_file):
    with pytest.raises(GroupError, match="does not exist"):
        remove_from_group(vault_file, PASSWORD, "ghost", "DB_HOST")


def test_remove_from_group_missing_key_raises(vault_file):
    create_group(vault_file, PASSWORD, "database")
    with pytest.raises(GroupError, match="not in group"):
        remove_from_group(vault_file, PASSWORD, "database", "DB_HOST")


def test_delete_group_success(vault_file):
    create_group(vault_file, PASSWORD, "temp")
    delete_group(vault_file, PASSWORD, "temp")
    assert "temp" not in list_groups(vault_file, PASSWORD)


def test_delete_group_missing_raises(vault_file):
    with pytest.raises(GroupError, match="does not exist"):
        delete_group(vault_file, PASSWORD, "nope")
