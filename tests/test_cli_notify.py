"""Tests for envault.cli_notify."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_notify import notify_group
from envault.vault import save_vault


PASSWORD = "testpass"


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def tmp_vault(tmp_path: Path) -> Path:
    path = tmp_path / "vault.enc"
    save_vault(path, PASSWORD, {})
    return path


def _args(tmp_vault: Path, *extra: str) -> list[str]:
    return ["--vault", str(tmp_vault), "--password", PASSWORD, *extra]


def test_add_slack_channel_output(runner: CliRunner, tmp_vault: Path) -> None:
    result = runner.invoke(
        notify_group,
        ["add"] + _args(tmp_vault, "--kind", "slack", "--target", "https://hooks.slack.com/T", "--events", "set,delete"),
    )
    assert result.exit_code == 0
    assert "slack" in result.output
    assert "https://hooks.slack.com/T" in result.output


def test_add_invalid_kind_shows_error(runner: CliRunner, tmp_vault: Path) -> None:
    result = runner.invoke(
        notify_group,
        ["add"] + _args(tmp_vault, "--kind", "sms", "--target", "123", "--events", "set"),
    )
    assert result.exit_code != 0


def test_list_empty_vault(runner: CliRunner, tmp_vault: Path) -> None:
    result = runner.invoke(notify_group, ["list"] + _args(tmp_vault))
    assert result.exit_code == 0
    assert "No notification channels" in result.output


def test_list_shows_channels(runner: CliRunner, tmp_vault: Path) -> None:
    runner.invoke(
        notify_group,
        ["add"] + _args(tmp_vault, "--kind", "email", "--target", "ops@example.com", "--events", "rotate"),
    )
    result = runner.invoke(notify_group, ["list"] + _args(tmp_vault))
    assert result.exit_code == 0
    assert "ops@example.com" in result.output
    assert "rotate" in result.output


def test_remove_channel_output(runner: CliRunner, tmp_vault: Path) -> None:
    runner.invoke(
        notify_group,
        ["add"] + _args(tmp_vault, "--kind", "email", "--target", "ops@example.com", "--events", "set"),
    )
    result = runner.invoke(notify_group, ["remove"] + _args(tmp_vault, "--target", "ops@example.com"))
    assert result.exit_code == 0
    assert "Removed" in result.output


def test_remove_missing_channel_shows_error(runner: CliRunner, tmp_vault: Path) -> None:
    result = runner.invoke(notify_group, ["remove"] + _args(tmp_vault, "--target", "ghost@example.com"))
    assert result.exit_code != 0
    assert "Error" in result.output
