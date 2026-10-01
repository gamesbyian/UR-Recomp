#!/usr/bin/env python3
"""Refine PAL/prototype snes2asm survivors at trusted code/data boundaries."""
from __future__ import annotations
from pathlib import Path
import json
from align_pal_snes2asm_windows import compare_roles, trace

ROOT = Path(__file__).resolve().parents[1]
EUROPE = ROOT / "reference/roms/retail/Unirally_Europe.sfc"
PROTO = ROOT / "reference/roms/prototypes/Unirally_1994-11-29_PAL_prototype.sfc"
OUT_JSON = ROOT / "analysis/generated/pal-snes2asm-subregion-alignment.json"
OUT_MD = ROOT / "analysis/generated/pal-snes2asm-subregion-alignment.md"

SURVIVORS = [
    {"parent":"00:ABA9..00:ADE2","parent_shift":-31,"parent_role_disagreements":91,"segments":[
        {"kind":"data","start_cpu":"00:ABA9","end_cpu":"00:ABB8","basis":"Nitrodon: frontend/text bytes before executable 80:ABB9."},
        {"kind":"code","start_cpu":"00:ABB9","end_cpu":"00:AD0F","basis":"Nitrodon: executable island from JSL 83:9558 through RTS at 80:AD0F."},
        {"kind":"data","start_cpu":"00:AD10","end_cpu":"00:AD33","basis":"Nitrodon: embedded frontend command/text stream consumed via 80:C3AB."},
        {"kind":"code","start_cpu":"00:AD34","end_cpu":"00:ADE2","basis":"Nitrodon: callable routine entry 80:AD34 through bounded survivor end."},
    ]},
    {"parent":"00:C3A9..00:C450","parent_shift":-19,"parent_role_disagreements":5,"segments":[
        {"kind":"data","start_cpu":"00:C3A9","end_cpu":"00:C3AA","basis":"Tail of preceding frontend string; parser entry independently known at 80:C3AB."},
        {"kind":"code","start_cpu":"00:C3AB","end_cpu":"00:C3CA","basis":"Known frontend/text interpreter entry through indirect dispatch setup."},
        {"kind":"data","start_cpu":"00:C3CB","end_cpu":"00:C3EC","basis":"Decoded 17-entry FF..EF handler-word table at 80:C3CB."},
        {"kind":"code","start_cpu":"00:C3ED","end_cpu":"00:C450","basis":"Executable handler region immediately following bounded dispatch table."},
    ]},
    {"parent":"00:8C49..00:8CCA","parent_shift":-9,"parent_role_disagreements":18,"segments":[
        {"kind":"boundary_tail","start_cpu":"00:8C49","end_cpu":"00:8C4D","basis":"Window begins inside final LDA operand of helper 80:8C41; exclude boundary fragment."},
        {"kind":"code","start_cpu":"00:8C4E","end_cpu":"00:8CCA","basis":"Nitrodon: clean PHP function entry at 80:8C4E through RTS at 80:8CCA."},
    ]},
]

def cpu_to_offset(cpu: str) -> int:
    bank_s, addr_s = cpu.split(":")
    bank = int(bank_s, 16)
    addr = int(addr_s, 16)
    if bank != 0 or addr < 0x8000:
        raise ValueError(cpu)
    return addr - 0x8000

def best_shift_near(source: bytes, target: bytes, start: int, end: int, center: int, radius: int = 48):
    src = source[start:end + 1]
    best = (center, -1.0)
    for shift in range(center-radius, center+radius+1):
        a = start + shift
        b = a + len(src)
        if a < 0 or b > len(target):
            continue
        score = sum(x == y for x, y in zip(src, target[a:b])) / len(src)
        if score > best[1]:
            best = (shift, score)
    return best

def build() -> dict:
    retail = EUROPE.read_bytes()
    proto = PROTO.read_bytes()
    rd = trace(retail)
    pd = trace(proto)
    parents = []
    before = 0
    after = 0
    for parent in SURVIVORS:
        before += parent["parent_role_disagreements"]
        row = {
            "parent": parent["parent"],
            "whole_window_shift": parent["parent_shift"],
            "whole_window_role_disagreements": parent["parent_role_disagreements"],
            "segments": [],
        }
        for seg in parent["segments"]:
            out = dict(seg)
            start = cpu_to_offset(seg["start_cpu"])
            end = cpu_to_offset(seg["end_cpu"])
            out["retail_start"] = start
            out["retail_end"] = end
            if seg["kind"] != "code":
                out["action"] = "excluded_from_executable_role_comparison"
                row["segments"].append(out)
                continue
            shift, sim = best_shift_near(retail, proto, start, end, parent["parent_shift"])
            metrics = compare_roles(rd, pd, retail, proto, start, end, shift)
            out.update({
                "prototype_shift": shift,
                "prototype_start": start + shift,
                "prototype_end": end + shift,
                "raw_similarity_after_alignment": round(sim, 6),
                **metrics,
            })
            after += metrics["aligned_role_disagreements"]
            row["segments"].append(out)
        parents.append(row)
    return {
        "schema_version": 1,
        "method": {
            "analyzer": "vendored snes2asm",
            "boundary_sources": [
                "reference/imported/reverse-engineering/nitrodon/bank 80.txt",
                "tools/analyze_frontend_text_dispatch.py",
                "known callable/control-flow entry points",
            ],
            "alignment": "each executable island independently raw-byte aligned around parent shift +/-48 bytes",
            "negative_result_policy": "vanished whole-window disagreements remain evidence of layout/analyzer noise",
        },
        "totals": {
            "survivor_windows": len(parents),
            "whole_window_role_disagreements": before,
            "subregion_aligned_role_disagreements": after,
            "reduction_fraction": 0 if before == 0 else round((before-after)/before, 6),
        },
        "windows": parents,
    }

def render(report: dict) -> str:
    t = report["totals"]
    lines = [
        "# PAL/prototype snes2asm survivor subregion alignment",
        "",
        "Refinement of the three survivors from pal-snes2asm-homolog-alignment; whole-window evidence is preserved.",
        "",
        f"Whole-window survivor role disagreements: **{t['whole_window_role_disagreements']}**.",
        f"After trusted-boundary executable-island alignment: **{t['subregion_aligned_role_disagreements']}**.",
        f"Additional reduction: **{t['reduction_fraction']:.1%}**.",
        "",
    ]
    for parent in report["windows"]:
        lines += [f"## {parent['parent']}", ""]
        for seg in parent["segments"]:
            if seg["kind"] != "code":
                lines.append(f"- {seg['start_cpu']}..{seg['end_cpu']}: excluded ({seg['kind']}); {seg['basis']}")
                continue
            lines.append(
                f"- {seg['start_cpu']}..{seg['end_cpu']}: shift {seg['prototype_shift']:+d}, "
                f"raw similarity {seg['raw_similarity_after_alignment']:.3f}, "
                f"role disagreements {seg['aligned_role_disagreements']}, "
                f"M/X disagreements {seg['aligned_mx_disagreements']}. {seg['basis']}"
            )
            for x in seg["aligned_residuals"]:
                lines.append(
                    f"  - +0x{x['relative_offset']:X}: Europe {x['retail_role']} {x['retail_byte']} "
                    f"vs prototype {x['prototype_role']} {x['prototype_byte']}"
                )
        lines.append("")
    lines += [
        "Removed disagreements are retained as negative evidence: a single shift had crossed independently known code/data or function boundaries.",
        "",
    ]
    return "\n".join(lines)

def main() -> int:
    report = build()
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(render(report), encoding="utf-8")
    print(OUT_MD.read_text(encoding="utf-8"))
    print("SUBREGION_JSON=" + json.dumps(report, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
