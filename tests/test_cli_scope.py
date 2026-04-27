"""CLI tests for the scope command group."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from envault.cli_scope import scope_group
from envault.vault import save_vault


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def tmp_vault(tmp_path):
    path = str(tmp_path / "vault.enc")
    data = {"vars": {"API_KEY": "s3cr3t", "DB_URL": "postgres://localhost"}}
    save_vault(path, "pass", data)
    return path


def _args(tmp_vault, *extra):
    return ["--vault", tmp_vault, "--password", "pass", *extra]


def test_assign_scope_output(runner, tmp_vault):
    result = runner.invoke(scope_group, ["assign", *_args(tmp_vault), "API_KEY", "prod"])
    assert result.exit_code == 0
    assert "assigned to scope 'prod'" in result.output


def test_assign_missing_key_shows_error(runner, tmp_vault):
    result = runner.invoke(scope_group, ["assign", *_args(tmp_vault), "NOPE", "prod"])
    assert result.exit_code != 0
    assert "does not exist" in result.output


def test_remove_scope_output(runner, tmp_vault):
    runner.invoke(scope_group, ["assign", *_args(tmp_vault), "API_KEY", "dev"])
    result = runner.invoke(scope_group, ["remove", *_args(tmp_vault), "API_KEY", "dev"])
    assert result.exit_code == 0
    assert "removed from key 'API_KEY'" in result.output


def test_remove_unassigned_shows_error(runner, tmp_vault):
    result = runner.invoke(scope_group, ["remove", *_args(tmp_vault), "API_KEY", "prod"])
    assert result.exit_code != 0
    assert "not assigned to scope" in result.output


def test_list_empty_shows_message(runner, tmp_vault):
    result = runner.invoke(scope_group, ["list", *_args(tmp_vault)])
    assert result.exit_code == 0
    assert "No scope assignments" in result.output


def test_list_shows_assignments(runner, tmp_vault):
    runner.invoke(scope_group, ["assign", *_args(tmp_vault), "API_KEY", "prod"])
    runner.invoke(scope_group, ["assign", *_args(tmp_vault), "DB_URL", "staging"])
    result = runner.invoke(scope_group, ["list", *_args(tmp_vault)])
    assert result.exit_code == 0
    assert "API_KEY" in result.output
    assert "prod" in result.output


def test_list_filter_by_scope(runner, tmp_vault):
    runner.invoke(scope_group, ["assign", *_args(tmp_vault), "API_KEY", "prod"])
    runner.invoke(scope_group, ["assign", *_args(tmp_vault), "DB_URL", "dev"])
    result = runner.invoke(scope_group, ["list", *_args(tmp_vault), "--scope", "prod"])
    assert result.exit_code == 0
    assert "API_KEY" in result.output
    assert "DB_URL" not in result.output
