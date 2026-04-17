"""CLI commands for template rendering."""
from __future__ import annotations

from pathlib import Path

import click

from envault.template import TemplateError, render_file


@click.group("template")
def template_group() -> None:
    """Render templates using vault variables."""


@template_group.command("render")
@click.argument("template_file", type=click.Path(exists=True, path_type=Path))
@click.option("--vault", "vault_path", required=True, type=click.Path(path_type=Path), help="Path to vault file.")
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
@click.option("--output", "output_path", type=click.Path(path_type=Path), default=None, help="Output file (default: stdout).")
@click.option("--no-strict", is_flag=True, default=False, help="Leave unknown placeholders as-is instead of erroring.")
def render_command(
    template_file: Path,
    vault_path: Path,
    password: str,
    output_path: Path | None,
    no_strict: bool,
) -> None:
    """Render TEMPLATE_FILE substituting {{VAR}} with vault values."""
    try:
        rendered = render_file(
            template_file,
            vault_path,
            password,
            output_path=output_path,
            strict=not no_strict,
        )
    except TemplateError as exc:
        raise click.ClickException(str(exc))

    if output_path is None:
        click.echo(rendered, nl=False)
    else:
        click.echo(f"Rendered output written to {output_path}")
