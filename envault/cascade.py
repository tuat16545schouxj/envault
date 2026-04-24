"""Cascade resolution: merge variables from multiple profiles/namespaces in priority order."""

from __future__ import annotations

from typing import Dict, List, Optional

from envault.vault import VaultError, load_vault


class CascadeError(Exception):
    """Raised when cascade resolution fails."""


class CascadeResult:
    """Result of a cascade resolution."""

    def __init__(self, resolved: Dict[str, str], sources: Dict[str, str]) -> None:
        # resolved: key -> final value
        self.resolved = resolved
        # sources: key -> layer name that provided the value
        self.sources = sources

    def to_dict(self) -> dict:
        return {
            "resolved": self.resolved,
            "sources": self.sources,
        }


def _vars_for_layer(vault_data: dict, layer: str) -> Dict[str, str]:
    """Extract variables for a given layer name.

    A layer can be:
      - "__root__"  -> top-level variables (no namespace prefix)
      - a profile name stored under vault_data["profiles"]
      - a namespace prefix (keys of the form "<layer>.<key>" stripped)
    """
    if layer == "__root__":
        return {k: v for k, v in vault_data.get("vars", {}).items()}

    # Check profiles first
    profiles = vault_data.get("profiles", {})
    if layer in profiles:
        keys = profiles[layer].get("keys", [])
        all_vars = vault_data.get("vars", {})
        return {k: all_vars[k] for k in keys if k in all_vars}

    # Treat as namespace prefix
    prefix = layer.rstrip(".") + "."
    result: Dict[str, str] = {}
    for k, v in vault_data.get("vars", {}).items():
        if k.startswith(prefix):
            stripped = k[len(prefix):]
            result[stripped] = v
    return result


def resolve_cascade(
    vault_path: str,
    password: str,
    layers: List[str],
    base: Optional[Dict[str, str]] = None,
) -> CascadeResult:
    """Resolve variables by merging *layers* in order (later layers win).

    Args:
        vault_path: Path to the vault file.
        password: Vault decryption password.
        layers: Ordered list of layer names (profiles / namespaces / '__root__').
                Later entries override earlier ones.
        base: Optional mapping to use as the lowest-priority base.

    Returns:
        CascadeResult with the merged variables and their winning source.
    """
    if not layers:
        raise CascadeError("At least one layer must be specified for cascade resolution.")

    try:
        vault_data = load_vault(vault_path, password)
    except VaultError as exc:
        raise CascadeError(f"Failed to load vault: {exc}") from exc

    resolved: Dict[str, str] = dict(base or {})
    sources: Dict[str, str] = {k: "__base__" for k in resolved}

    for layer in layers:
        layer_vars = _vars_for_layer(vault_data, layer)
        for k, v in layer_vars.items():
            resolved[k] = v
            sources[k] = layer

    return CascadeResult(resolved=resolved, sources=sources)
