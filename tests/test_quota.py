"""Tests for envault.quota."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.vault import save_vault
from envault.quota import (
    QuotaError,
    check_quota,
    enforce_quota,
    get_quota,
    remove_quota,
    set_quota,
)

PASSWORD = "test-secret"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    path = tmp_path / "vault.env"
    save_vault(path, PASSWORD, {"vars": {"KEY1": "val1", "KEY2": "val2"}})
    return path


def test_set_quota_stores_limit(vault_file: Path) -> None:
    set_quota(vault_file, PASSWORD, 10)
    assert get_quota(vault_file, PASSWORD) == 10


def test_set_quota_invalid_limit_raises(vault_file: Path) -> None:
    with pytest.raises(QuotaError, match="positive integer"):
        set_quota(vault_file, PASSWORD, 0)


def test_set_quota_negative_raises(vault_file: Path) -> None:
    with pytest.raises(QuotaError):
        set_quota(vault_file, PASSWORD, -5)


def test_get_quota_none_when_not_set(vault_file: Path) -> None:
    assert get_quota(vault_file, PASSWORD) is None


def test_remove_quota_clears_limit(vault_file: Path) -> None:
    set_quota(vault_file, PASSWORD, 5)
    remove_quota(vault_file, PASSWORD)
    assert get_quota(vault_file, PASSWORD) is None


def test_remove_quota_idempotent(vault_file: Path) -> None:
    remove_quota(vault_file, PASSWORD)  # no quota set — should not raise
    assert get_quota(vault_file, PASSWORD) is None


def test_check_quota_no_limit(vault_file: Path) -> None:
    status = check_quota(vault_file, PASSWORD)
    assert status["limit"] is None
    assert status["used"] == 2
    assert status["remaining"] is None
    assert status["exceeded"] is False


def test_check_quota_within_limit(vault_file: Path) -> None:
    set_quota(vault_file, PASSWORD, 5)
    status = check_quota(vault_file, PASSWORD)
    assert status["limit"] == 5
    assert status["used"] == 2
    assert status["remaining"] == 3
    assert status["exceeded"] is False


def test_check_quota_at_limit(vault_file: Path) -> None:
    set_quota(vault_file, PASSWORD, 2)
    status = check_quota(vault_file, PASSWORD)
    assert status["exceeded"] is False
    assert status["remaining"] == 0


def test_check_quota_exceeded(vault_file: Path) -> None:
    set_quota(vault_file, PASSWORD, 1)
    status = check_quota(vault_file, PASSWORD)
    assert status["exceeded"] is True
    assert status["remaining"] == 0


def test_enforce_quota_raises_when_exceeded(vault_file: Path) -> None:
    set_quota(vault_file, PASSWORD, 1)
    with pytest.raises(QuotaError, match="exceeds quota"):
        enforce_quota(vault_file, PASSWORD)


def test_enforce_quota_no_error_when_within_limit(vault_file: Path) -> None:
    set_quota(vault_file, PASSWORD, 10)
    enforce_quota(vault_file, PASSWORD)  # should not raise
