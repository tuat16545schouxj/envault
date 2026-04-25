"""Value transformation pipeline for vault variables."""
from __future__ import annotations

import re
from typing import Callable, Dict, List, Optional

from envault.vault import VaultError, load_vault, save_vault


class TransformError(Exception):
    """Raised when a transformation fails."""


# Built-in named transforms
_TRANSFORMS: Dict[str, Callable[[str], str]] = {
    "upper": str.upper,
    "lower": str.lower,
    "strip": str.strip,
    "reverse": lambda v: v[::-1],
    "base64_encode": lambda v: __import__("base64").b64encode(v.encode()).decode(),
    "base64_decode": lambda v: __import__("base64").b64decode(v.encode()).decode(),
    "url_encode": lambda v: __import__("urllib.parse", fromlist=["quote"]).quote(v, safe=""),
    "trim_quotes": lambda v: v.strip("'\"\n"),
}


def list_transforms() -> List[str]:
    """Return sorted list of available built-in transform names."""
    return sorted(_TRANSFORMS.keys())


def apply_transform(value: str, transform: str) -> str:
    """Apply a single named transform to *value*.

    Args:
        value: The string value to transform.
        transform: Name of the built-in transform to apply.

    Returns:
        The transformed string.

    Raises:
        TransformError: If the transform name is unknown or the operation fails.
    """
    fn = _TRANSFORMS.get(transform)
    if fn is None:
        raise TransformError(
            f"Unknown transform '{transform}'. "
            f"Available: {', '.join(list_transforms())}"
        )
    try:
        return fn(value)
    except Exception as exc:  # pragma: no cover
        raise TransformError(f"Transform '{transform}' failed: {exc}") from exc


def transform_var(
    vault_path: str,
    password: str,
    key: str,
    transforms: List[str],
    dry_run: bool = False,
) -> str:
    """Apply one or more transforms to a vault variable in sequence.

    Args:
        vault_path: Path to the vault file.
        password: Vault decryption password.
        key: Variable key to transform.
        transforms: Ordered list of transform names to apply.
        dry_run: If True, compute and return the result without saving.

    Returns:
        The final transformed value.

    Raises:
        TransformError: If the key is missing or any transform is unknown.
        VaultError: On vault I/O errors.
    """
    data = load_vault(vault_path, password)
    if key not in data:
        raise TransformError(f"Key '{key}' not found in vault.")

    value = data[key]
    for t in transforms:
        value = apply_transform(value, t)

    if not dry_run:
        data[key] = value
        save_vault(vault_path, password, data)

    return value
