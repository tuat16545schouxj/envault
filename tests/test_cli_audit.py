"""Tests for the audit CLI sub-commands."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.audit import record
from envault.cli_audit import audit_group


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def log_file(tmp_path: Path) -> str:
    return str(tmp_path / "audit.log")


def test_log_empty_message(runner, log_file):
    result = runner.invoke(audit_group, ["log", "--log-file", log_file])
    assert result.exit_code == 0
    assert "No audit log entries found" in result.output


def test_log_shows_entries(runner, log_file, monkeypatch):
    monkeypatch.setenv("USER", "alice")
    record("set", key="DB_URL", log_path=log_file)
    record("delete", key="OLD_KEY", log_path=log_file)
    result = runner.invoke(audit_group, ["log", "--log-file", log_file])
    assert result.exit_code == 0
    assert "set" in result.output
    assert "DB_URL" in result.output
    assert "delete" in result.output
    assert "OLD_KEY" in result.output
    assert "alice" in result.output


def test_log_filter_by_action(runner, log_file):
    record("set", key="A", log_path=log_file)
    record("export", key=None, log_path=log_file)
    result = runner.invoke(audit_group, ["log", "--log-file", log_file, "--action", "export"])
    assert result.exit_code == 0
    assert "export" in result.output
    assert "set" not in result.output


def test_log_limit(runner, log_file):
    for i in range(10):
        record("set", key=f"KEY_{i}", log_path=log_file)
    result = runner.invoke(audit_group, ["log", "--log-file", log_file, "--limit", "3"])
    assert result.exit_code == 0
    # only last 3 keys should appear
    assert "KEY_9" in result.output
    assert "KEY_0" not in result.output


def test_clear_removes_log(runner, log_file):
    record("set", key="X", log_path=log_file)
    assert Path(log_file).exists()
    result = runner.invoke(audit_group, ["clear", "--log-file", log_file], input="y\n")
    assert result.exit_code == 0
    assert "cleared" in result.output
    assert not Path(log_file).exists()


def test_clear_aborted(runner, log_file):
    record("set", key="X", log_path=log_file)
    result = runner.invoke(audit_group, ["clear", "--log-file", log_file], input="n\n")
    assert result.exit_code != 0 or "Aborted" in result.output
    assert Path(log_file).exists()
