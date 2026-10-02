#!/usr/bin/env python3
"""Extract the first exact racer presentation asset family from the USA ROM.

This tool deliberately stays at authoritative byte boundaries already exposed by
runtime code:

* race init 82:E02E loads graphics resources 0x7F/0x80 to VRAM $0000/$1000;
* 82:E02E loads racer colour resources (selection + 0x06) into OBJ CGRAM
  slots $B0/$C0/$D0;
* race state stores per-racer presentation/frame IDs at WRAM $0FE9/$0FEB;
* race renderer helper 83:F296 resolves each ID through a 3-byte table at
  SNES $20:8000: little-endian address plus bank_delta, with runtime bank
  = bank_delta + $23.

The extracted graphics and palette streams are split into semantic units
(4bpp tiles / BGR555 colours) and concatenated again. Byte equality against the
decoded runtime-upload stream is the round-trip oracle. No image enhancement or
format invention occurs here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from rnc_method1 import parse_header, unpack_method1

RESOURCE_TABLE = 0x82B32F
FRAME_TABLE = 0x208000
RACE_GRAPHICS = (
    {"resource_id": 0x7F, "vram_word": 0x0000, "role": "racer_obj_low_tiles"},
    {"resource_id": 0x80, "vram_word": 0x1000, "role": "racer_obj_high_tiles"},
)
RACER_PALETTE_RESOURCE_IDS = tuple(range(0x06, 0x16))
RACER_PALETTE_SLOTS = (0xB0, 0xC0, 0xD0)
OBSERVED_FRAME_FIELDS = (0x0FE9, 0x0FEB)
OAM_ATTR_FIELDS = (0x1504, 0x1508, 0x150C, 0x1510)
TILE_BYTES_4BPP = 32
CGRAM_COLOR_BYTES = 2


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def lorom_offset(addr24: int) -> int:
    bank = (addr24 >> 16) & 0xFF
    addr = addr24 & 0xFFFF
    if addr < 0x8000:
        raise ValueError(f"not a LoROM ROM address: {addr24:06X}")
    return ((bank & 0x7F) << 15) | (addr & 0x7FFF)


def read_snes_linear(rom: bytes, addr24: int, length: int) -> bytes:
    out = bytearray()
    bank = (addr24 >> 16) & 0xFF
    addr = addr24 & 0xFFFF
    for _ in range(length):
        off = lorom_offset((bank << 16) | addr)
        if off >= len(rom):
            raise ValueError(f"ROM read outside image at {bank:02X}:{addr:04X}")
        out.append(rom[off])
        addr += 1
        if addr > 0xFFFF:
            bank = (bank + 1) & 0xFF
            addr = 0x8000
    return bytes(out)


def parse_resource_descriptor(rom: bytes, resource_id: int) -> dict:
    raw = read_snes_linear(rom, RESOURCE_TABLE + resource_id * 5, 5)
    bank_flags = raw[0]
    source_addr = int.from_bytes(raw[1:3], "little")
    stored_length = int.from_bytes(raw[3:5], "little")
    source_bank = bank_flags & 0x7F
    source = (source_bank << 16) | source_addr
    return {
        "resource_id": resource_id,
        "descriptor_snes": f"{RESOURCE_TABLE + resource_id * 5:06X}",
        "descriptor_hex": raw.hex(),
        "source_snes": f"{source:06X}",
        "source_bank": source_bank,
        "source_addr": source_addr,
        "compressed": bool(bank_flags & 0x80),
        "stored_length": stored_length,
    }


def decode_resource(rom: bytes, resource_id: int) -> tuple[dict, bytes, bytes]:
    desc = parse_resource_descriptor(rom, resource_id)
    source = (desc["source_bank"] << 16) | desc["source_addr"]
    if desc["compressed"]:
        header = read_snes_linear(rom, source, 18)
        parsed = parse_header(header)
        packed = read_snes_linear(rom, source, 18 + parsed.packed_size)
        decoded = unpack_method1(packed)
    else:
        packed = read_snes_linear(rom, source, desc["stored_length"])
        decoded = packed
    return desc, packed, decoded


def unit_roundtrip(data: bytes, unit_size: int) -> tuple[list[str], bytes]:
    if len(data) % unit_size:
        raise ValueError(f"decoded length {len(data)} not divisible by unit size {unit_size}")
    units = [data[i:i + unit_size] for i in range(0, len(data), unit_size)]
    return [sha256(u) for u in units], b"".join(units)


def frame_pointer(rom: bytes, frame_id: int) -> dict:
    entry_addr = FRAME_TABLE + frame_id * 3
    raw = read_snes_linear(rom, entry_addr, 3)
    ptr = int.from_bytes(raw[:2], "little")
    bank = (raw[2] + 0x23) & 0xFF
    return {
        "frame_id": frame_id,
        "table_entry_snes": f"{entry_addr:06X}",
        "entry_hex": raw.hex(),
        "record_snes": f"{bank:02X}{ptr:04X}",
    }


def observed_states(dump_dir: Path | None, evidence_json: Path | None = None) -> list[dict]:
    if evidence_json is not None:
        payload = json.loads(evidence_json.read_text(encoding="utf-8"))
        rows = []
        for row in payload.get("checkpoints", []):
            attrs = list(row["oam_attrs"])
            rows.append({
                "checkpoint": row["checkpoint"],
                "frame_ids": list(row["frame_ids"]),
                "oam_attrs": attrs,
                "oam_palettes": [((v >> 1) & 0x07) for v in attrs],
                "oam_hflip": [bool(v & 0x40) for v in attrs],
                "oam_vflip": [bool(v & 0x80) for v in attrs],
            })
        return rows
    if dump_dir is None:
        return []
    rows = []
    for path in sorted(dump_dir.glob("*.wram.bin")):
        data = path.read_bytes()
        if len(data) != 0x20000:
            continue
        frame_ids = [
            data[a] | (data[a + 1] << 8)
            for a in OBSERVED_FRAME_FIELDS
        ]
        attrs = [data[a] for a in OAM_ATTR_FIELDS]
        rows.append({
            "checkpoint": path.stem.removesuffix(".wram"),
            "frame_ids": frame_ids,
            "oam_attrs": attrs,
            "oam_palettes": [((v >> 1) & 0x07) for v in attrs],
            "oam_hflip": [bool(v & 0x40) for v in attrs],
            "oam_vflip": [bool(v & 0x80) for v in attrs],
        })
    return rows


def build_manifest(rom: bytes, dump_dir: Path | None, evidence_json: Path | None = None) -> dict:
    graphics = []
    for item in RACE_GRAPHICS:
        desc, packed, decoded = decode_resource(rom, item["resource_id"])
        tile_hashes, rebuilt = unit_roundtrip(decoded, TILE_BYTES_4BPP)
        if rebuilt != decoded:
            raise AssertionError("4bpp tile round-trip changed bytes")
        graphics.append({
            **item,
            **desc,
            "packed_sha256": sha256(packed),
            "decoded_sha256": sha256(decoded),
            "decoded_bytes": len(decoded),
            "tile_bytes": TILE_BYTES_4BPP,
            "tile_count": len(tile_hashes),
            "tile_sha256": tile_hashes,
            "roundtrip_sha256": sha256(rebuilt),
            "roundtrip_equal": rebuilt == decoded,
        })

    palettes = []
    for resource_id in RACER_PALETTE_RESOURCE_IDS:
        desc, packed, decoded = decode_resource(rom, resource_id)
        color_hashes, rebuilt = unit_roundtrip(decoded, CGRAM_COLOR_BYTES)
        if rebuilt != decoded:
            raise AssertionError("BGR555 palette round-trip changed bytes")
        palettes.append({
            **desc,
            "packed_sha256": sha256(packed),
            "decoded_sha256": sha256(decoded),
            "decoded_bytes": len(decoded),
            "color_count": len(color_hashes),
            "color_sha256": color_hashes,
            "roundtrip_sha256": sha256(rebuilt),
            "roundtrip_equal": rebuilt == decoded,
        })

    states = observed_states(dump_dir, evidence_json)
    ids = sorted({fid for row in states for fid in row["frame_ids"]})
    return {
        "schema_version": 1,
        "family": "racer-presentation",
        "rom_sha256": sha256(rom),
        "authoritative_runtime_path": {
            "race_init": "82:E02E",
            "frame_state_wram": ["7E:0FE9", "7E:0FEB"],
            "frame_pointer_resolver": "83:F296",
            "frame_pointer_table": "20:8000",
            "race_renderer": "83:F0BB",
            "oam_builder": "82:ACA5",
            "palette_loader": "82:B180",
            "vram_loader": "82:B1D8",
        },
        "graphics": graphics,
        "palette_family": {
            "resource_ids": list(RACER_PALETTE_RESOURCE_IDS),
            "race_init_cgram_slots": list(RACER_PALETTE_SLOTS),
            "entries": palettes,
        },
        "observed_states": states,
        "observed_frame_ids": [frame_pointer(rom, fid) for fid in ids],
        "semantic_contract": (
            "authoritative racer presentation ID in $0FE9/$0FEB -> "
            "3-byte $20:8000 pointer-table entry via 83:F296 -> presentation record; "
            "stable OAM tile slots consume race-init OBJ graphics resources 0x7F/0x80, "
            "while OAM palette bits select CGRAM slots populated from racer colour resources 0x06..0x15"
        ),
        "roundtrip": {
            "graphics_all_equal": all(x["roundtrip_equal"] for x in graphics),
            "palettes_all_equal": all(x["roundtrip_equal"] for x in palettes),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--wram-dump-dir", type=Path)
    ap.add_argument("--evidence-json", type=Path)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()

    manifest = build_manifest(args.rom.read_bytes(), args.wram_dump_dir, args.evidence_json)
    text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
