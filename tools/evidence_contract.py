#!/usr/bin/env python3
"""Small dependency-free evidence-envelope helper.

Human-readable logs are diagnostic output. Durable gates should exchange this
structured envelope so later tools do not depend on grep-compatible prose.
Subsystem-specific metrics remain free-form; named assertions are the stable API.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


OUTCOMES = {"accepted", "rejected", "inconclusive"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def assertion(name: str, passed: bool, details: Any = None) -> dict[str, Any]:
    row: dict[str, Any] = {"name": name, "passed": bool(passed)}
    if details is not None:
        row["details"] = details
    return row


def make_envelope(
    *,
    evidence_type: str,
    producer: str,
    subject: dict[str, Any],
    inputs: dict[str, Any],
    assertions: Iterable[dict[str, Any]],
    metrics: dict[str, Any] | None = None,
    provenance: dict[str, Any] | None = None,
    outcome: str | None = None,
) -> dict[str, Any]:
    rows = list(assertions)
    if outcome is None:
        outcome = "accepted" if rows and all(row.get("passed") is True for row in rows) else "rejected"
    prov = dict(provenance or {})
    prov.setdefault("generated_at_utc", utc_now())
    envelope = {
        "schema_version": 1,
        "evidence_type": evidence_type,
        "producer": producer,
        "subject": dict(subject),
        "inputs": dict(inputs),
        "metrics": dict(metrics or {}),
        "assertions": rows,
        "outcome": outcome,
        "provenance": prov,
    }
    errors = validate_envelope(envelope)
    if errors:
        raise ValueError("; ".join(errors))
    return envelope


def validate_envelope(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["envelope must be an object"]
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    for key in ("evidence_type", "producer"):
        if not isinstance(data.get(key), str) or not data[key]:
            errors.append(f"{key} must be a non-empty string")
    for key in ("subject", "inputs", "provenance"):
        if not isinstance(data.get(key), dict):
            errors.append(f"{key} must be an object")
    assertions = data.get("assertions")
    if not isinstance(assertions, list):
        errors.append("assertions must be an array")
        assertions = []
    else:
        seen: set[str] = set()
        for index, row in enumerate(assertions):
            if not isinstance(row, dict):
                errors.append(f"assertions[{index}] must be an object")
                continue
            name = row.get("name")
            if not isinstance(name, str) or not name:
                errors.append(f"assertions[{index}].name must be a non-empty string")
            elif name in seen:
                errors.append(f"duplicate assertion name: {name}")
            else:
                seen.add(name)
            if not isinstance(row.get("passed"), bool):
                errors.append(f"assertions[{index}].passed must be boolean")
    outcome = data.get("outcome")
    if outcome not in OUTCOMES:
        errors.append(f"outcome must be one of {sorted(OUTCOMES)}")
    elif outcome == "accepted" and any(row.get("passed") is not True for row in assertions if isinstance(row, dict)):
        errors.append("accepted evidence cannot contain a failed assertion")
    elif outcome == "rejected" and assertions and all(row.get("passed") is True for row in assertions if isinstance(row, dict)):
        errors.append("rejected evidence must contain at least one failed assertion")
    provenance = data.get("provenance")
    if isinstance(provenance, dict) and not isinstance(provenance.get("generated_at_utc"), str):
        errors.append("provenance.generated_at_utc must be a string")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path)
    args = parser.parse_args()
    data = json.loads(args.evidence.read_text())
    errors = validate_envelope(data)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("EVIDENCE_ENVELOPE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
