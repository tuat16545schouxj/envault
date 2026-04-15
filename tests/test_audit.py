"""Tests for envault.audit module."""

import json
from pathlib import Path

import pytest

from envault.audit import (
    AuditEntry,
    clear_log,
    read_log,
    record,
)


@pytest.fixture()
def log_file(tmp_path: Path) -> str:
    return str(tmp_path / "audit.log")


def test_record_creates_log_file(log_file):
    record("set", key="API_KEY", log_path=log_file)
    assert Path(log_file).exists()


def test_record_appends_json_lines(log_file):
    record("set", key="FOO", log_path=log_file)
    record("delete", key="BAR", log_path=log_file)
    lines = Path(log_file).read_text().strip().splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    assert first["action"] == "set"
    assert first["key"] == "FOO"
    second = json.loads(lines[1])
    assert second["action"] == "delete"
    assert second["key"] == "BAR"


def test_record_includes_timestamp(log_file):
    record("list", log_path=log_file)
    lines = Path(log_file).read_text().strip().splitlines()
    entry = json.loads(lines[0])
    assert "timestamp" in entry
    assert entry["timestamp"].endswith("+00:00")


def test_record_includes_user(log_file, monkeypatch):
    monkeypatch.setenv("USER", "alice")
    record("export", log_path=log_file)
    entry = json.loads(Path(log_file).read_text().strip())
    assert entry["user"] == "alice"


def test_record_details_field(log_file):
    record("push", details="remote=https://example.com", log_path=log_file)
    entry = json.loads(Path(log_file).read_text().strip())
    assert entry["details"] == "remote=https://example.com"


def test_read_log_empty_when_no_file(log_file):
    entries = read_log(log_path=log_file)
    assert entries == []


def test_read_log_returns_entries(log_file):
    record("set", key="X", log_path=log_file)
    record("set", key="Y", log_path=log_file)
    entries = read_log(log_path=log_file)
    assert len(entries) == 2
    assert isinstance(entries[0], AuditEntry)
    assert entries[0].key == "X"
    assert entries[1].key == "Y"


def test_clear_log_removes_file(log_file):
    record("set", key="Z", log_path=log_file)
    assert Path(log_file).exists()
    clear_log(log_path=log_file)
    assert not Path(log_file).exists()


def test_clear_log_no_error_when_missing(log_file):
    clear_log(log_path=log_file)  # should not raise


def test_audit_entry_roundtrip():
    entry = AuditEntry(action="delete", key="SECRET", user="bob", details="forced")
    restored = AuditEntry.from_dict(entry.to_dict())
    assert restored.action == entry.action
    assert restored.key == entry.key
    assert restored.user == entry.user
    assert restored.details == entry.details
    assert restored.timestamp == entry.timestamp
