"""Import environment variables from .env files or shell exports into the vault."""

from __future__ import annotations

import re
import shlex
from pathlib import Path
from typing import Dict, Tuple

from envault.vault import set_var


class ImportError(Exception):
    """Raised when an import operation fails."""


_DOTENV_LINE = re.compile(
    r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$"
)


def parse_dotenv(text: str) -> Dict[str, str]:
    """Parse a .env-style file and return a dict of key/value pairs.

    Handles:
    - KEY=value
    - export KEY=value
    - Quoted values (single or double)
    - Inline comments after unquoted values
    - Blank lines and comment lines are skipped
    """
    result: Dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = _DOTENV_LINE.match(stripped)
        if not match:
            continue
        key, raw_value = match.group(1), match.group(2)
        # Strip inline comments for unquoted values
        if raw_value and raw_value[0] in ('"', "'"):
            try:
                value = shlex.split(raw_value)[0]
            except ValueError:
                value = raw_value
        else:
            # Strip trailing inline comment
            value = re.sub(r"\s+#.*$", "", raw_value).strip()
        result[key] = value
    return result


def import_from_file(
    source: Path,
    vault_path: Path,
    password: str,
    overwrite: bool = True,
) -> Tuple[int, int]:
    """Import variables from a .env file into the vault.

    Returns a tuple of (imported_count, skipped_count).
    Raises ImportError if the source file cannot be read.
    """
    try:
        text = source.read_text(encoding="utf-8")
    except OSError as exc:
        raise ImportError(f"Cannot read source file '{source}': {exc}") from exc

    variables = parse_dotenv(text)
    if not variables:
        return 0, 0

    imported = 0
    skipped = 0
    for key, value in variables.items():
        if not overwrite:
            from envault.vault import load_vault
            try:
                existing = load_vault(vault_path, password)
                if key in existing:
                    skipped += 1
                    continue
            except Exception:
                pass
        set_var(vault_path, password, key, value)
        imported += 1

    return imported, skipped
