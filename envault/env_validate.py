"""Validate vault variables against simple type/pattern rules."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from envault.vault import load_vault


class EnvValidateError(Exception):
    """Raised when validation cannot be performed."""


@dataclass
class ValidationResult:
    key: str
    passed: bool
    rule: str
    message: str

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "passed": self.passed,
            "rule": self.rule,
            "message": self.message,
        }


_BUILTIN_RULES: dict[str, tuple[str, re.Pattern]] = {
    "url": ("Must be a valid URL (http/https)", re.compile(r"^https?://.+")),
    "integer": ("Must be a valid integer", re.compile(r"^-?\d+$")),
    "boolean": ("Must be true/false/1/0", re.compile(r"^(true|false|1|0)$", re.I)),
    "alphanumeric": ("Must contain only letters and digits", re.compile(r"^[a-zA-Z0-9]+$")),
    "email": ("Must be a valid email address", re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")),
    "nonempty": ("Must not be empty", re.compile(r".+")),
}


def list_rules() -> list[str]:
    """Return the names of all built-in validation rules."""
    return sorted(_BUILTIN_RULES.keys())


def validate_value(value: str, rule: str, pattern: Optional[str] = None) -> tuple[bool, str]:
    """Return (passed, message) for a single value against a rule or custom regex."""
    if pattern is not None:
        try:
            compiled = re.compile(pattern)
        except re.error as exc:
            raise EnvValidateError(f"Invalid regex pattern: {exc}") from exc
        passed = bool(compiled.fullmatch(value))
        msg = "Matches custom pattern" if passed else f"Does not match pattern '{pattern}'"
        return passed, msg

    if rule not in _BUILTIN_RULES:
        raise EnvValidateError(
            f"Unknown rule '{rule}'. Available: {', '.join(list_rules())}"
        )
    description, compiled = _BUILTIN_RULES[rule]
    passed = bool(compiled.fullmatch(value))
    return passed, description if passed else f"Failed: {description}"


def validate_vault(
    vault_path: str,
    password: str,
    rules: dict[str, dict],  # {key: {"rule": ..., "pattern": ...}}
) -> list[ValidationResult]:
    """Validate vault variables against provided rules.

    Each entry in *rules* maps a variable key to a dict with:
      - ``rule``: a built-in rule name (optional if ``pattern`` is given)
      - ``pattern``: a custom regex pattern (takes precedence over ``rule``)
    """
    try:
        data = load_vault(vault_path, password)
    except FileNotFoundError as exc:
        raise EnvValidateError(f"Vault not found: {vault_path}") from exc

    results: list[ValidationResult] = []
    for key, spec in sorted(rules.items()):
        rule_name = spec.get("rule", "nonempty")
        custom_pattern = spec.get("pattern")
        if key not in data:
            results.append(
                ValidationResult(
                    key=key,
                    passed=False,
                    rule=rule_name,
                    message="Key not found in vault",
                )
            )
            continue
        passed, message = validate_value(data[key], rule_name, custom_pattern)
        results.append(
            ValidationResult(key=key, passed=passed, rule=rule_name, message=message)
        )
    return results
