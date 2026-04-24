"""Tests for envault.promote and envault.cli_promote."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from envault.cli_promote import promote_group
from envault.promote import PromoteError, promote_vars
from envault.vault import save_vault


PASSWORD = "test-secret"


@pytest.fixture()
def src_vault(tmp_path):
    path = tmp_path / "src.vault"
    save_vault(str(path), PASSWORD, {"KEY_A": "alpha", "KEY_B": "beta", "KEY_C": "gamma"})
    return str(path)


@pytest.fixture()
def dst_vault(tmp_path):
    path = tmp_path / "dst.vault"
    save_vault(str(path), PASSWORD, {"KEY_D": "delta"})
    return str(path)


def test_promote_all_vars(src_vault, dst_vault):
    promoted = promote_vars(src_vault, PASSWORD, dst_vault, PASSWORD)
    assert set(promoted.keys()) == {"KEY_A", "KEY_B", "KEY_C"}
    assert promoted["KEY_A"] == "alpha"


def test_promote_specific_keys(src_vault, dst_vault):
    promoted = promote_vars(src_vault, PASSWORD, dst_vault, PASSWORD, keys=["KEY_A"])
    assert promoted == {"KEY_A": "alpha"}


def test_promote_creates_dst_if_missing(src_vault, tmp_path):
    new_dst = str(tmp_path / "new_dst.vault")
    promoted = promote_vars(src_vault, PASSWORD, new_dst, PASSWORD, keys=["KEY_B"])
    assert promoted == {"KEY_B": "beta"}


def test_promote_missing_key_raises(src_vault, dst_vault):
    with pytest.raises(PromoteError, match="not found in source vault"):
        promote_vars(src_vault, PASSWORD, dst_vault, PASSWORD, keys=["MISSING"])


def test_promote_conflict_without_overwrite_raises(src_vault, tmp_path):
    dst = str(tmp_path / "conflict.vault")
    save_vault(dst, PASSWORD, {"KEY_A": "old_value"})
    with pytest.raises(PromoteError, match="already exist in destination"):
        promote_vars(src_vault, PASSWORD, dst, PASSWORD, keys=["KEY_A"])


def test_promote_conflict_with_overwrite(src_vault, tmp_path):
    dst = str(tmp_path / "overwrite.vault")
    save_vault(dst, PASSWORD, {"KEY_A": "old_value"})
    promoted = promote_vars(src_vault, PASSWORD, dst, PASSWORD, keys=["KEY_A"], overwrite=True)
    assert promoted["KEY_A"] == "alpha"


def test_promote_dry_run_does_not_write(src_vault, dst_vault):
    from envault.vault import load_vault

    before = load_vault(dst_vault, PASSWORD)
    promoted = promote_vars(src_vault, PASSWORD, dst_vault, PASSWORD, dry_run=True)
    after = load_vault(dst_vault, PASSWORD)
    assert set(promoted.keys()) == {"KEY_A", "KEY_B", "KEY_C"}
    assert before == after


def test_promote_wrong_src_password_raises(src_vault, dst_vault):
    with pytest.raises(PromoteError, match="Failed to load source vault"):
        promote_vars(src_vault, "wrong", dst_vault, PASSWORD)


# --- CLI tests ---


@pytest.fixture()
def runner():
    return CliRunner()


def test_cli_promote_run(runner, src_vault, dst_vault):
    result = runner.invoke(
        promote_group,
        ["run", src_vault, dst_vault, "--src-password", PASSWORD, "--dst-password", PASSWORD],
    )
    assert result.exit_code == 0
    assert "3 variable(s) promoted" in result.output


def test_cli_promote_dry_run_output(runner, src_vault, dst_vault):
    result = runner.invoke(
        promote_group,
        [
            "run", src_vault, dst_vault,
            "--src-password", PASSWORD,
            "--dst-password", PASSWORD,
            "--dry-run",
        ],
    )
    assert result.exit_code == 0
    assert "[dry-run]" in result.output


def test_cli_promote_missing_key_error(runner, src_vault, dst_vault):
    result = runner.invoke(
        promote_group,
        [
            "run", src_vault, dst_vault,
            "--src-password", PASSWORD,
            "--dst-password", PASSWORD,
            "-k", "DOES_NOT_EXIST",
        ],
    )
    assert result.exit_code != 0
    assert "not found in source vault" in result.output
