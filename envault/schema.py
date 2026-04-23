"""Schema validation for vault variables."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from envault.vault import VaultError, load_vault


class SchemaError(Exception):
    """Raised when schema validation fails."""


@dataclass
class SchemaRule:
    key: str
    required: bool = True
    pattern: str | None = None
    min_length: int | None = None
    max_length: int | None = None
    allowed_values: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "required": self.required,
            "pattern": self.pattern,
            "min_length": self.min_length,
            "max_length": self.max_length,
            "allowed_values": self.allowed_values,
        }


@dataclass
class SchemaViolation:
    key: str
    rule: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {"key": self.key, "rule": self.rule, "message": self.message}


def validate_schema(
    vault_path: str,
    password: str,
    rules: list[SchemaRule],
) -> list[SchemaViolation]:
    """Validate vault variables against a list of schema rules.

    Returns a (possibly empty) list of SchemaViolation objects.
    Raises SchemaError if the vault cannot be loaded.
    """
    try:
        variables: dict[str, str] = load_vault(vault_path, password).get("variables", {})
    except VaultError as exc:
        raise SchemaError(f"Could not load vault: {exc}") from exc

    violations: list[SchemaViolation] = []

    for rule in rules:
        value = variables.get(rule.key)

        if value is None:
            if rule.required:
                violations.append(
                    SchemaViolation(
                        key=rule.key,
                        rule="required",
                        message=f"Key '{rule.key}' is required but not present in the vault.",
                    )
                )
            continue

        if rule.min_length is not None and len(value) < rule.min_length:
            violations.append(
                SchemaViolation(
                    key=rule.key,
                    rule="min_length",
                    message=(
                        f"Value for '{rule.key}' is too short "
                        f"(min {rule.min_length}, got {len(value)})."
                    ),
                )
            )

        if rule.max_length is not None and len(value) > rule.max_length:
            violations.append(
                SchemaViolation(
                    key=rule.key,
                    rule="max_length",
                    message=(
                        f"Value for '{rule.key}' is too long "
                        f"(max {rule.max_length}, got {len(value)})."
                    ),
                )
            )

        if rule.pattern is not None and not re.fullmatch(rule.pattern, value):
            violations.append(
                SchemaViolation(
                    key=rule.key,
                    rule="pattern",
                    message=(
                        f"Value for '{rule.key}' does not match "
                        f"required pattern '{rule.pattern}'."
                    ),
                )
            )

        if rule.allowed_values is not None and value not in rule.allowed_values:
            violations.append(
                SchemaViolation(
                    key=rule.key,
                    rule="allowed_values",
                    message=(
                        f"Value for '{rule.key}' is not in allowed values: "
                        f"{rule.allowed_values}."
                    ),
                )
            )

    return violations
