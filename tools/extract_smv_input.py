#!/usr/bin/env python3
"""Extract standard-joypad controller input from an Snes9x SMV movie.

Produces a snesref-compatible start-frame:duration:hex-mask input file and
machine-readable metadata. This intentionally does not interpret game state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import zipfile
import zlib
from pathlib import Path

SMV_TO_SNESREF = {
    0x8000: 0x001,  # B
    0x4000: 0x002,  # Y
    0x2000: 0x004,  # Select
    0x1000: 0x008,  # Start
    0x0800: 0x010,  # Up
    0x0400: 0x020,  # Down
    0x0200: 0x040,  # Left
    0x0100: 0x080,  # Right
    0x0080: 0x100,  # A
    0x0040: 0x200,  # X
    0x0020: 0x400,  # L
    0x0010: 0x800,  # R
}


def u32(data: bytes, off: int) -> int:
    return struct.unpack_from("<I", data, off)[0]


def translate_mask(smv: int) -> int:
    out = 0
    for src, dst in SMV_TO_SNESREF.items():
        if smv & src:
            out |= dst
    return out


def runs(values: list[int]) -> list[tuple[int, int, int]]:
    out: list[tuple[int, int, int]] = []
    if not values:
        return out
    start = 0
    cur = values[0]
    for i, value in enumerate(values[1:], 1):
        if value != cur:
            if cur:
                out.append((start, i - start, cur))
            start = i
            cur = value
    if cur:
        out.append((start, len(values) - start, cur))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("smv", type=Path)
    ap.add_argument("--controller", type=int, default=1, help="1-based recorded controller index")
    ap.add_argument("--input-out", type=Path, required=True)
    ap.add_argument("--sram-out", type=Path)
    ap.add_argument("--sram-size", type=int, default=0, help="optional cartridge SRAM size to emit")
    ap.add_argument("--json-out", type=Path, required=True)
    args = ap.parse_args()

    container_bytes = args.smv.read_bytes()
    container = None
    contained_name = None
    if container_bytes[:4] == b"PK\x03\x04":
        container = "zip"
        with zipfile.ZipFile(args.smv) as zf:
            candidates = [n for n in zf.namelist() if n.lower().endswith(".smv")]
            if len(candidates) != 1:
                raise SystemExit(f"expected exactly one SMV in ZIP, found {candidates}")
            contained_name = candidates[0]
            data = zf.read(contained_name)
    else:
        data = container_bytes
    if len(data) < 32 or data[:4] != b"SMV\x1a":
        raise SystemExit("not an SMV file or ZIP containing one SMV")

    version = u32(data, 4)
    if version not in (1, 4, 5):
        raise SystemExit(f"unsupported SMV version {version}")

    frame_count = u32(data, 0x10)
    controller_mask = data[0x14]
    movie_options = data[0x15]
    sync_options = data[0x16] | (data[0x17] << 8)
    sync_data_exists = bool(data[0x17] & 0x01)
    legacy_sync = {
        "init_fastrom": bool(data[0x16] & 0x01),
        "wip1_timing": bool(data[0x17] & 0x02),
        "leftright": bool(data[0x17] & 0x04),
        "volumeenvx": bool(data[0x17] & 0x08),
        "fakemute": bool(data[0x17] & 0x10),
        "syncsound": bool(data[0x17] & 0x20),
        "has_rom_info": bool(data[0x17] & 0x40),
    }
    savestate_offset = u32(data, 0x18)
    controller_data_offset = u32(data, 0x1C)
    active_ids = [i for i in range(5) if controller_mask & (1 << i)]
    if not active_ids:
        raise SystemExit("SMV records no standard controllers")
    if not 1 <= args.controller <= len(active_ids):
        raise SystemExit(f"controller index {args.controller} outside 1..{len(active_ids)}")

    reset_anchored = bool(movie_options & 0x01)
    pal = bool(movie_options & 0x02)

    embedded_sram = None
    if reset_anchored:
        packed = data[savestate_offset:controller_data_offset]
        try:
            dec = zlib.decompressobj(16 + zlib.MAX_WBITS)
            embedded_sram = dec.decompress(packed) + dec.flush()
        except zlib.error as exc:
            raise SystemExit(f"could not decompress reset-movie SRAM block: {exc}")
        if len(embedded_sram) != 0x20000:
            raise SystemExit(
                f"reset-movie SRAM block decoded to {len(embedded_sram)} bytes, expected 131072"
            )
        if args.sram_out:
            emit = embedded_sram[: args.sram_size or len(embedded_sram)]
            if args.sram_size and len(emit) != args.sram_size:
                raise SystemExit("requested SRAM size exceeds embedded snapshot")
            args.sram_out.parent.mkdir(parents=True, exist_ok=True)
            args.sram_out.write_bytes(emit)

    if version == 1:
        sample_count = frame_count + 1
        port_types = None
        stride = 2 * len(active_ids)
    else:
        if len(data) < 64:
            raise SystemExit("truncated SMV 1.51+ header")
        sample_count = u32(data, 0x20)
        port_types = [data[0x24], data[0x25]]
        if any(t not in (0, 1) for t in port_types):
            raise SystemExit(
                f"peripheral SMV not supported by this extractor (port types {port_types})"
            )
        stride = 2 * len(active_ids)

    need = controller_data_offset + sample_count * stride
    if need > len(data):
        raise SystemExit(
            f"controller data truncated: need {need} bytes, file has {len(data)}"
        )

    slot = args.controller - 1
    values: list[int] = []
    reset_markers: list[int] = []
    raw_values: list[int] = []
    for frame in range(sample_count):
        off = controller_data_offset + frame * stride + slot * 2
        sample_raw = struct.unpack_from("<H", data, off)[0]
        raw_values.append(sample_raw)
        if sample_raw == 0xFFFF:
            reset_markers.append(frame)
            values.append(0)
        else:
            values.append(translate_mask(sample_raw))

    event_runs = runs(values)
    args.input_out.parent.mkdir(parents=True, exist_ok=True)
    with args.input_out.open("w", encoding="utf-8") as fh:
        fh.write(f"# Extracted from {args.smv.as_posix()}\n")
        fh.write(f"# SMV version={version} samples={sample_count} reset_anchored={str(reset_anchored).lower()}\n")
        for start, duration, mask in event_runs:
            fh.write(f"{start}:{duration}:{mask:03x}\n")

    meta = {
        "path": args.smv.as_posix(),
        "container": container,
        "contained_name": contained_name,
        "container_size_bytes": len(container_bytes),
        "smv_size_bytes": len(data),
        "version": version,
        "uid": u32(data, 8),
        "rerecord_count": u32(data, 0x0C),
        "frame_count_header": frame_count,
        "sample_count": sample_count,
        "controller_mask": controller_mask,
        "recorded_standard_controllers": len(active_ids),
        "selected_controller_index": args.controller,
        "movie_options": movie_options,
        "reset_anchored": reset_anchored,
        "pal": pal,
        "sync_options": sync_options,
        "sync_data_exists": sync_data_exists,
        "legacy_sync_flags": legacy_sync if sync_data_exists else None,
        "legacy_timing_review_required": bool(
            version == 1 and sync_data_exists and legacy_sync["wip1_timing"]
        ),
        "savestate_offset": savestate_offset,
        "controller_data_offset": controller_data_offset,
        "port_types": port_types,
        "stride": stride,
        "reset_markers": reset_markers,
        "embedded_sram_size": len(embedded_sram) if embedded_sram is not None else None,
        "embedded_sram_sha256": hashlib.sha256(embedded_sram).hexdigest() if embedded_sram is not None else None,
        "emitted_sram_size": args.sram_size if args.sram_out and args.sram_size else (len(embedded_sram) if args.sram_out and embedded_sram is not None else None),
        "emitted_sram_sha256": hashlib.sha256(args.sram_out.read_bytes()).hexdigest() if args.sram_out else None,
        "nonzero_frames": sum(v != 0 for v in values),
        "event_runs": len(event_runs),
        "first_nonzero_frame": next((i for i, v in enumerate(values) if v), None),
        "last_nonzero_frame": next((len(values)-1-i for i, v in enumerate(reversed(values)) if v), None),
        "distinct_snesref_masks": sorted(set(values)),
        "raw_reserved_bits_seen": sorted(set(v & 0x000F for v in raw_values if v != 0xFFFF)),
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(meta, indent=2))
    print(args.input_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
