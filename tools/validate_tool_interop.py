#!/usr/bin/env python3
"""Validate the repository's tool/data interoperability catalog."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEROP = Path(__file__).with_name("tool_interop.json")
TOOLCHAIN = Path(__file__).with_name("toolchain.json")
ALLOWED_STATUS = {"verified", "supported", "candidate"}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def duplicate_ids(items: list[dict]) -> set[str]:
    seen: set[str] = set()
    dup: set[str] = set()
    for item in items:
        ident = item.get("id")
        if ident in seen:
            dup.add(ident)
        seen.add(ident)
    return dup


def validate() -> list[str]:
    data = load(INTEROP)
    toolchain = load(TOOLCHAIN)
    failures: list[str] = []

    if data.get("schema_version") != 1:
        failures.append("unsupported tool_interop schema_version")

    formats = data.get("formats", [])
    components = data.get("components", [])
    handoffs = data.get("handoffs", [])
    chains = data.get("chains", [])

    for label, items in (("format", formats), ("component", components), ("chain", chains)):
        if not isinstance(items, list):
            failures.append(f"{label}s must be a list")
            continue
        for ident in sorted(duplicate_ids(items)):
            failures.append(f"duplicate {label} id: {ident}")

    format_ids = {x.get("id") for x in formats}
    component_ids = {x.get("id") for x in components}
    external_ids = {x.get("id") for x in toolchain.get("tools", [])}

    for c in components:
        cid = c.get("id")
        kind = c.get("kind")
        if kind not in {"project", "external"}:
            failures.append(f"{cid}: invalid component kind {kind!r}")
        if kind == "external" and cid not in external_ids:
            failures.append(f"{cid}: external component missing from toolchain.json")
        for direction in ("consumes", "produces"):
            values = c.get(direction, [])
            if not isinstance(values, list):
                failures.append(f"{cid}: {direction} must be a list")
                continue
            for fmt in values:
                if fmt not in format_ids:
                    failures.append(f"{cid}: unknown {direction} format {fmt!r}")

    component_by_id = {x.get("id"): x for x in components}
    for i, h in enumerate(handoffs):
        src = h.get("from")
        dst = h.get("to")
        fmt = h.get("format")
        status = h.get("status")
        if src not in component_ids:
            failures.append(f"handoff {i}: unknown source {src!r}")
            continue
        if dst not in component_ids:
            failures.append(f"handoff {i}: unknown destination {dst!r}")
            continue
        if fmt not in format_ids:
            failures.append(f"handoff {i}: unknown format {fmt!r}")
            continue
        if status not in ALLOWED_STATUS:
            failures.append(f"handoff {i}: invalid status {status!r}")
        if fmt not in component_by_id[src].get("produces", []):
            failures.append(f"handoff {src}->{dst}: source does not declare produced format {fmt}")
        if fmt not in component_by_id[dst].get("consumes", []):
            failures.append(f"handoff {src}->{dst}: destination does not declare consumed format {fmt}")
        if not h.get("evidence"):
            failures.append(f"handoff {src}->{dst}: missing evidence/rationale")

    for chain in chains:
        cid = chain.get("id")
        if chain.get("status") not in ALLOWED_STATUS:
            failures.append(f"{cid}: invalid chain status {chain.get('status')!r}")
        steps = chain.get("steps", [])
        if len(steps) < 2:
            failures.append(f"{cid}: chain needs at least two steps")
        for step in steps:
            if step not in component_ids:
                failures.append(f"{cid}: unknown component {step!r}")
        if not chain.get("purpose"):
            failures.append(f"{cid}: missing purpose")

    return failures


def main() -> int:
    failures = validate()
    if failures:
        print("Tool interoperability catalog failed:")
        for failure in failures:
            print(f"  {failure}")
        return 1
    data = load(INTEROP)
    print(
        "Tool interoperability catalog valid "
        f"({len(data['components'])} components, "
        f"{len(data['handoffs'])} handoffs, "
        f"{len(data['chains'])} chains)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
