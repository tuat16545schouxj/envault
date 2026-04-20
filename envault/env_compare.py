"""Compare vault variables against the current process environment."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envault.vault import VaultError, load_vault


class EnvCompareError(Exception):
    """Raised when env comparison fails."""


@dataclass
class CompareResult:
    key: str
    vault_value: str
    env_value: Optional[str]
    status: str  # "match", "mismatch", "missing_in_env"

    def to_dict(self) -> Dict:
        return {
            "key": self.key,
            "vault_value": self.vault_value,
            "env_value": self.env_value,
            "status": self.status,
        }


def compare_env(
    vault_path: str,
    password: str,
    keys: Optional[List[str]] = None,
    env: Optional[Dict[str, str]] = None,
) -> List[CompareResult]:
    """Compare vault variables to the given (or process) environment.

    Args:
        vault_path: Path to the vault file.
        password: Vault decryption password.
        keys: Optional subset of keys to compare. Defaults to all keys.
        env: Environment mapping to compare against. Defaults to os.environ.

    Returns:
        List of CompareResult entries sorted by key.

    Raises:
        EnvCompareError: If the vault cannot be loaded.
    """
    import os

    if env is None:
        env = dict(os.environ)

    try:
        data = load_vault(vault_path, password)
    except VaultError as exc:
        raise EnvCompareError(str(exc)) from exc

    variables: Dict[str, str] = data.get("variables", {})

    if keys:
        missing = [k for k in keys if k not in variables]
        if missing:
            raise EnvCompareError(
                f"Keys not found in vault: {', '.join(sorted(missing))}"
            )
        variables = {k: variables[k] for k in keys}

    results: List[CompareResult] = []
    for key in sorted(variables):
        vault_val = variables[key]
        env_val = env.get(key)
        if env_val is None:
            status = "missing_in_env"
        elif env_val == vault_val:
            status = "match"
        else:
            status = "mismatch"
        results.append(
            CompareResult(
                key=key,
                vault_value=vault_val,
                env_value=env_val,
                status=status,
            )
        )

    return results
