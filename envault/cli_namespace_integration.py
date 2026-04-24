"""Attach namespace commands to the main CLI and register auto-complete hints."""

from __future__ import annotations

import click

from envault.cli_namespace import namespace_group


def attach_namespace(cli: click.Group) -> None:
    """Register the namespace command group onto *cli*."""
    cli.add_command(namespace_group)


def namespace_summary(
    vault_path: str, password: str
) -> dict[str, int]:
    """Return a mapping of namespace -> variable count for display purposes.

    This is a convenience helper used by dashboard-style commands.
    """
    from envault.namespace import list_namespaces, get_namespace_vars

    summary: dict[str, int] = {}
    for ns in list_namespaces(vault_path, password):
        summary[ns] = len(get_namespace_vars(vault_path, password, ns))
    return summary


@click.command(name="ns-summary", help="Print a summary of all namespaces and their variable counts.")
@click.option("--vault", required=True, envvar="ENVAULT_PATH", help="Path to vault file.")
@click.password_option("--password", envvar="ENVAULT_PASSWORD", confirmation_prompt=False)
def ns_summary_command(vault: str, password: str) -> None:
    """Standalone command: print namespace -> count table."""
    from envault.namespace import NamespaceError

    try:
        summary = namespace_summary(vault, password)
    except NamespaceError as exc:
        raise click.ClickException(str(exc))

    if not summary:
        click.echo("No namespaces found.")
        return

    width = max(len(ns) for ns in summary)
    click.echo(f"{'NAMESPACE':<{width}}  COUNT")
    click.echo("-" * (width + 8))
    for ns, count in sorted(summary.items()):
        click.echo(f"{ns:<{width}}  {count}")
