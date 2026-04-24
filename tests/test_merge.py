"""Tests for envault.merge."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from envault.merge import ConflictStrategy, MergeError, merge_vaults
from envault.vault import load_vault, save_vault
from envault.cli_merge import merge_group


@pytest.fixture()
def src_vault(tmp_path):
    path = str(tmp_path / "src.vault")
    save_vault(path, "srcpass", {"A": "1", "B": "2", "C": "3"})
    return path


@pytest.fixture()
def dst_vault(tmp_path):
    path = str(tmp_path / "dst.vault")
    save_vault(path, "dstpass", {"B": "original_b", "D": "4"})
    return path


# ---------------------------------------------------------------------------
# merge_vaults unit tests
# ---------------------------------------------------------------------------

def test_merge_all_keys_added_when_no_conflicts(src_vault, tmp_path):
    dst = str(tmp_path / "empty.vault")
    result = merge_vaults(src_vault, "srcpass", dst, "dstpass")
    assert sorted(result.added) == ["A", "B", "C"]
    assert result.overwritten == []
    assert result.skipped == []
    merged = load_vault(dst, "dstpass")
    assert merged == {"A": "1", "B": "2", "C": "3"}


def test_merge_keep_dst_skips_conflicts(src_vault, dst_vault):
    result = merge_vaults(src_vault, "srcpass", dst_vault, "dstpass",
                          strategy=ConflictStrategy.KEEP_DST)
    assert "A" in result.added
    assert "C" in result.added
    assert "B" in result.skipped
    merged = load_vault(dst_vault, "dstpass")
    assert merged["B"] == "original_b"  # not overwritten
    assert merged["D"] == "4"           # preserved


def test_merge_keep_src_overwrites_conflicts(src_vault, dst_vault):
    result = merge_vaults(src_vault, "srcpass", dst_vault, "dstpass",
                          strategy=ConflictStrategy.KEEP_SRC)
    assert "B" in result.overwritten
    merged = load_vault(dst_vault, "dstpass")
    assert merged["B"] == "2"  # overwritten with src value


def test_merge_raise_strategy_raises_on_conflict(src_vault, dst_vault):
    with pytest.raises(MergeError, match="Conflict on key 'B'"):
        merge_vaults(src_vault, "srcpass", dst_vault, "dstpass",
                     strategy=ConflictStrategy.RAISE)


def test_merge_specific_keys_only(src_vault, dst_vault):
    result = merge_vaults(src_vault, "srcpass", dst_vault, "dstpass",
                          keys=["A", "C"])
    assert result.added == ["A", "C"]
    merged = load_vault(dst_vault, "dstpass")
    assert "A" in merged
    assert "C" in merged
    assert merged.get("B") == "original_b"  # untouched


def test_merge_missing_key_in_src_raises(src_vault, dst_vault):
    with pytest.raises(MergeError, match="Keys not found in source vault"):
        merge_vaults(src_vault, "srcpass", dst_vault, "dstpass", keys=["NOPE"])


def test_merge_wrong_src_password_raises(src_vault, dst_vault):
    with pytest.raises(MergeError, match="Cannot load source vault"):
        merge_vaults(src_vault, "wrongpass", dst_vault, "dstpass")


def test_merge_missing_src_file_raises(tmp_path, dst_vault):
    with pytest.raises(MergeError, match="Cannot load source vault"):
        merge_vaults(str(tmp_path / "ghost.vault"), "x", dst_vault, "dstpass")


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def runner():
    return CliRunner()


def test_cli_merge_run_success(runner, src_vault, tmp_path):
    dst = str(tmp_path / "new.vault")
    result = runner.invoke(
        merge_group,
        ["run", src_vault, dst,
         "--src-password", "srcpass",
         "--dst-password", "dstpass"],
    )
    assert result.exit_code == 0, result.output
    assert "Merge complete" in result.output
    assert "3 key(s)" in result.output


def test_cli_merge_run_conflict_raise(runner, src_vault, dst_vault):
    result = runner.invoke(
        merge_group,
        ["run", src_vault, dst_vault,
         "--src-password", "srcpass",
         "--dst-password", "dstpass",
         "--strategy", "raise"],
    )
    assert result.exit_code != 0
    assert "Conflict" in result.output


def test_cli_merge_run_keep_src(runner, src_vault, dst_vault):
    result = runner.invoke(
        merge_group,
        ["run", src_vault, dst_vault,
         "--src-password", "srcpass",
         "--dst-password", "dstpass",
         "--strategy", "keep_src"],
    )
    assert result.exit_code == 0, result.output
    assert "Updated" in result.output
