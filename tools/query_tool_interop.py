#!/usr/bin/env python3
"""Compact queries over tools/tool_interop.json for humans and agents."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

CATALOG = Path(__file__).with_name("tool_interop.json")


def load() -> dict:
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--component")
    group.add_argument("--format")
    group.add_argument("--chain")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    data = load()

    if args.component:
        item = next((x for x in data["components"] if x["id"] == args.component), None)
        if item is None:
            raise SystemExit(f"unknown component: {args.component}")
        result = {
            "component": item,
            "outgoing": [x for x in data["handoffs"] if x["from"] == args.component],
            "incoming": [x for x in data["handoffs"] if x["to"] == args.component],
            "chains": [x for x in data["chains"] if args.component in x["steps"]],
        }
    elif args.format:
        if args.format not in {x["id"] for x in data["formats"]}:
            raise SystemExit(f"unknown format: {args.format}")
        result = {
            "format": next(x for x in data["formats"] if x["id"] == args.format),
            "producers": [x["id"] for x in data["components"] if args.format in x.get("produces", [])],
            "consumers": [x["id"] for x in data["components"] if args.format in x.get("consumes", [])],
            "handoffs": [x for x in data["handoffs"] if x["format"] == args.format],
        }
    else:
        item = next((x for x in data["chains"] if x["id"] == args.chain), None)
        if item is None:
            raise SystemExit(f"unknown chain: {args.chain}")
        result = item

    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    if args.component:
        print(f"{args.component}: consumes={item.get('consumes', [])} produces={item.get('produces', [])}")
        for h in result["outgoing"]:
            print(f"  -> {h['to']} via {h['format']} [{h['status']}]")
        for h in result["incoming"]:
            print(f"  <- {h['from']} via {h['format']} [{h['status']}]")
        for chain in result["chains"]:
            print(f"  chain {chain['id']} [{chain['status']}]: " + " -> ".join(chain["steps"]))
    elif args.format:
        print(f"{args.format}: {result['format']['description']}")
        print("  producers: " + ", ".join(result["producers"]))
        print("  consumers: " + ", ".join(result["consumers"]))
        for h in result["handoffs"]:
            print(f"  {h['from']} -> {h['to']} [{h['status']}]")
    else:
        print(f"{item['id']} [{item['status']}]: " + " -> ".join(item["steps"]))
        print("  " + item["purpose"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
