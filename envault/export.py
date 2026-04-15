"""Export vault variables to shell-compatible formats."""

from __future__ import annotations

from typing import Dict


SUPPORTED_FORMATS = ("dotenv", "shell", "json")


class ExportError(Exception):
    """Raised when export fails due to an unsupported format or bad data."""


def export_dotenv(variables: Dict[str, str]) -> str:
    """Render variables as a .env file string."""
    lines = []
    for key, value in sorted(variables.items()):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'{key}="{escaped}"')
    return "\n".join(lines) + ("\n" if lines else "")


def export_shell(variables: Dict[str, str]) -> str:
    """Render variables as export statements for bash/zsh."""
    lines = []
    for key, value in sorted(variables.items()):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'export {key}="{escaped}"')
    return "\n".join(lines) + ("\n" if lines else "")


def export_json(variables: Dict[str, str]) -> str:
    """Render variables as a JSON object string."""
    import json
    return json.dumps(variables, indent=2, sort_keys=True) + "\n"


def export_variables(variables: Dict[str, str], fmt: str) -> str:
    """Dispatch export to the correct formatter.

    Args:
        variables: Mapping of env var names to values.
        fmt: One of 'dotenv', 'shell', or 'json'.

    Returns:
        Formatted string ready to write to stdout or a file.

    Raises:
        ExportError: If *fmt* is not supported.
    """
    if fmt == "dotenv":
        return export_dotenv(variables)
    if fmt == "shell":
        return export_shell(variables)
    if fmt == "json":
        return export_json(variables)
    raise ExportError(
        f"Unsupported format '{fmt}'. Choose from: {', '.join(SUPPORTED_FORMATS)}"
    )
