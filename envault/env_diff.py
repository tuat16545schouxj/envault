"""env_diff.py — Compare vault variables against the current process environment.

Provides a structured diff showing which vault keys are missing from the
environment, which are present but have different values, and which match.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

from envault.vault import VaultError, load_vault


class EnvDiffError(Exception):
    """Raised when an env-diff operation fails."""


@dataclass
class EnvDiffResult:
    """Result of comparing vault variables to the live environment."""

    key: str
    vault_value: str
    env_value: Optional[str]  # None if the key is absent from the environment
    status: str  # "match", "mismatch", "missing"

    def to_dict(self) -> Dict[str, Optional[str]]:
        return {
            "key": self.key,
            "vault_value": self.vault_value,
            "env_value": self.env_value,
            "status": self.status,
        }


def env_diff(
    vault_path: str,
    password: str,
    keys: Optional[Sequence[str]] = None,
    *,
    env: Optional[Dict[str, str]] = None,
) -> List[EnvDiffResult]:
    """Compare vault variables against the current (or supplied) environment.

    Args:
        vault_path: Path to the encrypted vault file.
        password:   Master password for decryption.
        keys:       Optional list of specific keys to check.  When *None* every
                    variable stored in the vault is compared.
        env:        Mapping to treat as the environment (defaults to
                    ``os.environ``).  Useful for testing.

    Returns:
        A list of :class:`EnvDiffResult` objects sorted by key name.

    Raises:
        EnvDiffError: If the vault cannot be loaded or a requested key does not
                      exist in the vault.
    """
    if env is None:
        env = dict(os.environ)

    try:
        data = load_vault(vault_path, password)
    except VaultError as exc:
        raise EnvDiffError(str(exc)) from exc

    variables: Dict[str, str] = data.get("variables", {})

    if keys:
        missing_from_vault = [k for k in keys if k not in variables]
        if missing_from_vault:
            raise EnvDiffError(
                f"Keys not found in vault: {', '.join(sorted(missing_from_vault))}"
            )
        target_keys = list(keys)
    else:
        target_keys = list(variables.keys())

    results: List[EnvDiffResult] = []
    for key in sorted(target_keys):
        vault_value = variables[key]
        env_value = env.get(key)  # None when absent

        if env_value is None:
            status = "missing"
        elif env_value == vault_value:
            status = "match"
        else:
            status = "mismatch"

        results.append(
            EnvDiffResult(
                key=key,
                vault_value=vault_value,
                env_value=env_value,
                status=status,
            )
        )

    return results
