"""Tests for envault.lifecycle."""

from __future__ import annotations

import pytest

from envault.vault import save_vault
from envault.lifecycle import (
    LifecycleError,
    set_hook,
    remove_hook,
    list_hooks,
    get_hook,
    LIFECYCLE_KEY,
)


@pytest.fixture()
def vault_file(tmp_path, password="secret"):
    path = str(tmp_path / "vault.enc")
    save_vault(path, password, {"vars": {"API_KEY": "abc123", "DB_URL": "postgres://"}})
    return path


PASSWORD = "secret"


def test_set_hook_success(vault_file):
    set_hook(vault_file, PASSWORD, "API_KEY", "on_create", "echo created")
    assert get_hook(vault_file, PASSWORD, "API_KEY", "on_create") == "echo created"


def test_set_hook_invalid_event_raises(vault_file):
    with pytest.raises(LifecycleError, match="Unknown event"):
        set_hook(vault_file, PASSWORD, "API_KEY", "on_read", "echo hi")


def test_set_hook_missing_key_raises(vault_file):
    with pytest.raises(LifecycleError, match="not found"):
        set_hook(vault_file, PASSWORD, "GHOST", "on_update", "echo hi")


def test_set_hook_overwrites_existing(vault_file):
    set_hook(vault_file, PASSWORD, "API_KEY", "on_update", "echo first")
    set_hook(vault_file, PASSWORD, "API_KEY", "on_update", "echo second")
    assert get_hook(vault_file, PASSWORD, "API_KEY", "on_update") == "echo second"


def test_remove_hook_success(vault_file):
    set_hook(vault_file, PASSWORD, "API_KEY", "on_delete", "echo bye")
    remove_hook(vault_file, PASSWORD, "API_KEY", "on_delete")
    assert get_hook(vault_file, PASSWORD, "API_KEY", "on_delete") is None


def test_remove_hook_missing_raises(vault_file):
    with pytest.raises(LifecycleError, match="No 'on_delete' hook"):
        remove_hook(vault_file, PASSWORD, "API_KEY", "on_delete")


def test_remove_hook_cleans_empty_key_entry(vault_file):
    set_hook(vault_file, PASSWORD, "API_KEY", "on_create", "echo hi")
    remove_hook(vault_file, PASSWORD, "API_KEY", "on_create")
    from envault.vault import load_vault
    vault = load_vault(vault_file, PASSWORD)
    assert "API_KEY" not in vault.get(LIFECYCLE_KEY, {})


def test_list_hooks_all(vault_file):
    set_hook(vault_file, PASSWORD, "API_KEY", "on_create", "echo created")
    set_hook(vault_file, PASSWORD, "DB_URL", "on_update", "echo updated")
    hooks = list_hooks(vault_file, PASSWORD)
    assert "API_KEY" in hooks
    assert "DB_URL" in hooks


def test_list_hooks_filtered_by_key(vault_file):
    set_hook(vault_file, PASSWORD, "API_KEY", "on_create", "echo hi")
    set_hook(vault_file, PASSWORD, "DB_URL", "on_delete", "echo bye")
    hooks = list_hooks(vault_file, PASSWORD, key="API_KEY")
    assert "API_KEY" in hooks
    assert "DB_URL" not in hooks


def test_get_hook_none_when_not_set(vault_file):
    assert get_hook(vault_file, PASSWORD, "API_KEY", "on_create") is None


def test_all_valid_events_accepted(vault_file):
    for event in ("on_create", "on_update", "on_delete"):
        set_hook(vault_file, PASSWORD, "API_KEY", event, f"echo {event}")
        assert get_hook(vault_file, PASSWORD, "API_KEY", event) == f"echo {event}"
