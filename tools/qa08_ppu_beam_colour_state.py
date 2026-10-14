#!/usr/bin/env python3
"""Replay tagged SNES PPU colour writes in authentic 225..261,0..224 beam order.

This intentionally cannot infer final per-pixel colour math, the pre-field
CGWSEL/fixed-colour baseline, or physical output-Y alignment. Consume only an
independently authenticated original PPU journal for empirical claims.
"""
from __future__ import annotations

import re

# SNESRecomp pinned ppu.c raster_key, captured field begins at the V=225 cut.
FIELD_LINES = 262
PRE_VISIBLE_LINES = 37
VISIBLE_LINES = 224  # Y 0..223; the field's final tagged line 224 is not output
COLOUR_REGISTERS = {0x2130: "CGWSEL", 0x2131: "CGADSUB", 0x2132: "COLDATA"}
HEX8 = re.compile(r"0x[0-9A-Fa-f]{2}\Z")
HEX16 = re.compile(r"0x[0-9A-Fa-f]{4}\Z")


def beam_key(line: int) -> int:
    if type(line) is not int or not 0 <= line < FIELD_LINES:
        raise ValueError("invalid native beam line tag")
    return line - 225 if line >= 225 else line + PRE_VISIBLE_LINES


def decode_field(base: dict, entries: list[dict]) -> dict:
    """Reconstruct provable per-registered-line state only, unknowns as null.

    No synthetic baseline from the sampled *end* PPU registers. COLDATA's
    write-enable bits permit provenance for R/G/B independently. Same-beam
    key writes remain in source order. Native renderer applies writes for a
    line before drawing its whole line; actual hardware mid-line effects and
    raster-to-image row alignment still require a separate witness.
    """
    if not isinstance(base, dict) or not isinstance(base.get("cgadsub"), str) or not HEX8.fullmatch(base["cgadsub"]):
        raise ValueError("original CGADSUB baseline required")
    if not isinstance(entries, list) or len(entries) > 4096:
        raise ValueError("invalid or overlong original PPU field journal")
    cgadsub = int(base["cgadsub"], 16)
    cgwsel = None  # not included in ppu_rasterDebugDump field.base
    fixed = [None, None, None]  # likewise no RGB15 field baseline
    events = []
    state_at_key = [None] * FIELD_LINES
    previous = -1
    next_fill = 0

    def snapshot() -> dict:
        return {
            "cgadsub": f"0x{cgadsub:02X}",
            "cgwsel": f"0x{cgwsel:02X}" if cgwsel is not None else None,
            "fixed_R5_G5_B5": list(fixed),
            "fixed_rgb15": (
                f"0x{fixed[0] | fixed[1] << 5 | fixed[2] << 10:04X}"
                if all(v is not None for v in fixed) else None
            ),
        }

    for journal_index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError("invalid native journal entry object")
        tag, reg, val = entry.get("l"), entry.get("r"), entry.get("v")
        key = beam_key(tag)
        if (key < previous or not isinstance(reg, str) or not HEX16.fullmatch(reg)
                or not isinstance(val, str) or not HEX8.fullmatch(val)):
            raise ValueError("out-of-order native beam keys or invalid register/write")
        address = int(reg, 16)
        if not (0x2100 <= address <= 0x2133 or address == 0x420C):
            raise ValueError("invalid original PPU register")
        for k in range(next_fill, key):
            state_at_key[k] = snapshot()
        next_fill = key  # same-key subsequent writes overwrite before line state
        previous = key
        value = int(val, 16)
        if address == 0x2130:
            cgwsel = value
        elif address == 0x2131:
            cgadsub = value
        elif address == 0x2132:
            for component, flag in enumerate((0x20, 0x40, 0x80)):
                if value & flag:
                    fixed[component] = value & 0x1F
        if address in COLOUR_REGISTERS:
            events.append({
                "journal_index": journal_index,
                "beam_key": key,
                "native_scanline_tag": tag,
                "register": COLOUR_REGISTERS[address],
                "written_value": f"0x{value:02X}",
                "state_after_write": snapshot(),
            })
    for k in range(next_fill, FIELD_LINES):
        state_at_key[k] = snapshot()

    def compress(rows: list[dict], first: int, label: str) -> list[dict]:
        if not rows:
            return []
        spans = []
        start = 0
        for i in range(1, len(rows) + 1):
            if i == len(rows) or rows[i] != rows[start]:
                spans.append({f"first_{label}": first + start,
                              f"last_{label}": first + i - 1,
                              **rows[start]})
                start = i
        return spans

    # Keys 37..260 mean genuine visible line tags 0..223, **not** 0..224.
    visible = state_at_key[PRE_VISIBLE_LINES:PRE_VISIBLE_LINES + VISIBLE_LINES]
    return {
        "schema": "qa08-ppu-beam-colour-knowledge/1",
        "beam_key_origin": "V=225 at key0; V=0 at key37",
        "baseline_cgadsub": f"0x{int(base['cgadsub'], 16):02X}",
        "baseline_cgwsel_known": False,
        "baseline_fixed_colour_known": False,
        "colour_writes_in_original_beam_order": events,
        "beam_key_intervals_after_same_line_final_write":
            compress(state_at_key, 0, "beam_key"),
        "visible_line_tag_intervals_after_same_line_final_write":
            compress(visible, 0, "visible_line_tag"),
        "completed_visible_line_tags": list(range(VISIBLE_LINES)),
        "source_colour_math_operand_per_pixel_proven": False,
        "beam_tag_to_output_image_row_calibrated": False,
        "raster_midline_write_timing_proven": False,
        "physical_oam_or_bg_priority_observed": False,
        "remastered_character_approved": False,
        "limitations": (
            "Derived from ordered source writes, with CGWSEL and fixed-RGB baselines "
            "deliberately unknown until written. The pinned SNESRecomp renderer "
            "replays whole-line register state; effective hardware intra-line "
            "timing, subscreen/window eligibility and final pixel source remain unproven."
        ),
    }
