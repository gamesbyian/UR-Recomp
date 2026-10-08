#!/usr/bin/env python3
"""Extract and validate the Snes9x freeze embedded in a savestate-anchored SMV.

Snes9x 1.51 movies whose ``movie_options`` bit 0 is clear start from a
savestate rather than from power-on. The complete freeze file is stored as a
gzip stream between the SMV savestate offset and the controller-data offset.
This tool decompresses that stream, validates the ``#!snes9x:NNNN`` freeze
container and its ``TAG:NNNNNN:`` blocks, and emits a compact JSON anchor
summary: hashes, block inventory, and already-symbolized WRAM fields.

It never executes the game. Extracted freezes are scratch material; write them
outside the repository with ``--freeze-out-dir`` when a local replay needs one.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
import zlib
from dataclasses import dataclass
from pathlib import Path

SMV_MAGIC = b"SMV\x1a"
GZIP_MAGIC = b"\x1f\x8b"
FREEZE_MAGIC_RE = re.compile(rb"^#!snes9x:(\d{4})\n")
BLOCK_HEADER_RE = re.compile(rb"^([A-Z0-9]{3}):(\d{6}):")
WRAM_SIZE = 0x20000
BLOCK_HEADER_LEN = 11


class FreezeError(ValueError):
    """Raised for malformed SMV headers, gzip streams or freeze containers."""


@dataclass(frozen=True)
class Field:
    name: str
    addr: int  # WRAM offset (7E:xxxx -> xxxx)
    width: int  # 1 or 2 bytes
    signed: bool = False
    mask: int | None = None
    symbol: str = ""


# Only fields already owned by docs/SYMBOLS.md. Pitch keeps the documented
# low-6-bit observation; the raw word is not interpreted further.
ANCHOR_FIELDS: tuple[Field, ...] = (
    Field("frontend_menu", 0x009F, 1, symbol="Frontend_CurrentMenu"),
    Field("track_id", 0x00CE, 1, symbol="historical current-track id (Dessyreqt; stream index - 1)"),
    Field("race_active", 0x0313, 1, symbol="Race_ActiveState"),
    Field("p1_x", 0x0411, 2, symbol="Player1_XPosition"),
    Field("p1_y", 0x0415, 2, symbol="Player1_YPosition"),
    Field("p1_x_speed", 0x04B7, 2, True, symbol="Player1_XSpeed"),
    Field("p1_y_speed", 0x04BB, 2, True, symbol="Player1_YSpeed"),
    Field("p1_pitch", 0x04C7, 2, mask=0x3F, symbol="Player1_PitchAngle"),
    Field("p1_air_time", 0x0545, 2, symbol="Player1_AirTime"),
    Field("p1_stunt_air_latch", 0x1361, 2, symbol="Player1_StuntAirLatch"),
    Field("p1_angular_velocity", 0x0BAD, 2, True, symbol="Player1_AngularVelocity"),
    Field("p1_z_rotation", 0x0DFD, 2, symbol="Player1_ZRotationState"),
    Field("p1_facing_at_takeoff", 0x033B, 2, symbol="Player1_FacingAtTakeoff"),
    Field("p1_roll_count", 0x11F9, 2, symbol="Player1_RollCount"),
    Field("p1_flip_count", 0x11FD, 2, symbol="Player1_FlipCount"),
    Field("p1_contact_word_persisted", 0x0E95, 2, symbol="P1 persistence slot of CurrentPlayer_CollisionContactWord ($0E95/$0E97)"),
    Field("current_contact_word", 0x0F09, 2, symbol="CurrentPlayer_CollisionContactWord"),
    Field("p1_next_checkpoint", 0x1199, 2, symbol="Player1_NextCheckpoint"),
    Field("p1_laps_remaining", 0x0EF1, 2, symbol="Player1_LapsRemaining"),
    Field("p2_x", 0x0413, 2, symbol="Player2_XPosition"),
    Field("p2_y", 0x0417, 2, symbol="Player2_YPosition"),
    Field("p2_x_speed", 0x04B9, 2, True, symbol="Player2_XSpeed"),
    Field("p2_y_speed", 0x04BD, 2, True, symbol="Player2_YSpeed"),
    Field("p2_pitch", 0x04C9, 2, mask=0x3F, symbol="Player2_PitchAngle"),
    Field("p2_air_time", 0x0547, 2, symbol="Player2_AirTime"),
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_smv_header(data: bytes) -> dict:
    if len(data) < 0x20 or data[:4] != SMV_MAGIC:
        raise FreezeError("not an SMV file (bad magic or shorter than 32 bytes)")
    version = struct.unpack_from("<I", data, 4)[0]
    if version not in (1, 4, 5):
        raise FreezeError(f"unsupported SMV version {version}")
    if version != 1 and len(data) < 0x40:
        raise FreezeError("truncated SMV 1.51+ header")
    savestate_offset, controller_data_offset = struct.unpack_from("<II", data, 0x18)
    if not 0x20 <= savestate_offset <= controller_data_offset <= len(data):
        raise FreezeError(
            f"inconsistent SMV offsets: savestate={savestate_offset} "
            f"controller={controller_data_offset} size={len(data)}"
        )
    return {
        "smv_version": version,
        "uid": struct.unpack_from("<I", data, 8)[0],
        "frame_count_header": struct.unpack_from("<I", data, 0x10)[0],
        "controller_mask": data[0x14],
        "movie_options": data[0x15],
        "reset_anchored": bool(data[0x15] & 0x01),
        "savestate_offset": savestate_offset,
        "controller_data_offset": controller_data_offset,
    }


def decompress_embedded_freeze(data: bytes, header: dict) -> tuple[bytes, bytes]:
    """Return (freeze bytes, bytes after the gzip stream inside the region)."""
    if header["reset_anchored"]:
        raise FreezeError("reset-anchored SMV embeds SRAM, not a freeze; use extract_smv_input.py")
    region = data[header["savestate_offset"]:header["controller_data_offset"]]
    if region[:2] != GZIP_MAGIC:
        raise FreezeError("embedded savestate region does not start with a gzip stream")
    dec = zlib.decompressobj(16 + zlib.MAX_WBITS)
    try:
        freeze = dec.decompress(region) + dec.flush()
    except zlib.error as exc:
        raise FreezeError(f"embedded gzip stream is corrupt: {exc}") from exc
    if not dec.eof:
        raise FreezeError("embedded gzip stream is truncated (no end-of-stream marker)")
    return freeze, dec.unused_data


def parse_freeze(freeze: bytes) -> tuple[int, list[dict]]:
    """Validate a Snes9x freeze container and return (version, blocks)."""
    m = FREEZE_MAGIC_RE.match(freeze)
    if not m:
        raise FreezeError("decompressed state does not begin with '#!snes9x:NNNN\\n'")
    version = int(m.group(1))
    pos = m.end()
    blocks: list[dict] = []
    seen: set[str] = set()
    while pos < len(freeze):
        hm = BLOCK_HEADER_RE.match(freeze[pos:pos + BLOCK_HEADER_LEN])
        if not hm:
            raise FreezeError(f"malformed freeze block header at offset {pos}")
        tag = hm.group(1).decode("ascii")
        length = int(hm.group(2))
        start = pos + BLOCK_HEADER_LEN
        end = start + length
        if end > len(freeze):
            raise FreezeError(f"freeze block {tag} truncated: needs {length} bytes at {start}")
        if tag in seen:
            raise FreezeError(f"duplicate freeze block {tag}")
        seen.add(tag)
        blocks.append({"tag": tag, "offset": start, "length": length})
        pos = end
    return version, blocks


def read_field(wram: bytes, field: Field) -> int:
    fmt = {(1, False): "<B", (1, True): "<b", (2, False): "<H", (2, True): "<h"}[(field.width, field.signed)]
    value = struct.unpack_from(fmt, wram, field.addr)[0]
    if field.mask is not None:
        value &= field.mask
    return value


def decode_registers(reg: bytes) -> dict | None:
    """Decode the 1.51 REG block (SnapRegisters: PB, DB, then big-endian P/A/D/S/X/Y/PC words)."""
    if len(reg) != 16:
        return None
    p, a, d, s, x, y, pc = struct.unpack(">7H", reg[2:])
    return {
        "pb_pc": f"{reg[0]:02X}:{pc:04X}",
        "db": f"{reg[1]:02X}",
        "p": f"{p:04X}",
        "a": f"{a:04X}",
        "d": f"{d:04X}",
        "s": f"{s:04X}",
        "x": f"{x:04X}",
        "y": f"{y:04X}",
    }


def summarize_movie(path: Path, display_path: str | None = None) -> tuple[dict, bytes]:
    data = path.read_bytes()
    header = parse_smv_header(data)
    freeze, trailing = decompress_embedded_freeze(data, header)
    version, blocks = parse_freeze(freeze)
    by_tag = {b["tag"]: b for b in blocks}
    ram = by_tag.get("RAM")
    if ram is None:
        raise FreezeError("freeze has no RAM (WRAM) block")
    if ram["length"] != WRAM_SIZE:
        raise FreezeError(f"freeze RAM block is {ram['length']} bytes, expected {WRAM_SIZE}")
    wram = freeze[ram["offset"]:ram["offset"] + WRAM_SIZE]
    rom_name = None
    if "NAM" in by_tag:
        nam = by_tag["NAM"]
        rom_name = freeze[nam["offset"]:nam["offset"] + nam["length"]].split(b"\x00", 1)[0].decode("latin-1")
    summary = {
        "path": display_path or path.as_posix(),
        "smv_sha256": sha256(data),
        "smv_size_bytes": len(data),
        **header,
        "embedded_gzip_bytes": header["controller_data_offset"] - header["savestate_offset"] - len(trailing),
        "post_gzip_padding_bytes": len(trailing),
        "freeze_version": version,
        "freeze_size_bytes": len(freeze),
        "freeze_sha256": sha256(freeze),
        "freeze_rom_name": rom_name,
        "wram_sha256": sha256(wram),
        "blocks": [
            {
                "tag": b["tag"],
                "length": b["length"],
                "sha256": sha256(freeze[b["offset"]:b["offset"] + b["length"]]),
            }
            for b in blocks
        ],
        "cpu_registers": (
            decode_registers(freeze[by_tag["REG"]["offset"]:by_tag["REG"]["offset"] + by_tag["REG"]["length"]])
            if "REG" in by_tag
            else None
        ),
        "anchor_fields": {f.name: read_field(wram, f) for f in ANCHOR_FIELDS},
    }
    return summary, freeze


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("smv", type=Path, nargs="+")
    ap.add_argument("--json-out", type=Path, help="write the anchor summary JSON here")
    ap.add_argument(
        "--freeze-out-dir",
        type=Path,
        help="scratch directory for decompressed freezes (<movie stem>.frz); never commit these",
    )
    args = ap.parse_args(argv)

    anchors = []
    try:
        for movie in args.smv:
            summary, freeze = summarize_movie(movie)
            anchors.append(summary)
            if args.freeze_out_dir:
                args.freeze_out_dir.mkdir(parents=True, exist_ok=True)
                (args.freeze_out_dir / (movie.stem + ".frz")).write_bytes(freeze)
    except (FreezeError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    doc = {
        "schema_version": 1,
        "kind": "smv-embedded-freeze-anchor",
        "tool": "tools/extract_smv_freeze.py",
        "field_symbols": {
            f.name: {"wram": f"7E:{f.addr:04X}", "width": f.width, "signed": f.signed,
                     **({"mask": f"0x{f.mask:02X}"} if f.mask is not None else {}), "symbol": f.symbol}
            for f in ANCHOR_FIELDS
        },
        "anchors": anchors,
    }
    text = json.dumps(doc, indent=2) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
