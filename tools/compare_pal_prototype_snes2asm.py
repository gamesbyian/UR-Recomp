#!/usr/bin/env python3
"""Normalize PAL retail vs 1994-11-29 PAL prototype deltas through snes2asm.

Produces a bounded machine-readable corpus for later da65/Ghidra adjudication.
Valid RNC payload bytes are excluded because course assets have their own lane.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
from types import SimpleNamespace
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
SNES2ASM_ROOT = ROOT / "third_party" / "src" / "snes2asm"
if str(SNES2ASM_ROOT) not in sys.path:
    sys.path.insert(0, str(SNES2ASM_ROOT))

from snes2asm.cartridge import Cartridge
from snes2asm.disassembler import Disassembler

try:
    from tools.analyze_rom_lineage_deltas import DEFAULTS, excluded_mask, file_to_cpu
except ModuleNotFoundError:
    from analyze_rom_lineage_deltas import DEFAULTS, excluded_mask, file_to_cpu

OUT_JSON = ROOT / "analysis" / "generated" / "pal-retail-vs-prototype-snes2asm.json"
OUT_MD = ROOT / "analysis" / "generated" / "pal-retail-vs-prototype-snes2asm.md"


def trace(data: bytes) -> Disassembler:
    options = SimpleNamespace(hex=False, nolabel=True)
    cart = Cartridge({"lorom": True, "hirom": False, "fastrom": False, "slowrom": False, "empty_fill": 255})
    cart.set(bytearray(data))
    d = Disassembler(cart, options)
    d.mark_vectors()
    d.find_valid_code_paths()
    return d


def role(d: Disassembler, off: int) -> str:
    mark = d.code_map[off]
    if mark & d.OP_CODE:
        return "opcode"
    if mark & d.OP_PARAM:
        return "operand"
    return "unreached"


def instruction_start(d: Disassembler, off: int) -> int | None:
    r = role(d, off)
    if r == "opcode":
        return off
    if r != "operand":
        return None
    for start in range(off - 1, max(-1, off - 4), -1):
        if start < 0:
            break
        if role(d, start) != "opcode":
            continue
        size = d.opSize(d.cart[start])
        if start <= off < start + size:
            return start
    return None


def cpu(off: int) -> str:
    value = file_to_cpu(off)
    return f"{(value >> 16) & 0xFF:02X}:{value & 0xFFFF:04X}"


def normalized_instruction(d: Disassembler, data: bytes, start: int | None) -> dict | None:
    if start is None:
        return None
    mark = d.code_map[start]
    size = d.opSize(data[start])
    return {
        "start": start,
        "cpu": cpu(start),
        "opcode": f"0x{data[start]:02X}",
        "size": size,
        "bytes": data[start:start + size].hex(" "),
        "m16": not bool(mark & 0x20),
        "x16": not bool(mark & 0x10),
    }


def classify(pr: str, rr: str, ps: int | None, rs: int | None, pi: dict | None, ri: dict | None) -> str:
    if pr == rr == "unreached":
        return "unreached-both"
    if "unreached" in (pr, rr):
        return "reachability-disagreement"
    if ps != rs:
        return "instruction-boundary-disagreement"
    if pi and ri and pi['opcode'] != ri['opcode']:
        return "opcode-change"
    if pi and ri and (pi['m16'], pi['x16']) != (ri['m16'], ri['x16']):
        return "mx-state-disagreement"
    return "operand-or-literal-change"


def build_report() -> dict:
    paths = {"europe": DEFAULTS["europe"], "prototype": DEFAULTS["prototype"]}
    all_blobs = {name: path.read_bytes() for name, path in DEFAULTS.items()}
    mask = excluded_mask(all_blobs)
    retail = paths["europe"].read_bytes()
    proto = paths["prototype"].read_bytes()
    rd = trace(retail)
    pd = trace(proto)
    rows=[]
    n=min(len(retail),len(proto))
    for off in range(n):
        if mask[off] or retail[off] == proto[off]:
            continue
        rr, pr = role(rd,off), role(pd,off)
        rs, ps = instruction_start(rd,off), instruction_start(pd,off)
        ri, pi = normalized_instruction(rd,retail,rs), normalized_instruction(pd,proto,ps)
        rows.append({
            "offset": off, "offset_hex": f"0x{off:06X}", "cpu": cpu(off),
            "retail_byte": f"0x{retail[off]:02X}", "prototype_byte": f"0x{proto[off]:02X}",
            "retail_role": rr, "prototype_role": pr,
            "retail_instruction": ri, "prototype_instruction": pi,
            "classification": classify(pr,rr,ps,rs,pi,ri),
        })
    counts=Counter(x['classification'] for x in rows)
    code_rows=[x for x in rows if x['classification'] != 'unreached-both']
    # Coalesce nearby code-related delta offsets into bounded analyzer windows.
    offsets=sorted(x['offset'] for x in code_rows)
    windows=[]
    if offsets:
        start=prev=offsets[0]
        for off in offsets[1:]:
            if off-prev <= 32:
                prev=off; continue
            windows.append((start,prev)); start=prev=off
        windows.append((start,prev))
    window_rows=[]
    for a,b in windows:
        members=[x for x in code_rows if a <= x['offset'] <= b]
        kinds=Counter(x['classification'] for x in members)
        window_rows.append({
            "start": a, "end": b, "start_cpu": cpu(a), "end_cpu": cpu(b),
            "changed_bytes": len(members), "span": b-a+1, "classifications": dict(kinds),
            "da65_candidate": any(k in kinds for k in ("opcode-change","instruction-boundary-disagreement","mx-state-disagreement")),
        })
    window_rows.sort(key=lambda x:(not x['da65_candidate'],-x['changed_bytes'],x['start']))
    return {
        "schema_version": 1,
        "pair": "europe-retail_vs_pal-prototype-1994-11-29",
        "method": {
            "analyzer": "vendored snes2asm recursive trace",
            "normalization": "file/SNES address + role + opcode/size + bytes + inferred M/X width state",
            "warning": "unreached means not reached by this static trace, not proven data",
        },
        "changed_non_rnc_bytes": len(rows),
        "code_related_changed_bytes": len(code_rows),
        "classification_counts": dict(sorted(counts.items(), key=lambda kv:(-kv[1],kv[0]))),
        "windows": window_rows,
        "rows": rows,
    }


def render_md(r: dict) -> str:
    lines=[
        "# PAL retail vs 1994-11-29 prototype: normalized snes2asm delta pass",
        "",
        f"Non-RNC differing bytes: **{r['changed_non_rnc_bytes']}**.",
        f"Changed bytes code-related in at least one snes2asm trace: **{r['code_related_changed_bytes']}**.",
        "",
        "## Classification",
        "",
        "| Class | Bytes |", "|---|---:|",
    ]
    for k,v in r["classification_counts"].items(): lines.append(f"| {k} | {v} |")
    lines += ['', '## Highest-value bounded windows', '', '| Range | Changed bytes | Span | Classes | da65? |', '|---|---:|---:|---|---|']
    for w in r["windows"][:80]:
        classes=", ".join(f"{k}:{v}" for k,v in w["classifications"].items())
        lines.append(f"| `{w['start_cpu']}..{w['end_cpu']}` | {w['changed_bytes']} | {w['span']} | {classes} | {'yes' if w['da65_candidate'] else 'no'} |")
    lines += ['', '## Next analyzer step', '', 'Run bounded da65 only on windows marked `da65=yes`, supplying CODE range and independently supported M/X state. Use Ghidra only where that bounded second witness disagrees with snes2asm or where xrefs/function boundaries are needed.', '']
    return "\n".join(lines)


def main() -> int:
    r=build_report()
    OUT_JSON.parent.mkdir(parents=True,exist_ok=True)
    OUT_JSON.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    OUT_MD.write_text(render_md(r),encoding="utf-8")
    print(OUT_MD.read_text())
    return 0


if __name__ == "__main__": raise SystemExit(main())
