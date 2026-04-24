"""Redaction utilities for masking sensitive variable values in output."""

from __future__ import annotations

import re
from typing import Dict, List, Optional

from envault.vault import VaultError, load_vault

REDACT_PLACEHOLDER = "***"

SENSITIVE_PATTERNS: List[re.Pattern] = [
    re.compile(r"(password|passwd|secret|token|key|api_key|auth|credential|private)", re.IGNORECASE),
]


class RedactError(Exception):
    """Raised when a redaction operation fails."""


def is_sensitive_key(key: str) -> bool:
    """Return True if *key* looks like it holds a sensitive value."""
    return any(pat.search(key) for pat in SENSITIVE_PATTERNS)


def redact_value(value: str, mask: str = REDACT_PLACEHOLDER) -> str:
    """Return *mask* unconditionally — the caller decides whether to redact."""
    return mask


def redact_dict(
    variables: Dict[str, str],
    *,
    keys: Optional[List[str]] = None,
    auto: bool = True,
    mask: str = REDACT_PLACEHOLDER,
) -> Dict[str, str]:
    """Return a copy of *variables* with sensitive values replaced by *mask*.

    Args:
        variables: Mapping of env-var name → value.
        keys:      Explicit list of keys to redact.  Combined with *auto*.
        auto:      When True, also redact keys that match SENSITIVE_PATTERNS.
        mask:      Replacement string (default ``"***"``).
    """
    explicit = set(keys or [])
    result: Dict[str, str] = {}
    for k, v in variables.items():
        if k in explicit or (auto and is_sensitive_key(k)):
            result[k] = mask
        else:
            result[k] = v
    return result


def redact_vault(
    vault_path: str,
    password: str,
    *,
    keys: Optional[List[str]] = None,
    auto: bool = True,
    mask: str = REDACT_PLACEHOLDER,
) -> Dict[str, str]:
    """Load a vault and return its variables with sensitive values redacted.

    Raises:
        RedactError: If the vault cannot be loaded.
    """
    try:
        data = load_vault(vault_path, password)
    except VaultError as exc:
        raise RedactError(str(exc)) from exc

    variables: Dict[str, str] = data.get("variables", {})
    return redact_dict(variables, keys=keys, auto=auto, mask=mask)
