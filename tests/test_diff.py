"""Tests for envault.diff module."""

import json
import os
import pytest

from envault.diff import DiffEntry, DiffError, diff_dicts, diff_vaults
from envault.vault import save_vault


# ---------------------------------------------------------------------------
# diff_dicts
# ---------------------------------------------------------------------------

def test_diff_dicts_added():
    entries = diff_dicts({}, {"NEW": "1"})
    assert len(entries) == 1
    assert entries[0].key == "NEW"
    assert entries[0].status == "added"


def test_diff_dicts_removed():
    entries = diff_dicts({"OLD": "1"}, {})
    assert len(entries) == 1
    assert entries[0].key == "OLD"
    assert entries[0].status == "removed"


def test_diff_dicts_changed():
    entries = diff_dicts({"K": "old"}, {"K": "new"})
    assert len(entries) == 1
    assert entries[0].status == "changed"


def test_diff_dicts_unchanged():
    entries = diff_dicts({"K": "same"}, {"K": "same"})
    assert len(entries) == 1
    assert entries[0].status == "unchanged"


def test_diff_dicts_sorted_keys():
    old = {"B": "1", "A": "1"}
    new = {"B": "1", "C": "1"}
    entries = diff_dicts(old, new)
    keys = [e.key for e in entries]
    assert keys == sorted(keys)


def test_diff_dicts_show_values_false_hides_values():
    entries = diff_dicts({"K": "secret"}, {"K": "other"}, show_values=False)
    assert entries[0].old_value is None
    assert entries[0].new_value is None


def test_diff_dicts_show_values_true_exposes_values():
    entries = diff_dicts({"K": "secret"}, {"K": "other"}, show_values=True)
    assert entries[0].old_value == "secret"
    assert entries[0].new_value == "other"


def test_diff_entry_to_dict():
    entry = DiffEntry(key="X", status="added", new_value="v")
    d = entry.to_dict()
    assert d["key"] == "X"
    assert d["status"] == "added"
    assert d["new_value"] == "v"
    assert d["old_value"] is None


# ---------------------------------------------------------------------------
# diff_vaults
# ---------------------------------------------------------------------------

@pytest.fixture()
def two_vaults(tmp_path):
    path_a = str(tmp_path / "a.vault")
    path_b = str(tmp_path / "b.vault")
    save_vault(path_a, "pass", {"variables": {"FOO": "bar", "SHARED": "same"}})
    save_vault(path_b, "pass", {"variables": {"BAZ": "qux", "SHARED": "same"}})
    return path_a, path_b


def test_diff_vaults_detects_added_and_removed(two_vaults):
    path_a, path_b = two_vaults
    entries = diff_vaults(path_a, "pass", path_b, "pass")
    statuses = {e.key: e.status for e in entries}
    assert statuses["FOO"] == "removed"
    assert statuses["BAZ"] == "added"
    assert statuses["SHARED"] == "unchanged"


def test_diff_vaults_wrong_password_raises(two_vaults):
    path_a, path_b = two_vaults
    with pytest.raises(DiffError, match="vault A"):
        diff_vaults(path_a, "wrong", path_b, "pass")


def test_diff_vaults_missing_file_raises(tmp_path):
    with pytest.raises(DiffError):
        diff_vaults(str(tmp_path / "nope.vault"), "p", str(tmp_path / "nope2.vault"), "p")
