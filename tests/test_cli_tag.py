import pytest
from click.testing import CliRunner
from envault.cli_tag import tag_group
from envault.vault import save_vault

PASSWORD = "testpass"


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def tmp_vault(tmp_path):
    path = str(tmp_path / "vault.enc")
    save_vault(path, PASSWORD, {"vars": {"DB_URL": "postgres://", "TOKEN": "xyz"}, "meta": {}})
    return path


def _args(vault, cmd_args):
    return ["--vault", vault, "--password", PASSWORD] + cmd_args


def test_add_tag_output(runner, tmp_vault):
    result = runner.invoke(tag_group, ["add", "DB_URL", "infra"] + ["--vault", tmp_vault, "--password", PASSWORD])
    assert result.exit_code == 0
    assert "added" in result.output


def test_remove_tag_output(runner, tmp_vault):
    runner.invoke(tag_group, ["add", "TOKEN", "auth", "--vault", tmp_vault, "--password", PASSWORD])
    result = runner.invoke(tag_group, ["remove", "TOKEN", "auth", "--vault", tmp_vault, "--password", PASSWORD])
    assert result.exit_code == 0
    assert "removed" in result.output


def test_list_no_tags(runner, tmp_vault):
    result = runner.invoke(tag_group, ["list", "--vault", tmp_vault, "--password", PASSWORD])
    assert result.exit_code == 0
    assert "No tags" in result.output


def test_list_filter_by_tag(runner, tmp_vault):
    runner.invoke(tag_group, ["add", "DB_URL", "infra", "--vault", tmp_vault, "--password", PASSWORD])
    runner.invoke(tag_group, ["add", "TOKEN", "infra", "--vault", tmp_vault, "--password", PASSWORD])
    result = runner.invoke(tag_group, ["list", "--vault", tmp_vault, "--password", PASSWORD, "--tag", "infra"])
    assert "DB_URL" in result.output
    assert "TOKEN" in result.output


def test_add_missing_key_error(runner, tmp_vault):
    result = runner.invoke(tag_group, ["add", "NOPE", "x", "--vault", tmp_vault, "--password", PASSWORD])
    assert result.exit_code != 0
    assert "not found" in result.output
