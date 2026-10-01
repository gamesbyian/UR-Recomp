#!/usr/bin/env python3
"""Compare the trusted USA semantic corpus against the 1994-11-29 PAL prototype."""
from __future__ import annotations

from pathlib import Path
import json

from compare_europe_usa_snes2asm_homologs import (
    ROOT,
    cpu_to_offset,
    offset_to_cpu,
    trace,
    seed_entries,
    compare_aligned_bytes,
)
from align_pal_snes2asm_windows import compare_roles

USA = ROOT / "reference/roms/retail/Uniracers_USA.sfc"
PROTO = ROOT / "reference/roms/prototypes/Unirally_1994-11-29_PAL_prototype.sfc"
OUT_JSON = ROOT / "analysis/generated/usa-pal-prototype-snes2asm-homologs.json"
OUT_MD = ROOT / "analysis/generated/usa-pal-prototype-snes2asm-homologs.md"

REGIONS = [
    ("Text_TestCharacterMetadataBit7", "80:8C41", "80:8C4D", -5),
    ("Player_ApplyVerticalAcceleration", "82:A968", "82:A9AB", -15),
    ("Input_DecodePlayer1Buttons:p1_decode", "82:AA6E", "82:AB54", -15),
    ("Input_DecodePlayer1Buttons:p2_decode", "82:AB55", "82:AC52", -15),
    ("Input_DecodePlayer1Buttons:postprocess", "82:AC53", "82:ACA0", -15),
    ("Collision_TransformVelocity:matrix_apply", "81:9546", "81:9624", -32),
    ("Collision_BuildContactShape", "81:9E2A", "81:9FBE", -32),
    ("HUD_QueueMessage", "81:C5B3", "81:C604", -35),
    ("Race_UpdateRacersFrame:state_marshal_prefix", "82:89B9", "82:8C26", -3),
    ("Stunt_FinalizeAndScoreAirTricks:air_entry", "82:9A42", "82:9AA8", -5),
    ("Stunt_FinalizeAndScoreAirTricks:rotation_progress", "82:9AAC", "82:9B54", -5),
    ("Course_LoadAndMaterialize:setup", "82:E165", "82:E1CF", -100),
    ("Course_LoadAndMaterialize:record_header", "82:E1D1", "82:E213", -100),
    ("Course_LoadAndMaterialize:dma_row_loop", "82:E216", "82:E2FF", -100),
    ("Race_HandleCheckpointFinish:entry_and_time", "81:8050", "81:8122", 0),
    ("Race_HandleCheckpointFinish:player_records", "81:8123", "81:8194", 0),
    ("Race_HandleCheckpointFinish:lap_hud", "81:8195", "81:81D3", 0),
    ("Race_BuildRacerOAMState:p1_projection", "82:ACF3", "82:ADA7", -15),
    ("Race_BuildRacerOAMState:p2_projection", "82:ADC1", "82:AE57", -15),
]


def align_near(source: bytes, target: bytes, start: int, end: int, center: int) -> tuple[int, float]:
    src = source[start:end + 1]
    best = (center, -1.0)
    for shift in range(center - 32, center + 33):
        a = start + shift
        b = a + len(src)
        if a < 0 or b > len(target):
            continue
        score = sum(x == y for x, y in zip(src, target[a:b])) / len(src)
        if score > best[1]:
            best = (shift, score)
    return best


def build() -> dict:
    usa = USA.read_bytes()
    proto = PROTO.read_bytes()
    ud = trace(usa)
    pd = trace(proto)

    usa_seeds = [
        cpu_to_offset("80:8C41"),
        cpu_to_offset("82:A968"),
        cpu_to_offset("82:AA6E"),
        cpu_to_offset("81:953D"),
        cpu_to_offset("81:9E2A"),
        cpu_to_offset("81:C5B3"),
        cpu_to_offset("82:89B9"),
        cpu_to_offset("82:9A42"),
        cpu_to_offset("82:E165"),
        cpu_to_offset("81:8050"),
        cpu_to_offset("82:ACA5"),
    ]
    proto_seeds = [
        cpu_to_offset("80:8C3C"),
        cpu_to_offset("82:A959"),
        cpu_to_offset("82:AA5F"),
        cpu_to_offset("81:951D"),
        cpu_to_offset("81:9E0A"),
        cpu_to_offset("81:C590"),
        cpu_to_offset("82:89B6"),
        cpu_to_offset("82:9A3D"),
        cpu_to_offset("82:E101"),
        cpu_to_offset("81:8050"),
        cpu_to_offset("82:AC96"),
    ]
    seed_entries(ud, usa_seeds)
    seed_entries(pd, proto_seeds)

    rows = []
    for name, start_cpu, end_cpu, expected_shift in REGIONS:
        start = cpu_to_offset(start_cpu)
        end = cpu_to_offset(end_cpu)
        shift, sim = align_near(usa, proto, start, end, expected_shift)
        metrics = compare_roles(ud, pd, usa, proto, start, end, shift)
        bytes_ = compare_aligned_bytes(ud, pd, usa, proto, start, end, shift)
        if metrics["aligned_opcode_pairs"] == 0:
            raise RuntimeError(f"{name}: zero aligned opcode pairs after trusted seeding")
        rows.append({
            "name": name,
            "usa_start": start_cpu,
            "usa_end": end_cpu,
            "prototype_start": offset_to_cpu(start + shift),
            "prototype_end": offset_to_cpu(end + shift),
            "expected_shift": expected_shift,
            "prototype_shift": shift,
            "raw_similarity_after_alignment": round(sim, 6),
            **metrics,
            **bytes_,
        })

    return {
        "schema_version": 1,
        "method": {
            "source": "USA retail",
            "target": "PAL prototype 1994-11-29",
            "analyzer": "vendored snes2asm",
            "reachability": "default vector walk plus independently trusted function-entry seeds",
            "alignment": "per bounded semantic/control-flow subregion near established structural correspondence",
        },
        "totals": {
            "regions": len(rows),
            "aligned_opcode_pairs": sum(r["aligned_opcode_pairs"] for r in rows),
            "aligned_opcode_byte_disagreements": sum(r["aligned_opcode_byte_disagreements"] for r in rows),
            "aligned_operand_byte_changes": sum(r["aligned_operand_byte_changes"] for r in rows),
            "aligned_role_disagreements": sum(r["aligned_role_disagreements"] for r in rows),
            "aligned_mx_disagreements": sum(r["aligned_mx_disagreements"] for r in rows),
            "zero_role_disagreement_regions": sum(r["aligned_role_disagreements"] == 0 for r in rows),
        },
        "regions": rows,
    }


def render(report: dict) -> str:
    t = report["totals"]
    lines = [
        "# USA / 1994-11-29 PAL prototype snes2asm homolog comparison",
        "",
        f"Regions compared: **{t['regions']}**.",
        f"Aligned opcode pairs: **{t['aligned_opcode_pairs']}**.",
        f"Opcode substitutions: **{t['aligned_opcode_byte_disagreements']}**.",
        f"Operand-byte changes: **{t['aligned_operand_byte_changes']}**.",
        f"Role disagreements: **{t['aligned_role_disagreements']}**.",
        f"M/X disagreements: **{t['aligned_mx_disagreements']}**.",
        "",
        "| Region | USA | Prototype | Shift | Raw sim | Opcode Δ | Operand Δ | Role Δ | M/X Δ |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in report["regions"]:
        lines.append(
            f"| {r['name']} | `{r['usa_start']}..{r['usa_end']}` | "
            f"`{r['prototype_start']}..{r['prototype_end']}` | {r['prototype_shift']:+d} | "
            f"{r['raw_similarity_after_alignment']:.3f} | {r['aligned_opcode_byte_disagreements']} | "
            f"{r['aligned_operand_byte_changes']} | {r['aligned_role_disagreements']} | "
            f"{r['aligned_mx_disagreements']} |"
        )
    survivors = [
        r for r in report["regions"]
        if r["aligned_opcode_byte_disagreements"] or r["aligned_role_disagreements"] or r["aligned_mx_disagreements"]
    ]
    lines += ["", "## Surviving disagreements", ""]
    if not survivors:
        lines.append("None.")
    for r in survivors:
        lines.append(f"### {r['name']}")
        for x in r["aligned_opcode_changes"]:
            lines.append(
                f"- opcode +0x{x['relative_offset']:X}: USA {x['usa_opcode']} vs prototype {x['europe_opcode']}"
            )
        for x in r["aligned_residuals"]:
            lines.append(
                f"- role +0x{x['relative_offset']:X}: USA {x['retail_role']} {x['retail_byte']} "
                f"vs prototype {x['prototype_role']} {x['prototype_byte']}"
            )
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    report = build()
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(render(report), encoding="utf-8")
    print(OUT_MD.read_text(encoding="utf-8"))
    print("USA_PROTO_JSON=" + json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
