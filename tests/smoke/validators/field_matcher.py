"""Field matching for extraction validation."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass
class FieldMatch:
    """Result of comparing a single field."""

    field_name: str
    expected: Any
    actual: Any
    matched: bool
    is_critical: bool

    def __str__(self) -> str:
        status = "MATCH" if self.matched else "MISMATCH"
        critical = " (critical)" if self.is_critical else ""
        return f"{self.field_name}: {status}{critical} - expected={self.expected}, actual={self.actual}"


CRITICAL_FIELDS = {"invoice_id", "vendor_type", "total_amount", "currency"}


def _normalize_value(value: Any) -> Any:
    """Normalize value for comparison."""
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return value.strip().lower() if value else value
    return value


def match_fields(
    expected: dict,
    actual: dict,
    critical_fields: set[str] | None = None,
) -> tuple[bool, list[FieldMatch]]:
    """Compare expected vs actual with critical field enforcement.

    Args:
        expected: Ground truth values (from invoice-gen)
        actual: Extracted values (from pipeline)
        critical_fields: Set of field names that must match exactly

    Returns:
        Tuple of (all_critical_passed, list of FieldMatch results)
    """
    critical = critical_fields or CRITICAL_FIELDS
    results: list[FieldMatch] = []

    for field_name in critical:
        exp_val = expected.get(field_name)
        act_val = actual.get(field_name)

        exp_normalized = _normalize_value(exp_val)
        act_normalized = _normalize_value(act_val)

        if field_name == "vendor_type":
            exp_normalized = str(exp_normalized).lower() if exp_normalized else None
            act_normalized = str(act_normalized).lower() if act_normalized else None

        matched = exp_normalized == act_normalized

        results.append(
            FieldMatch(
                field_name=field_name,
                expected=exp_val,
                actual=act_val,
                matched=matched,
                is_critical=True,
            )
        )

    all_critical_passed = all(r.matched for r in results if r.is_critical)
    return all_critical_passed, results


def format_mismatches(results: list[FieldMatch]) -> list[str]:
    """Format mismatched fields as human-readable strings."""
    return [str(r) for r in results if not r.matched]
