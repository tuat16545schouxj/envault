"""Tests for envault.watch."""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envault.watch import WatchError, _file_hash, watch_vault


# ---------------------------------------------------------------------------
# _file_hash
# ---------------------------------------------------------------------------


def test_file_hash_returns_string_for_existing_file(tmp_path: Path) -> None:
    f = tmp_path / "vault.enc"
    f.write_bytes(b"some content")
    result = _file_hash(f)
    assert isinstance(result, str)
    assert len(result) == 32  # MD5 hex digest length


def test_file_hash_returns_empty_string_for_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "nonexistent.enc"
    assert _file_hash(missing) == ""


def test_file_hash_changes_when_content_changes(tmp_path: Path) -> None:
    f = tmp_path / "vault.enc"
    f.write_bytes(b"original")
    h1 = _file_hash(f)
    f.write_bytes(b"modified")
    h2 = _file_hash(f)
    assert h1 != h2


def test_file_hash_stable_for_same_content(tmp_path: Path) -> None:
    f = tmp_path / "vault.enc"
    f.write_bytes(b"stable")
    assert _file_hash(f) == _file_hash(f)


# ---------------------------------------------------------------------------
# watch_vault
# ---------------------------------------------------------------------------


def test_watch_vault_invalid_interval_raises() -> None:
    with pytest.raises(WatchError, match="interval must be a positive number"):
        watch_vault("vault.enc", lambda p: None, interval=0, max_iterations=0)


def test_watch_vault_negative_interval_raises() -> None:
    with pytest.raises(WatchError):
        watch_vault("vault.enc", lambda p: None, interval=-1.0, max_iterations=0)


def test_watch_vault_calls_callback_on_change(tmp_path: Path) -> None:
    vault = tmp_path / "vault.enc"
    vault.write_bytes(b"initial")

    callback = MagicMock()
    call_count = 0

    def fake_sleep(seconds: float) -> None:  # noqa: ARG001
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            vault.write_bytes(b"changed")

    with patch("envault.watch.time.sleep", side_effect=fake_sleep):
        watch_vault(str(vault), callback, interval=0.01, max_iterations=2)

    callback.assert_called_once_with(str(vault))


def test_watch_vault_no_callback_when_unchanged(tmp_path: Path) -> None:
    vault = tmp_path / "vault.enc"
    vault.write_bytes(b"static")

    callback = MagicMock()

    with patch("envault.watch.time.sleep"):
        watch_vault(str(vault), callback, interval=0.01, max_iterations=3)

    callback.assert_not_called()


def test_watch_vault_detects_new_file(tmp_path: Path) -> None:
    vault = tmp_path / "vault.enc"
    # File does not exist initially

    callback = MagicMock()
    call_count = 0

    def fake_sleep(seconds: float) -> None:  # noqa: ARG001
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            vault.write_bytes(b"created")

    with patch("envault.watch.time.sleep", side_effect=fake_sleep):
        watch_vault(str(vault), callback, interval=0.01, max_iterations=2)

    callback.assert_called_once_with(str(vault))
