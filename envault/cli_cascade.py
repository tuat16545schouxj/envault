"""CLI commands for cascade variable resolution."""

from __future__ import annotations

import json

import click

from envault.cascade import CascadeError, resolve_cascade


@click.group(name="cascade")
def cascade_group() -> None:
    """Resolve variables by merging layers in priority order."""


@cascade_group.command(name="resolve")
@click.option("--vault", "vault_path", required=True, envvar="ENVAULT_VAULT", help="Path to vault file.")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", hide_input=True, help="Vault password.")
@click.option("--layer", "layers", multiple=True, required=True, help="Layer name (repeatable, later layers win).")
@click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table", show_default=True)
@click.option("--show-source", is_flag=True, default=False, help="Show which layer provided each value.")
def resolve_command(
    vault_path: str,
    password: str,
    layers: tuple,
    fmt: str,
    show_source: bool,
) -> None:
    """Merge variables from LAYERS in order and display the result."""
    try:
        result = resolve_cascade(vault_path, password, list(layers))
    except CascadeError as exc:
        raise click.ClickException(str(exc)) from exc

    if fmt == "json":
        data = result.to_dict() if show_source else {"resolved": result.resolved}
        click.echo(json.dumps(data, indent=2, sort_keys=True))
        return

    if not result.resolved:
        click.echo("No variables resolved.")
        return

    col_w = max(len(k) for k in result.resolved) + 2
    for key in sorted(result.resolved):
        value = result.resolved[key]
        if show_source:
            source = result.sources.get(key, "?")
            click.echo(f"{key:<{col_w}}{value}  ({source})")
        else:
            click.echo(f"{key:<{col_w}}{value}")
