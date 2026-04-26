"""CLI commands for managing variable annotations."""

from __future__ import annotations

import click

from envault.annotate import AnnotateError, get_annotation, list_annotations, remove_annotation, set_annotation


@click.group("annotate")
def annotate_group() -> None:
    """Attach or view notes on vault variables."""


@annotate_group.command("set")
@click.option("--vault", required=True, envvar="ENVAULT_PATH", help="Path to vault file.")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", help="Vault password.", hide_input=True)
@click.argument("key")
@click.argument("note")
def set_command(vault: str, password: str, key: str, note: str) -> None:
    """Attach NOTE to KEY."""
    try:
        set_annotation(vault, password, key, note)
        click.echo(f"Annotation set for '{key}'.")
    except AnnotateError as exc:
        raise click.ClickException(str(exc)) from exc


@annotate_group.command("remove")
@click.option("--vault", required=True, envvar="ENVAULT_PATH", help="Path to vault file.")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", help="Vault password.", hide_input=True)
@click.argument("key")
def remove_command(vault: str, password: str, key: str) -> None:
    """Remove the annotation for KEY."""
    try:
        remove_annotation(vault, password, key)
        click.echo(f"Annotation removed for '{key}'.")
    except AnnotateError as exc:
        raise click.ClickException(str(exc)) from exc


@annotate_group.command("show")
@click.option("--vault", required=True, envvar="ENVAULT_PATH", help="Path to vault file.")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", help="Vault password.", hide_input=True)
@click.argument("key")
def show_command(vault: str, password: str, key: str) -> None:
    """Show the annotation for KEY."""
    try:
        note = get_annotation(vault, password, key)
        if note is None:
            click.echo(f"No annotation for '{key}'.")
        else:
            click.echo(f"{key}: {note}")
    except AnnotateError as exc:
        raise click.ClickException(str(exc)) from exc


@annotate_group.command("list")
@click.option("--vault", required=True, envvar="ENVAULT_PATH", help="Path to vault file.")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", help="Vault password.", hide_input=True)
def list_command(vault: str, password: str) -> None:
    """List all annotations."""
    try:
        ann = list_annotations(vault, password)
        if not ann:
            click.echo("No annotations found.")
        else:
            for key, note in ann.items():
                click.echo(f"{key}: {note}")
    except AnnotateError as exc:
        raise click.ClickException(str(exc)) from exc
