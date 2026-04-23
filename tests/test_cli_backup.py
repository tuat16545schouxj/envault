"""Tests for envault.cli_backup."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_backup import backup_group


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def tmp_vault(tmp_path: Path) -> Path:
    vf = tmp_path / "vault.enc"
    vf.write_bytes(b"fake-vault-data")
    return vf


def _args(tmp_vault: Path, *extra: str) -> list[str]:
    return ["--vault", str(tmp_vault), *extra]


def test_create_outputs_path(runner: CliRunner, tmp_vault: Path) -> None:
    result = runner.invoke(backup_group, ["create", "--vault", str(tmp_vault)])
    assert result.exit_code == 0
    assert "Backup created" in result.output


def test_create_with_label(runner: CliRunner, tmp_vault: Path) -> None:
    result = runner.invoke(
        backup_group, ["create", "--vault", str(tmp_vault), "--label", "mytest"]
    )
    assert result.exit_code == 0
    assert "mytest" in result.output


def test_list_empty(runner: CliRunner, tmp_vault: Path) -> None:
    result = runner.invoke(backup_group, ["list", "--vault", str(tmp_vault)])
    assert result.exit_code == 0
    assert "No backups found" in result.output


def test_create_and_list(runner: CliRunner, tmp_vault: Path) -> None:
    runner.invoke(backup_group, ["create", "--vault", str(tmp_vault)])
    result = runner.invoke(backup_group, ["list", "--vault", str(tmp_vault)])
    assert result.exit_code == 0
    assert ".bak" in result.output


def test_restore_from_backup(runner: CliRunner, tmp_vault: Path) -> None:
    original = tmp_vault.read_bytes()
    create_result = runner.invoke(backup_group, ["create", "--vault", str(tmp_vault)])
    backup_path = create_result.output.strip().split(": ", 1)[1]
    tmp_vault.write_bytes(b"corrupted")
    result = runner.invoke(
        backup_group, ["restore", "--vault", str(tmp_vault), backup_path]
    )
    assert result.exit_code == 0
    assert "restored" in result.output
    assert tmp_vault.read_bytes() == original


def test_delete_backup(runner: CliRunner, tmp_vault: Path) -> None:
    create_result = runner.invoke(backup_group, ["create", "--vault", str(tmp_vault)])
    backup_path = create_result.output.strip().split(": ", 1)[1]
    result = runner.invoke(backup_group, ["delete", backup_path])
    assert result.exit_code == 0
    assert "Deleted" in result.output
    assert not Path(backup_path).exists()


def test_prune_removes_old(runner: CliRunner, tmp_vault: Path) -> None:
    for i in range(4):
        runner.invoke(backup_group, ["create", "--vault", str(tmp_vault), "--label", f"b{i}"])
    result = runner.invoke(
        backup_group, ["prune", "--vault", str(tmp_vault), "--keep", "2"]
    )
    assert result.exit_code == 0
    assert "Deleted" in result.output


def test_create_missing_vault_error(runner: CliRunner, tmp_path: Path) -> None:
    result = runner.invoke(
        backup_group, ["create", "--vault", str(tmp_path / "ghost.enc")]
    )
    assert result.exit_code != 0
    assert "Error" in result.output
