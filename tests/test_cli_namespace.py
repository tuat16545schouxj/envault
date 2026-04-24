"""CLI tests for the namespace command group."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from envault.cli_namespace import namespace_group
from envault.vault import save_vault

PASSWORD = "testpassword"


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def tmp_vault(tmp_path):
    path = str(tmp_path / "vault.env")
    save_vault(path, PASSWORD, {
        "variables": {
            "DB_HOST": "localhost",
            "DB_PORT": "5432",
            "APP__SECRET": "s3cr3t",
            "APP__DEBUG": "false",
        }
    })
    return path


def _args(vault, extra=None):
    base = ["--vault", vault, "--password", PASSWORD]
    return base + (extra or [])


def test_list_shows_namespaces(runner, tmp_vault):
    result = runner.invoke(namespace_group, ["list"] + _args(tmp_vault))
    assert result.exit_code == 0
    assert "APP" in result.output


def test_list_empty_vault(runner, tmp_path):
    path = str(tmp_path / "empty.env")
    save_vault(path, PASSWORD, {"variables": {}})
    result = runner.invoke(namespace_group, ["list"] + _args(path))
    assert result.exit_code == 0
    assert "No namespaces found" in result.output


def test_show_namespace_vars(runner, tmp_vault):
    result = runner.invoke(namespace_group, ["show", "APP"] + _args(tmp_vault))
    assert result.exit_code == 0
    assert "SECRET=s3cr3t" in result.output
    assert "DEBUG=false" in result.output


def test_show_unknown_namespace(runner, tmp_vault):
    result = runner.invoke(namespace_group, ["show", "UNKNOWN"] + _args(tmp_vault))
    assert result.exit_code == 0
    assert "No variables found" in result.output


def test_move_specific_keys(runner, tmp_vault):
    result = runner.invoke(
        namespace_group,
        ["move", "DB", "--key", "DB_HOST", "--key", "DB_PORT"] + _args(tmp_vault),
    )
    assert result.exit_code == 0
    assert "2 variable(s) moved" in result.output


def test_move_missing_key_error(runner, tmp_vault):
    result = runner.invoke(
        namespace_group,
        ["move", "X", "--key", "MISSING"] + _args(tmp_vault),
    )
    assert result.exit_code != 0
    assert "Error" in result.output


def test_delete_namespace(runner, tmp_vault):
    result = runner.invoke(namespace_group, ["delete", "APP"] + _args(tmp_vault))
    assert result.exit_code == 0
    assert "Deleted 2 variable(s)" in result.output


def test_delete_unknown_namespace(runner, tmp_vault):
    result = runner.invoke(namespace_group, ["delete", "GHOST"] + _args(tmp_vault))
    assert result.exit_code == 0
    assert "Deleted 0 variable(s)" in result.output
