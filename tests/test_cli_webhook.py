"""Tests for envault.cli_webhook CLI commands."""

from __future__ import annotations

import pytest
from click.testing import CliRunner
from unittest.mock import MagicMock, patch

from envault.cli_webhook import webhook_group
from envault.vault import save_vault


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def tmp_vault(tmp_path):
    path = str(tmp_path / "vault.enc")
    save_vault(path, "pw", {})
    return path


def _args(tmp_vault, *extra):
    return ["--vault", tmp_vault, "--password", "pw", *extra]


def test_add_webhook_output(runner, tmp_vault):
    result = runner.invoke(
        webhook_group,
        _args(tmp_vault, "add", "slack", "https://hooks.example.com", "--event", "set"),
    )
    assert result.exit_code == 0
    assert "slack" in result.output
    assert "registered" in result.output


def test_add_webhook_invalid_url(runner, tmp_vault):
    result = runner.invoke(
        webhook_group,
        _args(tmp_vault, "add", "bad", "ftp://bad", "--event", "set"),
    )
    assert result.exit_code != 0
    assert "Invalid URL" in result.output


def test_list_empty(runner, tmp_vault):
    result = runner.invoke(webhook_group, _args(tmp_vault, "list"))
    assert result.exit_code == 0
    assert "No webhooks" in result.output


def test_list_shows_hooks(runner, tmp_vault):
    runner.invoke(
        webhook_group,
        _args(tmp_vault, "add", "myhook", "https://example.com", "--event", "set"),
    )
    result = runner.invoke(webhook_group, _args(tmp_vault, "list"))
    assert "myhook" in result.output
    assert "https://example.com" in result.output


def test_remove_webhook(runner, tmp_vault):
    runner.invoke(
        webhook_group,
        _args(tmp_vault, "add", "hook", "https://example.com", "--event", "set"),
    )
    result = runner.invoke(webhook_group, _args(tmp_vault, "remove", "hook"))
    assert result.exit_code == 0
    assert "removed" in result.output


def test_fire_command_no_matching_hooks(runner, tmp_vault):
    result = runner.invoke(webhook_group, _args(tmp_vault, "fire", "set"))
    assert result.exit_code == 0
    assert "No webhooks matched" in result.output


def test_fire_command_with_hook(runner, tmp_vault):
    runner.invoke(
        webhook_group,
        _args(tmp_vault, "add", "hook", "https://example.com", "--event", "set"),
    )
    mock_resp = MagicMock(ok=True, status_code=200)
    with patch("envault.webhook.requests.post", return_value=mock_resp):
        result = runner.invoke(webhook_group, _args(tmp_vault, "fire", "set"))
    assert result.exit_code == 0
    assert "OK" in result.output
