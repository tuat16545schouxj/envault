"""Tests for envault.dependency and envault.cli_dependency."""
import pytest
from click.testing import CliRunner

from envault.cli_dependency import dep_group
from envault.dependency import (
    DependencyError,
    add_dependency,
    dependents_of,
    list_dependencies,
    remove_dependency,
)
from envault.vault import save_vault

PASSWORD = "testpass"


@pytest.fixture()
def vault_file(tmp_path):
    path = str(tmp_path / "vault.enc")
    data = {"vars": {"DB_URL": "postgres://", "DB_PASS": "secret", "API_KEY": "abc"}}
    save_vault(path, PASSWORD, data)
    return path


# --- unit tests ---

def test_add_dependency_success(vault_file):
    add_dependency(vault_file, PASSWORD, "DB_URL", "DB_PASS")
    deps = list_dependencies(vault_file, PASSWORD)
    assert "DB_PASS" in deps["DB_URL"]


def test_add_dependency_idempotent(vault_file):
    add_dependency(vault_file, PASSWORD, "DB_URL", "DB_PASS")
    add_dependency(vault_file, PASSWORD, "DB_URL", "DB_PASS")
    deps = list_dependencies(vault_file, PASSWORD)
    assert deps["DB_URL"].count("DB_PASS") == 1


def test_add_dependency_missing_key_raises(vault_file):
    with pytest.raises(DependencyError, match="Key not found"):
        add_dependency(vault_file, PASSWORD, "MISSING", "DB_PASS")


def test_add_dependency_missing_depends_on_raises(vault_file):
    with pytest.raises(DependencyError, match="Key not found"):
        add_dependency(vault_file, PASSWORD, "DB_URL", "MISSING")


def test_add_dependency_self_raises(vault_file):
    with pytest.raises(DependencyError, match="cannot depend on itself"):
        add_dependency(vault_file, PASSWORD, "DB_URL", "DB_URL")


def test_remove_dependency_success(vault_file):
    add_dependency(vault_file, PASSWORD, "DB_URL", "DB_PASS")
    remove_dependency(vault_file, PASSWORD, "DB_URL", "DB_PASS")
    deps = list_dependencies(vault_file, PASSWORD)
    assert "DB_URL" not in deps


def test_remove_nonexistent_dependency_raises(vault_file):
    with pytest.raises(DependencyError, match="No dependency"):
        remove_dependency(vault_file, PASSWORD, "DB_URL", "DB_PASS")


def test_list_dependencies_filtered(vault_file):
    add_dependency(vault_file, PASSWORD, "DB_URL", "DB_PASS")
    add_dependency(vault_file, PASSWORD, "API_KEY", "DB_PASS")
    deps = list_dependencies(vault_file, PASSWORD, key="DB_URL")
    assert list(deps.keys()) == ["DB_URL"]


def test_dependents_of(vault_file):
    add_dependency(vault_file, PASSWORD, "DB_URL", "DB_PASS")
    add_dependency(vault_file, PASSWORD, "API_KEY", "DB_PASS")
    result = dependents_of(vault_file, PASSWORD, "DB_PASS")
    assert result == ["API_KEY", "DB_URL"]


def test_dependents_of_empty(vault_file):
    result = dependents_of(vault_file, PASSWORD, "DB_PASS")
    assert result == []


# --- CLI tests ---

@pytest.fixture()
def runner():
    return CliRunner()


def _args(vault_file, *extra):
    return ["--vault", vault_file, "--password", PASSWORD, *extra]


def test_cli_add_and_list(runner, vault_file):
    r = runner.invoke(dep_group, ["add", *_args(vault_file), "DB_URL", "DB_PASS"])
    assert r.exit_code == 0
    assert "depends on" in r.output
    r2 = runner.invoke(dep_group, ["list", *_args(vault_file)])
    assert "DB_URL -> DB_PASS" in r2.output


def test_cli_list_empty(runner, vault_file):
    r = runner.invoke(dep_group, ["list", *_args(vault_file)])
    assert r.exit_code == 0
    assert "No dependencies" in r.output


def test_cli_remove(runner, vault_file):
    runner.invoke(dep_group, ["add", *_args(vault_file), "DB_URL", "DB_PASS"])
    r = runner.invoke(dep_group, ["remove", *_args(vault_file), "DB_URL", "DB_PASS"])
    assert r.exit_code == 0
    assert "no longer depends" in r.output


def test_cli_dependents(runner, vault_file):
    runner.invoke(dep_group, ["add", *_args(vault_file), "DB_URL", "DB_PASS"])
    r = runner.invoke(dep_group, ["dependents", *_args(vault_file), "DB_PASS"])
    assert r.exit_code == 0
    assert "DB_URL" in r.output
