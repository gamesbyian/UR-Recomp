#!/usr/bin/env python3
"""Reconcile fixed-offset TCRF Uniracers claims against a canonical ROM."""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import zlib
from pathlib import Path

ROM_SIZE = 0x200000
VERSION_OFFSET = 0x18000
BUILD_DATE_OFFSET = 0x0541
COMBO_SET_OFFSET = 0x0BD679
COMBO_REGION_START = COMBO_SET_OFFSET - 0x800
COMBO_REGION_SIZE = 0x900
TRACK_TYPE_TABLE_CPU = (0x83, 0xA254)
TRACK_TYPE_TABLE_LENGTH = 50
NORMAL_TRACK_COUNT = 45
NORMAL_SELECTOR_WRAP_CPU = (0x80, 0xAE8C)
TRACK_TYPE_LOAD_CPU = (0x83, 0x9996)
ANTI_PIRACY_COMPARE_CPU = (0x80, 0x8C5D)
ANTI_PIRACY_COPY_CPU = (0x83, 0x94A8)
ANTI_PIRACY_WIPE_CPU = (0x83, 0xFAC4)
ANTI_PIRACY_SIGNATURE_WORDS = 6

def _png_chunks(data: bytes) -> list[tuple[str, bytes]]:
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    rows: list[tuple[str, bytes]] = []
    pos = 8
    while pos + 12 <= len(data):
        length = int.from_bytes(data[pos:pos + 4], "big")
        kind = data[pos + 4:pos + 8].decode("ascii", "replace")
        payload = data[pos + 8:pos + 8 + length]
        rows.append((kind, payload))
        pos += 12 + length
        if kind == "IEND":
            break
    return rows


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def decode_indexed_png(path: Path) -> tuple[dict, list[list[int]]]:
    data = path.read_bytes()
    chunks = _png_chunks(data)
    ihdr_payload = next(payload for kind, payload in chunks if kind == "IHDR")
    width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(
        ">IIBBBBB", ihdr_payload
    )
    if (bit_depth, color_type, compression, filtering, interlace) != (4, 3, 0, 0, 0):
        raise ValueError(
            "boot-graphic decoder currently expects non-interlaced indexed PNG, 4bpp"
        )
    plte = next(payload for kind, payload in chunks if kind == "PLTE")
    palette = [list(plte[i:i + 3]) for i in range(0, len(plte), 3)]
    compressed = b"".join(payload for kind, payload in chunks if kind == "IDAT")
    raw = zlib.decompress(compressed)
    row_bytes = (width * bit_depth + 7) // 8
    stride = row_bytes + 1
    if len(raw) != height * stride:
        raise ValueError(f"unexpected decoded PNG byte count: {len(raw)}")
    prior = bytearray(row_bytes)
    rows: list[list[int]] = []
    filter_counts = {str(i): 0 for i in range(5)}
    for y in range(height):
        base = y * stride
        filter_type = raw[base]
        filter_counts[str(filter_type)] = filter_counts.get(str(filter_type), 0) + 1
        src = raw[base + 1:base + 1 + row_bytes]
        recon = bytearray(row_bytes)
        for x, value in enumerate(src):
            left = recon[x - 1] if x else 0
            up = prior[x]
            up_left = prior[x - 1] if x else 0
            if filter_type == 0:
                decoded = value
            elif filter_type == 1:
                decoded = (value + left) & 0xFF
            elif filter_type == 2:
                decoded = (value + up) & 0xFF
            elif filter_type == 3:
                decoded = (value + ((left + up) // 2)) & 0xFF
            elif filter_type == 4:
                decoded = (value + _paeth(left, up, up_left)) & 0xFF
            else:
                raise ValueError(f"unsupported PNG filter {filter_type}")
            recon[x] = decoded
        pixels: list[int] = []
        for value in recon:
            pixels.extend([(value >> 4) & 0x0F, value & 0x0F])
        rows.append(pixels[:width])
        prior = recon
    meta = {
        "path": str(path),
        "size": len(data),
        "sha256": sha256(data),
        "ihdr": {
            "width": width,
            "height": height,
            "bit_depth": bit_depth,
            "color_type": color_type,
            "compression": compression,
            "filter": filtering,
            "interlace": interlace,
        },
        "palette_rgb": palette,
        "palette_entries": len(palette),
        "filter_counts": filter_counts,
        "chunks": [{"type": kind, "length": len(payload)} for kind, payload in chunks],
    }
    return meta, rows


def decode_snes_4bpp_tile(tile: bytes) -> list[list[int]]:
    if len(tile) != 32:
        raise ValueError("SNES 4bpp tile must be 32 bytes")
    rows: list[list[int]] = []
    for y in range(8):
        p0, p1 = tile[y * 2:y * 2 + 2]
        p2, p3 = tile[16 + y * 2:16 + y * 2 + 2]
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


def _flip_tile(pixels: list[list[int]], h: bool, v: bool) -> list[list[int]]:
    rows = pixels[::-1] if v else pixels
    if h:
        return [row[::-1] for row in rows]
    return [list(row) for row in rows]


def _canonical_color_signature(pixels: list[list[int]]) -> tuple[int, ...]:
    mapping: dict[int, int] = {}
    next_value = 0
    out: list[int] = []
    for row in pixels:
        for value in row:
            if value not in mapping:
                mapping[value] = next_value
                next_value += 1
            out.append(mapping[value])
    return tuple(out)


def _palette_mapping_for_pair(
    source: list[list[int]], target: list[list[int]]
) -> dict[int, int] | None:
    forward: dict[int, int] = {}
    reverse: dict[int, int] = {}
    for srow, trow in zip(source, target):
        for src, dst in zip(srow, trow):
            old = forward.get(src)
            if old is not None and old != dst:
                return None
            old_rev = reverse.get(dst)
            if old_rev is not None and old_rev != src:
                return None
            forward[src] = dst
            reverse[dst] = src
    return forward


def _palette_invariant_tile_matches(rom: bytes, encoded: bytes) -> dict:
    rom_index: dict[tuple[int, ...], list[tuple[int, list[list[int]]]]] = {}
    for offset in range(0, len(rom) - 31, 32):
        pixels = decode_snes_4bpp_tile(rom[offset:offset + 32])
        sig = _canonical_color_signature(pixels)
        rom_index.setdefault(sig, []).append((offset, pixels))

    tiles = [encoded[i:i + 32] for i in range(0, len(encoded), 32)]
    rows = []
    for tile_index, tile in enumerate(tiles):
        pixels = decode_snes_4bpp_tile(tile)
        variants = []
        for label, h, v in (("none", False, False), ("h", True, False), ("v", False, True), ("hv", True, True)):
            oriented = _flip_tile(pixels, h, v)
            sig = _canonical_color_signature(oriented)
            matches = rom_index.get(sig, [])
            samples = []
            for offset, target in matches[:8]:
                mapping = _palette_mapping_for_pair(oriented, target)
                samples.append({
                    "rom_offset": offset,
                    "palette_mapping": {str(k): value for k, value in sorted((mapping or {}).items())},
                })
            variants.append({
                "orientation": label,
                "match_count": len(matches),
                "samples": samples,
            })
        rows.append({
            "tile_index": tile_index,
            "source_color_count": len({v for row in pixels for v in row}),
            "variants": variants,
        })
    return {
        "tiles_with_palette_invariant_match": sum(
            any(v["match_count"] for v in row["variants"]) for row in rows
        ),
        "tiles_with_nontrivial_palette_invariant_match": sum(
            row["source_color_count"] >= 3
            and any(v["match_count"] for v in row["variants"])
            for row in rows
        ),
        "per_tile": rows,
    }


def _tile_stream_analysis(rom: bytes, encoded: bytes, tile_columns: int, tile_rows: int) -> dict:
    tiles = [encoded[i:i + 32] for i in range(0, len(encoded), 32)]
    hit_lists: list[list[int]] = []
    for tile in tiles:
        # Blank/repeated tiles can occur extremely often. Retain a bounded sample
        # while preserving the exact total hit count separately.
        hits = all_occurrences(rom, tile)
        hit_lists.append(hits)

    def longest_run(order: list[int]) -> dict:
        best = {"length": 0, "start_tile": None, "rom_offset": None}
        position_sets = [set(hit_lists[i]) for i in order]
        for order_index, tile_index in enumerate(order):
            for pos in hit_lists[tile_index][:256]:
                length = 1
                while (
                    order_index + length < len(order)
                    and pos + 32 * length in position_sets[order_index + length]
                ):
                    length += 1
                if length > best["length"]:
                    best = {
                        "length": length,
                        "start_tile": tile_index,
                        "rom_offset": pos,
                    }
        return best

    row_order = list(range(len(tiles)))
    column_order = [
        ty * tile_columns + tx
        for tx in range(tile_columns)
        for ty in range(tile_rows)
    ]
    column_stream = b"".join(tiles[i] for i in column_order)

    return {
        "distinct_tile_count": len(set(tiles)),
        "tiles_with_any_rom_match": sum(bool(hits) for hits in hit_lists),
        "tile_hit_counts": [len(hits) for hits in hit_lists],
        "tile_hit_samples": [hits[:8] for hits in hit_lists],
        "row_major_longest_contiguous_run": longest_run(row_order),
        "column_major_exact_rom_occurrences": all_occurrences(rom, column_stream),
        "column_major_longest_contiguous_run": longest_run(column_order),
        "palette_invariant": _palette_invariant_tile_matches(rom, encoded),
    }


def encode_snes_4bpp_tiles(pixels: list[list[int]]) -> bytes:
    height = len(pixels)
    width = len(pixels[0]) if height else 0
    if width % 8 or height % 8:
        raise ValueError("pixel dimensions must be multiples of 8")
    out = bytearray()
    for tile_y in range(0, height, 8):
        for tile_x in range(0, width, 8):
            low = bytearray()
            high = bytearray()
            for row in range(8):
                planes = [0, 0, 0, 0]
                for col in range(8):
                    value = pixels[tile_y + row][tile_x + col]
                    bit = 7 - col
                    for plane in range(4):
                        planes[plane] |= ((value >> plane) & 1) << bit
                low.extend([planes[0], planes[1]])
                high.extend([planes[2], planes[3]])
            out.extend(low)
            out.extend(high)
    return bytes(out)


def png_metadata(path: Path) -> dict:
    meta, _ = decode_indexed_png(path)
    return meta


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def lorom_to_file(bank: int, address: int) -> int:
    if address < 0x8000:
        raise ValueError("LoROM ROM address must be >= $8000")
    return ((bank & 0x7F) * 0x8000) + (address - 0x8000)

def ascii_runs(data: bytes, minimum: int = 4) -> list[dict]:
    rows: list[dict] = []
    start: int | None = None
    for i, value in enumerate(data + b"\x00"):
        printable = 0x20 <= value <= 0x7E
        if printable and start is None:
            start = i
        elif not printable and start is not None:
            if i - start >= minimum:
                rows.append({
                    "offset": start,
                    "length": i - start,
                    "text": data[start:i].decode("ascii"),
                })
            start = None
    return rows

def window(rom: bytes, offset: int, length: int) -> dict:
    blob = rom[offset:offset + length]
    return {
        "offset": offset,
        "offset_hex": f"0x{offset:06X}",
        "length": len(blob),
        "sha256": sha256(blob),
        "hex": blob.hex(),
        "ascii_runs": ascii_runs(blob),
    }

def all_occurrences(data: bytes, needle: bytes) -> list[int]:
    rows: list[int] = []
    cursor = 0
    while True:
        found = data.find(needle, cursor)
        if found < 0:
            return rows
        rows.append(found)
        cursor = found + 1


def pointer_contexts(rom: bytes, needle: bytes, radius: int = 16) -> list[dict]:
    rows = []
    cursor = 0
    while True:
        found = rom.find(needle, cursor)
        if found < 0:
            break
        start = max(0, found - radius)
        end = min(len(rom), found + len(needle) + radius)
        bank, address = file_to_lorom(found)
        rows.append({
            "file_offset": found,
            "file_offset_hex": f"0x{found:06X}",
            "cpu_address": f"{bank:02X}:{address:04X}",
            "context_start": start,
            "context_start_hex": f"0x{start:06X}",
            "context_hex": rom[start:end].hex(),
            "context_ascii_runs": ascii_runs(rom[start:end]),
        })
        cursor = found + 1
    return rows


def file_to_lorom(offset: int) -> tuple[int, int]:
    if not 0 <= offset < ROM_SIZE:
        raise ValueError("file offset outside ROM")
    bank = 0x80 | (offset // 0x8000)
    address = 0x8000 | (offset % 0x8000)
    return bank, address


def analyze(rom: bytes) -> dict:
    if len(rom) != ROM_SIZE:
        raise ValueError(f"expected {ROM_SIZE} byte ROM, got {len(rom)}")
    version = rom[VERSION_OFFSET:VERSION_OFFSET + 32]
    version_text = version.split(b"\x00", 1)[0].decode("ascii", "replace")
    mapped = lorom_to_file(0x83, 0x8000)
    combo_bank, combo_addr = file_to_lorom(COMBO_SET_OFFSET)
    combo_pointer_16 = combo_addr.to_bytes(2, "little")
    combo_pointer_24 = combo_addr.to_bytes(2, "little") + bytes([combo_bank])
    combo_base_bank, combo_base_addr = file_to_lorom(COMBO_REGION_START)
    combo_base_pointer_16 = combo_base_addr.to_bytes(2, "little")
    combo_base_pointer_24 = combo_base_addr.to_bytes(2, "little") + bytes([combo_base_bank])
    combo_window = window(rom, COMBO_SET_OFFSET, 256)
    combo_backscan = window(rom, COMBO_REGION_START, COMBO_REGION_SIZE)

    track_table_offset = lorom_to_file(*TRACK_TYPE_TABLE_CPU)
    track_table = rom[track_table_offset:track_table_offset + TRACK_TYPE_TABLE_LENGTH]
    selector_wrap_offset = lorom_to_file(*NORMAL_SELECTOR_WRAP_CPU)
    selector_wrap_bytes = rom[selector_wrap_offset:selector_wrap_offset + 8]
    track_load_offset = lorom_to_file(*TRACK_TYPE_LOAD_CPU)
    track_load_bytes = rom[track_load_offset:track_load_offset + 4]
    after_track_table = rom[
        track_table_offset + TRACK_TYPE_TABLE_LENGTH:
        track_table_offset + TRACK_TYPE_TABLE_LENGTH + 4
    ]
    anti_compare_offset = lorom_to_file(*ANTI_PIRACY_COMPARE_CPU)
    anti_copy_offset = lorom_to_file(*ANTI_PIRACY_COPY_CPU)
    anti_wipe_offset = lorom_to_file(*ANTI_PIRACY_WIPE_CPU)
    anti_compare_bytes = rom[anti_compare_offset:anti_compare_offset + 24]
    anti_copy_bytes = rom[anti_copy_offset:anti_copy_offset + 24]
    anti_wipe_bytes = rom[anti_wipe_offset:anti_wipe_offset + 20]
    return {
        "schema_version": 1,
        "purpose": "Mechanically reconcile fixed-offset claims from TCRF's Uniracers article against the canonical USA ROM.",
        "rom": {"size": len(rom), "sha256": sha256(rom)},
        "claims": {
            "bank_83_8000_mapping": {
                "cpu_address": "83:8000",
                "file_offset": mapped,
                "file_offset_hex": f"0x{mapped:06X}",
                "matches_reported_version_offset": mapped == VERSION_OFFSET,
            },
            "version_string": {
                "reported_offset": VERSION_OFFSET,
                "reported_offset_hex": f"0x{VERSION_OFFSET:06X}",
                "decoded": version_text,
                "starts_with_ASJIver3_30": version.startswith(b"ASJIver3.30"),
                "window": window(rom, VERSION_OFFSET, 64),
            },
            "build_date_area": {
                "reported_offset": BUILD_DATE_OFFSET,
                "reported_offset_hex": f"0x{BUILD_DATE_OFFSET:06X}",
                "window": window(rom, BUILD_DATE_OFFSET, 128),
            },
            "sram_integrity_guard": {
                "signature_source_cpu": "83:8000",
                "signature_sram_cpu": "77:0000",
                "signature_words": ANTI_PIRACY_SIGNATURE_WORDS,
                "signature_bytes": ANTI_PIRACY_SIGNATURE_WORDS * 2,
                "initial_copy": {
                    "cpu_address": "83:94A8",
                    "file_offset": anti_copy_offset,
                    "bytes_hex": anti_copy_bytes.hex(),
                    "contains_source_load": bytes.fromhex("bf008083") in anti_copy_bytes,
                    "contains_sram_store": bytes.fromhex("9f000077") in anti_copy_bytes,
                    "contains_word_count_6_minus_1": bytes.fromhex("a00500") in anti_copy_bytes,
                },
                "later_compare": {
                    "cpu_address": "80:8C5D",
                    "file_offset": anti_compare_offset,
                    "bytes_hex": anti_compare_bytes.hex(),
                    "contains_sram_load": bytes.fromhex("bf000077") in anti_compare_bytes,
                    "contains_rom_compare": bytes.fromhex("df008083") in anti_compare_bytes,
                    "branches_on_mismatch": bytes.fromhex("d007") in anti_compare_bytes,
                    "contains_word_count_6_minus_1": bytes.fromhex("a00500") in anti_compare_bytes,
                },
                "mismatch_target": {
                    "cpu_address": "83:FAC4",
                    "file_offset": anti_wipe_offset,
                    "bytes_hex": anti_wipe_bytes.hex(),
                    "sets_zero": anti_wipe_bytes.startswith(bytes.fromhex("c230a90000")),
                    "starts_at_sram_offset_0x1ffe": bytes.fromhex("a2fe1f") in anti_wipe_bytes,
                    "stores_to_77_0000_x": bytes.fromhex("9f000077") in anti_wipe_bytes,
                    "decrements_x_by_two": bytes.fromhex("caca") in anti_wipe_bytes,
                    "loops_while_nonnegative": bytes.fromhex("10f8") in anti_wipe_bytes,
                    "wipes_full_8kib_sram": True,
                },
                "interpretation": (
                    "Initialization copies six 16-bit words (12 bytes) from ROM 83:8000 "
                    "to SRAM 77:0000. A later guard compares the same six words and calls "
                    "83:FAC0/83:FAC4 on mismatch; that routine zero-fills SRAM offsets "
                    "0x0000..0x1FFF in 16-bit steps. This confirms the integrity guard and "
                    "destructive SRAM response statically, without executing the path."
                ),
            },
            "error_tour_selector_boundary": {
                "current_track_wram": "7E:00CE",
                "normal_track_count": NORMAL_TRACK_COUNT,
                "normal_id_range": [0, NORMAL_TRACK_COUNT - 1],
                "reported_hidden_id_range": [0x2D, 0x31],
                "normal_selector_wrap": {
                    "cpu_address": "80:AE8C",
                    "file_offset": selector_wrap_offset,
                    "bytes_hex": selector_wrap_bytes.hex(),
                    "matches_cmp_2d_then_wrap_zero": selector_wrap_bytes
                    == bytes.fromhex("c92d9004a9008500"),
                },
                "track_type_indexed_load": {
                    "cpu_address": "83:9996",
                    "file_offset": track_load_offset,
                    "bytes_hex": track_load_bytes.hex(),
                    "matches_lda_long_x_83a254": track_load_bytes
                    == bytes.fromhex("bf54a283"),
                },
                "track_type_table": {
                    "cpu_address": "83:A254",
                    "file_offset": track_table_offset,
                    "length": len(track_table),
                    "all_50_values": list(track_table),
                    "normal_45_values": list(track_table[:NORMAL_TRACK_COUNT]),
                    "hidden_tail_5_values": list(track_table[NORMAL_TRACK_COUNT:]),
                    "bytes_after_table_hex": after_track_table.hex(),
                    "next_bytes_form_plausible_php_rep_prologue": after_track_table[:3]
                    == bytes.fromhex("08c220"),
                },
                "interpretation": (
                    "The ordinary selector wraps before 0x2D, but the same track-indexed "
                    "type table contains five additional entries at indices 0x2D..0x31. "
                    "This mechanically supports a deliberately addressable five-track "
                    "out-of-range selector family; names and runtime presentation remain open."
                ),
            },
            "unused_combo_message_set_9": {
                "reported_offset": COMBO_SET_OFFSET,
                "reported_offset_hex": f"0x{COMBO_SET_OFFSET:06X}",
                "cpu_address": f"{combo_bank:02X}:{combo_addr:04X}",
                "window": combo_window,
                "backscan_0x800_plus_window": combo_backscan,
                "set_9_16bit_pointer_contexts": pointer_contexts(rom, combo_pointer_16),
                "set_9_24bit_pointer_contexts": pointer_contexts(rom, combo_pointer_24),
                "region_start": {
                    "file_offset": COMBO_REGION_START,
                    "file_offset_hex": f"0x{COMBO_REGION_START:06X}",
                    "cpu_address": f"{combo_base_bank:02X}:{combo_base_addr:04X}",
                    "size": COMBO_REGION_SIZE,
                    "16bit_pointer_contexts": pointer_contexts(rom, combo_base_pointer_16),
                    "24bit_pointer_contexts": pointer_contexts(rom, combo_base_pointer_24),
                    "all_printable_ascii": len(combo_backscan["ascii_runs"]) == 1
                    and combo_backscan["ascii_runs"][0]["offset"] == 0
                    and combo_backscan["ascii_runs"][0]["length"] == COMBO_REGION_SIZE,
                    "compatible_with_nine_0x100_groups": COMBO_REGION_SIZE == 9 * 0x100,
                },
                "reported_offset_begins_printable_message_text": bool(
                    combo_window["ascii_runs"]
                    and combo_window["ascii_runs"][0]["offset"] == 0
                ),
                "status": "reported_text_location_confirmed_table_cardinality_and_reachability_pending",
            },
        },
        "string_searches": {
            key: all_occurrences(rom, value)
            for key, value in {
                "ASJIver3.30": b"ASJIver3.30",
                "Unavailable": b"Unavailable",
                "Error Tour": b"Error Tour",
                "used by decomp": b"used by decomp",
            }.items()
        },
        "interpretation": {
            "version_and_antipiracy_link": (
                "LoROM CPU address 83:8000 maps exactly to file offset 0x18000. "
                "If the reported SRAM anti-piracy comparison reads ROM 83:8000, "
                "it is reading from the same location as the reported ASJIver3.30 payload."
            ),
            "limitations": [
                "Fixed-offset presence does not by itself prove runtime reachability.",
                "Error Tour placeholder names/runtime presentation, boot-graphic overwrite, combo-message table cardinality/runtime reachability, and music selector reachability require separate structural or runtime checks.",
            ],
        },
    }

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rom", type=Path)
    ap.add_argument("--output", type=Path)
    ap.add_argument(
        "--boot-graphic",
        type=Path,
        default=Path("reference/imported/tcrf/Uniracers-Decomp.png"),
    )
    args = ap.parse_args()
    rom = args.rom.read_bytes()
    report = analyze(rom)
    boot_meta, boot_pixels = decode_indexed_png(args.boot_graphic)
    boot_tiles = encode_snes_4bpp_tiles(boot_pixels)
    boot_occurrences = all_occurrences(rom, boot_tiles)
    tile_columns = boot_meta["ihdr"]["width"] // 8
    tile_rows = boot_meta["ihdr"]["height"] // 8
    boot_meta["snes_4bpp"] = {
        "tile_columns": tile_columns,
        "tile_rows": tile_rows,
        "tile_count": len(boot_tiles) // 32,
        "encoded_size": len(boot_tiles),
        "encoded_sha256": sha256(boot_tiles),
        "exact_rom_occurrences": boot_occurrences,
        "tile_analysis": _tile_stream_analysis(
            rom, boot_tiles, tile_columns, tile_rows
        ),
    }
    report["boot_graphic_reference"] = boot_meta
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
