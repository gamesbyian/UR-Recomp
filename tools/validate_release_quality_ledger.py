#!/usr/bin/env python3
"""Validate explicit release QA gate claims without consulting GitHub or CI.

This is intentionally separate from developer-package smoke acceptance.
A user can run it against a source tree before labeling an alpha or beta.
Passing validates honest bookkeeping, not the underlying game or a release.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
VALID_STATUSES = {"unverified", "in_progress", "passed", "failed", "blocked", "waived"}
REQUIRED_IDS = {f"QA-{n:02d}" for n in range(1, 13)}
REQUIRED_LAYERS = {"L4", "L5"}
VALID_PRIORITIES = {"P0", "P1", "P2"}
GATE_ID = re.compile(r"QA-[0-9]{2}\Z")
JOURNEY_ID = re.compile(r"J-[0-9]{2}\Z")
SHA = re.compile(r"[0-9a-f]{40}\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
LAYER_RANK = {"L1": 1, "L2": 2, "L3": 3, "L4": 4, "L5": 5}


def check_registry(registry: object, repo_root: pathlib.Path) -> list[str]:
    errors: list[str] = []
    if not isinstance(registry, dict):
        return ["root must be an object"]
    if registry.get("schema") != "UR-RELEASE-QUALITY-LEDGER/1":
        errors.append("unexpected schema")
    candidate = registry.get("candidate")
    if not isinstance(candidate, dict):
        return errors + ["candidate must be an object"]
    commit = candidate.get("commit_sha")
    artifact = candidate.get("zip_sha256")
    if commit is not None and (not isinstance(commit, str) or not SHA.fullmatch(commit)):
        errors.append("candidate commit_sha must be 40 lowercase hex or null")
    if artifact is not None and (not isinstance(artifact, str) or not SHA256.fullmatch(artifact)):
        errors.append("candidate zip_sha256 must be 64 lowercase hex or null")
    if (commit is None) != (artifact is None):
        errors.append("candidate SHA and artifact SHA-256 must be pinned together")
    gates = registry.get("gates")
    if not isinstance(gates, list):
        return errors + ["gates must be an array"]
    seen: set[str] = set()
    journeys_path = repo_root / "docs" / "QA-PLAYER-JOURNEYS.md"
    try:
        journey_text = journeys_path.read_text(encoding="utf-8")
    except OSError:
        journey_text = ""
        errors.append("QA player journeys document unavailable")
    journey_ids = set(re.findall(r"\bJ-[0-9]{2}\b", journey_text))
    for index, gate in enumerate(gates):
        if not isinstance(gate, dict):
            errors.append(f"gates[{index}] must be an object")
            continue
        name = gate.get("id")
        if not isinstance(name, str) or not GATE_ID.fullmatch(name):
            errors.append(f"gates[{index}] has invalid id")
            continue
        if name in seen:
            errors.append(f"duplicate gate {name}")
        seen.add(name)
        if gate.get("priority") not in VALID_PRIORITIES:
            errors.append(f"{name} invalid priority")
        if not isinstance(gate.get("claim"), str) or not gate["claim"].strip():
            errors.append(f"{name} missing claim")
        if not isinstance(gate.get("next_action"), str) or not gate["next_action"].strip():
            errors.append(f"{name} missing next_action")
        status = gate.get("status")
        if status not in VALID_STATUSES:
            errors.append(f"{name} invalid status")
        minimum = gate.get("required_layer")
        if minimum not in REQUIRED_LAYERS:
            errors.append(f"{name} must require L4 or L5")
        journeys = gate.get("journeys")
        if not isinstance(journeys, list) or not journeys:
            errors.append(f"{name} missing journeys")
        else:
            for j in journeys:
                if not isinstance(j, str) or not JOURNEY_ID.fullmatch(j) or j not in journey_ids:
                    errors.append(f"{name} unknown journey {j!r}")
        refs = gate.get("evidence_refs")
        if not isinstance(refs, list) or not refs:
            errors.append(f"{name} missing source contracts")
        else:
            for ref in refs:
                if (not isinstance(ref, str) or not ref.startswith("docs/")
                        or ".." in pathlib.PurePosixPath(ref).parts
                        or not (repo_root / ref).is_file()):
                    errors.append(f"{name} missing or unsafe source contract {ref!r}")
        witnesses = gate.get("witnesses")
        if not isinstance(witnesses, list):
            errors.append(f"{name} witnesses must be a list")
            witnesses = []
        if status == "passed":
            if not commit or not artifact or gate.get("candidate_commit") != commit:
                errors.append(f"{name} passed without exact pinned candidate")
            if not witnesses:
                errors.append(f"{name} passed without independent recorded witnesses")
        if status == "waived" and not gate.get("waiver_reason"):
            errors.append(f"{name} waiver needs explicit rationale")
        for w in witnesses:
            if not isinstance(w, dict):
                errors.append(f"{name} malformed witness")
                continue
            if (w.get("source_commit") != commit or
                    w.get("artifact_sha256") != artifact or
                    not commit or not artifact):
                errors.append(f"{name} witness not tied to exact candidate artifact")
            if not isinstance(w.get("source"), str) or not w["source"].strip():
                errors.append(f"{name} witness must identify reproducible source")
            if not isinstance(w.get("tested_at"), str) or not w["tested_at"]:
                errors.append(f"{name} witness lacks tested_at")
            rank = LAYER_RANK.get(w.get("layer"), 0)
            if rank < LAYER_RANK.get(minimum, 99):
                errors.append(f"{name} witness below required layer {minimum}")
        if status != "passed" and witnesses and gate.get("candidate_commit") != commit:
            errors.append(f"{name} witness candidate mismatch")
    missing = REQUIRED_IDS - seen
    extra = seen - REQUIRED_IDS
    if missing:
        errors.append("missing mandatory gates: " + ", ".join(sorted(missing)))
    if extra:
        errors.append("unexpected gate IDs: " + ", ".join(sorted(extra)))
    if candidate.get("release_decision") in {"beta", "release_candidate", "public_release"}:
        incomplete = [g.get("id", "?") for g in gates
                      if not isinstance(g, dict) or g.get("status") not in {"passed", "waived"}]
        if incomplete:
            errors.append("release decision with unresolved gates: " + ", ".join(incomplete))
        if not candidate.get("physical_hardware_verified"):
            errors.append("release decision without physical Windows validation")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=pathlib.Path, default=ROOT)
    parser.add_argument("--ledger", type=pathlib.Path)
    args = parser.parse_args()
    root = args.repo_root.resolve()
    path = args.ledger or root / "docs" / "RELEASE-QUALITY-LEDGER.json"
    try:
        registry = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"release quality ledger unavailable/invalid: {exc}", file=sys.stderr)
        return 2
    errors = check_registry(registry, root)
    for error in errors:
        print("RELEASE_LEDGER_FAIL " + error, file=sys.stderr)
    if errors:
        return 1
    print(f"RELEASE_LEDGER_VALID gates={len(registry['gates'])} "
          "claim=bookkeeping-only release_verified=0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
