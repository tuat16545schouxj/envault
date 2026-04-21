"""Tests for envault/history.py and envault/cli_history.py."""

from __future__ import annotations

import json
import time

import pytest
from click.testing import CliRunner

from envault.cli_history import history_group
from envault.history import (
    HISTORY_KEY,
    HistoryEntry,
    clear_history,
    get_history,
    record_change,
)
from envault.vault import load_vault, save_vault


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------

def _empty_vault() -> dict:
    return {}


def test_record_change_appends_entry():
    vault = _empty_vault()
    record_change(vault, "FOO", None, "bar", "set")
    assert len(vault[HISTORY_KEY]) == 1
    assert vault[HISTORY_KEY][0]["key"] == "FOO"


def test_record_change_multiple_entries():
    vault = _empty_vault()
    record_change(vault, "A", None, "1", "set")
    record_change(vault, "A", "1", "2", "set")
    record_change(vault, "A", "2", None, "delete")
    assert len(vault[HISTORY_KEY]) == 3


def test_get_history_returns_all():
    vault = _empty_vault()
    record_change(vault, "X", None, "v", "set")
    record_change(vault, "Y", None, "w", "set")
    entries = get_history(vault)
    assert len(entries) == 2


def test_get_history_filter_by_key():
    vault = _empty_vault()
    record_change(vault, "X", None, "v", "set")
    record_change(vault, "Y", None, "w", "set")
    entries = get_history(vault, key="X")
    assert len(entries) == 1
    assert entries[0].key == "X"


def test_get_history_respects_limit():
    vault = _empty_vault()
    for i in range(10):
        record_change(vault, "K", str(i), str(i + 1), "set")
    entries = get_history(vault, limit=3)
    assert len(entries) == 3


def test_clear_history_all():
    vault = _empty_vault()
    record_change(vault, "A", None, "1", "set")
    record_change(vault, "B", None, "2", "set")
    removed = clear_history(vault)
    assert removed == 2
    assert vault[HISTORY_KEY] == []


def test_clear_history_by_key():
    vault = _empty_vault()
    record_change(vault, "A", None, "1", "set")
    record_change(vault, "B", None, "2", "set")
    removed = clear_history(vault, key="A")
    assert removed == 1
    remaining = get_history(vault)
    assert all(e.key == "B" for e in remaining)


def test_history_entry_roundtrip():
    entry = HistoryEntry(key="K", old_value="old", new_value="new", action="set", timestamp=1234.0)
    restored = HistoryEntry.from_dict(entry.to_dict())
    assert restored.key == entry.key
    assert restored.old_value == entry.old_value
    assert restored.new_value == entry.new_value
    assert restored.action == entry.action
    assert restored.timestamp == entry.timestamp


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def tmp_vault(tmp_path):
    path = str(tmp_path / "vault.enc")
    vault = {HISTORY_KEY: []}
    record_change(vault, "FOO", None, "bar", "set")
    record_change(vault, "BAZ", None, "qux", "set")
    save_vault(path, "secret", vault)
    return path


def _args(vault_path, extra=None):
    base = ["--vault", vault_path, "--password", "secret"]
    return base + (extra or [])


def test_log_shows_entries(runner, tmp_vault):
    result = runner.invoke(history_group, ["log"] + _args(tmp_vault))
    assert result.exit_code == 0
    assert "FOO" in result.output
    assert "BAZ" in result.output


def test_log_filter_by_key(runner, tmp_vault):
    result = runner.invoke(history_group, ["log"] + _args(tmp_vault, ["--key", "FOO"]))
    assert result.exit_code == 0
    assert "FOO" in result.output
    assert "BAZ" not in result.output


def test_log_empty_history(runner, tmp_path):
    path = str(tmp_path / "empty.enc")
    save_vault(path, "secret", {})
    result = runner.invoke(history_group, ["log"] + _args(path))
    assert result.exit_code == 0
    assert "No history" in result.output


def test_clear_removes_entries(runner, tmp_vault):
    result = runner.invoke(
        history_group, ["clear"] + _args(tmp_vault), input="y\n"
    )
    assert result.exit_code == 0
    assert "Cleared 2" in result.output
    vault = load_vault(tmp_vault, "secret")
    assert vault[HISTORY_KEY] == []
