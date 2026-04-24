"""Tests for envault.access — access control rules."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from envault.access import AccessError, check_access, list_rules, remove_rule, set_rule
from envault.cli_access import access_group
from envault.vault import save_vault


@pytest.fixture()
def vault_file(tmp_path):
    path = tmp_path / "vault.enc"
    save_vault(str(path), "pass", {"DB_HOST": "localhost", "API_KEY": "secret", "PORT": "5432"})
    return str(path)


# --- unit tests ---

def test_set_rule_stores_rule(vault_file):
    set_rule(vault_file, "pass", "DB_*", "ro")
    rules = list_rules(vault_file, "pass")
    assert any(r["pattern"] == "DB_*" and r["mode"] == "ro" for r in rules)


def test_set_rule_invalid_mode_raises(vault_file):
    with pytest.raises(AccessError, match="Invalid mode"):
        set_rule(vault_file, "pass", "DB_*", "write")


def test_list_rules_sorted(vault_file):
    set_rule(vault_file, "pass", "Z_*", "ro")
    set_rule(vault_file, "pass", "A_*", "rw")
    rules = list_rules(vault_file, "pass")
    patterns = [r["pattern"] for r in rules]
    assert patterns == sorted(patterns)


def test_remove_rule_success(vault_file):
    set_rule(vault_file, "pass", "API_*", "none")
    remove_rule(vault_file, "pass", "API_*")
    rules = list_rules(vault_file, "pass")
    assert not any(r["pattern"] == "API_*" for r in rules)


def test_remove_rule_missing_raises(vault_file):
    with pytest.raises(AccessError, match="No access rule"):
        remove_rule(vault_file, "pass", "NONEXISTENT_*")


def test_check_access_rw_default(vault_file):
    assert check_access(vault_file, "pass", "PORT", "rw") is True


def test_check_access_ro_rule_denies_rw(vault_file):
    set_rule(vault_file, "pass", "DB_*", "ro")
    assert check_access(vault_file, "pass", "DB_HOST", "rw") is False


def test_check_access_ro_rule_allows_ro(vault_file):
    set_rule(vault_file, "pass", "DB_*", "ro")
    assert check_access(vault_file, "pass", "DB_HOST", "ro") is True


def test_check_access_none_rule_denies_all(vault_file):
    set_rule(vault_file, "pass", "API_*", "none")
    assert check_access(vault_file, "pass", "API_KEY", "ro") is False
    assert check_access(vault_file, "pass", "API_KEY", "rw") is False


# --- CLI tests ---

@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def tmp_vault(tmp_path):
    path = tmp_path / "vault.enc"
    save_vault(str(path), "pass", {"SECRET": "val"})
    return str(path)


def _args(tmp_vault, *extra):
    return ["--vault", tmp_vault, "--password", "pass", *extra]


def test_cli_set_and_list(runner, tmp_vault):
    result = runner.invoke(access_group, ["set", *_args(tmp_vault), "SECRET*", "ro"])
    assert result.exit_code == 0
    assert "ro" in result.output
    result = runner.invoke(access_group, ["list", *_args(tmp_vault)])
    assert "SECRET*" in result.output


def test_cli_check_allowed(runner, tmp_vault):
    runner.invoke(access_group, ["set", *_args(tmp_vault), "SECRET*", "rw"])
    result = runner.invoke(access_group, ["check", *_args(tmp_vault), "SECRET", "rw"])
    assert result.exit_code == 0
    assert "ALLOWED" in result.output


def test_cli_check_denied(runner, tmp_vault):
    runner.invoke(access_group, ["set", *_args(tmp_vault), "SECRET*", "ro"])
    result = runner.invoke(access_group, ["check", *_args(tmp_vault), "SECRET", "rw"])
    assert result.exit_code != 0
    assert "DENIED" in result.output
