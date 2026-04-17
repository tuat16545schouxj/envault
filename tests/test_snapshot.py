"""Tests for envault.snapshot module."""

import pytest

from envault.snapshot import SnapshotError, create_snapshot, delete_snapshot, list_snapshots, restore_snapshot
from envault.vault import save_vault


PASSWORD = "test-password"


@pytest.fixture
def vault_file(tmp_path):
    path = str(tmp_path / "vault.enc")
    save_vault(path, PASSWORD, {"variables": {"KEY1": "val1", "KEY2": "val2"}})
    return path


def test_create_snapshot_returns_name(vault_file):
    name = create_snapshot(vault_file, PASSWORD, name="snap1")
    assert name == "snap1"


def test_create_snapshot_auto_name(vault_file):
    name = create_snapshot(vault_file, PASSWORD)
    assert len(name) > 0
    assert "T" in name  # timestamp format


def test_list_snapshots_empty(vault_file):
    assert list_snapshots(vault_file, PASSWORD) == []


def test_list_snapshots_returns_sorted(vault_file):
    create_snapshot(vault_file, PASSWORD, name="beta")
    create_snapshot(vault_file, PASSWORD, name="alpha")
    names = list_snapshots(vault_file, PASSWORD)
    assert names == ["alpha", "beta"]


def test_create_snapshot_duplicate_raises(vault_file):
    create_snapshot(vault_file, PASSWORD, name="dup")
    with pytest.raises(SnapshotError, match="already exists"):
        create_snapshot(vault_file, PASSWORD, name="dup")


def test_create_snapshot_empty_vault_raises(tmp_path):
    path = str(tmp_path / "empty.enc")
    save_vault(path, PASSWORD, {"variables": {}})
    with pytest.raises(SnapshotError, match="No variables"):
        create_snapshot(path, PASSWORD, name="s")


def test_restore_snapshot_no_overwrite(vault_file):
    create_snapshot(vault_file, PASSWORD, name="s1")
    from envault.vault import set_var
    set_var(vault_file, PASSWORD, "KEY3", "val3")
    restore_snapshot(vault_file, PASSWORD, "s1", overwrite=False)
    from envault.vault import load_vault
    data = load_vault(vault_file, PASSWORD)
    assert "KEY3" in data["variables"]  # existing key preserved
    assert data["variables"]["KEY1"] == "val1"


def test_restore_snapshot_overwrite(vault_file):
    create_snapshot(vault_file, PASSWORD, name="s1")
    from envault.vault import set_var, load_vault
    set_var(vault_file, PASSWORD, "KEY3", "val3")
    restore_snapshot(vault_file, PASSWORD, "s1", overwrite=True)
    data = load_vault(vault_file, PASSWORD)
    assert "KEY3" not in data["variables"]


def test_restore_snapshot_not_found_raises(vault_file):
    with pytest.raises(SnapshotError, match="not found"):
        restore_snapshot(vault_file, PASSWORD, "ghost")


def test_delete_snapshot(vault_file):
    create_snapshot(vault_file, PASSWORD, name="to_del")
    delete_snapshot(vault_file, PASSWORD, "to_del")
    assert "to_del" not in list_snapshots(vault_file, PASSWORD)


def test_delete_snapshot_not_found_raises(vault_file):
    with pytest.raises(SnapshotError, match="not found"):
        delete_snapshot(vault_file, PASSWORD, "nope")
