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
BETA = ROOT / "reference/roms/prototypes/Uniracers_Beta_legacy.sfc"
PROTO = ROOT / "reference/roms/prototypes/Unirally_1994-11-29_PAL_prototype.sfc"
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
    {
        "name": "Race_UpdateRacersFrame:state_marshal_prefix",
        "usa_start": "82:89B9",
        "usa_end": "82:8C26",
        "expected_europe_shift": 19,
        "basis": "Nitrodon function entry through the sequential state-marshal prefix immediately before the first long call at 82:8C27.",
    },
    {
        "name": "Stunt_FinalizeAndScoreAirTricks:air_entry",
        "usa_start": "82:9A42",
        "usa_end": "82:9AA8",
        "expected_europe_shift": 17,
        "basis": "Nitrodon stunt-finalizer entry through the first air-entry/reset block, bounded before JMP 82:9AA9.",
    },
    {
        "name": "Stunt_FinalizeAndScoreAirTricks:rotation_progress",
        "usa_start": "82:9AAC",
        "usa_end": "82:9B54",
        "expected_europe_shift": 17,
        "basis": "Nitrodon rotation/progress block through the stored quadrant, bounded before JMP 82:9B55.",
    },
    {
        "name": "Course_LoadAndMaterialize:setup",
        "usa_start": "82:E165",
        "usa_end": "82:E1CF",
        "expected_europe_shift": -58,
        "basis": "Nitrodon course-loader entry through initial clear/DMA/pointer setup and width transition at 82:E1CF.",
    },
    {
        "name": "Course_LoadAndMaterialize:record_header",
        "usa_start": "82:E1D1",
        "usa_end": "82:E213",
        "expected_europe_shift": -58,
        "basis": "Nitrodon course-record header read and materialization pointer setup, bounded before the DMA row loop at 82:E216.",
    },
    {
        "name": "Course_LoadAndMaterialize:dma_row_loop",
        "usa_start": "82:E216",
        "usa_end": "82:E2FF",
        "expected_europe_shift": -58,
        "basis": "Nitrodon bounded VRAM/DMA row loop through the post-loop VRAM pointer load, before exit/range dispatch at 82:E302.",
    },
    {
        "name": "Race_HandleCheckpointFinish:entry_and_time_prefix",
        "usa_start": "81:8050",
        "usa_end": "81:8101",
        "expected_europe_shift": 0,
        "basis": "Dispatch-confirmed handler entry through accumulated minute/second/tenths total; Europe remains at the same code layout through this boundary.",
    },
    {
        "name": "Race_HandleCheckpointFinish:frame_normalization_delta",
        "usa_start": "81:8102",
        "usa_end": "81:8117",
        "expected_europe_shift": -6,
        "allow_structural_delta": True,
        "europe_explicit_start": "81:8102",
        "europe_explicit_end": "81:8109",
        "basis": "Bounded timer-frame normalization block. USA uses 22 bytes (8102..8117); Europe uses 8 bytes (8102..8109), after which the shared suffix resumes at Europe 810A / USA 8118 for a net -14 shift.",
    },
    {
        "name": "Race_HandleCheckpointFinish:time_suffix",
        "usa_start": "81:8118",
        "usa_end": "81:8122",
        "expected_europe_shift": -14,
        "basis": "Post-normalization race-time sum and player branch; local profile independently shows exact downstream homolog shift -14.",
    },
    {
        "name": "Race_HandleCheckpointFinish:player_records",
        "usa_start": "81:8123",
        "usa_end": "81:8194",
        "expected_europe_shift": 0,
        "basis": "Player-specific persistent record update block; bounded at the shared lap-update join 81:8195.",
    },
    {
        "name": "Race_HandleCheckpointFinish:lap_hud",
        "usa_start": "81:8195",
        "usa_end": "81:81D3",
        "expected_europe_shift": 0,
        "basis": "Shared lap decrement and HUD-message phase; stops before the later Nitrodon listing becomes width-ambiguous around 81:81EC.",
    },
    {
        "name": "Race_BuildRacerOAMState:p1_projection",
        "usa_start": "82:ACF3",
        "usa_end": "82:ADA7",
        "expected_europe_shift": 7,
        "basis": "Player-1 world/camera-to-screen projection begins with REP #$30 and runs through its bounded offscreen-classification join.",
    },
    {
        "name": "Race_BuildRacerOAMState:p2_projection",
        "usa_start": "82:ADC1",
        "usa_end": "82:AE57",
        "expected_europe_shift": 7,
        "basis": "Player-2 sibling projection begins with REP #$30 and runs through its bounded offscreen-classification jump.",
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



def local_shift_profile(source: bytes, target: bytes, start: int, end: int, chunk: int = 8) -> list[dict]:
    rows = []
    pos = start
    while pos <= end:
        stop = min(end, pos + chunk - 1)
        shift, sim = best_shift(source, target, pos, stop, radius=64)
        rows.append({
            "relative_start": pos - start,
            "relative_end": stop - start,
            "usa_start": offset_to_cpu(pos),
            "usa_end": offset_to_cpu(stop),
            "europe_shift": shift,
            "raw_similarity": round(sim, 6),
            "usa_hex": source[pos:stop + 1].hex(" "),
            "europe_hex": target[pos + shift:stop + shift + 1].hex(" "),
        })
        pos = stop + 1
    return rows



def checkpoint_frame_normalization_lineage(usa: bytes, europe: bytes) -> dict:
    beta = BETA.read_bytes()
    proto = PROTO.read_bytes()
    start = cpu_to_offset("81:8102")
    usa_span = usa[start:cpu_to_offset("81:8117") + 1]
    europe_span = europe[start:cpu_to_offset("81:8109") + 1]

    builds = {
        "usa-retail": usa,
        "legacy-beta": beta,
        "pal-prototype-1994-11-29": proto,
        "europe-retail": europe,
    }
    rows = {}
    for name, data in builds.items():
        usa_candidate = data[start:start + len(usa_span)]
        europe_candidate = data[start:start + len(europe_span)]
        if usa_candidate == usa_span:
            style = "usa-style-22-byte"
        elif europe_candidate == europe_span:
            style = "europe-style-8-byte"
        else:
            style = "other"
        rows[name] = {
            "style": style,
            "bytes_8102_8117": usa_candidate.hex(" "),
            "bytes_8102_8109": europe_candidate.hex(" "),
        }

    return {
        "cpu_start": "81:8102",
        "usa_style_span": "81:8102..81:8117",
        "europe_style_span": "81:8102..81:8109",
        "usa_style_hex": usa_span.hex(" "),
        "europe_style_hex": europe_span.hex(" "),
        "builds": rows,
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
        cpu_to_offset("82:89B9"),
        cpu_to_offset("82:9A42"),
        cpu_to_offset("82:E165"),
        cpu_to_offset("81:8050"),
        cpu_to_offset("82:ACA5"),
    ]
    europe_seeds = [
        cpu_to_offset("80:8C41"),
        cpu_to_offset("82:A96F"),
        cpu_to_offset("82:AA75"),
        cpu_to_offset("81:9523"),
        cpu_to_offset("81:9E1B"),
        cpu_to_offset("81:C59C"),
        cpu_to_offset("82:89CC"),
        cpu_to_offset("82:9A53"),
        cpu_to_offset("82:E12B"),
        cpu_to_offset("81:8050"),
        cpu_to_offset("82:ACAC"),
    ]
    seed_entries(ud, usa_seeds)
    seed_entries(ed, europe_seeds)

    rows = []

    for region in REGIONS:
        start = cpu_to_offset(region["usa_start"])
        end = cpu_to_offset(region["usa_end"])
        center = int(region["expected_europe_shift"])
        # Constrain the search around the already-established structural candidate.
        center = int(region["expected_europe_shift"])
        src = usa[start:end + 1]
        best = (center, -1.0)
        for candidate_shift in range(center - 32, center + 33):
            a = start + candidate_shift
            b = a + len(src)
            if a < 0 or b > len(europe):
                continue
            score = sum(x == y for x, y in zip(src, europe[a:b])) / len(src)
            if score > best[1]:
                best = (candidate_shift, score)
        shift, sim = best
        metrics = compare_roles(ud, ed, usa, europe, start, end, shift)
        byte_metrics = compare_aligned_bytes(ud, ed, usa, europe, start, end, shift)
        if metrics["aligned_opcode_pairs"] == 0:
            raise RuntimeError(
                f"{region['name']}: seeded snes2asm still found zero aligned opcode pairs"
            )
        row = {
            **region,
            "usa_file_start": start,
            "usa_file_end": end,
            "europe_shift": shift,
            "europe_start": offset_to_cpu(start + shift),
            "europe_end": offset_to_cpu(end + shift),
            "raw_similarity_after_alignment": round(sim, 6),
            **metrics,
            **byte_metrics,
        }
        if region.get("allow_structural_delta"):
            eu_start = cpu_to_offset(region["europe_explicit_start"])
            eu_end = cpu_to_offset(region["europe_explicit_end"])
            row["structural_delta"] = {
                "usa_span_bytes": end - start + 1,
                "europe_span_bytes": eu_end - eu_start + 1,
                "net_size_delta_europe_minus_usa": (eu_end - eu_start + 1) - (end - start + 1),
                "usa_hex": usa[start:end + 1].hex(" "),
                "europe_hex": europe[eu_start:eu_end + 1].hex(" "),
                "usa_opcode_bytes": [
                    f"0x{usa[off]:02X}" for off in range(start, end + 1)
                    if ud.code_map[off] & ud.OP_CODE
                ],
                "europe_opcode_bytes": [
                    f"0x{europe[off]:02X}" for off in range(eu_start, eu_end + 1)
                    if ed.code_map[off] & ed.OP_CODE
                ],
                "europe_start": region["europe_explicit_start"],
                "europe_end": region["europe_explicit_end"],
            }
        elif metrics["aligned_role_disagreements"] or byte_metrics["aligned_opcode_byte_disagreements"]:
            row["raw_local_shift_profile_8byte"] = local_shift_profile(usa, europe, start, end)
        rows.append(row)

    comparable = [x for x in rows if not x.get("allow_structural_delta")]
    deltas = [x for x in rows if x.get("allow_structural_delta")]
    totals = {
        "regions": len(rows),
        "comparable_homolog_regions": len(comparable),
        "structural_delta_regions": len(deltas),
        "aligned_role_disagreements": sum(x["aligned_role_disagreements"] for x in comparable),
        "aligned_mx_disagreements": sum(x["aligned_mx_disagreements"] for x in comparable),
        "zero_role_disagreement_regions": sum(x["aligned_role_disagreements"] == 0 for x in comparable),
        "aligned_opcode_pairs": sum(x["aligned_opcode_pairs"] for x in comparable),
        "aligned_opcode_byte_disagreements": sum(x["aligned_opcode_byte_disagreements"] for x in comparable),
        "aligned_operand_byte_changes": sum(x["aligned_operand_byte_changes"] for x in comparable),
    }
    return {
        "schema_version": 1,
        "checkpoint_frame_normalization_lineage": checkpoint_frame_normalization_lineage(usa, europe),
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
    opcode_survivors = [
        r for r in report["regions"]
        if not r.get("allow_structural_delta") and r["aligned_opcode_byte_disagreements"]
    ]
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

    deltas = [r for r in report["regions"] if r.get("allow_structural_delta")]
    lines += ["", "## Genuine structural deltas", ""]
    if not deltas:
        lines.append("None.")
    for r in deltas:
        d = r["structural_delta"]
        lines += [
            f"### {r['name']}",
            "",
            r["basis"],
            f"- USA span: \`{r['usa_start']}..{r['usa_end']}\` ({d['usa_span_bytes']} bytes)",
            f"- Europe span: \`{d['europe_start']}..{d['europe_end']}\` ({d['europe_span_bytes']} bytes)",
            f"- Net Europe size delta: {d['net_size_delta_europe_minus_usa']:+d} bytes",
            f"- USA opcodes: {' '.join(d['usa_opcode_bytes'])}",
            f"- Europe opcodes: {' '.join(d['europe_opcode_bytes'])}",
            "",
        ]

    survivors = [
        r for r in report["regions"]
        if not r.get("allow_structural_delta")
        and (r["aligned_role_disagreements"] or r["aligned_mx_disagreements"])
    ]
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
        if r.get("raw_local_shift_profile_8byte"):
            lines.append("- local raw shift profile:")
            for p in r["raw_local_shift_profile_8byte"]:
                lines.append(
                    f"  - +0x{p['relative_start']:X}..+0x{p['relative_end']:X} "
                    f"({p['usa_start']}..{p['usa_end']}): shift {p['europe_shift']:+d}, "
                    f"sim {p['raw_similarity']:.3f}; USA [{p['usa_hex']}] / Europe [{p['europe_hex']}]"
                )
        lines.append("")
    lineage = report["checkpoint_frame_normalization_lineage"]
    lines += ["", "## Checkpoint timer-normalization lineage", ""]
    for build, row in lineage["builds"].items():
        lines.append(f"- {build}: **{row['style']}**")
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
