"""Tests for envault.cli_pin."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from envault.cli_pin import pin_group
from envault.vault import save_vault


PASSWORD = "test-password"


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def tmp_vault(tmp_path):
    path = str(tmp_path / "vault.enc")
    data = {"variables": {"API_KEY": "secret", "DB_URL": "postgres://"}}
    save_vault(path, PASSWORD, data)
    return path


def _args(vault, extra=None):
    base = ["--vault", vault, "--password", PASSWORD]
    return base + (extra or [])


def test_add_pin_output(runner, tmp_vault):
    result = runner.invoke(pin_group, ["add", "API_KEY"] + _args(tmp_vault))
    assert result.exit_code == 0
    assert "Pinned 'API_KEY'" in result.output


def test_add_pin_with_reason(runner, tmp_vault):
    result = runner.invoke(
        pin_group, ["add", "API_KEY", "--reason", "do not change"] + _args(tmp_vault)
    )
    assert result.exit_code == 0
    assert "do not change" in result.output


def test_add_pin_missing_key_error(runner, tmp_vault):
    result = runner.invoke(pin_group, ["add", "NOPE"] + _args(tmp_vault))
    assert result.exit_code != 0
    assert "does not exist" in result.output


def test_remove_pin_output(runner, tmp_vault):
    runner.invoke(pin_group, ["add", "API_KEY"] + _args(tmp_vault))
    result = runner.invoke(pin_group, ["remove", "API_KEY"] + _args(tmp_vault))
    assert result.exit_code == 0
    assert "Unpinned 'API_KEY'" in result.output


def test_remove_pin_not_pinned_error(runner, tmp_vault):
    result = runner.invoke(pin_group, ["remove", "API_KEY"] + _args(tmp_vault))
    assert result.exit_code != 0
    assert "not pinned" in result.output


def test_list_empty(runner, tmp_vault):
    result = runner.invoke(pin_group, ["list"] + _args(tmp_vault))
    assert result.exit_code == 0
    assert "No pinned" in result.output


def test_list_shows_pinned_keys(runner, tmp_vault):
    runner.invoke(pin_group, ["add", "API_KEY", "--reason", "prod key"] + _args(tmp_vault))
    runner.invoke(pin_group, ["add", "DB_URL"] + _args(tmp_vault))
    result = runner.invoke(pin_group, ["list"] + _args(tmp_vault))
    assert result.exit_code == 0
    assert "API_KEY" in result.output
    assert "prod key" in result.output
    assert "DB_URL" in result.output
