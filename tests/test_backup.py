"""Tests for envault.backup."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from envault.backup import (
    BackupError,
    create_backup,
    delete_backup,
    list_backups,
    prune_backups,
    restore_backup,
    _backup_dir,
)


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    vf = tmp_path / "vault.enc"
    vf.write_bytes(b"fake-encrypted-content")
    return vf


def test_create_backup_returns_path(vault_file: Path) -> None:
    dest = create_backup(vault_file)
    assert dest.exists()
    assert dest.suffix == ".bak"


def test_create_backup_content_matches(vault_file: Path) -> None:
    dest = create_backup(vault_file)
    assert dest.read_bytes() == vault_file.read_bytes()


def test_create_backup_with_label(vault_file: Path) -> None:
    dest = create_backup(vault_file, label="pre-rotate")
    assert "pre-rotate" in dest.name


def test_create_backup_missing_vault(tmp_path: Path) -> None:
    with pytest.raises(BackupError, match="not found"):
        create_backup(tmp_path / "missing.enc")


def test_list_backups_empty(vault_file: Path) -> None:
    assert list_backups(vault_file) == []


def test_list_backups_returns_sorted(vault_file: Path) -> None:
    b1 = create_backup(vault_file, label="first")
    time.sleep(0.01)
    b2 = create_backup(vault_file, label="second")
    result = list_backups(vault_file)
    assert result[0] == b1
    assert result[1] == b2


def test_restore_backup_overwrites_vault(vault_file: Path) -> None:
    original = vault_file.read_bytes()
    backup = create_backup(vault_file)
    vault_file.write_bytes(b"new-content")
    restore_backup(vault_file, backup)
    assert vault_file.read_bytes() == original


def test_restore_backup_missing_raises(vault_file: Path, tmp_path: Path) -> None:
    with pytest.raises(BackupError, match="not found"):
        restore_backup(vault_file, tmp_path / "ghost.bak")


def test_delete_backup_removes_file(vault_file: Path) -> None:
    backup = create_backup(vault_file)
    delete_backup(backup)
    assert not backup.exists()


def test_delete_backup_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(BackupError, match="not found"):
        delete_backup(tmp_path / "nope.bak")


def test_prune_keeps_most_recent(vault_file: Path) -> None:
    for i in range(5):
        create_backup(vault_file, label=f"b{i}")
        time.sleep(0.01)
    deleted = prune_backups(vault_file, keep=3)
    assert len(deleted) == 2
    assert len(list_backups(vault_file)) == 3


def test_prune_nothing_to_delete(vault_file: Path) -> None:
    create_backup(vault_file)
    deleted = prune_backups(vault_file, keep=5)
    assert deleted == []


def test_prune_invalid_keep_raises(vault_file: Path) -> None:
    with pytest.raises(BackupError, match="keep must be"):
        prune_backups(vault_file, keep=0)


def test_backup_dir_location(vault_file: Path) -> None:
    expected = vault_file.parent / ".envault_backups"
    assert _backup_dir(vault_file) == expected
