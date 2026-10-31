#!/usr/bin/env python3
"""Source-linked incremental progress candidates, never automatic acceptance.

Receipt files are untrusted review requests even when present on a checkout.
Only a separate independently reviewed inventory change can admit a criterion.
"""
import copy
import json
from pathlib import Path
from tools.atomic_progress_v2 import validate

REPO = "https://github.com/gamesbyian/UR-Recomp/"
RECEIPTS = Path(__file__).resolve().parents[1] / "docs/progress/receipts"


def apply_receipts(inventory, ledger, receipts):
    """Validate candidate receipts without mutating accepted inventory coverage.

    An arbitrary reviewer string or GitHub URL cannot establish source-bound,
    criterion-specific independent acceptance. This remains true on a PR head.
    """
    result = copy.deepcopy(inventory)
    rows = {c["id"]: c for c in result["criteria"]}
    used = set()
    pending = []
    for receipt in receipts:
        if not isinstance(receipt, dict):
            raise ValueError("Progress receipt must be an object")
        key = receipt.get("criterion_id")
        if key in used or key not in rows:
            raise ValueError("Unknown or duplicate progress receipt criterion")
        used.add(key)
        if receipt.get("schema") != "ur-progress-receipt/1":
            raise ValueError("Unknown receipt schema")
        if not receipt.get("independent_reviewer") or not receipt.get("rationale"):
            raise ValueError("Missing reviewer claim and rationale")
        if receipt.get("kind") not in ("new_implementation", "retroactive_evidence"):
            raise ValueError("Missing new versus retrospective attribution")
        references = receipt.get("evidence")
        audit = receipt.get("audit_receipt")
        if (not isinstance(references, list) or not references or
            not all(isinstance(u, str) and u.startswith(REPO) for u in references)
            or not isinstance(audit, str) or not audit.startswith(REPO)):
            raise ValueError("Receipt needs evidence and independent audit links")
        row = rows[key]
        if row["area"] == "FID":
            raise ValueError("USA complete-event admission requires authoritative QA ledger, not this mechanism")
        if row["status"] == "bounded_verified":
            raise ValueError("Receipt duplicates an already verified criterion")
        if row["status"] != "unverified":
            raise ValueError("Regression rehabilitation requires explicit separate review")
        pending.append({"criterion_id": key, "kind": receipt["kind"],
                        "reviewer_claim": receipt["independent_reviewer"],
                        "audit_receipt": audit,
                        "admission_status": "pending_independent_review"})
    validate(result, ledger)
    return result, pending


def read_receipts(folder=RECEIPTS):
    if not folder.exists():
        return []
    return [json.loads(f.read_text(encoding="utf-8")) for f in sorted(folder.glob("*.json"))]
