"""Tests for envault.lint module."""
import json
import pytest
from click.testing import CliRunner

from envault.vault import save_vault
from envault.lint import lint_vars, LintError


@pytest.fixture
def vault_file(tmp_path):
    return str(tmp_path / "vault.json")


def _make_vault(vault_file, variables: dict, password="pass"):
    data = {"variables": variables}
    save_vault(vault_file, password, data)


def test_no_issues_clean_vault(vault_file):
    _make_vault(vault_file, {"DATABASE_URL": "postgres://localhost/db"})
    issues = lint_vars(vault_file, "pass")
    assert issues == []


def test_e001_lowercase_key(vault_file):
    _make_vault(vault_file, {"my_key": "value"})
    issues = lint_vars(vault_file, "pass")
    codes = [i.code for i in issues]
    assert "E001" in codes


def test_e002_empty_value(vault_file):
    _make_vault(vault_file, {"EMPTY_VAR": ""})
    issues = lint_vars(vault_file, "pass")
    codes = [i.code for i in issues]
    assert "E002" in codes


def test_w001_unexpanded_variable(vault_file):
    _make_vault(vault_file, {"PATH_VAR": "/home/$USER/bin"})
    issues = lint_vars(vault_file, "pass")
    codes = [i.code for i in issues]
    assert "W001" in codes


def test_w002_short_secret(vault_file):
    _make_vault(vault_file, {"API_SECRET": "abc"})
    issues = lint_vars(vault_file, "pass")
    codes = [i.code for i in issues]
    assert "W002" in codes


def test_w002_not_triggered_for_long_secret(vault_file):
    _make_vault(vault_file, {"API_SECRET": "supersecretvalue"})
    issues = lint_vars(vault_file, "pass")
    codes = [i.code for i in issues]
    assert "W002" not in codes


def test_multiple_issues_same_key(vault_file):
    _make_vault(vault_file, {"bad key!": ""})
    issues = lint_vars(vault_file, "pass")
    codes = [i.code for i in issues]
    assert "E001" in codes
    assert "E002" in codes


def test_lint_error_wrong_password(vault_file):
    _make_vault(vault_file, {"FOO": "bar"})
    with pytest.raises(LintError):
        lint_vars(vault_file, "wrongpass")


def test_to_dict(vault_file):
    _make_vault(vault_file, {"bad": ""})
    issues = lint_vars(vault_file, "pass")
    assert len(issues) > 0
    d = issues[0].to_dict()
    assert "key" in d and "code" in d and "message" in d
