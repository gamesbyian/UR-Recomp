#!/usr/bin/env python3
"""Inspect the source-grounded three-project reuse opportunities for a work lane.

Advisory only: the live WORK-QUEUE selects tasks and the release ledger owns
acceptance. This prints existing reuse choices before a new implementation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "analysis/three-project-reuse-opportunities.json"
MATRIX = ROOT / "analysis/data/three-project-apparatus-capability-matrix-20261010.json"
LANES = ROOT / "analysis/agent-context-lanes.json"
ACTIVATIONS = {"now", "on_blocker", "after_baseline"}
ORDER = {"now": 0, "on_blocker": 1, "after_baseline": 2}
PRIORITY = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
REQUIRED = {"id", "activation", "lanes", "payoff", "trigger", "action", "qualification", "stop"}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(register: dict, matrix: dict, lanes: dict) -> list[str]:
    """Reject unsourced candidates, unknown lanes and missing admission tests."""
    errors: list[str] = []
    if register.get("schema_version") != 1:
        errors.append("unsupported reuse register schema")
    if register.get("capability_matrix") != MATRIX.relative_to(ROOT).as_posix():
        errors.append("reuse register does not refer to the audited capability matrix")
    if register.get("policy") != "docs/TRUSTED-UPSTREAM-ADOPTION.md":
        errors.append("reuse register does not link to the adopted policy")
    expected = {row["id"]: row for row in matrix.get("entries", [])}
    valid_lanes = set(lanes.get("lanes", {}))
    entries = register.get("entries")
    if not isinstance(entries, list) or not entries:
        return errors + ["no reusable capability entries"]
    seen: set[str] = set()
    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"entry[{idx}] is not an object")
            continue
        name = entry.get("id")
        if not isinstance(name, str) or name not in expected:
            errors.append(f"unknown capability: {name!r}")
            continue
        if name in seen:
            errors.append(f"duplicate capability: {name}")
        seen.add(name)
        if entry.get("activation") not in ACTIVATIONS:
            errors.append(f"{name}: invalid activation")
        membership = entry.get("lanes")
        if not isinstance(membership, list) or not membership or len(membership) != len(set(membership)):
            errors.append(f"{name}: invalid or duplicate lanes")
        elif not set(membership) <= valid_lanes:
            errors.append(f"{name}: nonexistent lane(s) {sorted(set(membership) - valid_lanes)}")
        for key in sorted(REQUIRED - {"id", "activation", "lanes"}):
            if not isinstance(entry.get(key), str) or not entry[key].strip():
                errors.append(f"{name}: missing {key}")
        source = expected[name]
        if not source.get("ur") or not (source.get("baldosa") or source.get("malmazuke")):
            errors.append(f"{name}: not a sourced local/upstream capability")
        if not source.get("proof") or not source.get("gap"):
            errors.append(f"{name}: capability matrix has no defined proof/gap")
        if entry.get("activation") == "after_baseline" and source.get("priority") == "P0":
            errors.append(f"{name}: P0 capability incorrectly deferred behind a baseline")
    return errors


def candidates(register: dict, matrix: dict, *, lane: str = "all", focus: str = "",
               include_conditional: bool = False, include_future: bool = False) -> list[dict]:
    by_id = {x["id"]: x for x in matrix["entries"]}
    selection: list[dict] = []
    for entry in register["entries"]:
        if lane != "all" and lane not in entry["lanes"]:
            continue
        activation = entry["activation"]
        if activation == "after_baseline" and not include_future:
            continue
        if activation == "on_blocker" and not include_conditional:
            continue
        upstream = by_id[entry["id"]]
        item = {**entry, "priority": upstream["priority"],
                "matrix_decision": upstream["decision"],
                "sources": {name: upstream.get(name, []) for name in ("ur", "baldosa", "malmazuke")}}
        searchable = " ".join(str(value) for value in [
            item["id"], item["payoff"], item["trigger"], item["action"],
            upstream["gap"], upstream["proof"], item["sources"],
        ]).lower()
        if focus and focus.casefold() not in searchable.casefold():
            continue
        selection.append(item)
    # Execution readiness first, then the live campaign's P0/P1 distinctions.
    # Agent-work-packets is meta-help and should not crowd out gameplay candidates.
    selection.sort(key=lambda item: (ORDER[item["activation"]],
                                    PRIORITY[item["priority"]],
                                    item["id"] == "agent-work-packets",
                                    item["id"]))
    return selection


def render(item: dict, *, show_sources: bool = True) -> str:
    lines = [
        f"[{item['priority']}/{item['activation']}] {item['id']} ({item['matrix_decision']})",
        f"  Payoff: {item['payoff']}",
        f"  Trigger: {item['trigger']}",
        f"  Reuse: {item['action']}",
        f"  Admit: {item['qualification']}",
        f"  Stop: {item['stop']}",
    ]
    if show_sources:
        for name in ("ur", "baldosa", "malmazuke"):
            paths = item["sources"][name]
            if paths:
                lines.append(f"  {name}: {', '.join(paths[:3])}" +
                             (f" (+{len(paths)-3})" if len(paths) > 3 else ""))
    return "\n".join(lines)


def context_hint(register: dict, matrix: dict, lane: str) -> str:
    """Small automatic addendum for existing agent lane packets."""
    selected = candidates(register, matrix, lane=lane, include_conditional=True)
    active = [x for x in selected if x["activation"] == "now" and x["id"] != "agent-work-packets"][:2]
    conditional = [x for x in selected if x["activation"] == "on_blocker"][:1]
    chosen = active + conditional
    lines = ["## Three-project reuse before new implementation", "",
             "Advisory: WORK-QUEUE selects the task; no upstream claim is release proof.",
             "Inspect UR's implementation and pinned Baldosa/Malmazuke solutions first.",
             "Only use a conditional pilot if its stated trigger actually occurs.",
             "Full, source-linked choices: python3 tools/select_three_project_reuse.py --lane " + lane + " --include-conditional"]
    for item in chosen:
        lines += ["", f"- **{item['id']}** [{item['activation']}]: {item['action']}",
                  f"  Test: {item['qualification']}"]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lane", default="all", help="agent lane, or all")
    parser.add_argument("--focus", default="", help="filter to a task/source/QA keyword")
    parser.add_argument("--include-conditional", action="store_true",
                        help="show on-blocker pilots without implying they are due")
    parser.add_argument("--include-future", action="store_true",
                        help="include baseline-blocked pilots")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--audit", action="store_true", help="validate all register entries")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    register, matrix, lanes = read_json(REGISTER), read_json(MATRIX), read_json(LANES)
    errors = validate(register, matrix, lanes)
    if errors:
        for error in errors:
            print("THREE_PROJECT_REUSE_INVALID", error)
        return 1
    if args.audit:
        print(f"THREE_PROJECT_REUSE_OK {len(register['entries'])} grounded choices")
        return 0
    if args.lane != "all" and args.lane not in lanes["lanes"]:
        parser.error(f"unknown lane: {args.lane}")
    if args.limit < 1:
        parser.error("--limit must be positive")
    found = candidates(register, matrix, lane=args.lane, focus=args.focus,
                       include_conditional=args.include_conditional,
                       include_future=args.include_future)
    shown = found[:args.limit]
    if args.json:
        print(json.dumps({
            "schema_version": 1,
            "authority": register["authority"],
            "lane": args.lane, "focus": args.focus,
            "matches": len(found), "truncated": len(shown) != len(found),
            "opportunities": shown,
        }, indent=2, ensure_ascii=False))
    else:
        print(f"Three-project reuse: {len(found)} matching choices, {len(shown)} shown.")
        print("Advisory only: select actual work from docs/WORK-QUEUE.md; certify via QA ledger.")
        for item in shown:
            print("\n" + render(item))
        if len(shown) < len(found):
            print(f"\n... {len(found)-len(shown)} more; use --limit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
