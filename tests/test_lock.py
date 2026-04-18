"""Tests for envault.lock module."""

import time
import pytest
from pathlib import Path
from envault.lock import lock_vault, unlock_vault, is_locked, get_lock_info, LockError


@pytest.fixture
def vault_file(tmp_path):
    vf = tmp_path / "test.vault"
    vf.write_bytes(b"dummy")
    return str(vf)


def test_lock_creates_lock_file(vault_file):
    lock_vault(vault_file, reason="maintenance")
    assert Path(vault_file).with_suffix(".lock").exists()


def test_is_locked_true_after_lock(vault_file):
    lock_vault(vault_file)
    assert is_locked(vault_file) is True


def test_is_locked_false_before_lock(vault_file):
    assert is_locked(vault_file) is False


def test_lock_twice_raises(vault_file):
    lock_vault(vault_file)
    with pytest.raises(LockError, match="already locked"):
        lock_vault(vault_file)


def test_unlock_removes_lock_file(vault_file):
    lock_vault(vault_file)
    unlock_vault(vault_file)
    assert not Path(vault_file).with_suffix(".lock").exists()


def test_unlock_when_not_locked_raises(vault_file):
    with pytest.raises(LockError, match="not locked"):
        unlock_vault(vault_file)


def test_get_lock_info_returns_metadata(vault_file):
    lock_vault(vault_file, reason="deploy")
    info = get_lock_info(vault_file)
    assert info is not None
    assert info["reason"] == "deploy"
    assert "user" in info
    assert "locked_at" in info
    assert "expires_at" in info


def test_get_lock_info_none_when_not_locked(vault_file):
    assert get_lock_info(vault_file) is None


def test_lock_expires_automatically(vault_file):
    lock_vault(vault_file, ttl_seconds=1)
    time.sleep(2)
    assert is_locked(vault_file) is False
