#!/usr/bin/env python3
"""QA-08: strict native post-GO 2P original PPU raster register journal.

Consume ONE original native raster journal from the already existing
stock 2P route. Capture and validate which $2130/$2131/$2132 register
writes were recorded, not whether color math owned any specific HUD or
racer pixel. No new guest process or renderer/art changes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

try:
    from tools.check_baldosa_wide_slot_final_visibility import read_pam
except ModuleNotFoundError:
    from check_baldosa_wide_slot_final_visibility import read_pam

FRAME = 2208
ROUTE_CRC_LINES = 2473
EXPECTED_STOCK_SHA256 = (
    "f9ca59c19dc3e8d51c7ca1dbce25d5dc14e56ba36011128abbadee8cec0e7b4a"
)
REGEX = re.compile(
    r"^UR_QA08_PPU_COLOUR_JOURNAL guest=2208 guest_unchanged=1 "
    r"cgadsub=([0-9A-F]{2}) cgwsel=([0-9A-F]{2}) "
    r"fixed15=([0-9A-F]{4}) raster=(\{.*\})$"
)
COLOR_REGS = {0x2130: "CGWSEL", 0x2131: "CGADSUB", 0x2132: "COLDATA"}

MAX_NATIVE_SCANLINE = 261

try:
    from tools.qa08_ppu_beam_colour_state import decode_field as decode_beam_colour
except ModuleNotFoundError:
    from qa08_ppu_beam_colour_state import decode_field as decode_beam_colour


def reject_duplicate_json_keys(pairs: list[tuple[str, object]]) -> dict:
    """A forged duplicate field must not silently override genuine evidence."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate native PPU journal JSON key: {key}")
        result[key] = value
    return result


def cgadsub_line_intervals(baseline: str, entries: list[dict]) -> dict:
    """Lossless register chronology in native line tags, not a pixel oracle.

    Retain all same-line writes in journal order, but show intervals after the
    final write on each tag. SNES line tags are not calibrated to final PPU y.
    """
    initial = int(baseline, 16)
    by_line = {}
    events = []
    for index, entry in enumerate(entries):
        if int(entry["r"], 16) != 0x2131:
            continue
        line = entry["l"]
        value = int(entry["v"], 16)
        events.append({
            "journal_index": index,
            "native_scanline_tag": line,
            "written_value": f"0x{value:02X}",
        })
        by_line.setdefault(line, []).append(value)
    intervals = []
    previous = 0
    current = initial
    for line in sorted(by_line):
        if line > previous:
            intervals.append({
                "first_scanline_tag": previous,
                "last_scanline_tag": line - 1,
                "cgadsub": f"0x{current:02X}",
            })
        current = by_line[line][-1]
        previous = line
    if previous <= MAX_NATIVE_SCANLINE:
        intervals.append({
            "first_scanline_tag": previous,
            "last_scanline_tag": MAX_NATIVE_SCANLINE,
            "cgadsub": f"0x{current:02X}",
        })
    return {
        "initial_cgadsub": f"0x{initial:02X}",
        "cgadsub_write_count": len(events),
        "cgadsub_writes_in_original_journal_order": events,
        "same_scanline_rewrites": sum(len(values) - 1 for values in by_line.values()),
        "line_tag_intervals_after_last_same_line_write": intervals,
        "tag_to_original_output_y_calibrated": False,
        "effective_per_pixel_colour_math_proven": False,
    }


def parse_record(line: str) -> dict:
    m = REGEX.fullmatch(line.strip())
    if not m:
        raise ValueError("one exact genuine guest2208 read-only original PPU journal required")
    end_adsub, end_wsel, end_fixed = (int(x, 16) for x in m.group(1, 2, 3))
    trace = json.loads(m.group(4), object_pairs_hook=reject_duplicate_json_keys)
    if (type(trace.get("armed")) is not int or trace["armed"] != 1 or
        type(trace.get("have_completed")) is not int or trace["have_completed"] != 1):
        raise ValueError("raster journal was not armed/completed in native PPU")
    field_reports = {}
    for field_name in ("completed", "recording"):
        field = trace.get(field_name)
        if (not isinstance(field, dict) or type(field.get("dropped")) is not int
            or field["dropped"] != 0):
            raise ValueError("missing or dropped original PPU raster journal field")
        entries = field.get("entries")
        if (not isinstance(entries, list) or type(field.get("count")) is not int
            or field["count"] != len(entries)):
            raise ValueError("incomplete native PPU raster journal entries")
        base = field.get("base")
        if (not isinstance(base, dict) or
            not isinstance(base.get("cgadsub"), str) or
            re.fullmatch(r"0x[0-9A-Fa-f]{2}", base["cgadsub"]) is None):
            raise ValueError("raster CGADSUB baseline missing")
        matched = []
        for entry in entries:
            if not isinstance(entry, dict) or type(entry.get("l")) is not int:
                raise ValueError("raster entry has no original SNES scanline")
            line_no = entry["l"]
            reg, val = entry.get("r"), entry.get("v")
            if (not 0 <= line_no <= MAX_NATIVE_SCANLINE or
                not isinstance(reg, str) or
                not isinstance(val, str) or
                re.fullmatch(r"0x[0-9A-Fa-f]{4}", reg) is None or
                re.fullmatch(r"0x[0-9A-Fa-f]{2}", val) is None):
                raise ValueError("invalid original PPU scanline/register/write byte")
            register = int(reg, 16)
            if not (0x2100 <= register <= 0x2133 or register == 0x420C):
                raise ValueError("non-PPU address in native PPU display journal")
            if register in COLOR_REGS:
                matched.append({"line": line_no, "register": COLOR_REGS[register],
                                "address": reg, "written_byte": val})
        field_reports[field_name] = {
            "baseline_cgadsub": base["cgadsub"],
            "raster_writes_total": len(entries),
            "colour_register_write_count": len(matched),
            "colour_register_write_examples_bounded": matched[:128],
            "colour_write_examples_truncated": len(matched) > 128,
            "raster_journal_dropped": 0,
            "cgadsub_scanline_tag_chronology":
                cgadsub_line_intervals(base["cgadsub"], entries),
            "beam_order_colour_knowledge": decode_beam_colour(base, entries),
            "legacy_numeric_tag_order_is_not_beam_field_order": True,
        }
    return {
        "schema_version": 1,
        "status": "native-original-2p-postgo-PPU-register-journal-observed",
        "guest_frame": FRAME,
        "raster_journal_armed_and_completed": True,
        "no_dropped_raster_writes": True,
        "sampled_after_render_registers": {
            "CGADSUB": f"0x{end_adsub:02X}",
            "CGWSEL": f"0x{end_wsel:02X}",
            "fixed_color_RGB15": f"0x{end_fixed:04X}",
            "fixed_R5": end_fixed & 31,
            "fixed_G5": (end_fixed >> 5) & 31,
            "fixed_B5": (end_fixed >> 10) & 31,
        },
        "field_register_journals": field_reports,
        "13_red5_original_racer_source_signature_already_known": True,
        "PPU_registers_per_racer_pixel_or_line_proven": False,
        "native_scanline_tag_to_final_PPU_row_alignment_proven": False,
        "specific_PPU_window_BG_OBJ_ownership_proven": False,
        "native_graphics_changed": False,
        "remastered_HD_art_approved": False,
        "limits": (
            "Captured the pinned SNESRecomp original native PPU field's "
            "read-only register journal, CGADSUB line-tag intervals and sampled end-of-frame state. "
            "A baseline plus written values are not necessarily the "
            "effective per-PIXEL colour operands, windows or priority; "
            "this does not prove what made any of the 13 +red5 pixels."
        ),
    }


def verify(stock: Path, log: Path, reference_crc: Path, candidate_crc: Path) -> dict:
    if stock.name != f"ur-baldosa-ws342-{FRAME:06d}.pam":
        raise ValueError("expected exact authentic post-GO Original capture")
    original = read_pam(stock)
    digest = hashlib.sha256(original).hexdigest()
    if digest != EXPECTED_STOCK_SHA256:
        raise ValueError("native stock Original frame2208 SHA changed")
    base = reference_crc.read_bytes().splitlines()
    observed = candidate_crc.read_bytes().splitlines()
    if len(base) != ROUTE_CRC_LINES or base != observed:
        raise ValueError("native 2P stock/journal full 2473 guest CRC streams differ")
    lines = [l for l in log.read_text(encoding="utf-8", errors="replace").splitlines()
             if "UR_QA08_PPU_COLOUR_JOURNAL" in l]
    if len(lines) != 1 or "UR_QA08_PPU_COLOUR_JOURNAL_FAIL" in lines[0]:
        raise ValueError("not exactly one successful native colour raster journal record")
    record = parse_record(lines[0])
    record["full_native_guest_CRC_entries_equal"] = ROUTE_CRC_LINES
    record["full_original_342x224_RGBA_SHA256"] = digest
    return record


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    for key in ("stock", "log", "reference-crc", "candidate-crc", "out"):
        p.add_argument("--" + key, required=True, type=Path)
    a = p.parse_args()
    result = verify(a.stock, a.log, a.reference_crc, a.candidate_crc)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                     encoding="utf-8")
    samples = result["sampled_after_render_registers"]
    observed = sum(
        f["colour_register_write_count"]
        for f in result["field_register_journals"].values()
    )
    print("UR_QA08_PPU_COLOUR_JOURNAL_ACCEPTED "
          f"guest={FRAME} crc={ROUTE_CRC_LINES} "
          f"colour_writes={observed} "
          f"end_cgadsub={samples['CGADSUB']} "
          f"end_cgwsel={samples['CGWSEL']} "
          f"end_fixed={samples['fixed_color_RGB15']} "
          "original_guest_unchanged=1 HD_admitted=0")


if __name__ == "__main__":
    main()
