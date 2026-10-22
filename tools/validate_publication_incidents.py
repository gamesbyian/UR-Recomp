#!/usr/bin/env python3
"""Fail-closed, offline incident *integrity* validation; never retry blocked writes."""
from __future__ import annotations
import json
import re
from pathlib import Path
from agent_control import (BOARD, REGISTRY, HISTORICAL_WORK_IDS, extract_board,
                           load_json, validate_registry)

ROOT = Path(__file__).resolve().parents[1]
INCIDENTS = ROOT / "docs/recovery/publication-incidents.json"
DRIVE_ID = re.compile(r"[A-Za-z0-9_-]{15,}\Z")
SHA40 = re.compile(r"[0-9a-f]{40}\Z")
SHA64 = re.compile(r"[0-9a-f]{64}\Z")
READBACK = {"pending", "verified", "failed", "unknown"}
DISPOSITIONS = {"held_for_independent_review", "escalated", "independently_resolved", "unknown"}
DENIALS = {"explicit_safety_denial", "explicit_policy_denial"}
RETRYABLE = {"transport_error", "source_conflict", "unknown"}

def check(incidents, board, registry):
    if type(incidents) is not dict or incidents.get("schema") != "ur-publication-incidents/1":
        raise ValueError("unknown incident schema")
    if incidents.get("scope") != "curated_not_exhaustive":
        raise ValueError("incident registry must be explicitly nonexhaustive")
    rows = incidents.get("incidents")
    if type(rows) is not list:
        raise ValueError("incidents array missing")
    # Historical refusals retain their IDs when the live board rotates.
    # Do not admit arbitrary orphan work IDs.
    known = {x["work_id"] for x in board["work"]} | HISTORICAL_WORK_IDS
    candidates = {x["candidate_id"]: x for x in registry["candidates"]}
    ids = set()
    for entry in rows:
        if type(entry) is not dict:
            raise ValueError("incident must be object")
        required = ("incident_id", "work_id", "candidate_id", "operation", "target_path",
                    "original_error", "classification", "vault_file_id", "vault_sha256",
                    "byte_readback", "disposition", "next_authorized_action",
                    "release_gate_credit", "source_main_sha")
        if any(k not in entry for k in required):
            raise ValueError("incident missing required field")
        cid = entry["incident_id"]
        if type(cid) is not str or not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,95}", cid) or cid in ids:
            raise ValueError("invalid or duplicate incident ID")
        ids.add(cid)
        if entry["work_id"] not in known:
            raise ValueError("orphan incident work ID")
        if type(entry["candidate_id"]) is not str or not entry["candidate_id"].strip():
            raise ValueError("missing incident candidate ID")
        matching = candidates.get(entry["candidate_id"])
        if matching and matching["work_id"] != entry["work_id"]:
            raise ValueError("candidate work ID conflict")
        for key in ("operation", "target_path", "original_error", "next_authorized_action"):
            if type(entry[key]) is not str or not entry[key].strip():
                raise ValueError("missing original incident evidence: " + key)
        if entry["release_gate_credit"] is not False:
            raise ValueError("incident cannot award release acceptance")
        if entry["classification"] not in DENIALS | RETRYABLE:
            raise ValueError("unknown incident classification")
        if entry["byte_readback"] not in READBACK:
            raise ValueError("invalid byte readback status")
        if entry["disposition"] not in DISPOSITIONS:
            raise ValueError("invalid incident disposition")
        if entry["classification"] in DENIALS and entry["disposition"] not in {
            "held_for_independent_review", "escalated", "independently_resolved"}:
            raise ValueError("explicit denial cannot be actionable retry")
        if entry["byte_readback"] == "verified" and entry["vault_sha256"] is None:
            raise ValueError("verified readback requires digest")
        if entry["vault_sha256"] is not None and (
                type(entry["vault_sha256"]) is not str
                or not SHA64.fullmatch(entry["vault_sha256"])):
            raise ValueError("invalid vault SHA-256")
        if entry["source_main_sha"] is not None and (
                type(entry["source_main_sha"]) is not str
                or not SHA40.fullmatch(entry["source_main_sha"])):
            raise ValueError("invalid source main SHA")
        if entry["vault_file_id"] is not None and (
                type(entry["vault_file_id"]) is not str
                or not DRIVE_ID.fullmatch(entry["vault_file_id"])):
            raise ValueError("invalid Vault Drive ID")
        if entry["classification"] in DENIALS:
            denied_text = entry["original_error"].lower()
            if "blocked" not in denied_text and "denied" not in denied_text and "refus" not in denied_text:
                raise ValueError("explicit denial lacks original refusal wording")
    return {"incidents": len(rows), "held": sum(x["disposition"] == "held_for_independent_review" for x in rows)}

def main():
    board = extract_board(BOARD.read_text(encoding="utf8"))
    candidates = load_json(REGISTRY)
    validate_registry(candidates, board)
    print(json.dumps(check(load_json(INCIDENTS), board, candidates), sort_keys=True))

if __name__ == "__main__":
    main()
