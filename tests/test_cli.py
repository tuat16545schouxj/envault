"""Tests for the envault CLI commands."""

import pytest
from click.testing import CliRunner
from envault.cli import cli


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def tmp_vault(tmp_path):
    return str(tmp_path / "test.envault")


PASSWORD = "cli-test-password"


def test_set_creates_and_confirms(runner, tmp_vault):
    result = runner.invoke(
        cli,
        ["set", "MY_KEY", "my_value", "--vault", tmp_vault,
         "--password", PASSWORD, "--password", PASSWORD],
    )
    assert result.exit_code == 0
    assert "MY_KEY" in result.output


def test_set_and_list_keys(runner, tmp_vault):
    runner.invoke(
        cli,
        ["set", "FOO", "bar", "--vault", tmp_vault,
         "--password", PASSWORD, "--password", PASSWORD],
    )
    result = runner.invoke(
        cli,
        ["list", "--vault", tmp_vault, "--password", PASSWORD],
    )
    assert result.exit_code == 0
    assert "FOO" in result.output
    assert "bar" not in result.output  # values hidden by default


def test_list_show_values(runner, tmp_vault):
    runner.invoke(
        cli,
        ["set", "SECRET", "s3cr3t", "--vault", tmp_vault,
         "--password", PASSWORD, "--password", PASSWORD],
    )
    result = runner.invoke(
        cli,
        ["list", "--vault", tmp_vault, "--password", PASSWORD, "--show-values"],
    )
    assert result.exit_code == 0
    assert "SECRET=s3cr3t" in result.output


def test_delete_removes_key(runner, tmp_vault):
    runner.invoke(
        cli,
        ["set", "TO_DELETE", "gone", "--vault", tmp_vault,
         "--password", PASSWORD, "--password", PASSWORD],
    )
    result = runner.invoke(
        cli,
        ["delete", "TO_DELETE", "--vault", tmp_vault,
         "--password", PASSWORD, "--password", PASSWORD],
    )
    assert result.exit_code == 0
    assert "TO_DELETE" in result.output


def test_list_empty_vault_message(runner, tmp_vault):
    # Create vault with one key then delete it
    runner.invoke(
        cli,
        ["set", "K", "v", "--vault", tmp_vault,
         "--password", PASSWORD, "--password", PASSWORD],
    )
    runner.invoke(
        cli,
        ["delete", "K", "--vault", tmp_vault,
         "--password", PASSWORD, "--password", PASSWORD],
    )
    result = runner.invoke(
        cli,
        ["list", "--vault", tmp_vault, "--password", PASSWORD],
    )
    assert result.exit_code == 0
    assert "empty" in result.output.lower()


def test_set_wrong_confirm_password_aborts(runner, tmp_vault):
    result = runner.invoke(
        cli,
        ["set", "X", "1", "--vault", tmp_vault,
         "--password", PASSWORD, "--password", "wrong-confirm"],
    )
    assert result.exit_code != 0
