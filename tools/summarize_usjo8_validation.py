#!/usr/bin/env python3
"""Cross-reference recovered USJO v8 WRAM reads against the canonical symbol map."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "analysis" / "generated" / "usjo8-static-inventory.json"
SYMBOLS = ROOT / "docs" / "SYMBOLS.md"
JSON_OUT = ROOT / "analysis" / "generated" / "usjo8-validation-matrix.json"
MD_OUT = ROOT / "analysis" / "generated" / "usjo8-validation-matrix.md"
BT = chr(96)

ROW_RE = re.compile(
    r"^\\| `(?P<address>7E:[0-9A-F]{4})` \\| `(?P<name>[^`]+)` \\| "
    r"(?P<width>[^|]+?) \\| (?P<confidence>\\d+) \\| (?P<notes>.*?) \\|$"
)


def to_symbol_address(address: str) -> str:
    raw = address.removeprefix("0x")
    return f"{raw[:2]}:{raw[2:]}"


def classify(confidence: int, width: str, notes: str) -> tuple[str, int, str]:
    low = f"{width} {notes}".lower()
    if "width conflict" in low or "verify width" in low:
        return "width-or-units-conflict", 1, "Resolve runtime width/units and byte-vs-word behavior."
    if confidence <= 2:
        return "source-lead", 1, "Reproduce the claimed semantic transition locally before promotion."
    if confidence == 3:
        return "corroborated-unreproduced", 2, "Trigger the claimed state change and verify this field causally."
    if confidence == 4:
        return "strong-partial", 3, "Close any remaining semantic/unit ambiguity when convenient."
    return "runtime-confirmed", 4, "No additional USJO-specific validation required unless new evidence conflicts."


def main() -> None:
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    symbols_text = SYMBOLS.read_text(encoding="utf-8")
    symbols = {}
    for line in symbols_text.splitlines():
        match = ROW_RE.match(line)
        if match:
            symbols[match.group("address")] = {
                "name": match.group("name"),
                "width": match.group("width").strip(),
                "confidence": int(match.group("confidence")),
                "notes": match.group("notes"),
            }

    rows = []
    for address, reads in inventory["memory_reads_by_address"].items():
        symbol_address = to_symbol_address(address)
        symbol = symbols.get(symbol_address)
        if symbol is None:
            status, priority, action = "missing-symbol", 1, "Add a provisional symbol entry, then reproduce locally."
            symbol = {"name": None, "width": None, "confidence": 0, "notes": ""}
        else:
            status, priority, action = classify(symbol["confidence"], symbol["width"], symbol["notes"])
        rows.append({
            "address": symbol_address,
            "usjo_variables": sorted({item["variable"] for item in reads}),
            "usjo_width_bits": sorted({item["width_bits"] for item in reads}),
            "symbol_name": symbol["name"],
            "symbol_width": symbol["width"],
            "confidence": symbol["confidence"],
            "status": status,
            "validation_priority": priority,
            "next_action": action,
            "symbol_notes": symbol["notes"],
        })

    rows.sort(key=lambda row: (row["validation_priority"], row["confidence"], row["address"]))
    payload = {
        "schema_version": 1,
        "source_inventory": str(INVENTORY.relative_to(ROOT)),
        "source_symbols": str(SYMBOLS.relative_to(ROOT)),
        "entries": rows,
        "summary": {status: sum(row["status"] == status for row in rows) for status in sorted({row["status"] for row in rows})},
    }
    JSON_OUT.write_text(json.dumps(payload, indent=2) + "\\n", encoding="utf-8")

    lines = [
        "# USJO v8 validation matrix",
        "",
        "Generated from the recovered-source inventory and the canonical symbol map.",
        "Priority 1 means unresolved semantic conflict/source-only evidence; priority 4 means",
        "the USJO-specific claim is already causally confirmed in the current runtime evidence.",
        "",
        "| Priority | Address | USJO variable | Canonical symbol | Confidence | Status | Next action |",
        "|---:|---|---|---|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['validation_priority']} | {BT}{row['address']}{BT} | "
            f"{BT}{', '.join(row['usjo_variables'])}{BT} | "
            f"{BT}{row['symbol_name'] or '—'}{BT} | {row['confidence']} | "
            f"{row['status']} | {row['next_action']} |"
        )
    lines += [
        "",
        "## Immediate queue",
        "",
        "The narrowest unresolved targets are the boost-meter width/units question at " + BT + "7E:11CD" + BT,
        "and the source-only Z-rotation working fields " + BT + "7E:0DFD" + BT + " / " + BT + "7E:0F57" + BT + ".",
        "The five stunt counters are independently corroborated but still need causal transition fixtures.",
        "X speed, Y speed and air state are already runtime-confirmed and should not consume more",
        "USJO-validation effort unless conflicting evidence appears.",
        "",
    ]
    MD_OUT.write_text("\\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
