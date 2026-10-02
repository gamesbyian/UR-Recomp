#!/usr/bin/env python3
"""Trace the racer presentation tile-upload path around staging and VRAM DMA.

This is intentionally narrow. It records executable instructions around the
known presentation staging consumers and the F2BB helper, highlighting PPU/DMA
register traffic and the recovered staging arrays. The goal is to resolve the
remaining ROM-source -> retained-VRAM byte-layout discrepancy without reopening
the already-closed occupancy/order contract.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from compare_europe_usa_snes2asm_homologs import cpu_to_offset, seed_entries, trace
from extract_racer_presentation_family import (
    extract_frame,
    lorom_offset,
    packed_word_source,
)
from analyze_racer_piece_render_binding import (
    decode_obsel,
    decode_oam_slot,
    object_tile_number,
    object_tile_vram_byte_address,
)

RANGES = (
    ("race_render_body", "83:F0BB", "83:F2BA"),
    ("dma_consumer_a", "82:B8D1", "82:B980"),
    ("dma_consumer_b", "82:C53A", "82:C5E0"),
    ("tile_pair_helper", "83:F2BB", "83:F4D1"),
)
SEEDS = ("83:F0BB", "82:B8D1", "82:C53A", "83:F2BB")
REGISTER_TARGETS = {
    "DMAP0": 0x4300,
    "BBAD0": 0x4301,
    "DMASRC0L": 0x4302,
    "DMASRC0B": 0x4304,
    "DMALEN0L": 0x4305,
    "VMAIN": 0x2115,
    "VMADDL": 0x2116,
    "VMDATAL": 0x2118,
    "VMDATAH": 0x2119,
    "MDMAEN": 0x420B,
}
WRITE_OPS = {
    0x8D: "STA abs",
    0x8E: "STX abs",
    0x8C: "STY abs",
    0x9C: "STZ abs",
}

INTEREST = (
    "VMAIN", "VMADD", "VMDATA", "DMA", "MDMAEN",
    "$1645", "$15A1", "$16E9",
    "$1647", "$15A3", "$16EB",
    "$1649", "$15A5", "$16ED",
    "$76", "$79", "$7C", "$7F", "$0C83", "$0C85", "$F2BB",
)


def decoded_ranges(rom: bytes) -> list[dict]:
    d = trace(rom)
    seed_entries(d, [cpu_to_offset(x) for x in SEEDS])
    out = []
    for name, start_cpu, end_cpu in RANGES:
        start = cpu_to_offset(start_cpu)
        end = cpu_to_offset(end_cpu) + 1
        d.decode(start, end)
        rows = []
        for off, ins in d.code.item_range(start, end):
            size = d.opSize(rom[off])
            text = ins.text()
            rows.append({
                "cpu": f"{(off // 0x8000) | 0x80:02X}:{0x8000 + (off % 0x8000):04X}",
                "text": text,
                "bytes": rom[off:off + size].hex(" "),
                "interesting": any(token.upper() in text.upper() for token in INTEREST),
            })
        out.append({
            "name": name,
            "start": start_cpu,
            "end": end_cpu,
            "rows": rows,
            "interesting_rows": [r for r in rows if r["interesting"]],
        })
    return out



def register_write_sites(rom: bytes) -> list[dict]:
    """Find literal absolute writes to DMA/VRAM control registers.

    Keep raw candidates as evidence even when the static tracer does not mark
    the surrounding code reachable from the narrow racer seeds.
    """
    d = trace(rom)
    seed_entries(d, [cpu_to_offset(x) for x in SEEDS])
    rows = []
    by_addr = {addr: name for name, addr in REGISTER_TARGETS.items()}
    for off in range(len(rom) - 2):
        op = rom[off]
        if op not in WRITE_OPS:
            continue
        addr = rom[off + 1] | (rom[off + 2] << 8)
        if addr not in by_addr:
            continue
        status = d.code_map[off] if off < len(d.code_map) else 0
        rows.append({
            "cpu": f"{(off // 0x8000) | 0x80:02X}:{0x8000 + (off % 0x8000):04X}",
            "register": by_addr[addr],
            "address": f"0x{addr:04X}",
            "mnemonic": WRITE_OPS[op],
            "bytes": rom[off:off + 3].hex(" "),
            "tracer_executable": bool(status & d.OP_CODE),
        })
    return rows


def nearby_register_setup(rom: bytes, writes: list[dict]) -> list[dict]:
    """Decode bounded context around candidate control-register writes."""
    d = trace(rom)
    seed_entries(d, [cpu_to_offset(x) for x in SEEDS])
    out = []
    # Prefer bank-82 candidates because both racer DMA consumers live there.
    for row in writes:
        if not row["cpu"].startswith("82:"):
            continue
        off = cpu_to_offset(row["cpu"])
        bank_start = (off // 0x8000) * 0x8000
        bank_end = bank_start + 0x8000
        start = max(bank_start, off - 24)
        end = min(bank_end, off + 32)
        try:
            d.decode(start, end)
        except Exception:
            pass
        ctx = []
        for q, ins in d.code.item_range(start, end):
            try:
                size = d.opSize(rom[q])
            except Exception:
                size = 1
            ctx.append({
                "cpu": f"{(q // 0x8000) | 0x80:02X}:{0x8000 + (q % 0x8000):04X}",
                "text": ins.text(),
                "bytes": rom[q:q + size].hex(" "),
            })
        out.append({"write": row, "context": ctx})
    return out



def u16(data: bytes, off: int) -> int:
    return data[off] | (data[off + 1] << 8)


def runtime_staging_checks(rom: bytes, dump_dir: Path | None) -> list[dict]:
    """Compare live staging tuples to the VRAM bytes at their programmed destination."""
    if dump_dir is None:
        return []
    out = []
    for wram_path in sorted(dump_dir.glob("*.wram.bin")):
        tag = wram_path.name[:-9]
        vram_path = dump_dir / f"{tag}.vram.bin"
        oam_path = dump_dir / f"{tag}.oam.bin"
        regs_path = dump_dir / f"{tag}.regs.json"
        if not (vram_path.exists() and oam_path.exists() and regs_path.exists()):
            continue
        wram = wram_path.read_bytes()
        vram = vram_path.read_bytes()
        oam = oam_path.read_bytes()
        regs = json.loads(regs_path.read_text(encoding="utf-8"))
        obsel = decode_obsel(int(regs["obsel"]))
        oam_slots = [decode_oam_slot(oam, slot, obsel) for slot in (96, 97, 98, 99)]
        object_destinations = {}
        for slot in oam_slots:
            if slot["size_pixels"] != [64, 64]:
                continue
            for gy in range(8):
                for gx in range(8):
                    tile = object_tile_number(slot["tile"], gx, gy)
                    byte_addr = object_tile_vram_byte_address(obsel, slot, tile)
                    object_destinations.setdefault(byte_addr // 2, []).append({
                        "oam_slot": slot["slot"],
                        "grid_x": gx,
                        "grid_y": gy,
                        "tile": f"0x{tile:02X}",
                        "hflip": slot["hflip"],
                        "vflip": slot["vflip"],
                        "palette_number": slot["palette_number"],
                    })
        if len(wram) < 0x1800 or len(vram) < 0x10000:
            continue
        consumer = "a" if wram[0x12EB] == 0 else "b"
        mode_0300 = u16(wram, 0x0300)
        source_labels = {}
        for label, fid in (
            ("p1_primary", u16(wram, 0x0FE9)),
            ("p2_primary", u16(wram, 0x0FEB)),
            ("p1_companion", u16(wram, 0x0D3F)),
            ("p2_companion", u16(wram, 0x0D41)),
        ):
            if not fid:
                continue
            try:
                frame = extract_frame(rom, fid)
            except Exception:
                continue
            for piece in frame["pieces"]:
                key = packed_word_source(int(piece["word_hex"], 16))
                source_labels.setdefault(key, []).append({
                    "stream": label,
                    "frame_id": f"0x{fid:04X}",
                    "word_index": piece["word_index"],
                    "major_slot": piece["major_slot"],
                    "minor_slot": piece["minor_slot"],
                })
        source_labels.setdefault((0x27, 0x8000), []).append({"stream": "blank"})

        rows = []
        exact = 0
        valid = 0
        for i in range(82):
            q = i * 2
            bank = wram[0x15A1 + q]
            src = u16(wram, 0x1645 + q)
            dest = u16(wram, 0x16E9 + q)
            if bank & 0x80 or src < 0x8000:
                continue
            try:
                source_off = lorom_offset(bank, src)
            except ValueError:
                continue
            source = rom[source_off:source_off + 0x20]
            if len(source) != 0x20:
                continue
            effective = dest
            if consumer == "a":
                if dest & 0x0080:
                    effective = (dest + 0x0800) & 0xFFFF
            elif mode_0300:
                effective = (dest + 0x0800) & 0xFFFF
            vram_off = (effective & 0x7FFF) * 2
            actual = vram[vram_off:vram_off + 0x20]
            same = len(actual) == 0x20 and actual == source
            valid += 1
            exact += int(same)
            rows.append({
                "slot": i,
                "source_bank": f"0x{bank:02X}",
                "source_addr": f"0x{src:04X}",
                "source_rom_offset": source_off,
                "staged_vram_word": f"0x{dest:04X}",
                "effective_vram_word": f"0x{effective:04X}",
                "vram_byte_offset": f"0x{vram_off:04X}",
                "source_equals_vram": same,
                "source_candidates": source_labels.get((bank, src), []),
                "cache_grid": {
                    "row": ((effective & 0x7FFF) - 0x6000) // 0x0100,
                    "column": (((effective & 0x7FFF) - 0x6000) % 0x0100) // 0x0010,
                } if 0x6000 <= (effective & 0x7FFF) < 0x6500 else None,
                "object_tiles": object_destinations.get(effective & 0x7FFF, []),
            })
        grid_entries = {
            (e["cache_grid"]["row"], e["cache_grid"]["column"]): e
            for e in rows
            if e["cache_grid"] is not None
        }
        def grid_label(row: int, col: int) -> str:
            e = grid_entries.get((row, col))
            if e is None or not e["source_candidates"]:
                return "unknown"
            streams = sorted({x["stream"] for x in e["source_candidates"]})
            return "+".join(streams)

        out.append({
            "checkpoint": tag,
            "consumer": consumer,
            "mode_0300": f"0x{mode_0300:04X}",
            "composition_state": {
                "p1_current_id": f"0x{u16(wram, 0x0FE9):04X}",
                "p2_current_id": f"0x{u16(wram, 0x0FEB):04X}",
                "p1_companion_id": f"0x{u16(wram, 0x0D3F):04X}",
                "p2_companion_id": f"0x{u16(wram, 0x0D41):04X}",
                "p1_selector_0c83": f"0x{u16(wram, 0x0C83):04X}",
                "p2_selector_0c85": f"0x{u16(wram, 0x0C85):04X}",
            },
            "racer_object_slots": oam_slots,
            "valid_staging_entries": valid,
            "exact_source_vram_matches": exact,
            "entries": rows,
            "cache_grid_streams": [
                {
                    "row": row,
                    "columns": [grid_label(row, col) for col in range(14)],
                }
                for row in range(5)
            ],
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--md-out", type=Path)
    ap.add_argument("--dump-dir", type=Path)
    args = ap.parse_args()

    rom = args.rom.read_bytes()
    writes = register_write_sites(rom)
    report = {
        "schema_version": 2,
        "purpose": "Bound racer presentation staging -> DMA/VRAM upload semantics.",
        "ranges": decoded_ranges(rom),
        "register_write_sites": writes,
        "bank82_register_write_contexts": nearby_register_setup(rom, writes),
        "runtime_staging_checks": runtime_staging_checks(rom, args.dump_dir),
    }
    md = ["# Racer tile-upload path", ""]
    md += ["## Literal DMA/VRAM control-register writes", ""]
    for row in report["register_write_sites"]:
        md.append(
            f"- \`{row['cpu']}\` {row['mnemonic']} -> {row['register']} "
            f"({row['address']}), bytes \`{row['bytes']}\`, "
            f"tracer_executable={row['tracer_executable']}"
        )
    md.append("")
    md += ["## Bank-82 setup contexts", ""]
    for block in report["bank82_register_write_contexts"]:
        row = block["write"]
        md.append(f"### {row['cpu']} -> {row['register']}")
        md.append("")
        for ctx in block["context"]:
            md.append(f"    {ctx['cpu']}  {ctx['text']}    ; {ctx['bytes']}")
        md.append("")

    if report["runtime_staging_checks"]:
        md += ["## Retained runtime staging -> VRAM byte checks", ""]
        for cp in report["runtime_staging_checks"]:
            state = cp["composition_state"]
            bound = sum(bool(e["object_tiles"]) for e in cp["entries"])
            md.append(
                f"- {cp['checkpoint']}: consumer {cp['consumer']}, "
                f"{cp['exact_source_vram_matches']}/{cp['valid_staging_entries']} "
                "live staging entries match the programmed VRAM destination byte-for-byte; "
                f"{bound} staging entries bind to retained racer OAM tiles; "
                f"IDs {state['p1_current_id']}/{state['p1_companion_id']} and "
                f"{state['p2_current_id']}/{state['p2_companion_id']}, "
                f"selectors {state['p1_selector_0c83']}/{state['p2_selector_0c85']}."
            )
            md.append("  cache-grid streams:")
            for row in cp["cache_grid_streams"]:
                md.append(
                    f"    row {row['row']}: " + " | ".join(row["columns"])
                )
            bound_rows = [e for e in cp["entries"] if e["object_tiles"]]
            md.append("  OAM-bound staged entries:")
            for e in bound_rows:
                labels = sorted({
                    c["stream"] for c in e["source_candidates"]
                }) or ["unknown"]
                objects = ", ".join(
                    f"slot{o['oam_slot']}[{o['grid_x']},{o['grid_y']}]"
                    for o in e["object_tiles"]
                )
                md.append(
                    f"    slot {e['slot']}: {e['source_bank']}:{e['source_addr']} -> "
                    f"{e['effective_vram_word']} [{'+'.join(labels)}] -> {objects}; "
                    f"bytes_equal={e['source_equals_vram']}"
                )
        md.append("")

    for block in report["ranges"]:
        md += [f"## {block['name']} ({block['start']}..{block['end']})", ""]
        md.append("### PPU/DMA/staging references")
        md.append("")
        for row in block["interesting_rows"]:
            md.append(f"- \`{row['cpu']}\`  \`{row['bytes']}\`  {row['text']}")
        md.append("")
        md.append("### Full decoded range")
        md.append("")
        for row in block["rows"]:
            md.append(f"    {row['cpu']}  {row['text']}    ; {row['bytes']}")
        md.append("")

    js = json.dumps(report, indent=2, sort_keys=True) + "\n"
    text = "\n".join(md) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(js, encoding="utf-8")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        args.md_out.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
