"""Tests for CLI template commands."""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_template import template_group
from envault.vault import save_vault


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def tmp_vault(tmp_path):
    path = tmp_path / "vault.env"
    save_vault(path, "pass", {"APP": "envault", "ENV": "test"})
    return path


def _args(vault: Path, tpl: Path, **kwargs):
    base = ["render", str(tpl), "--vault", str(vault), "--password", "pass"]
    if kwargs.get("output"):
        base += ["--output", str(kwargs["output"])]
    if kwargs.get("no_strict"):
        base.append("--no-strict")
    return base


def test_render_to_stdout(runner, tmp_vault, tmp_path):
    tpl = tmp_path / "t.tpl"
    tpl.write_text("app={{APP}} env={{ENV}}")
    result = runner.invoke(template_group, _args(tmp_vault, tpl))
    assert result.exit_code == 0
    assert "app=envault env=test" in result.output


def test_render_to_file(runner, tmp_vault, tmp_path):
    tpl = tmp_path / "t.tpl"
    tpl.write_text("{{APP}}")
    out = tmp_path / "out.txt"
    result = runner.invoke(template_group, _args(tmp_vault, tpl, output=out))
    assert result.exit_code == 0
    assert out.read_text() == "envault"


def test_render_missing_var_strict_fails(runner, tmp_vault, tmp_path):
    tpl = tmp_path / "t.tpl"
    tpl.write_text("{{UNDEFINED}}")
    result = runner.invoke(template_group, _args(tmp_vault, tpl))
    assert result.exit_code != 0
    assert "UNDEFINED" in result.output


def test_render_missing_var_no_strict_keeps(runner, tmp_vault, tmp_path):
    tpl = tmp_path / "t.tpl"
    tpl.write_text("{{UNDEFINED}}")
    result = runner.invoke(template_group, _args(tmp_vault, tpl, no_strict=True))
    assert result.exit_code == 0
    assert "{{UNDEFINED}}" in result.output
