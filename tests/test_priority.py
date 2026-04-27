"""Tests for envault.priority."""
from __future__ import annotations

import pytest

from envault.priority import (
    DEFAULT_PRIORITY,
    PriorityError,
    get_priority,
    list_priorities,
    remove_priority,
    set_priority,
    sorted_by_priority,
)
from envault.vault import save_vault


@pytest.fixture()
def vault_file(tmp_path):
    path = tmp_path / "vault.env"
    data = {"vars": {"ALPHA": "1", "BETA": "2", "GAMMA": "3"}}
    save_vault(str(path), "secret", data)
    return str(path)


def test_set_priority_success(vault_file):
    set_priority(vault_file, "secret", "ALPHA", 10)
    assert get_priority(vault_file, "secret", "ALPHA") == 10


def test_set_priority_missing_key_raises(vault_file):
    with pytest.raises(PriorityError, match="not found"):
        set_priority(vault_file, "secret", "MISSING", 5)


def test_get_priority_default_when_not_set(vault_file):
    assert get_priority(vault_file, "secret", "BETA") == DEFAULT_PRIORITY


def test_set_priority_overwrites_existing(vault_file):
    set_priority(vault_file, "secret", "ALPHA", 5)
    set_priority(vault_file, "secret", "ALPHA", 99)
    assert get_priority(vault_file, "secret", "ALPHA") == 99


def test_remove_priority_success(vault_file):
    set_priority(vault_file, "secret", "ALPHA", 10)
    remove_priority(vault_file, "secret", "ALPHA")
    assert get_priority(vault_file, "secret", "ALPHA") == DEFAULT_PRIORITY


def test_remove_priority_not_set_raises(vault_file):
    with pytest.raises(PriorityError, match="no explicit priority"):
        remove_priority(vault_file, "secret", "BETA")


def test_list_priorities_empty(vault_file):
    assert list_priorities(vault_file, "secret") == []


def test_list_priorities_sorted_by_level_desc(vault_file):
    set_priority(vault_file, "secret", "ALPHA", 1)
    set_priority(vault_file, "secret", "BETA", 5)
    set_priority(vault_file, "secret", "GAMMA", 3)
    entries = list_priorities(vault_file, "secret")
    levels = [e["priority"] for e in entries]
    assert levels == sorted(levels, reverse=True)


def test_list_priorities_tiebreak_by_key(vault_file):
    set_priority(vault_file, "secret", "GAMMA", 5)
    set_priority(vault_file, "secret", "ALPHA", 5)
    entries = list_priorities(vault_file, "secret")
    keys = [e["key"] for e in entries]
    assert keys == ["ALPHA", "GAMMA"]


def test_sorted_by_priority_high_first(vault_file):
    set_priority(vault_file, "secret", "GAMMA", 10)
    set_priority(vault_file, "secret", "ALPHA", 5)
    keys = sorted_by_priority(vault_file, "secret")
    assert keys[0] == "GAMMA"
    assert keys[1] == "ALPHA"


def test_sorted_by_priority_unset_keys_last(vault_file):
    set_priority(vault_file, "secret", "ALPHA", 1)
    keys = sorted_by_priority(vault_file, "secret")
    assert keys[0] == "ALPHA"
    # BETA and GAMMA have default priority 0, come after ALPHA
    assert set(keys[1:]) == {"BETA", "GAMMA"}
