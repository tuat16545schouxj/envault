"""Tests for envault.label."""
from __future__ import annotations

import pytest
from click.testing import CliRunner

from envault.cli_label import label_group
from envault.label import LabelError, add_label, keys_for_label, list_labels, remove_label
from envault.vault import save_vault


@pytest.fixture()
def vault_file(tmp_path):
    path = str(tmp_path / "vault.env")
    save_vault(path, "pass", {"API_KEY": "abc", "DB_URL": "postgres://", "SECRET": "s3cr3t"})
    return path


def test_add_label_success(vault_file):
    add_label(vault_file, "pass", "API_KEY", "production")
    assert "production" in list_labels(vault_file, "pass", "API_KEY")


def test_add_label_idempotent(vault_file):
    add_label(vault_file, "pass", "API_KEY", "production")
    add_label(vault_file, "pass", "API_KEY", "production")
    assert list_labels(vault_file, "pass", "API_KEY").count("production") == 1


def test_add_label_missing_key_raises(vault_file):
    with pytest.raises(LabelError, match="not found"):
        add_label(vault_file, "pass", "MISSING", "env")


def test_add_label_empty_label_raises(vault_file):
    with pytest.raises(LabelError, match="empty"):
        add_label(vault_file, "pass", "API_KEY", "   ")


def test_list_labels_sorted(vault_file):
    add_label(vault_file, "pass", "API_KEY", "zebra")
    add_label(vault_file, "pass", "API_KEY", "alpha")
    assert list_labels(vault_file, "pass", "API_KEY") == ["alpha", "zebra"]


def test_list_labels_empty(vault_file):
    assert list_labels(vault_file, "pass", "DB_URL") == []


def test_remove_label_success(vault_file):
    add_label(vault_file, "pass", "API_KEY", "staging")
    remove_label(vault_file, "pass", "API_KEY", "staging")
    assert "staging" not in list_labels(vault_file, "pass", "API_KEY")


def test_remove_label_not_present_raises(vault_file):
    with pytest.raises(LabelError, match="not found"):
        remove_label(vault_file, "pass", "API_KEY", "nonexistent")


def test_keys_for_label_returns_correct_keys(vault_file):
    add_label(vault_file, "pass", "API_KEY", "critical")
    add_label(vault_file, "pass", "SECRET", "critical")
    result = keys_for_label(vault_file, "pass", "critical")
    assert result == ["API_KEY", "SECRET"]


def test_keys_for_label_empty_when_none(vault_file):
    assert keys_for_label(vault_file, "pass", "ghost") == []


# --- CLI tests ---

@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def tmp_vault(tmp_path):
    path = str(tmp_path / "vault.env")
    save_vault(path, "pass", {"FOO": "bar", "BAZ": "qux"})
    return path


def _args(tmp_vault, *extra):
    return ["--vault", tmp_vault, "--password", "pass", *extra]


def test_cli_add_label_output(runner, tmp_vault):
    result = runner.invoke(label_group, ["add"] + _args(tmp_vault, "FOO", "env:prod"))
    assert result.exit_code == 0
    assert "added" in result.output


def test_cli_list_labels_output(runner, tmp_vault):
    runner.invoke(label_group, ["add"] + _args(tmp_vault, "FOO", "env:prod"))
    result = runner.invoke(label_group, ["list"] + _args(tmp_vault, "FOO"))
    assert "env:prod" in result.output


def test_cli_keys_command(runner, tmp_vault):
    runner.invoke(label_group, ["add"] + _args(tmp_vault, "FOO", "shared"))
    runner.invoke(label_group, ["add"] + _args(tmp_vault, "BAZ", "shared"))
    result = runner.invoke(label_group, ["keys"] + _args(tmp_vault, "shared"))
    assert "FOO" in result.output
    assert "BAZ" in result.output


def test_cli_remove_label_output(runner, tmp_vault):
    runner.invoke(label_group, ["add"] + _args(tmp_vault, "FOO", "temp"))
    result = runner.invoke(label_group, ["remove"] + _args(tmp_vault, "FOO", "temp"))
    assert result.exit_code == 0
    assert "removed" in result.output
