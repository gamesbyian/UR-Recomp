#!/usr/bin/env python3
"""Validate analysis/frontend-modernization-policy.json against the UI state map.

The policy file classifies every original frontend conceptual state/feature as a
presentation artifact, gameplay mechanic or administrative system and records its
Modern-mode disposition. This validator enforces the PROJECT-PLAN.md subtraction
rule mechanically:

- every conceptual state in analysis/ui-state-map.yml is covered by a feature;
- presentation artifacts and gameplay mechanics may only be preserved/augmented;
- a decided redesign cites an existing policy heading; an open one names its gate.

Standard library only. ``--summary`` prints a per-state classification table.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from validate_ui_state_model import state_ids_from_yaml

POLICY_PATH = "analysis/frontend-modernization-policy.json"
STATE_MAP_PATH = "analysis/ui-state-map.yml"
REQUIRED_CLASSES = {"presentation_artifact", "gameplay_mechanic", "administrative"}
REDESIGN = {"redesign_decided", "redesign_candidate"}


def heading_slugs(path: Path) -> set[str]:
    slugs: set[str] = set()
    for line in path.read_text().splitlines():
        m = re.match(r"^#{1,6}\s+(.*?)\s*$", line)
        if not m:
            continue
        text = re.sub(r"[^\w\s-]", "", m.group(1).lower())
        slugs.add(re.sub(r"\s", "-", text.strip()))
    return slugs


def check_doc_ref(root: Path, ref: str, where: str) -> list[str]:
    path_part, _, anchor = ref.partition("#")
    path = root / path_part
    if not path.is_file():
        return [f"{where}: missing document {path_part!r}"]
    if anchor and anchor not in heading_slugs(path):
        return [f"{where}: no heading anchor #{anchor} in {path_part}"]
    return []


def validate(root: Path) -> list[str]:
    failures: list[str] = []
    policy_path = root / POLICY_PATH
    if not policy_path.is_file():
        return [f"missing {POLICY_PATH}"]
    policy = json.loads(policy_path.read_text())
    states = state_ids_from_yaml(root / STATE_MAP_PATH)

    classes = set(policy.get("classes", {}))
    if classes != REQUIRED_CLASSES:
        failures.append(f"classes must be exactly {sorted(REQUIRED_CLASSES)}, got {sorted(classes)}")
    dispositions = set(policy.get("dispositions", {}))
    allowed = policy.get("allowed_dispositions_by_class", {})
    for cls, values in allowed.items():
        if cls not in REQUIRED_CLASSES:
            failures.append(f"allowed_dispositions_by_class: unknown class {cls!r}")
        unknown = set(values) - dispositions
        if unknown:
            failures.append(f"allowed_dispositions_by_class[{cls}]: unknown dispositions {sorted(unknown)}")
        if cls != "administrative" and set(values) & REDESIGN:
            failures.append(
                f"allowed_dispositions_by_class[{cls}]: only administrative features may be redesigned"
            )

    owner = policy.get("owner")
    if owner:
        failures.extend(check_doc_ref(root, owner, "owner"))

    features = policy.get("features", [])
    ids = [f.get("id", "") for f in features]
    for dup in sorted(v for v, n in Counter(ids).items() if n > 1):
        failures.append(f"duplicate feature id {dup!r}")

    covered: set[str] = set()
    for feature in features:
        fid = feature.get("id") or "<missing id>"
        cls = feature.get("class")
        modern = feature.get("modern")
        if cls not in REQUIRED_CLASSES:
            failures.append(f"{fid}: unknown class {cls!r}")
            continue
        if modern not in allowed.get(cls, []):
            failures.append(f"{fid}: disposition {modern!r} not allowed for class {cls}")
        if not feature.get("rationale"):
            failures.append(f"{fid}: rationale required")
        fstates = feature.get("states") or []
        if not fstates:
            failures.append(f"{fid}: states must be a non-empty list")
        for state in fstates:
            if state not in states:
                failures.append(f"{fid}: unknown state {state!r}")
        covered.update(fstates)
        if modern == "redesign_decided":
            ref = feature.get("policy_source")
            if not ref:
                failures.append(f"{fid}: redesign_decided requires policy_source")
            else:
                failures.extend(check_doc_ref(root, ref, f"{fid}.policy_source"))
        elif feature.get("policy_source"):
            failures.extend(check_doc_ref(root, feature["policy_source"], f"{fid}.policy_source"))
        if modern == "redesign_candidate" and not feature.get("decision_gate"):
            failures.append(f"{fid}: redesign_candidate requires decision_gate")

    uncovered = sorted(states - covered)
    if uncovered:
        failures.append("states without a modernization classification: " + ", ".join(uncovered))
    return failures


def summary(root: Path) -> str:
    policy = json.loads((root / POLICY_PATH).read_text())
    by_state: dict[str, list[str]] = {}
    for feature in policy["features"]:
        for state in feature["states"]:
            by_state.setdefault(state, []).append(
                f"{feature['id']} [{feature['class']} -> {feature['modern']}]"
            )
    lines = []
    for state in sorted(by_state):
        lines.append(state)
        lines.extend(f"  {entry}" for entry in by_state[state])
    counts = Counter((f["class"], f["modern"]) for f in policy["features"])
    lines.append("")
    for (cls, modern), n in sorted(counts.items()):
        lines.append(f"{cls:22} {modern:22} {n}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--summary", action="store_true", help="print the per-state classification")
    args = ap.parse_args()

    failures = validate(args.root)
    if failures:
        print("Frontend modernization policy validation failed:")
        for failure in failures:
            print(f"  {failure}")
        return 1
    policy = json.loads((args.root / POLICY_PATH).read_text())
    print(f"Frontend modernization policy valid ({len(policy['features'])} features).")
    if args.summary:
        print(summary(args.root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
