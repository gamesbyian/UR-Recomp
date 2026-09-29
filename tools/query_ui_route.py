#!/usr/bin/env python3
"""Plan conceptual Uniracers frontend routes from the machine-readable transition contract."""

from __future__ import annotations

import argparse
import json
from collections import deque
from pathlib import Path

STATUS_ORDER = {
    "verified": 0,
    "documented": 1,
    "historical": 2,
    "hypothesis": 3,
}


def load_contract(path: Path) -> dict:
    data = json.loads(path.read_text())
    if data.get("schema_version") != 1:
        raise ValueError("unsupported transition contract schema")
    return data


def allowed(status: str, max_status: str) -> bool:
    return STATUS_ORDER[status] <= STATUS_ORDER[max_status]


def find_route(
    data: dict,
    start: str,
    goal: str,
    max_status: str,
    allow_blocked: bool = False,
) -> list[dict] | None:
    dependencies = data.get("capability_dependencies", {})
    edges = []
    for edge in data["edges"]:
        if not allowed(edge["status"], max_status):
            continue
        blocker = edge.get("blocked_by")
        if blocker and not allow_blocked:
            dep = dependencies.get(blocker, {})
            if dep.get("status") != "complete":
                continue
        edges.append(edge)
    outgoing: dict[str, list[dict]] = {}
    for edge in edges:
        outgoing.setdefault(edge["from"], []).append(edge)

    q = deque([(start, [])])
    seen = {start}
    while q:
        state, route = q.popleft()
        if state == goal:
            return route
        for edge in outgoing.get(state, []):
            nxt = edge["to"]
            if nxt in seen:
                continue
            seen.add(nxt)
            q.append((nxt, route + [edge]))
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--contract", type=Path, default=Path("analysis/ui-transition-contract.json"))
    ap.add_argument("--from", dest="start", required=True)
    ap.add_argument("--to", dest="goal", required=True)
    ap.add_argument(
        "--max-status",
        choices=list(STATUS_ORDER),
        default="hypothesis",
        help="weakest evidence class permitted in the route",
    )
    ap.add_argument("--json", action="store_true", dest="as_json")
    ap.add_argument(
        "--allow-blocked",
        action="store_true",
        help="include transitions blocked by an open capability dependency",
    )
    args = ap.parse_args()

    data = load_contract(args.contract)
    route = find_route(data, args.start.upper(), args.goal.upper(), args.max_status, args.allow_blocked)
    if route is None:
        print("no route")
        return 1

    if args.as_json:
        print(json.dumps(route, indent=2))
        return 0

    print(args.start.upper())
    for edge in route:
        note = f" [{edge['status']}]"
        if edge.get("fixture"):
            note += f" fixture={edge['fixture']}"
        if edge.get("probe"):
            note += f" probe={edge['probe']}"
        if edge.get("blocked_by"):
            note += f" BLOCKED_BY={edge['blocked_by']}"
        print(f"  -- {edge['trigger']} --> {edge['to']}{note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
