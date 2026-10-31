#!/usr/bin/env python3
"""Incremental independently reviewed progress receipts, no merge-interval audit.

Receipt files are reviewed and merged through GitHub; they are never generated
from commit counts, PR titles, or successful CI status alone.
"""
import copy
import json
from pathlib import Path
from tools.atomic_progress_v2 import validate

REPO = "https://github.com/gamesbyian/UR-Recomp/"
RECEIPTS = Path(__file__).resolve().parents[1] / "docs/progress/receipts"

def apply_receipts(inventory, ledger, receipts):
    result = copy.deepcopy(inventory)
    rows = {c["id"]: c for c in result["criteria"]}
    used = set()
    admitted = []
    for receipt in receipts:
        key = receipt.get("criterion_id")
        if key in used or key not in rows:
            raise ValueError("Unknown or duplicate progress receipt criterion")
        used.add(key)
        if receipt.get("schema") != "ur-progress-receipt/1":
            raise ValueError("Unknown receipt schema")
        if not receipt.get("independent_reviewer") or not receipt.get("rationale"):
            raise ValueError("Missing independent reviewer and rationale")
        if receipt.get("kind") not in ("new_implementation", "retroactive_evidence"):
            raise ValueError("Missing new versus retrospective attribution")
        references = receipt.get("evidence")
        audit = receipt.get("audit_receipt")
        if (not isinstance(references, list) or not references or
            not all(isinstance(u,str) and u.startswith(REPO) for u in references)
            or not isinstance(audit,str) or not audit.startswith(REPO)):
            raise ValueError("Receipt needs original source and independent audit links")
        row = rows[key]
        if row["area"] == "FID":
            raise ValueError("USA complete-event admission requires authoritative QA ledger, not this mechanism")
        if row["status"] == "bounded_verified":
            raise ValueError("Receipt duplicates an already verified criterion")
        if row["status"] != "unverified":
            raise ValueError("Regression rehabilitation requires explicit separate review")
        row.update(status="bounded_verified", audit_state="independent_reviewed",
                   evidence=references, audit_receipt=audit,
                   evidence_class="incremental_independent_progress_receipt",
                   independent_review_note=receipt["rationale"])
        admitted.append({"criterion_id":key, "kind":receipt["kind"],
                         "audit_receipt":audit})
    validate(result, ledger)
    return result, admitted

def read_receipts(folder=RECEIPTS):
    if not folder.exists():
        return []
    return [json.loads(f.read_text(encoding="utf-8")) for f in sorted(folder.glob("*.json"))]
