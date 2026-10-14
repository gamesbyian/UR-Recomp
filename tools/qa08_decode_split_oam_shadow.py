#!/usr/bin/env python3
"""Read-only QA-08 decoder of reserved racer OAM *WRAM shadow* checkpoints.

The $1501..$1510 low-OAM buffer and $1599 high-table byte are not the
effective per-scanline PPU OAM after Uniracers' active-display sprite rip.
This does not infer final visible pixels, culling, or split-screen correctness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

try:
    from tools.decode_uniracers_oam_split import decode_high_oam_byte
except ModuleNotFoundError:
    from decode_uniracers_oam_split import decode_high_oam_byte

WRAM_BYTES = 0x20000
LOW_OAM_START = 0x1501
HIGH_OAM = 0x1599
ROLES = {
    96: "lower/P2 candidate",
    97: "lower/P1 candidate",
    98: "upper/P1 candidate",
    99: "upper/P2 candidate",
}
TAG = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}\Z")


def u16(data: bytes, addr: int) -> int:
    return int.from_bytes(data[addr:addr + 2], "little")


def inspect_bytes(data: bytes) -> dict:
    """Decode only structural SNES OAM fields, never a visibility predicate."""
    if len(data) != WRAM_BYTES:
        raise ValueError(f"expected exact 128 KiB WRAM, got {len(data)} bytes")
    high = data[HIGH_OAM]
    fields = decode_high_oam_byte(high)
    records = []
    for i, bits in enumerate(fields):
        slot = 96 + i
        pos = LOW_OAM_START + i * 4
        x_low, y, tile, attr = data[pos:pos + 4]
        x9 = x_low | (bits["x_msb"] << 8)
        records.append({
            "slot": slot,
            "candidate_viewport_owner": ROLES[slot],
            "buffer_wram_start": f"0x{pos:04X}",
            "raw_oam_bytes": [x_low, y, tile, attr],
            "x_unsigned9": x9,
            "x_signed9_wrapped": x9 - 512 if x9 >= 256 else x9,
            "y_unsigned8": y,
            "tile_raw": tile,
            "attributes_raw": attr,
            "x_msb": bits["x_msb"],
            "size_select": bits["size_select"],
            "possible_sentinel_or_offscreen": "unclassified",
        })
    return {
        "oam_high_shadow_1599": high,
        "oam_high_slots96_99": fields,
        "reserved_slots": records,
        "second_camera_enable_0ddb_raw_word": u16(data, 0x0DDB),
        "offscreen_flags_121b_121d_raw_words":
            [u16(data, 0x121B), u16(data, 0x121D)],
        "camera_x_0419_041b_raw_words":
            [u16(data, 0x0419), u16(data, 0x041B)],
    }


def audit(directory: Path, checkpoints: list[str]) -> dict:
    if not checkpoints or len(set(checkpoints)) != len(checkpoints):
        raise ValueError("nonempty ordered distinct checkpoints required")
    if any(not TAG.fullmatch(tag) or tag in (".", "..") for tag in checkpoints):
        raise ValueError("invalid checkpoint label")
    frames = []
    for tag in checkpoints:
        path = directory / f"{tag}.wram.bin"
        data = path.read_bytes()
        frame = {
            "checkpoint": tag,
            "wram_sha256": hashlib.sha256(data).hexdigest(),
            **inspect_bytes(data),
        }
        frames.append(frame)
    changes = []
    for before, after in zip(frames, frames[1:]):
        entries = []
        for left, right in zip(before["reserved_slots"], after["reserved_slots"]):
            if (left["raw_oam_bytes"], left["x_msb"], left["size_select"]) != (
                    right["raw_oam_bytes"], right["x_msb"], right["size_select"]):
                entries.append(left["slot"])
        changes.append({
            "from_checkpoint": before["checkpoint"],
            "to_checkpoint": after["checkpoint"],
            "changed_reserved_oam_shadow_slots": entries,
            "high_shadow_byte_changed":
                before["oam_high_shadow_1599"] != after["oam_high_shadow_1599"],
            "second_camera_raw_changed":
                before["second_camera_enable_0ddb_raw_word"] !=
                after["second_camera_enable_0ddb_raw_word"],
        })
    return {
        "schema": "qa08-split-oam-shadow-wram/1",
        "data_origin": "provided original native WRAM checkpoints (not authenticated here)",
        "checkpoints": frames,
        "transitions": changes,
        "actual_active_display_high_oam_captured": False,
        "source_obj_emission_or_final_raster_verified": False,
        "offscreen_sentinel_meaning_proven": False,
        "native_original_event_parity_proven": False,
        "remastered_racer_admission": False,
        "limits": (
            "WRAM $1599 is the shared high-OAM shadow for slots 96..99, "
            "not a P1 visible/hidden boolean. Raw $121B/$121D flags are "
            "separate. The guest can rewrite physical OAM[0x218] at "
            "scanlines 0 and 112; compare independent per-slot source "
            "PPU and final raster controls before any visibility claim."
        ),
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("dump_dir", type=Path)
    p.add_argument("--checkpoint", action="append", required=True)
    p.add_argument("--out", type=Path)
    a = p.parse_args()
    try:
        result = audit(a.dump_dir, a.checkpoint)
    except (ValueError, OSError) as exc:
        p.exit(2, f"invalid QA-08 source input: {exc}\n")
    content = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(content, encoding="utf-8")
    print(content, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
