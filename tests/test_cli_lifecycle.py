"""Tests for envault.cli_lifecycle."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from envault.vault import save_vault
from envault.cli_lifecycle import lifecycle_group

PASSWORD = "secret"


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def tmp_vault(tmp_path):
    path = str(tmp_path / "vault.enc")
    save_vault(path, PASSWORD, {"vars": {"API_KEY": "abc", "DB_URL": "pg://"}})
    return path


def _args(tmp_vault, *extra):
    return ["--vault", tmp_vault, "--password", PASSWORD, *extra]


def test_set_hook_output(runner, tmp_vault):
    result = runner.invoke(lifecycle_group, ["set", *_args(tmp_vault), "API_KEY", "on_create", "echo hi"])
    assert result.exit_code == 0
    assert "on_create" in result.output
    assert "API_KEY" in result.output


def test_set_hook_invalid_event(runner, tmp_vault):
    result = runner.invoke(lifecycle_group, ["set", *_args(tmp_vault), "API_KEY", "on_read", "echo hi"])
    assert result.exit_code != 0
    assert "Unknown event" in result.output


def test_set_hook_missing_key(runner, tmp_vault):
    result = runner.invoke(lifecycle_group, ["set", *_args(tmp_vault), "MISSING", "on_create", "echo hi"])
    assert result.exit_code != 0
    assert "not found" in result.output


def test_remove_hook_output(runner, tmp_vault):
    runner.invoke(lifecycle_group, ["set", *_args(tmp_vault), "API_KEY", "on_delete", "echo bye"])
    result = runner.invoke(lifecycle_group, ["remove", *_args(tmp_vault), "API_KEY", "on_delete"])
    assert result.exit_code == 0
    assert "removed" in result.output


def test_remove_hook_not_found(runner, tmp_vault):
    result = runner.invoke(lifecycle_group, ["remove", *_args(tmp_vault), "API_KEY", "on_delete"])
    assert result.exit_code != 0


def test_list_hooks_empty(runner, tmp_vault):
    result = runner.invoke(lifecycle_group, ["list", *_args(tmp_vault)])
    assert result.exit_code == 0
    assert "No lifecycle hooks" in result.output


def test_list_hooks_shows_entries(runner, tmp_vault):
    runner.invoke(lifecycle_group, ["set", *_args(tmp_vault), "API_KEY", "on_create", "echo created"])
    runner.invoke(lifecycle_group, ["set", *_args(tmp_vault), "DB_URL", "on_update", "echo updated"])
    result = runner.invoke(lifecycle_group, ["list", *_args(tmp_vault)])
    assert result.exit_code == 0
    assert "API_KEY" in result.output
    assert "on_create" in result.output
    assert "DB_URL" in result.output


def test_list_hooks_filtered_by_key(runner, tmp_vault):
    runner.invoke(lifecycle_group, ["set", *_args(tmp_vault), "API_KEY", "on_create", "echo hi"])
    runner.invoke(lifecycle_group, ["set", *_args(tmp_vault), "DB_URL", "on_delete", "echo bye"])
    result = runner.invoke(lifecycle_group, ["list", "--key", "API_KEY", *_args(tmp_vault)])
    assert result.exit_code == 0
    assert "API_KEY" in result.output
    assert "DB_URL" not in result.output
