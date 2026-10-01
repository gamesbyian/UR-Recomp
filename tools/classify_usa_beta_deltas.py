#!/usr/bin/env python3
"""Classify sparse USA-retail vs legacy-beta ROM deltas with snes2asm reachability.

The byte-level delta set comes from analyze_rom_lineage_deltas.py and excludes the
union of valid RNC payloads. snes2asm is used here as a bounded static witness:
its recursive vector/branch trace marks bytes as opcode starts, instruction
parameters, or not statically reached as code.

This tool does not equate "not reached" with data. It records that weaker fact
explicitly so later da65/Ghidra/runtime evidence can adjudicate high-value sites.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
from types import SimpleNamespace
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
SNES2ASM_ROOT = ROOT / "third_party" / "src" / "snes2asm"
if str(SNES2ASM_ROOT) not in sys.path:
    sys.path.insert(0, str(SNES2ASM_ROOT))

from snes2asm.cartridge import Cartridge
from snes2asm.disassembler import Disassembler

from tools.analyze_rom_lineage_deltas import DEFAULTS, build_report, excluded_mask

OUT_JSON = ROOT / "analysis" / "generated" / "usa-beta-cross-analyzer.json"
OUT_MD = ROOT / "analysis" / "generated" / "usa-beta-cross-analyzer.md"

ROLE = {
    Disassembler.NO_CODE: "unreached",
    Disassembler.OP_CODE: "opcode",
    Disassembler.OP_PARAM: "operand",
}


def trace_code_map(data: bytes) -> tuple[list[int], Disassembler]:
    options = SimpleNamespace(hex=False, nolabel=True)
    cart = Cartridge({"lorom": True, "hirom": False, "fastrom": False, "slowrom": False, "empty_fill": 255})
    cart.set(bytearray(data))
    disasm = Disassembler(cart, options)
    disasm.mark_vectors()
    disasm.find_valid_code_paths()
    return disasm.code_map, disasm


def base_role(mark: int) -> str:
    if mark & Disassembler.OP_CODE:
        return "opcode"
    if mark & Disassembler.OP_PARAM:
        return "operand"
    return "unreached"


def instruction_start(code_map: list[int], offset: int) -> int | None:
    role = base_role(code_map[offset])
    if role == "opcode":
        return offset
    if role != "operand":
        return None
    for start in range(offset - 1, max(-1, offset - 4), -1):
        if start < 0:
            break
        if base_role(code_map[start]) != "opcode":
            continue
        if all(base_role(code_map[i]) == "operand" for i in range(start + 1, offset + 1)):
            return start
    return None


def classify_pair(usa_role: str, beta_role: str, usa_start: int | None, beta_start: int | None) -> str:
    if usa_role == beta_role == "opcode":
        return "opcode-byte-change"
    if usa_role == beta_role == "operand":
        if usa_start == beta_start:
            return "operand-byte-change"
        return "operand-boundary-disagreement"
    if usa_role == beta_role == "unreached":
        return "unreached-by-snes2asm"
    if "unreached" in (usa_role, beta_role):
        return "reachability-disagreement"
    return "instruction-boundary-disagreement"


def build_classification() -> dict:
    paths = DEFAULTS
    lineage = build_report(paths)
    blobs = {name: paths[name].read_bytes() for name in ("usa", "europe", "beta", "prototype")}
    mask = excluded_mask(blobs)
    usa_map, _ = trace_code_map(blobs["usa"])
    beta_map, _ = trace_code_map(blobs["beta"])

    rows = []
    n = min(len(blobs["usa"]), len(blobs["beta"]))
    for off in range(n):
        if mask[off] or blobs["usa"][off] == blobs["beta"][off]:
            continue
        ur = base_role(usa_map[off])
        br = base_role(beta_map[off])
        us = instruction_start(usa_map, off)
        bs = instruction_start(beta_map, off)
        rows.append({
            "offset": off,
            "offset_hex": f"0x{off:06X}",
            "cpu": f"{(off // 0x8000):02X}:{0x8000 + (off % 0x8000):04X}",
            "usa": f"0x{blobs['usa'][off]:02X}",
            "beta": f"0x{blobs['beta'][off]:02X}",
            "europe": f"0x{blobs['europe'][off]:02X}",
            "prototype": f"0x{blobs['prototype'][off]:02X}",
            "usa_role": ur,
            "beta_role": br,
            "usa_instruction_start": None if us is None else f"0x{us:06X}",
            "beta_instruction_start": None if bs is None else f"0x{bs:06X}",
            "usa_opcode": None if us is None else f"0x{blobs['usa'][us]:02X}",
            "beta_opcode": None if bs is None else f"0x{blobs['beta'][bs]:02X}",
            "classification": classify_pair(ur, br, us, bs),
        })

    counts = Counter(row["classification"] for row in rows)
    role_pairs = Counter(f"{row['usa_role']}->{row['beta_role']}" for row in rows)
    code_rows = [r for r in rows if r["classification"] != "unreached-by-snes2asm"]

    return {
        "schema_version": 1,
        "method": {
            "delta_source": "tools/analyze_rom_lineage_deltas.py; USA vs legacy beta; valid RNC union excluded",
            "static_witness": "vendored snes2asm recursive code-path trace from SNES vectors",
            "important": (
                "unreached-by-snes2asm does not mean data; it means this static trace did not "
                "mark the byte as reachable code"
            ),
        },
        "usa_beta_changed_bytes": len(rows),
        "classification_counts": dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))),
        "role_pair_counts": dict(sorted(role_pairs.items(), key=lambda kv: (-kv[1], kv[0]))),
        "statically_code_related_bytes": len(code_rows),
        "rows": rows,
        "known_long_bank_byte_sites": lineage["beta_77_to_70_sites"],
    }


def render_markdown(report: dict) -> str:
    lines = [
        "# USA retail vs legacy beta: snes2asm classification",
        "",
        "Generated by `tools/classify_usa_beta_deltas.py`.",
        "",
        f"Corpus: **{report['usa_beta_changed_bytes']}** non-RNC byte differences.",
        f"snes2asm marks **{report['statically_code_related_bytes']}** changed bytes as code-related or as a code-boundary/reachability disagreement in at least one build.",
        "",
        "Important: `unreached-by-snes2asm` is not equivalent to data. It only means the vector/branch static trace did not reach that byte.",
        "",
        "## Classification counts",
        "",
        "| Classification | Bytes |",
        "|---|---:|",
    ]
    for name, count in report["classification_counts"].items():
        lines.append(f"| {name} | {count} |")

    lines += [
        "",
        "## Code-related changed bytes",
        "",
        "| Offset | CPU | USA→beta | Roles | Instruction starts | Class |",
        "|---|---|---|---|---|---|",
    ]
    for row in report["rows"]:
        if row["classification"] == "unreached-by-snes2asm":
            continue
        starts = f"{row['usa_instruction_start'] or '-'} / {row['beta_instruction_start'] or '-'}"
        lines.append(
            f"| `{row['offset_hex']}` | `{row['cpu']}` | "
            f"`{row['usa']}→{row['beta']}` | {row['usa_role']}→{row['beta_role']} | "
            f"{starts} | {row['classification']} |"
        )

    sites = [s for s in report["known_long_bank_byte_sites"] if s["is_long_address_bank_byte"]]
    lines += [
        "",
        "## Independently recognizable long-address bank-byte changes",
        "",
    ]
    if not sites:
        lines.append("None.")
    else:
        lines += [
            "| Instruction | Opcode | USA target | Beta target |",
            "|---|---|---|---|",
        ]
        for site in sites:
            lines.append(
                f"| `{site['instruction_cpu']}` | {site['opcode_name']} "
                f"(`{site['opcode_hex']}`) | `{site['usa_target']}` | `{site['beta_target']}` |"
            )

    lines += [
        "",
        "## Next discriminator",
        "",
        "Use da65 only for code-related sites whose instruction boundaries and 65816 M/X state can be seeded independently. Use Ghidra/runtime evidence only where snes2asm reports a boundary/reachability disagreement or where an executable change intersects a current semantic question.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-out", type=Path, default=OUT_JSON)
    ap.add_argument("--md-out", type=Path, default=OUT_MD)
    args = ap.parse_args()
    report = build_classification()
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.md_out.write_text(render_markdown(report), encoding="utf-8")
    print(args.json_out)
    print(args.md_out)
    print(json.dumps({
        "usa_beta_changed_bytes": report["usa_beta_changed_bytes"],
        "statically_code_related_bytes": report["statically_code_related_bytes"],
        "classification_counts": report["classification_counts"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
