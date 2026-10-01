#!/usr/bin/env python3
"""Inventory recovered USJO v8 semantics without promoting them as game truth.

This is intentionally a static source inventory. It turns the recovered Lua bot into
machine-queryable evidence while preserving the distinction between "the bot reads
this address / uses this rule" and "the game semantics have been reproduced locally".
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

MEM_RE = re.compile(
    r"(?P<lhs>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*memory\.(?P<kind>readbyte|readword)\((?P<addr>0x[0-9A-Fa-f]+)\)"
)
LOCAL_RE = re.compile(
    r"^local\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<value>-?\d+(?:\.\d+)?|true|false|\"[^\"]*\"|'[^']*')\s*(?:--\s*(?P<comment>.*))?$"
)
ENUM_PAIR_RE = re.compile(r"(?P<value>\d+)\s*=\s*(?P<label>[^,]+)")
ASSIGN_RE = re.compile(r"^(?P<indent>\s*)(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<value>[^-].*?)\s*(?:--.*)?$")

STATE_NAMES = {
    "mode",
    "jumpstatus",
    "twiststatus",
    "tabletopstatus",
    "zflipstatus",
    "rollstatus",
    "flipstatus",
    "strategy",
}
CONTROL_NAMES = {"jumping", "reverse", "rolling", "flipping", "xing"}


def find_block(lines: list[str], start_pat: str, end_pat: str) -> dict:
    start = next(i for i, line in enumerate(lines) if start_pat in line)
    end = next(i for i in range(start, len(lines)) if end_pat in lines[i])
    return {
        "start_line": start + 1,
        "end_line": end + 1,
        "lines": [{"line": i + 1, "text": lines[i].rstrip()} for i in range(start, end + 1)],
    }


def build_inventory(source: Path) -> dict:
    raw = source.read_bytes()
    text = raw.decode("utf-8")
    lines = text.splitlines()

    memory_reads = []
    for lineno, line in enumerate(lines, 1):
        match = MEM_RE.search(line)
        if not match:
            continue
        memory_reads.append(
            {
                "line": lineno,
                "variable": match.group("lhs"),
                "read": match.group("kind"),
                "width_bits": 8 if match.group("kind") == "readbyte" else 16,
                "address": match.group("addr").upper().replace("0X", "0x"),
                "source": line.strip(),
            }
        )

    setup_marker = next(i for i, line in enumerate(lines) if "Setup our task" in line)
    constants = []
    enums = {}
    for lineno, line in enumerate(lines[:setup_marker], 1):
        match = LOCAL_RE.match(line.strip())
        if not match:
            continue
        entry = {
            "line": lineno,
            "name": match.group("name"),
            "value": match.group("value"),
        }
        comment = match.group("comment")
        if comment:
            entry["comment"] = comment.strip()
            pairs = {}
            for pair in ENUM_PAIR_RE.finditer(comment):
                pairs[pair.group("value")] = pair.group("label").strip()
            if len(pairs) >= 2:
                enums[match.group("name")] = pairs
        constants.append(entry)

    transitions = []
    controls = []
    for lineno, line in enumerate(lines, 1):
        match = ASSIGN_RE.match(line)
        if not match:
            continue
        name = match.group("name")
        record = {"line": lineno, "name": name, "value": match.group("value").strip()}
        if name in STATE_NAMES:
            transitions.append(record)
        if name in CONTROL_NAMES:
            controls.append(record)

    unique_reads = {}
    for item in memory_reads:
        unique_reads.setdefault(item["address"], []).append(item)

    return {
        "schema_version": 1,
        "source": str(source).replace("\\", "/"),
        "source_line_count": len(lines),
        "memory_reads": memory_reads,
        "memory_reads_by_address": unique_reads,
        "preloop_local_constants": constants,
        "comment_enums": enums,
        "state_assignments": transitions,
        "control_signal_assignments": controls,
        "boost_scoring_block": find_block(lines, "thisboostmeter = 0", "finalscore = thisboostmeter + lastspeed"),
        "controller_output_block": find_block(lines, "buttontable = {", "joypad.set(1, buttontable)"),
        "interpretation": {
            "status": "recovered-source evidence only",
            "warning": (
                "Names and rules in this inventory describe what USJO v8 assumes or observes. "
                "They are not promoted game semantics until reproduced against the canonical ROM/runtime."
            ),
        },
    }


def render_markdown(data: dict) -> str:
    rows = []
    seen = set()
    for read in data["memory_reads"]:
        key = (read["address"], read["variable"], read["width_bits"])
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            f"| \`{read['address']}\` | {read['width_bits']} | \`{read['variable']}\` | {read['line']} |"
        )

    enum_lines = []
    for name, values in data["comment_enums"].items():
        rendered = "; ".join(f"\`{value}\` = {label}" for value, label in values.items())
        enum_lines.append(f"- \`{name}\`: {rendered}")

    score = data["boost_scoring_block"]
    controller = data["controller_output_block"]
    return f"""# USJO v8 static inventory

Generated from \`{data['source']}\` by \`tools/inventory_usjo8.py\`.

This is **recovered-source evidence**, not promoted game truth. The variable names,
addresses, timing assumptions and scoring rules below describe what the 2008 bot
reads or assumes. Each item still needs canonical-ROM/runtime reproduction before it
can become an authoritative symbol or gameplay rule.

Source lines: {data['source_line_count']}

## RAM reads

| Address | Width | USJO v8 variable | First/only source line |
|---|---:|---|---:|
{chr(10).join(rows)}

The alternative X-speed address mentioned only in a source comment is deliberately
not classified as a read. Static comments remain leads until tested.

## Comment-encoded state enums

{chr(10).join(enum_lines) if enum_lines else "_No multi-value enums found._"}

## Search/timing constants

The JSON artifact records every literal top-level local initialized before the bot's
savestate/setup section, including search-window, jump, tabletop, twist, rut and
loop-detection parameters. They are source constants, not yet game constants.

## Boost/scoring rule source block

The recovered bot's hand-authored boost estimate and final score calculation occupy
lines {score['start_line']}-{score['end_line']}. The machine-readable artifact preserves
that complete source block. It combines stunt-count thresholds into
\`thisboostmeter\`, zeros that estimate when direction/speed is wrong or
\`realboostmeter == 0\`, then sets \`finalscore = thisboostmeter + lastspeed\`.

A useful source-level distinction: v8 reads \`7E:11CD\` with \`memory.readbyte()\` even though the retained TAS watch list records a 2-byte unsigned Booster Meter at that address. The bot does not use that byte as the score magnitude; it only tests \`realboostmeter == 0\` as a gate, while its own \`thisboostmeter\` value is reconstructed from stunt counts. The full 16-bit runtime meaning still needs local validation.


## Controller policy source block

The final controller-output policy occupies lines {controller['start_line']}-{controller['end_line']}.
The JSON preserves the whole block plus every assignment to the intermediate control
signals \`jumping\`, \`reverse\`, \`rolling\`, \`flipping\`, and \`xing\`.

## How to use this

1. Pick one RAM field or source rule from the JSON inventory.
2. Reproduce it against the canonical ROM/runtime with the smallest deterministic fixture.
3. Promote only the reproduced semantics into \`docs/SYMBOLS.md\`,
   \`docs/RESEARCH-LEDGER.md\`, and regression fixtures.
4. Keep unsupported USJO names as historical aliases/leads rather than silently treating
   the 2008 script as specification.
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("reference/imported/tas-bots/usjo8.lua"),
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=Path("analysis/generated/usjo8-static-inventory.json"),
    )
    parser.add_argument(
        "--md-out",
        type=Path,
        default=Path("analysis/generated/usjo8-static-inventory.md"),
    )
    args = parser.parse_args()

    data = build_inventory(args.source)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    args.md_out.write_text(render_markdown(data), encoding="utf-8")


if __name__ == "__main__":
    main()
