"""Check vault variables against the current environment."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Optional

from envault.vault import VaultError, load_vault


class EnvCheckError(Exception):
    """Raised when an environment check operation fails."""


@dataclass
class EnvCheckResult:
    key: str
    status: str  # 'ok' | 'missing' | 'mismatch'
    vault_value: Optional[str]
    env_value: Optional[str]

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "status": self.status,
            "vault_value": self.vault_value,
            "env_value": self.env_value,
        }


def check_env(
    vault_path: str,
    password: str,
    keys: Optional[List[str]] = None,
    check_values: bool = False,
) -> List[EnvCheckResult]:
    """Compare vault variables against the current process environment.

    Args:
        vault_path: Path to the vault file.
        password: Vault decryption password.
        keys: Optional list of specific keys to check. Defaults to all.
        check_values: If True, also compare values (not just presence).

    Returns:
        List of EnvCheckResult, one per vault key checked.

    Raises:
        EnvCheckError: If the vault cannot be loaded.
    """
    try:
        vault = load_vault(vault_path, password)
    except VaultError as exc:
        raise EnvCheckError(str(exc)) from exc

    variables: dict = vault.get("variables", {})

    target_keys = sorted(keys if keys else variables.keys())

    results: List[EnvCheckResult] = []
    for key in target_keys:
        if key not in variables:
            raise EnvCheckError(f"Key '{key}' not found in vault.")

        vault_val = variables[key]
        env_val = os.environ.get(key)

        if env_val is None:
            status = "missing"
        elif check_values and env_val != vault_val:
            status = "mismatch"
        else:
            status = "ok"

        results.append(
            EnvCheckResult(
                key=key,
                status=status,
                vault_value=vault_val if check_values else None,
                env_value=env_val if check_values else None,
            )
        )

    return results
