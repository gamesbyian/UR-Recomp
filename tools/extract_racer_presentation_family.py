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
import struct
import zlib
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
RASTER_WIDTH = 64
RASTER_HEIGHT = 64
RASTER_TILE_OFFSET = (1, 0)
RACER_PALETTE_RESOURCE_IDS = tuple(range(0x06, 0x16))
RACER_GRAPHICS_RESOURCES = (
    (0x7F, 0x0000, "racer_obj_low_tiles"),
    (0x80, 0x1000, "racer_obj_high_tiles"),
)

MASK_BITS = (0x04, 0x08, 0x10, 0x20, 0x40, 0x80)
OCCUPANCY_BITS = tuple((byte, bit) for byte in range(4) for bit in range(7, -1, -1) if not (byte == 3 and bit < 2))

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


def decode_piece_mapping(record: FrameRecord) -> list[dict]:
    occupied = []
    for scan_index, (byte_index, bit_in_byte) in enumerate(OCCUPANCY_BITS):
        if record.header[byte_index] & (1 << bit_in_byte):
            occupied.append((scan_index, byte_index, bit_in_byte))
    if len(occupied) != len(record.packed_words):
        raise ValueError(
            f"30-cell occupancy count {len(occupied)} != packed words {len(record.packed_words)}"
        )
    pieces = []
    for word_index, ((scan_index, byte_index, bit_in_byte), raw) in enumerate(zip(occupied, record.packed_words)):
        word = int.from_bytes(raw, "little")
        pieces.append({
            "word_index": word_index,
            "occupancy_scan_index": scan_index,
            "major_slot": scan_index // 6,
            "minor_slot": scan_index % 6,
            "header_byte": byte_index,
            "header_bit_msb_first": bit_in_byte,
            "global_lsb_bit": byte_index * 8 + bit_in_byte,
            "word_hex": f"0x{word:04X}",
            "word_high_byte": word >> 8,
            "word_low_byte": word & 0xFF,
            "staged_1645_value": f"0x{(0x8000 | ((word >> 8) << 5)) & 0xFFFF:04X}",
            "staged_15a1_value": f"0x{0x27 + ((word & 0x00FC) >> 2):04X}",
            "low2_renderer_ignored_value": word & 0x03,
        })
    return pieces


def census_record_structure(rom: bytes) -> dict:
    max_id = ((0x10000 - FRAME_TABLE_ADDR) // FRAME_ENTRY_SIZE) - 2
    comparable = matches = reserved_nonzero = 0
    for frame_id in range(max_id + 1):
        try:
            ptr = frame_pointer(rom, frame_id)
            nxt = frame_pointer(rom, frame_id + 1)
        except (ValueError, IndexError):
            continue
        if ptr.source_bank != nxt.source_bank:
            continue
        if ptr.source_addr < 0x8000 or nxt.source_addr < 0x8000:
            continue
        length = nxt.source_addr - ptr.source_addr
        if length < 4 or length > 68 or (length - 4) % 2:
            continue
        try:
            off = lorom_offset(ptr.source_bank, ptr.source_addr)
            header = rom[off:off + 4]
        except (ValueError, IndexError):
            continue
        if len(header) != 4:
            continue
        occupied = sum(
            bool(header[byte] & (1 << bit))
            for byte, bit in OCCUPANCY_BITS
        )
        words = (length - 4) // 2
        comparable += 1
        matches += occupied == words
        reserved_nonzero += bool(header[3] & 0x03)
    return {
        "comparable_monotonic_records": comparable,
        "matches_30_cell_popcount": matches,
        "reserved_low2_nonzero_records": reserved_nonzero,
    }


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



def decode_4bpp_tile(data: bytes) -> list[list[int]]:
    """Decode one SNES planar 4bpp tile to 8x8 palette indices."""
    if len(data) != TILE_BYTES_4BPP:
        raise ValueError("SNES 4bpp tile must be exactly 32 bytes")
    rows: list[list[int]] = []
    for y in range(8):
        p0, p1 = data[y * 2:y * 2 + 2]
        p2, p3 = data[16 + y * 2:16 + y * 2 + 2]
        row = []
        for x in range(8):
            bit = 7 - x
            row.append(
                ((p0 >> bit) & 1)
                | (((p1 >> bit) & 1) << 1)
                | (((p2 >> bit) & 1) << 2)
                | (((p3 >> bit) & 1) << 3)
            )
        rows.append(row)
    return rows


def packed_word_source(word: int) -> tuple[int, int]:
    """Recover the exact 32-byte DMA source selected by 83:F20F..F227.

    #216 proves $15A1 supplies DMA source bank and $1645 supplies source
    address. Packed low bits 1..0 are intentionally absent from this mapping.
    """
    source_addr = 0x8000 | (((word >> 8) & 0xFF) << 5)
    source_bank = 0x27 + (((word & 0x00FC) >> 2) & 0x3F)
    return source_bank, source_addr


def piece_source_tile(rom: bytes, word: int) -> tuple[bytes, dict]:
    bank, addr = packed_word_source(word)
    off = lorom_offset(bank, addr)
    raw = rom[off:off + TILE_BYTES_4BPP]
    if len(raw) != TILE_BYTES_4BPP:
        raise ValueError(f"piece tile source {snes(bank, addr)} is outside ROM")
    return raw, {
        "source_snes": snes(bank, addr),
        "source_rom_offset": off,
        "source_length": TILE_BYTES_4BPP,
        "source_sha256": sha256(raw),
    }


def bgr555_rgba(word: int, transparent: bool = False) -> tuple[int, int, int, int]:
    r5 = word & 0x1F
    g5 = (word >> 5) & 0x1F
    b5 = (word >> 10) & 0x1F
    expand = lambda v: (v << 3) | (v >> 2)
    return (expand(r5), expand(g5), expand(b5), 0 if transparent else 255)


def rgba_palette(rom: bytes, asset_id: int) -> list[tuple[int, int, int, int]]:
    ent = palette_entry(rom, asset_id)
    if ent.compressed_flag:
        raise ValueError("racer palette unexpectedly uses compressed loader path")
    off = lorom_offset(ent.source_bank, ent.source_addr)
    payload = rom[off:off + ent.length]
    colors = decode_bgr555(payload)
    if len(colors) < 16:
        raise ValueError("racer palette has fewer than 16 colors")
    return [bgr555_rgba(c["word"], transparent=(i == 0)) for i, c in enumerate(colors[:16])]


def rasterize_frame_rgba(
    rom: bytes,
    frame: dict,
    palette_asset_id: int,
    *,
    hflip: bool = False,
    vflip: bool = False,
) -> bytes:
    """Rasterize one frame in its 64x64 large-OBJ local coordinate system."""
    palette = rgba_palette(rom, palette_asset_id)
    pixels = bytearray(RASTER_WIDTH * RASTER_HEIGHT * 4)
    ox, oy = RASTER_TILE_OFFSET
    for piece in frame["pieces"]:
        raw, _ = piece_source_tile(rom, int(piece["word_hex"], 16))
        tile = decode_4bpp_tile(raw)
        gx = ox + piece["minor_slot"]
        gy = oy + piece["major_slot"]
        for ty, row in enumerate(tile):
            for tx, ci in enumerate(row):
                x = gx * 8 + tx
                y = gy * 8 + ty
                if hflip:
                    x = RASTER_WIDTH - 1 - x
                if vflip:
                    y = RASTER_HEIGHT - 1 - y
                q = (y * RASTER_WIDTH + x) * 4
                pixels[q:q + 4] = bytes(palette[ci])
    return bytes(pixels)


def encode_png_rgba(width: int, height: int, rgba: bytes) -> bytes:
    """Deterministic dependency-free PNG encoder for 8-bit RGBA."""
    if len(rgba) != width * height * 4:
        raise ValueError("RGBA payload length does not match dimensions")
    sig = b"\x89PNG\r\n\x1a\n"
    def chunk(kind: bytes, payload: bytes) -> bytes:
        body = kind + payload
        return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)
    rows = b"".join(
        b"\x00" + rgba[y * width * 4:(y + 1) * width * 4]
        for y in range(height)
    )
    return (
        sig
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(rows, 9))
        + chunk(b"IEND", b"")
    )


def frame_raster_metadata(rom: bytes, frame: dict, palette_asset_id: int) -> dict:
    rgba = rasterize_frame_rgba(rom, frame, palette_asset_id)
    png = encode_png_rgba(RASTER_WIDTH, RASTER_HEIGHT, rgba)
    return {
        "palette_asset_id": f"0x{palette_asset_id:02X}",
        "dimensions": [RASTER_WIDTH, RASTER_HEIGHT],
        "origin": [0, 0],
        "occupancy_tile_offset": list(RASTER_TILE_OFFSET),
        "stored_orientation": {"hflip": False, "vflip": False},
        "rgba_sha256": sha256(rgba),
        "png_sha256": sha256(png),
        "transparent_palette_index": 0,
    }


def confident_frame_ids(rom: bytes) -> list[int]:
    """Enumerate records satisfying the closed 30-cell contract and valid tile sources."""
    max_id = ((0x10000 - FRAME_TABLE_ADDR) // FRAME_ENTRY_SIZE) - 2
    out = []
    for frame_id in range(max_id + 1):
        try:
            frame = extract_frame(rom, frame_id)
            for piece in frame["pieces"]:
                piece_source_tile(rom, int(piece["word_hex"], 16))
        except (ValueError, IndexError):
            continue
        out.append(frame_id)
    return out


def emit_frame_images(
    rom: bytes,
    frame_ids: Iterable[int],
    output_dir: Path,
    palette_asset_ids: Iterable[int] = (0x06,),
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = []
    rom_digest = sha256(rom)
    palette_asset_ids = tuple(palette_asset_ids)
    for frame_id in frame_ids:
        frame = extract_frame(rom, frame_id)
        for palette_asset_id in palette_asset_ids:
            rgba = rasterize_frame_rgba(rom, frame, palette_asset_id)
            png = encode_png_rgba(RASTER_WIDTH, RASTER_HEIGHT, rgba)
            name = f"frame-{frame_id:04x}-pal{palette_asset_id:02x}.png"
            path = output_dir / name
            path.write_bytes(png)
            manifest.append({
                "frame_id": f"0x{frame_id:04X}",
                "palette_asset_id": f"0x{palette_asset_id:02X}",
                "path": name,
                "png_sha256": sha256(png),
                "rgba_sha256": sha256(rgba),
                "dimensions": [RASTER_WIDTH, RASTER_HEIGHT],
                "origin": [0, 0],
                "occupancy_header": frame["record_header_hex"],
                "source_record": {
                    "snes": frame["source_snes"],
                    "rom_offset": frame["source_rom_offset"],
                    "sha256": frame["record_sha256"],
                },
                "rom_sha256": rom_digest,
                "orientation": {"hflip": False, "vflip": False},
                "uncertainty": None,
            })
    return {
        "schema_version": 2,
        "family": "ordinary-race-racer-presentation-contract-compatible-corpus",
        "rom_sha256": rom_digest,
        "confidence_basis": [
            "monotonic same-bank frame boundary",
            "four-byte 30-cell occupancy header",
            "record length equals header popcount-derived packed-word count",
            "every packed word resolves through the #216 DMA-source transform to a complete 32-byte ROM tile",
            "stable first-family lattice placement at object tile offset (1,0)",
        ],
        "palette_family": {
            "authority": "tools/extract_racer_asset_roundtrip.py",
            "available_resource_ids": [f"0x{x:02X}" for x in RACER_PALETTE_RESOURCE_IDS],
            "emitted_resource_ids": [f"0x{x:02X}" for x in palette_asset_ids],
        },
        "orientation": {
            "canonical_images": "stored orientation",
            "runtime_rule": "apply OAM H/V flip afterward to the complete 64x64 object-local raster",
        },
        "count": len(manifest),
        "images": manifest,
    }



def extract_frame(rom: bytes, frame_id: int) -> dict:
    ptr = frame_pointer(rom, frame_id)
    length, next_boundary = infer_record_length(rom, frame_id, ptr)
    off = lorom_offset(ptr.source_bank, ptr.source_addr)
    raw = rom[off:off + length]
    if len(raw) != length:
        raise ValueError("truncated racer presentation record")
    record = decode_frame_record(raw)
    pieces = decode_piece_mapping(record)
    for piece in pieces:
        _, provenance = piece_source_tile(rom, int(piece["word_hex"], 16))
        piece["source_tile"] = provenance
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
        "occupancy_layout": {
            "major_slots": 5,
            "minor_slots": 6,
            "scan_order": "header bytes in storage order, MSB-first; byte3 bits1..0 excluded",
            "reserved_zero_bits": ["byte3.bit1", "byte3.bit0"],
            "reserved_zero_value": record.header[3] & 0x03,
        },
        "pieces": pieces,
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
    for frame in frames:
        frame["raster_exports"] = [frame_raster_metadata(rom, frame, p) for p in (0x06, 0x07)]
    graphics = [
        extract_graphics_resource(rom, asset_id, vram_word, role)
        for asset_id, vram_word, role in RACER_GRAPHICS_RESOURCES
    ]
    palettes = [extract_palette(rom, 0x06, 0xB0), extract_palette(rom, 0x07, 0xC0)]
    observed = []
    for checkpoint, frame, player, frame_id, attr, color_index, palette_asset, cgram in OBSERVED_STATES:
        observed_frame = next(x for x in frames if x["frame_id"] == frame_id)
        hflip = bool(attr & 0x40)
        vflip = bool(attr & 0x80)
        presented_rgba = rasterize_frame_rgba(
            rom, observed_frame, palette_asset, hflip=hflip, vflip=vflip
        )
        presented_png = encode_png_rgba(RASTER_WIDTH, RASTER_HEIGHT, presented_rgba)
        observed.append({
            "checkpoint": checkpoint,
            "emulator_frame": frame,
            "player": player,
            "authoritative_frame_state": "$0FE9" if player == 1 else "$0FEB",
            "frame_id": f"0x{frame_id:04X}",
            "oam_attribute": f"0x{attr:02X}",
            "oam_palette_number": (attr >> 1) & 0x07,
            "oam_hflip": hflip,
            "oam_vflip": vflip,
            "cgram_start": f"0x{cgram:02X}",
            "player_color_selector": "$017D" if player == 1 else "$017F",
            "player_color_index": color_index,
            "palette_asset_formula": "0x06 + player_color_index",
            "palette_asset_id": f"0x{palette_asset:02X}",
            "presented_raster": {
                "dimensions": [RASTER_WIDTH, RASTER_HEIGHT],
                "origin": [0, 0],
                "rgba_sha256": sha256(presented_rgba),
                "png_sha256": sha256(presented_png),
                "orientation_rule": "OAM H/V flip applied to complete 64x64 object-local raster",
            },
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
        "piece_semantics": {
            "status": "mechanically_recovered_for_observed_family_with_retained_spatial_binding",
            "occupancy_shape": "5 major slots x 6 minor slots",
            "ordering": "30 occupancy positions scan MSB-first by header byte; each set position consumes the next packed 16-bit word",
            "renderer_proof": [
                "83:F338..F3C6 and 83:F441..F4CF reshape the header into six-bit masks",
                "83:F1AE initializes the construction mask to $8000 and 83:F1DC..F270 shifts it once per slot",
                "occupied slots read one 16-bit word and increment the selected frame pointer by two bytes",
                "83:F20F..F227 derives staging values from the packed word high byte and low-byte bits7..2",
                "83:F20F stores the full word in $2A; the only later $2A read at 83:F21D is immediately masked by AND #$00FC, so packed low-byte bits1..0 do not affect this renderer consumer",
            ],
            "packed_word_fields": {
                "high_byte": "83:F20F..F21A -> $1645,Y = $8000 | (high_byte << 5)",
                "low_byte_bits_7_2": "83:F21D..F227 -> $15A1,Y = $0027 + ((low_byte & $FC) >> 2)",
                "low_byte_bits_1_0": "renderer-ignored in the bounded 83:F190..F290 consumer; producer-side meaning remains unresolved",
            },
            "corpus_check": {
                **census_record_structure(rom),
                "evidence_workflow_run": 36973753703,
            },
            "oam_binding": {
                "layering": "packed records populate 8x8 racer subtile content before later 82:ACA5 OAM composition",
                "retained_reference_run": 36943103609,
                "obj_mode": "OBSEL 0x83 => 16x16 small / 64x64 large objects",
                "spatial_layout": {
                    "occupancy_rectangle_in_large_obj_tiles": [1, 0, 6, 5],
                    "major_slot_semantics": "stored 8x8 tile row",
                    "minor_slot_semantics": "stored 8x8 tile column",
                    "orientation_rule": "OAM H/V flip is applied after packed-cell placement to obtain presented coordinates",
                    "exact_persistent_id_bindings": 8,
                    "retained_snapshots_inspected": 9,
                    "all_exact_and_nearby_unique_bindings_at_same_offset": True,
                    "evidence_workflow_run": 36978560724,
                },
                "checkpoints": {
                    "two-player-race-1220": "persistent P1/P2 IDs 0x0541/0x0540; both exact occupancy matches use 5x6 offset (1,0) inside stable 64x64 OAM slots",
                    "two-player-race-1420": "persistent P2 ID 0x0544 exactly matches the same 5x6 offset (1,0); P1 renderer/persistent timing differs at this endpoint",
                },
            },
        },
        "rasterization": {
            "status": "automated_first_family_original_art_extraction",
            "canvas": {"width": RASTER_WIDTH, "height": RASTER_HEIGHT, "origin": [0, 0]},
            "occupancy_tile_offset": list(RASTER_TILE_OFFSET),
            "source_tile_rule": "$1645/$15A1 DMA source recovered in PR #216: address=$8000|(high_byte<<5), bank=$27+((low_byte&$FC)>>2)",
            "palette_assets": ["0x06", "0x07"],
            "transparent_palette_index": 0,
            "oam_orientation": "canonical exports are stored orientation; observed OAM H/V flips apply afterward to the full 64x64 object-local raster",
            "bulk_policy": "use --all-confident --emit-images; bulk PNGs are workflow artifacts, not committed",
        },
        "replacement_key": {
            "authoritative_state": "$0FE9/$0FEB",
            "semantic_frame_identity": "16-bit racer presentation ID",
            "source_lookup": "20:8000 + frame_id*3 via 83:F296",
            "graphics_identity": "race-init OBJ assets 0x7F/0x80 at VRAM $0000/$1000, addressed by stable racer OAM tile slots",
            "palette_identity": "0x06 + player color selector, loaded by 82:DDD8/82:DDFC",
        },
    }


def parse_palette_assets(spec: str) -> tuple[int, ...]:
    if spec.strip().lower() == "all":
        return RACER_PALETTE_RESOURCE_IDS
    out = []
    for token in spec.split(","):
        value = int(token.strip(), 0)
        if value not in RACER_PALETTE_RESOURCE_IDS:
            raise ValueError(
                f"palette asset {value:#x} is outside established racer palette family 0x06..0x15"
            )
        out.append(value)
    if not out:
        raise ValueError("at least one palette asset is required")
    return tuple(dict.fromkeys(out))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--emit-images", type=Path, help="write deterministic transparent PNGs")
    ap.add_argument("--all-confident", action="store_true", help="rasterize every record satisfying the closed first-family contract")
    ap.add_argument("--bulk-manifest", type=Path, help="manifest for --emit-images output")
    ap.add_argument(
        "--palette-assets",
        default="0x06",
        help="comma-separated racer palette resource IDs, or 'all' (default: 0x06)",
    )
    args = ap.parse_args()
    rom = args.rom.read_bytes()
    manifest = build_manifest(rom)
    text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    if args.emit_images:
        ids = confident_frame_ids(rom) if args.all_confident else sorted({row[3] for row in OBSERVED_STATES})
        bulk = emit_frame_images(
            rom, ids, args.emit_images, parse_palette_assets(args.palette_assets)
        )
        if args.bulk_manifest:
            args.bulk_manifest.parent.mkdir(parents=True, exist_ok=True)
            args.bulk_manifest.write_text(json.dumps(bulk, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"emitted {bulk['count']} PNGs from {len(ids)} confident frames", file=__import__("sys").stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
