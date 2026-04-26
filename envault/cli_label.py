"""CLI commands for the label feature."""
from __future__ import annotations

import click

from envault.label import LabelError, add_label, keys_for_label, list_labels, remove_label


@click.group(name="label", help="Manage labels on vault variables.")
def label_group() -> None:  # pragma: no cover
    pass


@label_group.command("add")
@click.argument("key")
@click.argument("label")
@click.option("--vault", required=True, envvar="ENVAULT_VAULT", help="Path to vault file.")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", prompt=True, hide_input=True)
def add_command(key: str, label: str, vault: str, password: str) -> None:
    """Attach LABEL to KEY."""
    try:
        add_label(vault, password, key, label)
        click.echo(f"Label '{label}' added to '{key}'.")
    except LabelError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@label_group.command("remove")
@click.argument("key")
@click.argument("label")
@click.option("--vault", required=True, envvar="ENVAULT_VAULT")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", prompt=True, hide_input=True)
def remove_command(key: str, label: str, vault: str, password: str) -> None:
    """Detach LABEL from KEY."""
    try:
        remove_label(vault, password, key, label)
        click.echo(f"Label '{label}' removed from '{key}'.")
    except LabelError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@label_group.command("list")
@click.argument("key")
@click.option("--vault", required=True, envvar="ENVAULT_VAULT")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", prompt=True, hide_input=True)
def list_command(key: str, vault: str, password: str) -> None:
    """List labels attached to KEY."""
    try:
        labels = list_labels(vault, password, key)
        if labels:
            for lbl in labels:
                click.echo(lbl)
        else:
            click.echo(f"No labels on '{key}'.")
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@label_group.command("keys")
@click.argument("label")
@click.option("--vault", required=True, envvar="ENVAULT_VAULT")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", prompt=True, hide_input=True)
def keys_command(label: str, vault: str, password: str) -> None:
    """List keys that carry LABEL."""
    try:
        keys = keys_for_label(vault, password, label)
        if keys:
            for k in keys:
                click.echo(k)
        else:
            click.echo(f"No keys carry label '{label}'.")
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
