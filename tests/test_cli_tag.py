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


def _invoke(runner, tmp_vault, *cmd_args):
    """Helper to invoke tag_group with vault and password options."""
    return runner.invoke(
        tag_group,
        list(cmd_args) + ["--vault", tmp_vault, "--password", PASSWORD],
    )


def test_add_tag_output(runner, tmp_vault):
    result = _invoke(runner, tmp_vault, "add", "DB_URL", "infra")
    assert result.exit_code == 0
    assert "added" in result.output


def test_remove_tag_output(runner, tmp_vault):
    _invoke(runner, tmp_vault, "add", "TOKEN", "auth")
    result = _invoke(runner, tmp_vault, "remove", "TOKEN", "auth")
    assert result.exit_code == 0
    assert "removed" in result.output


def test_list_no_tags(runner, tmp_vault):
    result = _invoke(runner, tmp_vault, "list")
    assert result.exit_code == 0
    assert "No tags" in result.output


def test_list_filter_by_tag(runner, tmp_vault):
    _invoke(runner, tmp_vault, "add", "DB_URL", "infra")
    _invoke(runner, tmp_vault, "add", "TOKEN", "infra")
    result = _invoke(runner, tmp_vault, "list", "--tag", "infra")
    assert "DB_URL" in result.output
    assert "TOKEN" in result.output


def test_add_missing_key_error(runner, tmp_vault):
    result = _invoke(runner, tmp_vault, "add", "NOPE", "x")
    assert result.exit_code != 0
    assert "not found" in result.output
