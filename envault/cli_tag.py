"""CLI commands for variable tagging."""
import click
from envault.tag import TagError, add_tag, remove_tag, list_tags, vars_by_tag


@click.group("tag")
def tag_group():
    """Manage tags on environment variables."""


@tag_group.command("add")
@click.argument("key")
@click.argument("tag")
@click.option("--vault", required=True, envvar="ENVAULT_PATH")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", hide_input=True)
def add_command(key, tag, vault, password):
    """Add TAG to KEY."""
    try:
        add_tag(vault, password, key, tag)
        click.echo(f"Tag '{tag}' added to '{key}'.")
    except TagError as e:
        raise click.ClickException(str(e))


@tag_group.command("remove")
@click.argument("key")
@click.argument("tag")
@click.option("--vault", required=True, envvar="ENVAULT_PATH")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", hide_input=True)
def remove_command(key, tag, vault, password):
    """Remove TAG from KEY."""
    try:
        remove_tag(vault, password, key, tag)
        click.echo(f"Tag '{tag}' removed from '{key}'.")
    except TagError as e:
        raise click.ClickException(str(e))


@tag_group.command("list")
@click.option("--vault", required=True, envvar="ENVAULT_PATH")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", hide_input=True)
@click.option("--tag", default=None, help="Filter keys by tag.")
def list_command(vault, password, tag):
    """List tags or keys matching a tag."""
    try:
        if tag:
            keys = vars_by_tag(vault, password, tag)
            if not keys:
                click.echo(f"No variables tagged '{tag}'.")
            for k in keys:
                click.echo(k)
        else:
            mapping = list_tags(vault, password)
            if not mapping:
                click.echo("No tags defined.")
            for k, tags in sorted(mapping.items()):
                click.echo(f"{k}: {', '.join(sorted(tags))}")
    except TagError as e:
        raise click.ClickException(str(e))
