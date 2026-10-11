#!/usr/bin/env python3
"""Validate the pinned three-project apparatus census and functional dispositions.

Offline only. Inventories are commit-bound research snapshots, NOT a claim that
upstream tools execute correctly or that UR's release ledger has new passes.
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
BALD = ROOT / "analysis/data/baldosa-upstream-file-census.json"
MAL = ROOT / "analysis/data/malmazuke-upstream-file-census-20261010.json"
UR = ROOT / "analysis/data/ur-project-apparatus-census-20261010.json"
MATRIX = ROOT / "analysis/data/three-project-apparatus-capability-matrix-20261010.json"
PINS = {
    "ur": "a6537bd10d76e95e239529b9133a89cd00dab4d0",
    "baldosa": "10b864b9d14a7b7416dd909eb7b054c88faef101",
    "malmazuke": "42d444594641d23f5d3c15da7b7c454bb5180e43",
}
SHA = re.compile(r"^[a-f0-9]{40}$")
PRIORITIES = {"P0", "P1", "P2", "P3"}
DECISIONS = {
    "keep_existing", "integrated_reference", "integrated_bounded",
    "reference", "integrate_seam", "pilot_needs_real_capture",
    "pilot_on_demand", "pilot_read_only", "conditional",
    "defer_until_first_accept", "defer", "adapt_read_only",
}


def read(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected object")
    return value


def check_records(entries: list, *, expected: int, label: str) -> list[str]:
    errors = []
    if not isinstance(entries, list) or len(entries) != expected:
        return [f"{label}: expected {expected} entries"]
    seen = set()
    for item in entries:
        if not isinstance(item, dict):
            errors.append(f"{label}: bad entry")
            continue
        p = item.get("path")
        if not isinstance(p, str) or not p or p.startswith("/") or ".." in p.split("/"):
            errors.append(f"{label}: invalid path {p!r}")
        if p in seen:
            errors.append(f"{label}: duplicate path {p}")
        seen.add(p)
        if not isinstance(item.get("sha"), str) or not SHA.fullmatch(item["sha"]):
            errors.append(f"{label}: malformed Git object {p}")
    return errors


def validate(bald: dict, mal: dict, ur: dict, matrix: dict) -> list[str]:
    errors = []
    if bald.get("pinned_commit") != PINS["baldosa"] or bald.get("source_tree_entries") != 210:
        errors.append("Baldosa pin or count changed")
    errors += check_records(bald.get("entries"), expected=210, label="Baldosa")
    if mal.get("pinned_commit") != PINS["malmazuke"] or mal.get("tree_entries") != 1062 or mal.get("truncated") is not False:
        errors.append("malmazuke pin, count or completeness changed")
    errors += check_records(mal.get("entries"), expected=1062, label="malmazuke")
    if mal.get("blob_entries") != 1006:
        errors.append("malmazuke tracked file count changed")
    if ur.get("source_commit") != PINS["ur"] or ur.get("total_file_entries") != 7908 or ur.get("truncated") is not False:
        errors.append("UR audited snapshot pin, file count or completeness changed")
    errors += check_records(ur.get("entries"), expected=2680, label="UR apparatus")
    expected_scopes = {
        "tools": 506, "tests": 938, "docs": 200, "workflows": 132,
        "analysis": 358, "reference": 311, "native": 235,
    }
    counts = Counter(x.get("scope") for x in ur.get("entries", []) if isinstance(x, dict))
    if dict(counts) != expected_scopes:
        errors.append(f"UR apparatus scope count mismatch: {dict(counts)}")
    if mal.get("blob_entries") != sum(x.get("type") == "blob" for x in mal.get("entries", [])):
        errors.append("malmazuke blob count mismatch")
    if matrix.get("pins") != PINS:
        errors.append("matrix lacks exact reviewed revision pins")
    sources = {
        "ur": {x["path"] for x in ur.get("entries", []) if isinstance(x, dict)},
        "baldosa": {x["path"] for x in bald.get("entries", []) if isinstance(x, dict)},
        "malmazuke": {x["path"] for x in mal.get("entries", []) if isinstance(x, dict)},
    }
    items = matrix.get("entries")
    if not isinstance(items, list) or len(items) < 30:
        errors.append("capability matrix too small or invalid")
        return errors
    ids = set()
    for row in items:
        name = row.get("id")
        if not isinstance(name, str) or not name or name in ids:
            errors.append(f"missing or duplicate capability {name!r}")
        ids.add(name)
        if row.get("priority") not in PRIORITIES:
            errors.append(f"{name}: bad priority")
        if row.get("decision") not in DECISIONS:
            errors.append(f"{name}: bad disposition")
        if not row.get("gap") or not row.get("proof"):
            errors.append(f"{name}: gap or acceptance proof missing")
        for project, valid in sources.items():
            refs = row.get(project)
            if not isinstance(refs, list):
                errors.append(f"{name}: missing {project} source list")
                continue
            for ref in refs:
                if ref not in valid:
                    errors.append(f"{name}: ungrounded {project} path: {ref}")
    return errors


def main() -> int:
    errors = validate(read(BALD), read(MAL), read(UR), read(MATRIX))
    if errors:
        for error in errors:
            print("APPARATUS_AUDIT_ERROR", error)
        return 1
    print("APPARATUS_CENSUS_OK Baldosa=210 malmazuke=1062 UR-apparatus=2680")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
