"""Tests for envault.cli_quota."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_quota import quota_group
from envault.vault import save_vault
from envault.quota import get_quota

PASSWORD = "cli-secret"


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def tmp_vault(tmp_path: Path) -> Path:
    path = tmp_path / "vault.env"
    save_vault(path, PASSWORD, {"vars": {"A": "1", "B": "2", "C": "3"}})
    return path


def _args(tmp_vault: Path, *extra: str) -> list[str]:
    return ["--vault", str(tmp_vault), "--password", PASSWORD, *extra]


def test_set_quota_output(runner: CliRunner, tmp_vault: Path) -> None:
    result = runner.invoke(quota_group, ["set", *_args(tmp_vault), "10"])
    assert result.exit_code == 0
    assert "Quota set to 10" in result.output


def test_set_quota_invalid_persists_error(runner: CliRunner, tmp_vault: Path) -> None:
    result = runner.invoke(quota_group, ["set", *_args(tmp_vault), "0"])
    assert result.exit_code != 0
    assert "positive integer" in result.output


def test_remove_quota_output(runner: CliRunner, tmp_vault: Path) -> None:
    runner.invoke(quota_group, ["set", *_args(tmp_vault), "5"])
    result = runner.invoke(quota_group, ["remove", *_args(tmp_vault)])
    assert result.exit_code == 0
    assert "removed" in result.output.lower()
    assert get_quota(tmp_vault, PASSWORD) is None


def test_show_no_quota(runner: CliRunner, tmp_vault: Path) -> None:
    result = runner.invoke(quota_group, ["show", *_args(tmp_vault)])
    assert result.exit_code == 0
    assert "No quota set" in result.output
    assert "3" in result.output  # 3 vars in use


def test_show_within_limit(runner: CliRunner, tmp_vault: Path) -> None:
    runner.invoke(quota_group, ["set", *_args(tmp_vault), "10"])
    result = runner.invoke(quota_group, ["show", *_args(tmp_vault)])
    assert result.exit_code == 0
    assert "3/10" in result.output
    assert "7 remaining" in result.output
    assert "EXCEEDED" not in result.output


def test_show_exceeded(runner: CliRunner, tmp_vault: Path) -> None:
    runner.invoke(quota_group, ["set", *_args(tmp_vault), "2"])
    result = runner.invoke(quota_group, ["show", *_args(tmp_vault)])
    assert result.exit_code == 0
    assert "EXCEEDED" in result.output
