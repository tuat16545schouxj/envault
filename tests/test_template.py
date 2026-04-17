"""Tests for envault.template."""
from __future__ import annotations

import pytest
from pathlib import Path

from envault.template import TemplateError, render_string, render_file
from envault.vault import save_vault


VARS = {"HOST": "localhost", "PORT": "5432", "DB": "mydb"}


# --- render_string ---

def test_render_string_basic():
    result = render_string("{{HOST}}:{{PORT}}", VARS)
    assert result == "localhost:5432"


def test_render_string_whitespace_in_placeholder():
    result = render_string("{{ HOST }}", VARS)
    assert result == "localhost"


def test_render_string_no_placeholders():
    assert render_string("hello world", VARS) == "hello world"


def test_render_string_missing_strict_raises():
    with pytest.raises(TemplateError, match="MISSING"):
        render_string("{{MISSING}}", VARS, strict=True)


def test_render_string_missing_non_strict_keeps_placeholder():
    result = render_string("{{MISSING}}", VARS, strict=False)
    assert result == "{{MISSING}}"


def test_render_string_multiple_missing_lists_all():
    with pytest.raises(TemplateError) as exc_info:
        render_string("{{A}} {{B}}", {}, strict=True)
    assert "A" in str(exc_info.value)
    assert "B" in str(exc_info.value)


def test_render_string_repeated_placeholder():
    result = render_string("{{HOST}} {{HOST}}", VARS)
    assert result == "localhost localhost"


# --- render_file ---

@pytest.fixture()
def vault_file(tmp_path):
    path = tmp_path / "vault.env"
    save_vault(path, "secret", VARS)
    return path


def test_render_file_basic(tmp_path, vault_file):
    tpl = tmp_path / "app.conf.tpl"
    tpl.write_text("host={{HOST}} port={{PORT}}")
    result = render_file(tpl, vault_file, "secret")
    assert result == "host=localhost port=5432"


def test_render_file_writes_output(tmp_path, vault_file):
    tpl = tmp_path / "t.tpl"
    tpl.write_text("db={{DB}}")
    out = tmp_path / "out.conf"
    render_file(tpl, vault_file, "secret", output_path=out)
    assert out.read_text() == "db=mydb"


def test_render_file_missing_template_raises(tmp_path, vault_file):
    with pytest.raises(TemplateError, match="not found"):
        render_file(tmp_path / "ghost.tpl", vault_file, "secret")


def test_render_file_wrong_password_raises(tmp_path, vault_file):
    tpl = tmp_path / "t.tpl"
    tpl.write_text("{{HOST}}")
    with pytest.raises(Exception):
        render_file(tpl, vault_file, "wrong")
