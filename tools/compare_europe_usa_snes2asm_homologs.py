#!/usr/bin/env python3
"""Compare selected USA/Europe executable homologs with vendored snes2asm.

The regions are chosen from trusted semantic correspondences and subdivided only
at independently recovered Nitrodon/control-flow boundaries. Raw-byte alignment
is performed per executable subregion before comparing snes2asm code roles and
M/X state.
"""
from __future__ import annotations

from pathlib import Path
import json

from align_pal_snes2asm_windows import best_shift, compare_roles, trace

ROOT = Path(__file__).resolve().parents[1]
USA = ROOT / "reference/roms/retail/Uniracers_USA.sfc"
EUROPE = ROOT / "reference/roms/retail/Unirally_Europe.sfc"
OUT_JSON = ROOT / "analysis/generated/europe-usa-snes2asm-homologs.json"
OUT_MD = ROOT / "analysis/generated/europe-usa-snes2asm-homologs.md"

REGIONS = [
    {
        "name": "Text_TestCharacterMetadataBit7",
        "usa_start": "80:8C41",
        "usa_end": "80:8C4D",
        "expected_europe_shift": 0,
        "basis": "Nitrodon helper entry/body; structural matcher places Europe homolog at the same CPU address.",
    },
    {
        "name": "Player_ApplyVerticalAcceleration",
        "usa_start": "82:A968",
        "usa_end": "82:A9AB",
        "expected_europe_shift": 7,
        "basis": "Nitrodon function entry through RTS; structural matcher places Europe homolog at 82:A96F.",
    },
    {
        "name": "Input_DecodePlayer1Buttons:p1_decode",
        "usa_start": "82:AA6E",
        "usa_end": "82:AB54",
        "expected_europe_shift": 7,
        "basis": "Nitrodon input function entry through byte immediately before the independently visible AB55 second-controller/shared phase.",
    },
    {
        "name": "Input_DecodePlayer1Buttons:p2_decode",
        "usa_start": "82:AB55",
        "usa_end": "82:AC52",
        "expected_europe_shift": 7,
        "basis": "Nitrodon AB55 second-controller/shared phase through byte before AC53 post-processing.",
    },
    {
        "name": "Input_DecodePlayer1Buttons:postprocess",
        "usa_start": "82:AC53",
        "usa_end": "82:ACA0",
        "expected_europe_shift": 7,
        "basis": "Nitrodon AC53 post-processing block through RTS at ACA0.",
    },
    {
        "name": "Collision_TransformVelocity:matrix_apply",
        "usa_start": "81:9546",
        "usa_end": "81:9624",
        "expected_europe_shift": -26,
        "basis": "Nitrodon matrix/velocity transform body through working-field clears; bounded before the JMP at 81:9627. M/X state is seeded from the independently visible REP/SEP setup at 81:953D.",
    },
    {
        "name": "Collision_BuildContactShape",
        "usa_start": "81:9E2A",
        "usa_end": "81:9FBE",
        "expected_europe_shift": -15,
        "basis": "Nitrodon function entry establishes M/X with REP #$30 and runs through RTS at 81:9FBE.",
    },
    {
        "name": "HUD_QueueMessage",
        "usa_start": "81:C5B3",
        "usa_end": "81:C604",
        "expected_europe_shift": -23,
        "basis": "Nitrodon message-queue function entry establishes accumulator/index widths and runs through RTS at 81:C604.",
    },
]


def cpu_to_offset(cpu: str) -> int:
    bank_s, addr_s = cpu.split(":")
    bank = int(bank_s, 16)
    addr = int(addr_s, 16)
    if addr < 0x8000:
        raise ValueError(cpu)
    return ((bank & 0x7F) * 0x8000) + (addr - 0x8000)


def offset_to_cpu(off: int) -> str:
    bank = (off // 0x8000) | 0x80
    addr = (off % 0x8000) | 0x8000
    return f"{bank:02X}:{addr:04X}"



def seed_entries(disassembler, offsets: list[int]) -> None:
    """Add trusted entry labels and rerun snes2asm path discovery.

    The default vector walk does not reach several bank-82 routines. Seeding is
    valid here because each entry is independently recovered from Nitrodon's
    listing / structural correspondence, and the compared functions immediately
    establish or safely preserve the M/X state needed by this bounded pass.
    """
    for off in offsets:
        disassembler.label_name(off)
    disassembler.find_valid_code_paths()



def compare_aligned_bytes(ud, ed, usa: bytes, europe: bytes, start: int, end: int, shift: int) -> dict:
    opcode_changes = []
    operand_byte_changes = 0
    equal_opcode_pairs = 0
    for off in range(start, end + 1):
        eo = off + shift
        ur = ud.code_map[off]
        er = ed.code_map[eo]
        u_opcode = bool(ur & ud.OP_CODE)
        e_opcode = bool(er & ed.OP_CODE)
        u_operand = bool(ur & ud.OP_PARAM)
        e_operand = bool(er & ed.OP_PARAM)
        if u_opcode and e_opcode:
            if usa[off] == europe[eo]:
                equal_opcode_pairs += 1
            else:
                opcode_changes.append({
                    "relative_offset": off - start,
                    "usa_offset": off,
                    "europe_offset": eo,
                    "usa_opcode": f"0x{usa[off]:02X}",
                    "europe_opcode": f"0x{europe[eo]:02X}",
                })
        elif u_operand and e_operand and usa[off] != europe[eo]:
            operand_byte_changes += 1
    total = equal_opcode_pairs + len(opcode_changes)
    return {
        "aligned_equal_opcode_pairs": equal_opcode_pairs,
        "aligned_opcode_byte_disagreements": len(opcode_changes),
        "aligned_opcode_byte_consensus_fraction": 0 if total == 0 else round(equal_opcode_pairs / total, 6),
        "aligned_operand_byte_changes": operand_byte_changes,
        "aligned_opcode_changes": opcode_changes,
    }


def build() -> dict:
    usa = USA.read_bytes()
    europe = EUROPE.read_bytes()
    ud = trace(usa)
    ed = trace(europe)

    usa_seeds = [
        cpu_to_offset("80:8C41"),
        cpu_to_offset("82:A968"),
        cpu_to_offset("82:AA6E"),
        cpu_to_offset("81:953D"),
        cpu_to_offset("81:9E2A"),
        cpu_to_offset("81:C5B3"),
    ]
    europe_seeds = [
        cpu_to_offset("80:8C41"),
        cpu_to_offset("82:A96F"),
        cpu_to_offset("82:AA75"),
        cpu_to_offset("81:9523"),
        cpu_to_offset("81:9E1B"),
        cpu_to_offset("81:C59C"),
    ]
    seed_entries(ud, usa_seeds)
    seed_entries(ed, europe_seeds)

    rows = []

    for region in REGIONS:
        start = cpu_to_offset(region["usa_start"])
        end = cpu_to_offset(region["usa_end"])
        center = int(region["expected_europe_shift"])
        # Constrain the search around the already-established structural candidate.
        shift, sim = best_shift(usa, europe, start, end, radius=64)
        metrics = compare_roles(ud, ed, usa, europe, start, end, shift)
        byte_metrics = compare_aligned_bytes(ud, ed, usa, europe, start, end, shift)
        if metrics["aligned_opcode_pairs"] == 0:
            raise RuntimeError(
                f"{region['name']}: seeded snes2asm still found zero aligned opcode pairs"
            )
        rows.append({
            **region,
            "usa_file_start": start,
            "usa_file_end": end,
            "europe_shift": shift,
            "europe_start": offset_to_cpu(start + shift),
            "europe_end": offset_to_cpu(end + shift),
            "raw_similarity_after_alignment": round(sim, 6),
            **metrics,
            **byte_metrics,
        })

    totals = {
        "regions": len(rows),
        "aligned_role_disagreements": sum(x["aligned_role_disagreements"] for x in rows),
        "aligned_mx_disagreements": sum(x["aligned_mx_disagreements"] for x in rows),
        "zero_role_disagreement_regions": sum(x["aligned_role_disagreements"] == 0 for x in rows),
        "aligned_opcode_pairs": sum(x["aligned_opcode_pairs"] for x in rows),
        "aligned_opcode_byte_disagreements": sum(x["aligned_opcode_byte_disagreements"] for x in rows),
        "aligned_operand_byte_changes": sum(x["aligned_operand_byte_changes"] for x in rows),
    }
    return {
        "schema_version": 1,
        "method": {
            "source": "USA retail",
            "target": "Europe retail",
            "analyzer": "vendored snes2asm",
            "boundaries": "Nitrodon/control-flow recovered boundaries",
            "alignment": "per executable subregion raw-byte similarity within +/-64 bytes",
            "reachability": "default vector walk plus independently trusted function-entry seeds",
            "promotion_rule": "only residual role/MX disagreement after homolog alignment is an analyzer-adjudication candidate",
        },
        "totals": totals,
        "regions": rows,
    }


def render(report: dict) -> str:
    t = report["totals"]
    lines = [
        "# Europe/USA selected snes2asm homolog comparison",
        "",
        f"Executable subregions compared: **{t['regions']}**.",
        f"Aligned opcode pairs: **{t['aligned_opcode_pairs']}**.",
        f"Aligned opcode-byte disagreements: **{t['aligned_opcode_byte_disagreements']}**.",
        f"Aligned operand-byte changes: **{t['aligned_operand_byte_changes']}**.",
        f"Aligned role disagreements: **{t['aligned_role_disagreements']}**.",
        f"Aligned M/X disagreements: **{t['aligned_mx_disagreements']}**.",
        f"Zero-role-disagreement subregions: **{t['zero_role_disagreement_regions']} / {t['regions']}**.",
        "",
        "| Region | USA | Europe | Shift | Raw sim | Opcode Δ | Operand-byte Δ | Role disagree | M/X disagree |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in report["regions"]:
        lines.append(
            f"| {r['name']} | `{r['usa_start']}..{r['usa_end']}` | "
            f"`{r['europe_start']}..{r['europe_end']}` | {r['europe_shift']:+d} | "
            f"{r['raw_similarity_after_alignment']:.3f} | {r['aligned_opcode_byte_disagreements']} | "
            f"{r['aligned_operand_byte_changes']} | {r['aligned_role_disagreements']} | "
            f"{r['aligned_mx_disagreements']} |"
        )
    opcode_survivors = [r for r in report["regions"] if r["aligned_opcode_byte_disagreements"]]
    lines += ["", "## Genuine aligned opcode substitutions", ""]
    if not opcode_survivors:
        lines.append("None.")
    for r in opcode_survivors:
        lines += [f"### {r['name']}", ""]
        for x in r["aligned_opcode_changes"]:
            lines.append(
                f"- +0x{x['relative_offset']:X}: USA {x['usa_opcode']} vs Europe {x['europe_opcode']}"
            )
        lines.append("")

    survivors = [r for r in report["regions"] if r["aligned_role_disagreements"] or r["aligned_mx_disagreements"]]
    lines += ["", "## Surviving analyzer disagreements", ""]
    if not survivors:
        lines.append("None.")
    for r in survivors:
        lines += [f"### {r['name']}", "", r["basis"]]
        for x in r["aligned_residuals"]:
            lines.append(
                f"- +0x{x['relative_offset']:X}: USA {x['retail_role']} {x['retail_byte']} "
                f"vs Europe {x['prototype_role']} {x['prototype_byte']}"
            )
        lines.append("")
    lines += [
        "",
        "Aligned opcode-byte substitutions are genuine executable deltas even when instruction boundaries and M/X state remain stable. Operand-byte changes are retained separately as likely addresses/constants/layout motion until semantics say otherwise.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    report = build()
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(render(report), encoding="utf-8")
    print(OUT_MD.read_text(encoding="utf-8"))
    print("EU_US_JSON=" + json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
