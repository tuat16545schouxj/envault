"""Tests for snapshot CLI commands."""

import pytest
from click.testing import CliRunner

from envault.cli_snapshot import snapshot_group
from envault.vault import save_vault


PASSWORD = "cli-pass"


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def tmp_vault(tmp_path):
    path = str(tmp_path / "vault.enc")
    save_vault(path, PASSWORD, {"variables": {"A": "1", "B": "2"}})
    return path


def _args(vault, extra=None):
    base = ["--vault", vault, "--password", PASSWORD]
    return base + (extra or [])


def test_create_and_list(runner, tmp_vault):
    r = runner.invoke(snapshot_group, ["create"] + _args(tmp_vault, ["--name", "v1"]))
    assert r.exit_code == 0
    assert "v1" in r.output

    r = runner.invoke(snapshot_group, ["list"] + _args(tmp_vault))
    assert r.exit_code == 0
    assert "v1" in r.output


def test_list_empty(runner, tmp_vault):
    r = runner.invoke(snapshot_group, ["list"] + _args(tmp_vault))
    assert r.exit_code == 0
    assert "No snapshots" in r.output


def test_restore(runner, tmp_vault):
    runner.invoke(snapshot_group, ["create"] + _args(tmp_vault, ["--name", "snap"]))
    r = runner.invoke(snapshot_group, ["restore", "snap"] + _args(tmp_vault))
    assert r.exit_code == 0
    assert "Restored" in r.output


def test_delete(runner, tmp_vault):
    runner.invoke(snapshot_group, ["create"] + _args(tmp_vault, ["--name", "del_me"]))
    r = runner.invoke(snapshot_group, ["delete", "del_me"] + _args(tmp_vault))
    assert r.exit_code == 0
    assert "deleted" in r.output


def test_create_duplicate_shows_error(runner, tmp_vault):
    runner.invoke(snapshot_group, ["create"] + _args(tmp_vault, ["--name", "dup"]))
    r = runner.invoke(snapshot_group, ["create"] + _args(tmp_vault, ["--name", "dup"]))
    assert r.exit_code != 0
    assert "already exists" in r.output
