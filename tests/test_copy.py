"""Tests for envault.copy module."""

import pytest

from envault.copy import CopyError, copy_vars
from envault.vault import save_vault


@pytest.fixture
def src_vault(tmp_path):
    path = str(tmp_path / "src.vault")
    save_vault(path, "srcpass", {"FOO": "bar", "BAZ": "qux", "SECRET": "s3cr3t"})
    return path


@pytest.fixture
def dst_vault(tmp_path):
    path = str(tmp_path / "dst.vault")
    save_vault(path, "dstpass", {"EXISTING": "value"})
    return path


def test_copy_all_vars(src_vault, dst_vault):
    copied = copy_vars(src_vault, dst_vault, "srcpass", "dstpass")
    assert set(copied.keys()) == {"FOO", "BAZ", "SECRET"}


def test_copy_specific_keys(src_vault, dst_vault):
    copied = copy_vars(src_vault, dst_vault, "srcpass", "dstpass", keys=["FOO"])
    assert copied == {"FOO": "bar"}


def test_copy_preserves_existing_dst_keys(src_vault, dst_vault):
    from envault.vault import load_vault
    copy_vars(src_vault, dst_vault, "srcpass", "dstpass", keys=["FOO"])
    data = load_vault(dst_vault, "dstpass")
    assert data["EXISTING"] == "value"
    assert data["FOO"] == "bar"


def test_copy_missing_key_raises(src_vault, dst_vault):
    with pytest.raises(CopyError, match="Keys not found in source"):
        copy_vars(src_vault, dst_vault, "srcpass", "dstpass", keys=["MISSING"])


def test_copy_conflict_raises_without_overwrite(src_vault, dst_vault):
    from envault.vault import save_vault
    save_vault(dst_vault, "dstpass", {"FOO": "old"})
    with pytest.raises(CopyError, match="already exist in destination"):
        copy_vars(src_vault, dst_vault, "srcpass", "dstpass", keys=["FOO"])


def test_copy_conflict_overwrite(src_vault, dst_vault):
    from envault.vault import save_vault, load_vault
    save_vault(dst_vault, "dstpass", {"FOO": "old"})
    copy_vars(src_vault, dst_vault, "srcpass", "dstpass", keys=["FOO"], overwrite=True)
    data = load_vault(dst_vault, "dstpass")
    assert data["FOO"] == "bar"


def test_copy_wrong_src_password_raises(src_vault, dst_vault):
    with pytest.raises(CopyError, match="Failed to load source vault"):
        copy_vars(src_vault, dst_vault, "wrongpass", "dstpass")


def test_copy_to_nonexistent_dst(src_vault, tmp_path):
    new_dst = str(tmp_path / "new.vault")
    copied = copy_vars(src_vault, new_dst, "srcpass", "newpass", keys=["FOO"])
    assert copied == {"FOO": "bar"}
