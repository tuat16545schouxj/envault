"""Tests for envault.rotate and the rotate CLI command."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.rotate import RotateError, rotate_key
from envault.vault import load_vault, save_vault
from envault.cli_rotate import rotate_command


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    path = tmp_path / ".envault"
    save_vault(path, {"KEY1": "value1", "KEY2": "value2"}, "old-pass")
    return path


def test_rotate_key_reencrypts_variables(vault_file: Path) -> None:
    count = rotate_key(vault_file, "old-pass", "new-pass", audit=False)
    assert count == 2


def test_rotate_key_new_password_works(vault_file: Path) -> None:
    rotate_key(vault_file, "old-pass", "new-pass", audit=False)
    variables = load_vault(vault_file, "new-pass")
    assert variables == {"KEY1": "value1", "KEY2": "value2"}


def test_rotate_key_old_password_no_longer_works(vault_file: Path) -> None:
    from envault.vault import VaultError

    rotate_key(vault_file, "old-pass", "new-pass", audit=False)
    with pytest.raises(VaultError):
        load_vault(vault_file, "old-pass")


def test_rotate_key_wrong_old_password_raises(vault_file: Path) -> None:
    with pytest.raises(RotateError, match="Failed to load vault"):
        rotate_key(vault_file, "wrong-pass", "new-pass", audit=False)


def test_rotate_key_same_password_raises(vault_file: Path) -> None:
    with pytest.raises(RotateError, match="must differ"):
        rotate_key(vault_file, "old-pass", "old-pass", audit=False)


def test_rotate_key_empty_old_password_raises(vault_file: Path) -> None:
    with pytest.raises(RotateError, match="Old password must not be empty"):
        rotate_key(vault_file, "", "new-pass", audit=False)


def test_rotate_key_empty_new_password_raises(vault_file: Path) -> None:
    with pytest.raises(RotateError, match="New password must not be empty"):
        rotate_key(vault_file, "old-pass", "", audit=False)


def test_rotate_command_success(vault_file: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        rotate_command,
        ["--vault", str(vault_file), "--old-password", "old-pass", "--new-password", "new-pass"],
    )
    assert result.exit_code == 0
    assert "Key rotated successfully" in result.output
    assert "2 variable(s)" in result.output


def test_rotate_command_wrong_password(vault_file: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        rotate_command,
        ["--vault", str(vault_file), "--old-password", "bad", "--new-password", "new-pass"],
    )
    assert result.exit_code != 0
    assert "Error" in result.output
