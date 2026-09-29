#!/usr/bin/env python3
"""Validate the Uniracers UI state-model surfaces against each other.

This intentionally uses only the Python standard library. The semantic state map
remains YAML for humans; this validator extracts only top-level state ids from
that file and treats the JSON artifacts as machine contracts.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

STATE_ID_RE = re.compile(r"^  - id: ([A-Z0-9_]+)\s*$")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def state_ids_from_yaml(path: Path) -> set[str]:
    ids: set[str] = set()
    in_states = False
    for raw in path.read_text().splitlines():
        if raw == "states:":
            in_states = True
            continue
        if in_states and raw == "open_questions:":
            break
        if not in_states:
            continue
        m = STATE_ID_RE.match(raw)
        if m:
            ids.add(m.group(1))
    return ids


def duplicates(values: list[str]) -> set[str]:
    return {v for v, n in Counter(values).items() if n > 1}


def validate(root: Path) -> list[str]:
    failures: list[str] = []

    state_map = root / "analysis/ui-state-map.yml"
    transition_path = root / "analysis/ui-transition-contract.json"
    capture_path = root / "analysis/ui-capture-manifest.json"
    menu_path = root / "analysis/ui-menu-index.json"
    frame_compare_path = root / "analysis/ui-frame-comparisons.json"
    reference_index_path = root / "analysis/ui-reference-index.json"
    text_entry_path = root / "analysis/ui-text-entry-layout.json"
    fixture_path = root / "tests/fixtures.json"

    states = state_ids_from_yaml(state_map)
    if not states:
        failures.append("no state ids extracted from analysis/ui-state-map.yml")

    transitions = load_json(transition_path)
    captures = load_json(capture_path)
    menu = load_json(menu_path)
    frame_compare = load_json(frame_compare_path)
    reference_index = load_json(reference_index_path)
    text_entry = load_json(text_entry_path)
    fixtures = load_json(fixture_path)

    if transitions.get("schema_version") != 1:
        failures.append("unsupported ui-transition-contract schema_version")
    if captures.get("schema_version") != 1:
        failures.append("unsupported ui-capture-manifest schema_version")
    if menu.get("schema_version") != 1:
        failures.append("unsupported ui-menu-index schema_version")

    edges = transitions.get("edges", [])
    dependencies = transitions.get("capability_dependencies", {})
    capture_exempt = transitions.get("capture_exempt_states", [])
    for state in capture_exempt:
        if state not in states:
            failures.append(f"capture_exempt_states: unknown state {state!r}")

    transition_exempt = transitions.get("transition_exempt_states", [])
    for state in transition_exempt:
        if state not in states:
            failures.append(f"transition_exempt_states: unknown state {state!r}")

    completion_tiers = transitions.get("completion_tiers", {})
    tier_states: list[str] = []
    for tier_id, tier in completion_tiers.items():
        if tier_id not in {"1", "2", "3"}:
            failures.append(f"completion_tiers: unknown tier {tier_id!r}")
        listed = tier.get("states", [])
        if not isinstance(listed, list):
            failures.append(f"completion_tiers[{tier_id!r}]: states must be a list")
            continue
        for state in listed:
            tier_states.append(state)
            if state not in states:
                failures.append(
                    f"completion_tiers[{tier_id!r}]: unknown state {state!r}"
                )
    for dup in sorted(duplicates(tier_states)):
        failures.append(f"completion_tiers: state appears in multiple tiers: {dup}")
    unclassified = sorted(states - set(tier_states))
    if completion_tiers and unclassified:
        failures.append(
            "completion_tiers: unclassified states: " + ", ".join(unclassified)
        )
    edge_ids = [e.get("id") for e in edges]
    for dup in sorted(duplicates([x for x in edge_ids if isinstance(x, str)])):
        failures.append(f"duplicate transition id: {dup}")

    allowed_status = set(transitions.get("status_meanings", {}))
    fixture_ids = {f.get("id") for f in fixtures.get("fixtures", [])}

    for i, edge in enumerate(edges):
        label = edge.get("id") or f"edge[{i}]"
        for endpoint in ("from", "to"):
            value = edge.get(endpoint)
            if value not in states:
                failures.append(f"{label}: unknown {endpoint} state {value!r}")
        status = edge.get("status")
        if status not in allowed_status:
            failures.append(f"{label}: unknown status {status!r}")
        if edge.get("fixture") and edge["fixture"] not in fixture_ids:
            failures.append(f"{label}: unknown fixture {edge['fixture']!r}")
        if edge.get("blocked_by") and edge["blocked_by"] not in dependencies:
            failures.append(f"{label}: unknown capability dependency {edge['blocked_by']!r}")
        if edge.get("probe") and edge["probe"] not in fixture_ids:
            failures.append(f"{label}: unknown probe fixture {edge['probe']!r}")
        if not edge.get("trigger"):
            failures.append(f"{label}: missing trigger")

    capture_tags = [c.get("tag") for c in captures.get("captures", [])]
    for dup in sorted(duplicates([x for x in capture_tags if isinstance(x, str)])):
        failures.append(f"duplicate capture tag: {dup}")

    for capture in captures.get("captures", []):
        tag = capture.get("tag", "<untagged>")
        state = capture.get("state_id")
        if state not in states:
            failures.append(f"capture {tag}: unknown state {state!r}")
        source_fixture = capture.get("source_fixture")
        if source_fixture and source_fixture not in fixture_ids:
            failures.append(f"capture {tag}: unknown source fixture {source_fixture!r}")

    menu_values: dict[str, list[dict]] = {}
    for entry in menu.get("entries", []):
        state = entry.get("state_id")
        if state not in states:
            failures.append(f"menu {entry.get('value')}: unknown state {state!r}")
        value = entry.get("value")
        if value:
            menu_values.setdefault(value.upper(), []).append(entry)

    # Multiple meanings for one byte are permitted only when each entry is
    # explicitly variant-qualified or marked ambiguous.
    for value, entries in sorted(menu_values.items()):
        if len(entries) < 2:
            continue
        if not all(e.get("variant") or "ambiguous" in str(e.get("status", "")) for e in entries):
            names = ", ".join(str(e.get("state_id")) for e in entries)
            failures.append(f"menu value {value} has unqualified multiple meanings: {names}")

    for dep_id, dep in dependencies.items():
        for state in dep.get("blocks_states", []):
            if state not in states:
                failures.append(f"capability {dep_id}: unknown blocked state {state!r}")
        plan = dep.get("plan")
        if plan and not (root / plan).is_file():
            failures.append(f"capability {dep_id}: missing plan {plan!r}")
        acceptance_fixture = dep.get("acceptance_fixture")
        if acceptance_fixture and acceptance_fixture not in fixture_ids:
            failures.append(
                f"capability {dep_id}: unknown acceptance fixture {acceptance_fixture!r}"
            )

    capture_tag_set = {c.get("tag") for c in captures.get("captures", [])}
    pair_ids = []
    for pair in frame_compare.get("pairs", []):
        pair_id = pair.get("id")
        pair_ids.append(pair_id)
        for side in ("before", "after"):
            tag = pair.get(side)
            if tag not in capture_tag_set:
                failures.append(f"frame pair {pair_id}: unknown {side} capture tag {tag!r}")
    for dup in sorted(duplicates([x for x in pair_ids if isinstance(x, str)])):
        failures.append(f"duplicate frame-comparison id: {dup}")

    reference_states = []
    for entry in reference_index.get("entries", []):
        state = entry.get("state_id")
        reference_states.append(state)
        if state not in states:
            failures.append(f"visual reference index: unknown state {state!r}")
        if not entry.get("references"):
            failures.append(f"visual reference index: {state!r} has no references")
    for dup in sorted(duplicates([x for x in reference_states if isinstance(x, str)])):
        failures.append(f"duplicate visual-reference state entry: {dup}")

    for state in text_entry.get("applies_to", []):
        if state not in states:
            failures.append(f"text-entry layout: unknown state {state!r}")
    next_probe = text_entry.get("next_probe")
    if next_probe:
        if not (root / next_probe).is_file():
            failures.append(f"text-entry layout: missing next probe {next_probe!r}")

    # Every capture contract should point at a fixture that actually declares
    # the tag when the fixture has an explicit checkpoint list.
    fixture_by_id = {f.get("id"): f for f in fixtures.get("fixtures", [])}
    for capture in captures.get("captures", []):
        fid = capture.get("source_fixture")
        if not fid:
            continue
        fixture = fixture_by_id.get(fid)
        if not fixture:
            continue
        checkpoints = fixture.get("checkpoints")
        if isinstance(checkpoints, list) and capture.get("tag") not in checkpoints:
            failures.append(
                f"capture {capture.get('tag')}: not declared by fixture {fid}"
            )

    return failures


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = ap.parse_args()

    failures = validate(args.root)
    if failures:
        print("UI state model validation failed:")
        for failure in failures:
            print(f"  {failure}")
        return 1

    states = state_ids_from_yaml(args.root / "analysis/ui-state-map.yml")
    transitions = load_json(args.root / "analysis/ui-transition-contract.json")
    captures = load_json(args.root / "analysis/ui-capture-manifest.json")
    menu = load_json(args.root / "analysis/ui-menu-index.json")
    print(
        "UI state model valid "
        f"({len(states)} states, {len(transitions['edges'])} transitions, "
        f"{len(captures['captures'])} captures, {len(menu['entries'])} menu-index entries)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
