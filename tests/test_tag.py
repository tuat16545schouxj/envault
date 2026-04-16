import pytest
from envault.tag import TagError, add_tag, remove_tag, list_tags, vars_by_tag
from envault.vault import save_vault

PASSWORD = "testpass"


@pytest.fixture
def vault_file(tmp_path):
    path = str(tmp_path / "vault.enc")
    save_vault(path, PASSWORD, {"vars": {"DB_URL": "postgres://", "API_KEY": "abc"}, "meta": {}})
    return path


def test_add_tag_success(vault_file):
    add_tag(vault_file, PASSWORD, "DB_URL", "database")
    tags = list_tags(vault_file, PASSWORD)
    assert "database" in tags["DB_URL"]


def test_add_tag_idempotent(vault_file):
    add_tag(vault_file, PASSWORD, "DB_URL", "database")
    add_tag(vault_file, PASSWORD, "DB_URL", "database")
    tags = list_tags(vault_file, PASSWORD)
    assert tags["DB_URL"].count("database") == 1


def test_add_tag_missing_key_raises(vault_file):
    with pytest.raises(TagError, match="not found"):
        add_tag(vault_file, PASSWORD, "MISSING", "x")


def test_remove_tag_success(vault_file):
    add_tag(vault_file, PASSWORD, "API_KEY", "auth")
    remove_tag(vault_file, PASSWORD, "API_KEY", "auth")
    tags = list_tags(vault_file, PASSWORD)
    assert "API_KEY" not in tags


def test_remove_tag_not_present_raises(vault_file):
    with pytest.raises(TagError, match="not found"):
        remove_tag(vault_file, PASSWORD, "DB_URL", "ghost")


def test_list_tags_empty(vault_file):
    assert list_tags(vault_file, PASSWORD) == {}


def test_vars_by_tag(vault_file):
    add_tag(vault_file, PASSWORD, "DB_URL", "infra")
    add_tag(vault_file, PASSWORD, "API_KEY", "infra")
    result = vars_by_tag(vault_file, PASSWORD, "infra")
    assert result == ["API_KEY", "DB_URL"]


def test_vars_by_tag_no_match(vault_file):
    assert vars_by_tag(vault_file, PASSWORD, "nonexistent") == []
