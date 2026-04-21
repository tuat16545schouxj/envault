"""Push local environment variables into the vault from the current process environment."""

from __future__ import annotations

import os
from typing import Optional

from envault.vault import VaultError, load_vault, save_vault, set_var
from envault.audit import record


class EnvPushError(Exception):
    """Raised when pushing env vars into the vault fails."""


def push_from_env(
    vault_path: str,
    password: str,
    keys: Optional[list[str]] = None,
    prefix: Optional[str] = None,
    overwrite: bool = True,
) -> dict[str, str]:
    """Read variables from the current process environment and write them into the vault.

    Args:
        vault_path: Path to the vault file.
        password: Encryption password for the vault.
        keys: Explicit list of env var names to import. If None, uses *prefix*.
        prefix: If *keys* is None, import all env vars whose names start with this
                prefix (the prefix is preserved in the vault key).
        overwrite: When True, existing vault entries are overwritten. When False,
                   existing keys are skipped.

    Returns:
        A dict mapping each key that was written to its value.

    Raises:
        EnvPushError: If neither *keys* nor *prefix* is provided, or if no matching
                      variables are found in the environment.
        VaultError: Propagated from vault operations on invalid password / corruption.
    """
    if keys is None and prefix is None:
        raise EnvPushError("Either 'keys' or 'prefix' must be specified.")

    if keys is not None:
        candidates = {k: os.environ[k] for k in keys if k in os.environ}
        missing = [k for k in keys if k not in os.environ]
        if missing:
            raise EnvPushError(
                f"The following keys were not found in the environment: {', '.join(missing)}"
            )
    else:
        candidates = {
            k: v for k, v in os.environ.items() if k.startswith(prefix)  # type: ignore[arg-type]
        }

    if not candidates:
        raise EnvPushError("No matching environment variables found.")

    try:
        vault = load_vault(vault_path, password)
    except FileNotFoundError:
        vault = {}

    written: dict[str, str] = {}
    for key, value in candidates.items():
        if not overwrite and key in vault:
            continue
        set_var(vault_path, password, key, value)
        written[key] = value
        record(vault_path, action="env_push", key=key)

    return written
