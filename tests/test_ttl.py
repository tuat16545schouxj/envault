"""Tests for envault.ttl module."""
from __future__ import annotations

import time
import pytest

from envault.vault import save_vault
from envault.ttl import TTLError, set_ttl, remove_ttl, get_ttl, purge_expired, list_ttls

PASSWORD = "test-pass"


@pytest.fixture
def vault_file(tmp_path):
    path = str(tmp_path / "vault.enc")
    save_vault(path, PASSWORD, {"vars": {"FOO": "bar", "BAZ": "qux"}, "ttl": {}})
    return path


def test_set_ttl_stores_future_timestamp(vault_file):
    before = time.time()
    set_ttl(vault_file, PASSWORD, "FOO", 60)
    exp = get_ttl(vault_file, PASSWORD, "FOO")
    assert exp is not None
    assert exp > before + 55


def test_set_ttl_missing_key_raises(vault_file):
    with pytest.raises(TTLError, match="not found"):
        set_ttl(vault_file, PASSWORD, "MISSING", 60)


def test_set_ttl_zero_or_negative_raises(vault_file):
    with pytest.raises(TTLError, match="positive"):
        set_ttl(vault_file, PASSWORD, "FOO", 0)
    with pytest.raises(TTLError, match="positive"):
        set_ttl(vault_file, PASSWORD, "FOO", -10)


def test_get_ttl_none_when_not_set(vault_file):
    assert get_ttl(vault_file, PASSWORD, "FOO") is None


def test_remove_ttl_clears_expiry(vault_file):
    set_ttl(vault_file, PASSWORD, "FOO", 60)
    remove_ttl(vault_file, PASSWORD, "FOO")
    assert get_ttl(vault_file, PASSWORD, "FOO") is None


def test_remove_ttl_not_set_raises(vault_file):
    with pytest.raises(TTLError, match="No TTL"):
        remove_ttl(vault_file, PASSWORD, "FOO")


def test_purge_expired_removes_keys(vault_file):
    set_ttl(vault_file, PASSWORD, "FOO", 1)
    set_ttl(vault_file, PASSWORD, "BAZ", 3600)
    time.sleep(1.1)
    purged = purge_expired(vault_file, PASSWORD)
    assert purged == ["FOO"]
    ttls = list_ttls(vault_file, PASSWORD)
    assert "FOO" not in ttls
    assert "BAZ" in ttls


def test_purge_expired_returns_empty_when_none_expired(vault_file):
    set_ttl(vault_file, PASSWORD, "FOO", 3600)
    purged = purge_expired(vault_file, PASSWORD)
    assert purged == []


def test_list_ttls_returns_all(vault_file):
    set_ttl(vault_file, PASSWORD, "FOO", 100)
    set_ttl(vault_file, PASSWORD, "BAZ", 200)
    ttls = list_ttls(vault_file, PASSWORD)
    assert set(ttls.keys()) == {"FOO", "BAZ"}
