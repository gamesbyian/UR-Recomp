#!/usr/bin/env python3
"""Extract and round-trip a small racer presentation family from the USA ROM.

This tool deliberately stays at the exact-original boundary. It decodes the
ROM-owned racer presentation pointer table used by 83:F296, losslessly
round-trips selected frame records, decodes race palette assets through the
82:B32F five-byte asset table, and emits hashes/metadata rather than committing
copyrighted binary payloads.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Iterable

FRAME_TABLE_BANK = 0x20
FRAME_TABLE_ADDR = 0x8000
FRAME_ENTRY_SIZE = 3
FRAME_SOURCE_BANK_BASE = 0x23

PALETTE_TABLE_BANK = 0x82
PALETTE_TABLE_ADDR = 0xB32F
PALETTE_ENTRY_SIZE = 5
TILE_BYTES_4BPP = 32
RACER_GRAPHICS_RESOURCES = (
    (0x7F, 0x0000, "racer_obj_low_tiles"),
    (0x80, 0x1000, "racer_obj_high_tiles"),
)

MASK_BITS = (0x04, 0x08, 0x10, 0x20, 0x40, 0x80)

# Promoted from the retained MesenCE ordinary-2P evidence run 36948109734.
OBSERVED_STATES = (
    ("two-player-race-1220", 1220, 1, 0x0542, 0x66, 0, 0x06, 0xB0),
    ("two-player-race-1220", 1220, 2, 0x0540, 0x68, 1, 0x07, 0xC0),
    ("two-player-race-1420", 1420, 1, 0x057E, 0x66, 0, 0x06, 0xB0),
    ("two-player-race-1420", 1420, 2, 0x0544, 0x68, 1, 0x07, 0xC0),
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def lorom_offset(bank: int, addr: int) -> int:
    if not 0 <= bank <= 0xFF:
        raise ValueError(f"bank out of range: {bank:#x}")
    if not 0x8000 <= addr <= 0xFFFF:
        raise ValueError(f"LoROM address must be >= $8000, got {bank:02X}:{addr:04X}")
    return (bank & 0x7F) * 0x8000 + (addr & 0x7FFF)


def snes(bank: int, addr: int) -> str:
    return f"{bank:02X}:{addr:04X}"


@dataclass(frozen=True)
class FramePointer:
    frame_id: int
    entry: bytes
    source_bank: int
    source_addr: int

    def repack(self) -> bytes:
        delta = self.source_bank - FRAME_SOURCE_BANK_BASE
        if not 0 <= delta <= 0xFF:
            raise ValueError("frame source bank cannot be represented by 83:F296")
        return self.source_addr.to_bytes(2, "little") + bytes((delta,))


@dataclass(frozen=True)
class FrameRecord:
    header: bytes
    packed_words: tuple[bytes, ...]
    renderer_prefix_length: int

    def repack(self) -> bytes:
        return self.header + b"".join(self.packed_words)


@dataclass(frozen=True)
class PaletteEntry:
    asset_id: int
    entry: bytes
    source_bank: int
    source_addr: int
    length: int
    compressed_flag: bool

    def repack(self) -> bytes:
        bank_byte = self.source_bank | (0x80 if self.compressed_flag else 0)
        return bytes((bank_byte,)) + self.source_addr.to_bytes(2, "little") + self.length.to_bytes(2, "little")


def frame_pointer(rom: bytes, frame_id: int) -> FramePointer:
    if frame_id < 0:
        raise ValueError("negative frame id")
    table_addr = FRAME_TABLE_ADDR + frame_id * FRAME_ENTRY_SIZE
    if table_addr + 2 > 0xFFFF:
        raise ValueError(f"frame id {frame_id:#x} exceeds the 83:F296 table bank")
    off = lorom_offset(FRAME_TABLE_BANK, table_addr)
    entry = rom[off:off + FRAME_ENTRY_SIZE]
    if len(entry) != FRAME_ENTRY_SIZE:
        raise ValueError("truncated frame pointer table")
    source_addr = int.from_bytes(entry[:2], "little")
    source_bank = entry[2] + FRAME_SOURCE_BANK_BASE
    ptr = FramePointer(frame_id, entry, source_bank, source_addr)
    if ptr.repack() != entry:
        raise AssertionError("frame pointer round-trip failed")
    return ptr


def infer_record_length(rom: bytes, frame_id: int, ptr: FramePointer) -> tuple[int, str]:
    """Use the next table entry as the authoritative packed-record boundary.

    The observed family is expected to be packed monotonically. We also report
    the structural minimum implied by the four-byte header and mask words.
    """
    nxt = frame_pointer(rom, frame_id + 1)
    if nxt.source_bank != ptr.source_bank or nxt.source_addr <= ptr.source_addr:
        raise ValueError(
            f"frame {frame_id:#06x}: next entry is not a monotonic same-bank boundary "
            f"({snes(ptr.source_bank, ptr.source_addr)} -> {snes(nxt.source_bank, nxt.source_addr)})"
        )
    return nxt.source_addr - ptr.source_addr, snes(nxt.source_bank, nxt.source_addr)


def decode_frame_record(raw: bytes) -> FrameRecord:
    if len(raw) < 4:
        raise ValueError("racer presentation record shorter than four-byte header")
    if (len(raw) - 4) % 2:
        raise ValueError("racer presentation stream tail is not 16-bit aligned")
    header = raw[:4]
    renderer_prefix_length = 4 + 2 * sum(bool(header[0] & bit) for bit in MASK_BITS)
    if renderer_prefix_length > len(raw):
        raise ValueError("header-selected renderer prefix exceeds table-bounded frame stream")
    words = tuple(raw[i:i + 2] for i in range(4, len(raw), 2))
    record = FrameRecord(header, words, renderer_prefix_length)
    if record.repack() != raw:
        raise AssertionError("frame record round-trip failed")
    return record


def palette_entry(rom: bytes, asset_id: int) -> PaletteEntry:
    addr = PALETTE_TABLE_ADDR + asset_id * PALETTE_ENTRY_SIZE
    if addr + 4 > 0xFFFF:
        raise ValueError("palette asset id exceeds table bank")
    off = lorom_offset(PALETTE_TABLE_BANK, addr)
    entry = rom[off:off + PALETTE_ENTRY_SIZE]
    if len(entry) != PALETTE_ENTRY_SIZE:
        raise ValueError("truncated palette table")
    bank_byte = entry[0]
    decoded = PaletteEntry(
        asset_id=asset_id,
        entry=entry,
        source_bank=bank_byte & 0x7F,
        source_addr=int.from_bytes(entry[1:3], "little"),
        length=int.from_bytes(entry[3:5], "little"),
        compressed_flag=bool(bank_byte & 0x80),
    )
    if decoded.repack() != entry:
        raise AssertionError("palette table round-trip failed")
    return decoded


def split_4bpp_tiles(payload: bytes) -> tuple[bytes, ...]:
    if len(payload) % TILE_BYTES_4BPP:
        raise ValueError("4bpp graphics payload length must be divisible by 32")
    tiles = tuple(
        payload[i:i + TILE_BYTES_4BPP]
        for i in range(0, len(payload), TILE_BYTES_4BPP)
    )
    if b"".join(tiles) != payload:
        raise AssertionError("4bpp graphics round-trip failed")
    return tiles


def decode_bgr555(payload: bytes) -> list[dict[str, int]]:
    if len(payload) % 2:
        raise ValueError("BGR555 palette payload length must be even")
    colors = []
    for i in range(0, len(payload), 2):
        word = int.from_bytes(payload[i:i + 2], "little")
        colors.append({
            "word": word,
            "r5": word & 0x1F,
            "g5": (word >> 5) & 0x1F,
            "b5": (word >> 10) & 0x1F,
        })
    rebuilt = b"".join(c["word"].to_bytes(2, "little") for c in colors)
    if rebuilt != payload:
        raise AssertionError("palette BGR555 round-trip failed")
    return colors


def extract_frame(rom: bytes, frame_id: int) -> dict:
    ptr = frame_pointer(rom, frame_id)
    length, next_boundary = infer_record_length(rom, frame_id, ptr)
    off = lorom_offset(ptr.source_bank, ptr.source_addr)
    raw = rom[off:off + length]
    if len(raw) != length:
        raise ValueError("truncated racer presentation record")
    record = decode_frame_record(raw)
    return {
        "frame_id": frame_id,
        "frame_id_hex": f"0x{frame_id:04X}",
        "table_entry_snes": snes(FRAME_TABLE_BANK, FRAME_TABLE_ADDR + frame_id * FRAME_ENTRY_SIZE),
        "table_entry_rom_offset": lorom_offset(FRAME_TABLE_BANK, FRAME_TABLE_ADDR + frame_id * FRAME_ENTRY_SIZE),
        "table_entry_hex": ptr.entry.hex(),
        "table_entry_sha256": sha256(ptr.entry),
        "source_snes": snes(ptr.source_bank, ptr.source_addr),
        "source_rom_offset": off,
        "next_frame_boundary_snes": next_boundary,
        "record_length": length,
        "record_sha256": sha256(raw),
        "record_header_hex": record.header.hex(),
        "mask": record.header[0] & 0xFC,
        "renderer_prefix_length": record.renderer_prefix_length,
        "packed_word_count": len(record.packed_words),
        "roundtrip_equal": record.repack() == raw and ptr.repack() == ptr.entry,
    }


def extract_graphics_resource(rom: bytes, asset_id: int, vram_word: int, role: str) -> dict:
    ent = palette_entry(rom, asset_id)
    if ent.compressed_flag:
        raise ValueError(
            f"graphics asset {asset_id:#x} uses the compressed/special loader path; "
            "recover that smallest missing transform before claiming an exact round trip"
        )
    off = lorom_offset(ent.source_bank, ent.source_addr)
    payload = rom[off:off + ent.length]
    if len(payload) != ent.length:
        raise ValueError("truncated graphics payload")
    tiles = split_4bpp_tiles(payload)
    return {
        "asset_id": asset_id,
        "asset_id_hex": f"0x{asset_id:02X}",
        "role": role,
        "vram_word": vram_word,
        "vram_word_hex": f"0x{vram_word:04X}",
        "table_entry_snes": snes(PALETTE_TABLE_BANK, PALETTE_TABLE_ADDR + asset_id * PALETTE_ENTRY_SIZE),
        "table_entry_hex": ent.entry.hex(),
        "table_entry_sha256": sha256(ent.entry),
        "source_snes": snes(ent.source_bank, ent.source_addr),
        "source_rom_offset": off,
        "length": ent.length,
        "tile_format": "SNES 4bpp planar",
        "tile_bytes": TILE_BYTES_4BPP,
        "tile_count": len(tiles),
        "payload_sha256": sha256(payload),
        "roundtrip_equal": ent.repack() == ent.entry and b"".join(tiles) == payload,
    }


def extract_palette(rom: bytes, asset_id: int, cgram_addr: int) -> dict:
    ent = palette_entry(rom, asset_id)
    if ent.compressed_flag:
        raise ValueError(
            f"palette asset {asset_id:#x} uses the compressed/special loader path; "
            "the smallest missing transform must be recovered before exact payload extraction"
        )
    off = lorom_offset(ent.source_bank, ent.source_addr)
    payload = rom[off:off + ent.length]
    if len(payload) != ent.length:
        raise ValueError("truncated palette payload")
    colors = decode_bgr555(payload)
    return {
        "asset_id": asset_id,
        "asset_id_hex": f"0x{asset_id:02X}",
        "cgram_start": cgram_addr,
        "cgram_start_hex": f"0x{cgram_addr:02X}",
        "table_entry_snes": snes(PALETTE_TABLE_BANK, PALETTE_TABLE_ADDR + asset_id * PALETTE_ENTRY_SIZE),
        "table_entry_hex": ent.entry.hex(),
        "table_entry_sha256": sha256(ent.entry),
        "source_snes": snes(ent.source_bank, ent.source_addr),
        "source_rom_offset": off,
        "length": ent.length,
        "payload_sha256": sha256(payload),
        "bgr555_words": [f"0x{c['word']:04X}" for c in colors],
        "roundtrip_equal": ent.repack() == ent.entry
        and b"".join(c["word"].to_bytes(2, "little") for c in colors) == payload,
    }


def build_manifest(rom: bytes) -> dict:
    unique_frames = sorted({row[3] for row in OBSERVED_STATES})
    frames = [extract_frame(rom, frame_id) for frame_id in unique_frames]
    graphics = [
        extract_graphics_resource(rom, asset_id, vram_word, role)
        for asset_id, vram_word, role in RACER_GRAPHICS_RESOURCES
    ]
    palettes = [extract_palette(rom, 0x06, 0xB0), extract_palette(rom, 0x07, 0xC0)]
    observed = []
    for checkpoint, frame, player, frame_id, attr, color_index, palette_asset, cgram in OBSERVED_STATES:
        observed.append({
            "checkpoint": checkpoint,
            "emulator_frame": frame,
            "player": player,
            "authoritative_frame_state": "$0FE9" if player == 1 else "$0FEB",
            "frame_id": f"0x{frame_id:04X}",
            "oam_attribute": f"0x{attr:02X}",
            "oam_palette_number": (attr >> 1) & 0x07,
            "cgram_start": f"0x{cgram:02X}",
            "player_color_selector": "$017D" if player == 1 else "$017F",
            "player_color_index": color_index,
            "palette_asset_formula": "0x06 + player_color_index",
            "palette_asset_id": f"0x{palette_asset:02X}",
        })
    return {
        "schema_version": 1,
        "family": "ordinary-race-racer-presentation",
        "rom_sha256": sha256(rom),
        "evidence": {
            "runtime_fixture": "MesenCE ordinary 2P evidence",
            "workflow_run": 36948109734,
            "frame_state_chain": [
                "$0FE9/$0FEB persistent racer presentation IDs",
                "83:F0BB copies IDs into render state",
                "83:F296 indexes 3-byte pointer table at 20:8000",
                "83:F2BB consumes selected presentation records",
                "82:ACA5 builds racer OAM using stable tile slots and state-dependent attributes",
            ],
            "graphics_state_chain": [
                "82:E02E loads asset 0x7F to VRAM $0000 and asset 0x80 to VRAM $1000",
                "82:ACA5 emits stable racer OAM tile slots 00/08/80/88",
                "SNES 4bpp 32-byte tile addressing places those slots inside the two exact loaded ranges",
                "82:B1D8 resolves both assets through the five-byte table at 82:B32F",
            ],
            "palette_state_chain": [
                "$017D/$017F player color selectors are 0/1 in retained fixture WRAM",
                "80:99FA/80:9A01 mirror selectors to $770748/$770749",
                "82:DDD8/82:DDFC load asset 0x06+selector into CGRAM B0/C0",
                "ordinary fixture OAM attributes select OBJ palettes 3/4 => CGRAM B0/C0",
                "82:B180 resolves palette assets through 5-byte table at 82:B32F",
            ],
        },
        "observed_states": observed,
        "frames": frames,
        "graphics": graphics,
        "palettes": palettes,
        "roundtrip": {
            "frame_pointer_entries": all(x["roundtrip_equal"] for x in frames),
            "frame_records": all(x["roundtrip_equal"] for x in frames),
            "graphics_entries_and_4bpp_payloads": all(x["roundtrip_equal"] for x in graphics),
            "palette_entries_and_bgr555_payloads": all(x["roundtrip_equal"] for x in palettes),
        },
        "replacement_key": {
            "authoritative_state": "$0FE9/$0FEB",
            "semantic_frame_identity": "16-bit racer presentation ID",
            "source_lookup": "20:8000 + frame_id*3 via 83:F296",
            "graphics_identity": "race-init OBJ assets 0x7F/0x80 at VRAM $0000/$1000, addressed by stable racer OAM tile slots",
            "palette_identity": "0x06 + player color selector, loaded by 82:DDD8/82:DDFC",
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    rom = args.rom.read_bytes()
    manifest = build_manifest(rom)
    text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
