"""Tests for envault.cli_profile CLI commands."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_profile import profile_group
from envault.vault import save_vault

PASSWORD = "cli-test-pass"


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def tmp_vault(tmp_path: Path) -> Path:
    path = tmp_path / ".envault"
    save_vault(path, PASSWORD, {"DB_URL": "postgres://localhost", "PORT": "5432"})
    return path


def _args(vault: Path, subcmd: str, *extra: str) -> list:
    return [subcmd, "--vault", str(vault), "--password", PASSWORD, *extra]


def test_save_and_list_profile(runner: CliRunner, tmp_vault: Path) -> None:
    result = runner.invoke(profile_group, _args(tmp_vault, "save", "dev"))
    assert result.exit_code == 0
    assert "saved" in result.output

    result = runner.invoke(profile_group, _args(tmp_vault, "list"))
    assert result.exit_code == 0
    assert "dev" in result.output


def test_list_empty_vault(runner: CliRunner, tmp_path: Path) -> None:
    path = tmp_path / ".envault"
    save_vault(path, PASSWORD, {})
    result = runner.invoke(profile_group, _args(path, "list"))
    assert result.exit_code == 0
    assert "No profiles found" in result.output


def test_show_profile_displays_vars(runner: CliRunner, tmp_vault: Path) -> None:
    runner.invoke(profile_group, _args(tmp_vault, "save", "dev"))
    result = runner.invoke(profile_group, _args(tmp_vault, "show", "dev"))
    assert result.exit_code == 0
    assert "DB_URL" in result.output
    assert "PORT" in result.output


def test_show_nonexistent_profile_errors(runner: CliRunner, tmp_vault: Path) -> None:
    result = runner.invoke(profile_group, _args(tmp_vault, "show", "ghost"))
    assert result.exit_code != 0
    assert "does not exist" in result.output


def test_delete_profile(runner: CliRunner, tmp_vault: Path) -> None:
    runner.invoke(profile_group, _args(tmp_vault, "save", "staging"))
    result = runner.invoke(profile_group, _args(tmp_vault, "delete", "staging"))
    assert result.exit_code == 0
    assert "deleted" in result.output

    result = runner.invoke(profile_group, _args(tmp_vault, "list"))
    assert "staging" not in result.output


def test_delete_nonexistent_profile_errors(runner: CliRunner, tmp_vault: Path) -> None:
    result = runner.invoke(profile_group, _args(tmp_vault, "delete", "missing"))
    assert result.exit_code != 0
    assert "does not exist" in result.output
