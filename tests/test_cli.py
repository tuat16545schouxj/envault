"""Tests for envault CLI commands, including the new export command."""

import json
import os

import pytest
from click.testing import CliRunner

from envault.cli import cli


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def tmp_vault(tmp_path):
    return str(tmp_path / ".envault")


# ── existing command smoke tests ──────────────────────────────────────────────

def test_set_creates_and_confirms(runner, tmp_vault):
    result = runner.invoke(
        cli, ["set", "FOO", "bar", "--vault", tmp_vault, "--password", "pw", "--password", "pw"]
    )
    assert result.exit_code == 0
    assert "Set FOO" in result.output


def test_set_and_list_keys(runner, tmp_vault):
    runner.invoke(cli, ["set", "A", "1", "--vault", tmp_vault, "--password", "pw", "--password", "pw"])
    runner.invoke(cli, ["set", "B", "2", "--vault", tmp_vault, "--password", "pw", "--password", "pw"])
    result = runner.invoke(cli, ["list", "--vault", tmp_vault, "--password", "pw", "--password", "pw"])
    assert "A=***" in result.output
    assert "B=***" in result.output


def test_list_show_values(runner, tmp_vault):
    runner.invoke(cli, ["set", "KEY", "secret", "--vault", tmp_vault, "--password", "pw", "--password", "pw"])
    result = runner.invoke(
        cli, ["list", "--show-values", "--vault", tmp_vault, "--password", "pw", "--password", "pw"]
    )
    assert "KEY=secret" in result.output


# ── export command tests ──────────────────────────────────────────────────────

def _seed_vault(runner, tmp_vault):
    for key, val in [("DB_URL", "postgres://localhost/mydb"), ("TOKEN", "abc123")]:
        runner.invoke(
            cli, ["set", key, val, "--vault", tmp_vault, "--password", "pw", "--password", "pw"]
        )


def test_export_dotenv_stdout(runner, tmp_vault):
    _seed_vault(runner, tmp_vault)
    result = runner.invoke(
        cli, ["export", "--vault", tmp_vault, "--format", "dotenv", "--password", "pw", "--password", "pw"]
    )
    assert result.exit_code == 0
    assert 'DB_URL="postgres://localhost/mydb"' in result.output
    assert 'TOKEN="abc123"' in result.output


def test_export_shell_stdout(runner, tmp_vault):
    _seed_vault(runner, tmp_vault)
    result = runner.invoke(
        cli, ["export", "--vault", tmp_vault, "--format", "shell", "--password", "pw", "--password", "pw"]
    )
    assert result.exit_code == 0
    assert "export DB_URL=" in result.output
    assert "export TOKEN=" in result.output


def test_export_json_stdout(runner, tmp_vault):
    _seed_vault(runner, tmp_vault)
    result = runner.invoke(
        cli, ["export", "--vault", tmp_vault, "--format", "json", "--password", "pw", "--password", "pw"]
    )
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed["TOKEN"] == "abc123"
    assert parsed["DB_URL"] == "postgres://localhost/mydb"


def test_export_to_file(runner, tmp_vault, tmp_path):
    _seed_vault(runner, tmp_vault)
    out_file = str(tmp_path / "env.json")
    result = runner.invoke(
        cli,
        ["export", "--vault", tmp_vault, "--format", "json", "-o", out_file,
         "--password", "pw", "--password", "pw"],
    )
    assert result.exit_code == 0
    assert os.path.exists(out_file)
    with open(out_file) as fh:
        parsed = json.load(fh)
    assert parsed["TOKEN"] == "abc123"


def test_export_empty_vault(runner, tmp_vault):
    """Exporting an empty vault should succeed and produce empty output."""
    # create vault first by setting then deleting a key
    runner.invoke(cli, ["set", "TMP", "v", "--vault", tmp_vault, "--password", "pw", "--password", "pw"])
    runner.invoke(cli, ["delete", "TMP", "--vault", tmp_vault, "--password", "pw", "--password", "pw"])
    result = runner.invoke(
        cli, ["export", "--vault", tmp_vault, "--format", "dotenv", "--password", "pw", "--password", "pw"]
    )
    assert result.exit_code == 0
    assert result.output == ""
