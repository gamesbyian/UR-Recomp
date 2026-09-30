#!/usr/bin/env python3
"""Build a compact machine-readable inventory of decompilation/semantic gaps.

This intentionally separates:
- SNESRecomp execution-analysis coverage;
- named/understood functions in docs/SYMBOLS.md;
- explicit semantic placeholders;
- bounded analyzer-proof gaps and unresolved dispatch sites.

It does not pretend that AOT coverage is semantic decompilation coverage.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

FUNC_ROW = re.compile(
    r"^\|\s*(?P<address>[^|]+?)\s*\|\s*`(?P<name>[^`]+)`\s*\|\s*(?P<confidence>\d+)\s*\|\s*(?P<notes>.*?)\s*\|$"
)
LLE_ROW = re.compile(r"^\d+\.\s+`(?P<pc>[0-9A-F]{2}:[0-9A-F]{4})\s+M(?P<m>[01])X(?P<x>[01])`\s+—\s+(?P<count>\d+)")
INDIRECT_ROW = re.compile(
    r"^-\s+`(?P<pc>[0-9A-F]{2}:[0-9A-F]{4})`\s+—\s+(?P<variants>[^,]+),\s+`(?P<opcode>JMP)`\s+indirect through operand\s+`(?P<operand>\$[0-9A-F]{4})`"
)


def parse_functions(text: str) -> tuple[list[dict], list[dict]]:
    in_functions = False
    understood: list[dict] = []
    placeholders: list[dict] = []
    for raw in text.splitlines():
        line = raw.strip()
        if line == "## Functions":
            in_functions = True
            continue
        if in_functions and line.startswith("## ") and line != "## Functions":
            break
        if not in_functions:
            continue
        m = FUNC_ROW.match(line)
        if not m:
            continue
        row = {
            "address": m.group("address").strip(),
            "name": m.group("name"),
            "confidence": int(m.group("confidence")),
            "notes": m.group("notes").strip(),
        }
        if row["address"] == "TBD" or row["name"].startswith("TBD_"):
            placeholders.append(row)
        else:
            understood.append(row)
    return understood, placeholders


def parse_recon(text: str) -> dict:
    lle = []
    indirect = []
    in_lle = False
    for raw in text.splitlines():
        line = raw.strip()
        if line == "## LLE-only variants":
            in_lle = True
            continue
        if in_lle and line.startswith("## "):
            in_lle = False
        if in_lle:
            m = LLE_ROW.match(line)
            if m:
                lle.append({
                    "pc": m.group("pc"),
                    "m": int(m.group("m")),
                    "x": int(m.group("x")),
                    "instruction_count": int(m.group("count")),
                })
        m = INDIRECT_ROW.match(line)
        if m:
            indirect.append({
                "pc": m.group("pc"),
                "opcode": m.group("opcode"),
                "operand": m.group("operand"),
                "variant_description": m.group("variants"),
            })

    def metric(pattern: str):
        m = re.search(pattern, text)
        return int(m.group(1)) if m else None

    return {
        "analysis_roots": metric(r"analysis roots:\s+\*\*(\d+)\*\*"),
        "exact_variants": metric(r"exact variants:\s+\*\*(\d+)\*\*"),
        "aot_eligible_variants": metric(r"AOT-eligible variants:\s+\*\*(\d+)\*\*"),
        "lle_only_variants": metric(r"LLE-only variants:\s+\*\*(\d+)\*\*"),
        "decoded_instruction_instances": metric(r"decoded instruction instances across manifest nodes:\s+\*\*(\d+)\*\*"),
        "lle_examples": lle,
        "unresolved_indirect_guest_sites": indirect,
    }


def build(symbols: str, recon: str) -> dict:
    understood, placeholders = parse_functions(symbols)
    analyzer = parse_recon(recon)
    queue = []
    for row in placeholders:
        queue.append({
            "kind": "semantic_placeholder",
            "name": row["name"],
            "address": row["address"],
            "priority": "high",
            "reason": "explicit core-subsystem placeholder in SYMBOLS.md",
        })
    for row in analyzer["unresolved_indirect_guest_sites"]:
        queue.append({
            "kind": "unresolved_indirect_dispatch",
            "name": None,
            "address": row["pc"],
            "priority": "high",
            "reason": f"{row['opcode']} indirect via {row['operand']}; static targets unresolved",
        })
    for row in analyzer["lle_examples"]:
        queue.append({
            "kind": "lle_only_variant",
            "name": None,
            "address": row["pc"],
            "priority": "medium",
            "reason": f"SNESRecomp proof gap for M{row['m']}X{row['x']} ({row['instruction_count']} decoded instructions)",
        })
    return {
        "schema_version": 1,
        "coverage_dimensions": {
            "execution_analysis": analyzer,
            "semantic_functions_named": len(understood),
            "semantic_placeholders": len(placeholders),
        },
        "understood_functions": understood,
        "semantic_placeholders": placeholders,
        "gap_queue": queue,
        "warning": "AOT/execution-analysis coverage is not semantic decompilation coverage.",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", type=Path, default=Path("docs/SYMBOLS.md"))
    ap.add_argument("--recon", type=Path, default=Path("analysis/generated/analyzer-reconnaissance.md"))
    ap.add_argument("--json-out", type=Path, default=Path("analysis/generated/decomp-gap-inventory.json"))
    args = ap.parse_args()
    report = build(args.symbols.read_text(encoding="utf-8"), args.recon.read_text(encoding="utf-8"))
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
