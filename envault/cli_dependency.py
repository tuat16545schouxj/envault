"""CLI commands for vault variable dependency management."""
import click

from envault.dependency import (
    DependencyError,
    add_dependency,
    dependents_of,
    list_dependencies,
    remove_dependency,
)


@click.group(name="dep")
def dep_group() -> None:
    """Manage dependencies between vault variables."""


@dep_group.command(name="add")
@click.argument("key")
@click.argument("depends_on")
@click.option("--vault", required=True, envvar="ENVAULT_PATH", help="Vault file path.")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", prompt=True, hide_input=True)
def add_command(key: str, depends_on: str, vault: str, password: str) -> None:
    """Add a dependency: KEY depends on DEPENDS_ON."""
    try:
        add_dependency(vault, password, key, depends_on)
        click.echo(f"Added: {key!r} depends on {depends_on!r}.")
    except DependencyError as exc:
        raise click.ClickException(str(exc)) from exc


@dep_group.command(name="remove")
@click.argument("key")
@click.argument("depends_on")
@click.option("--vault", required=True, envvar="ENVAULT_PATH", help="Vault file path.")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", prompt=True, hide_input=True)
def remove_command(key: str, depends_on: str, vault: str, password: str) -> None:
    """Remove a dependency between KEY and DEPENDS_ON."""
    try:
        remove_dependency(vault, password, key, depends_on)
        click.echo(f"Removed: {key!r} no longer depends on {depends_on!r}.")
    except DependencyError as exc:
        raise click.ClickException(str(exc)) from exc


@dep_group.command(name="list")
@click.option("--key", default=None, help="Filter to a specific key.")
@click.option("--vault", required=True, envvar="ENVAULT_PATH", help="Vault file path.")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", prompt=True, hide_input=True)
def list_command(key: str, vault: str, password: str) -> None:
    """List all dependencies, optionally filtered by KEY."""
    try:
        deps = list_dependencies(vault, password, key)
    except DependencyError as exc:
        raise click.ClickException(str(exc)) from exc
    if not deps:
        click.echo("No dependencies recorded.")
        return
    for k, v in deps.items():
        click.echo(f"{k} -> {', '.join(v)}")


@dep_group.command(name="dependents")
@click.argument("key")
@click.option("--vault", required=True, envvar="ENVAULT_PATH", help="Vault file path.")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", prompt=True, hide_input=True)
def dependents_command(key: str, vault: str, password: str) -> None:
    """Show which keys depend on KEY."""
    try:
        result = dependents_of(vault, password, key)
    except DependencyError as exc:
        raise click.ClickException(str(exc)) from exc
    if not result:
        click.echo(f"No keys depend on {key!r}.")
        return
    for dep in result:
        click.echo(dep)
