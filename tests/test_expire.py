"""Tests for envault/expire.py."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from envault.vault import save_vault
from envault.ttl import set_ttl
from envault.expire import (
    ExpireError,
    ExpirationStatus,
    expiration_report,
    extend_ttl_bulk,
    purge_and_report,
)

PASSWORD = "test-password"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    path = tmp_path / "vault.enc"
    data: dict = {"variables": {"FOO": "bar", "BAZ": "qux", "GONE": "expired"}}
    # FOO: TTL 9999 seconds in the future
    data = set_ttl(data, "FOO", 9999)
    # GONE: TTL already expired (set 1 second, then manually backdate)
    data = set_ttl(data, "GONE", 1)
    ttl_meta = data.setdefault("_ttl", {})
    ttl_meta["GONE"] = time.time() - 60  # expired 60 seconds ago
    save_vault(path, PASSWORD, data)
    return path


def test_expiration_report_no_ttl(vault_file: Path) -> None:
    statuses = expiration_report(vault_file, PASSWORD, keys=["BAZ"])
    assert len(statuses) == 1
    assert statuses[0].key == "BAZ"
    assert statuses[0].expires_at is None
    assert statuses[0].is_expired is False
    assert statuses[0].seconds_remaining is None


def test_expiration_report_active_ttl(vault_file: Path) -> None:
    statuses = expiration_report(vault_file, PASSWORD, keys=["FOO"])
    assert len(statuses) == 1
    s = statuses[0]
    assert s.key == "FOO"
    assert s.is_expired is False
    assert s.seconds_remaining is not None
    assert s.seconds_remaining > 9000


def test_expiration_report_expired_key(vault_file: Path) -> None:
    statuses = expiration_report(vault_file, PASSWORD, keys=["GONE"])
    assert statuses[0].is_expired is True
    assert statuses[0].seconds_remaining is None


def test_expiration_report_all_keys(vault_file: Path) -> None:
    statuses = expiration_report(vault_file, PASSWORD)
    keys = [s.key for s in statuses]
    assert "FOO" in keys
    assert "BAZ" in keys
    assert "GONE" in keys


def test_expiration_report_missing_key_raises(vault_file: Path) -> None:
    with pytest.raises(ExpireError, match="not found"):
        expiration_report(vault_file, PASSWORD, keys=["NONEXISTENT"])


def test_expiration_report_wrong_password_raises(vault_file: Path) -> None:
    with pytest.raises(ExpireError):
        expiration_report(vault_file, "wrong", keys=["FOO"])


def test_extend_ttl_bulk_extends_existing(vault_file: Path) -> None:
    extended = extend_ttl_bulk(vault_file, PASSWORD, extra_seconds=3600)
    # FOO and GONE have TTLs; BAZ does not
    assert "FOO" in extended
    assert "GONE" in extended
    assert "BAZ" not in extended


def test_extend_ttl_bulk_specific_keys(vault_file: Path) -> None:
    extended = extend_ttl_bulk(vault_file, PASSWORD, extra_seconds=100, keys=["FOO"])
    assert extended == ["FOO"]


def test_extend_ttl_bulk_zero_seconds_raises(vault_file: Path) -> None:
    with pytest.raises(ExpireError, match="positive"):
        extend_ttl_bulk(vault_file, PASSWORD, extra_seconds=0)


def test_extend_ttl_bulk_missing_key_raises(vault_file: Path) -> None:
    with pytest.raises(ExpireError, match="not found"):
        extend_ttl_bulk(vault_file, PASSWORD, extra_seconds=60, keys=["MISSING"])


def test_purge_and_report_removes_expired(vault_file: Path) -> None:
    removed = purge_and_report(vault_file, PASSWORD)
    assert "GONE" in removed
    assert "FOO" not in removed
    assert "BAZ" not in removed


def test_purge_and_report_empty_when_none_expired(tmp_path: Path) -> None:
    path = tmp_path / "clean.enc"
    data: dict = {"variables": {"KEY": "value"}}
    save_vault(path, PASSWORD, data)
    removed = purge_and_report(path, PASSWORD)
    assert removed == []


def test_to_dict_contains_expected_keys(vault_file: Path) -> None:
    statuses = expiration_report(vault_file, PASSWORD, keys=["FOO"])
    d = statuses[0].to_dict()
    assert set(d.keys()) == {"key", "expires_at", "is_expired", "seconds_remaining"}
