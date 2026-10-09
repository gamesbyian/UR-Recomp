#!/usr/bin/env python3
"""Extract a bounded, scene-relative P1 input sequence from an original SMV.

The 2014 reset-anchored SMV is known NOT to provide frame-zero absolute
parity with the native runtime. This tool NEVER identifies the stunt event or
assigns a guest race-entry frame. An independently verified movie-frame
anchor and local original/native race-entry anchors are required to use the
relative masks as a semantic experiment. No ROM bytes, freezes or SRAM
content are written.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import zipfile
from pathlib import Path

from extract_smv_input import translate_mask, runs

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "reference/imported/tas-bots/dessyreqt-4250-submission.smv"
METADATA = ROOT / "analysis/generated/historical-2014-smv-metadata.json"
LIMIT = 24000


class MovieWindowError(ValueError):
    pass


def read_movie(path: Path) -> tuple[bytes, str | None]:
    source = path.read_bytes()
    if source.startswith(b"PK\x03\x04"):
        with zipfile.ZipFile(path) as zf:
            entries = [n for n in zf.namelist() if n.lower().endswith(".smv")]
            if len(entries) != 1:
                raise MovieWindowError("expected exactly one contained SMV")
            return zf.read(entries[0]), entries[0]
    return source, None


def window(data: bytes, meta: dict, first: int, frames: int) -> dict:
    if (type(first) is not int or type(frames) is not int
            or first < 0 or not 1 <= frames <= LIMIT):
        raise MovieWindowError("invalid bounded movie frame span")
    if len(data) < 64 or data[:4] != b"SMV\x1a":
        raise MovieWindowError("invalid SMV signature or header")
    u32 = lambda off: struct.unpack_from("<I", data, off)[0]
    version, uid, size = u32(4), u32(8), u32(0x20)
    mask = data[0x14]
    if (version != 4 or uid != meta.get("uid")
            or size != meta.get("sample_count")
            or meta.get("version") != version
            or meta.get("controller_mask") != 1
            or mask != 1
            or not meta.get("reset_anchored")
            or not (data[0x15] & 1)
            or (data[0x15] & 2) != 0):
        raise MovieWindowError("movie metadata differs from reset-anchored NTSC P1 archive")
    if not (data[0x17] & 0x40) or meta.get("rom_info", {}).get("crc32") is None:
        raise MovieWindowError("original ROM CRC must be present")
    rom_info_start = u32(0x18) - 30
    if rom_info_start < 64 or rom_info_start + 7 > len(data):
        raise MovieWindowError("truncated or invalid archived SMV ROM-info header")
    if f"{u32(rom_info_start + 3):08x}" != meta["rom_info"]["crc32"]:
        raise MovieWindowError("movie ROM CRC differs from pinned source metadata")
    controller_data_offset = u32(0x1C)
    if controller_data_offset != meta.get("controller_data_offset"):
        raise MovieWindowError("controller stream offset differs from source manifest")
    if first + frames > size:
        raise MovieWindowError("requested movie window extends past sample_count")
    start = controller_data_offset + first * 2
    stop = start + frames * 2
    if stop > len(data):
        raise MovieWindowError("movie controller stream truncated")
    raw = data[start:stop]
    samples = struct.unpack("<" + "H" * frames, raw)
    if any(value == 0xFFFF or value & 0x000F for value in samples):
        raise MovieWindowError("window contains a reset marker or reserved joypad bits")
    masks = [translate_mask(value) for value in samples]
    segments = runs(masks)
    return {
        "schema_version": 1,
        "movie_frame_range": [first, first + frames - 1],
        "frames": frames,
        "movie_uid": uid,
        "movie_original_rom_crc32": meta["rom_info"]["crc32"],
        "raw_controller_window_sha256": hashlib.sha256(raw).hexdigest(),
        "relative_input_segments": [
            {"start": start, "duration": duration, "mask": f"0x{mask:03X}"}
            for start, duration, mask in segments
        ],
        "source_limit": (
            "This is source controller evidence only. Input offset zero is "
            "NOT a known race entry. An independent original movie-state "
            "trace must calibrate the movie-frame anchor; scene-keyed native "
            "and original race entry must be measured before replay."
        ),
    }


def shifted_input_file(report: dict, race_entry_frame: int) -> str:
    if type(race_entry_frame) is not int or race_entry_frame < 0:
        raise MovieWindowError("guest race-entry frame must be nonnegative integer")
    lines = [
        "# SCENE-RELATIVE archived P1 movie input; input origin remains caller-supplied.",
        f"# original movie frames {report['movie_frame_range']} (not independently anchored here)",
        f"# assigned target race-entry frame {race_entry_frame}",
    ]
    for item in report["relative_input_segments"]:
        lines.append(
            f"{race_entry_frame + item['start']}:{item['duration']}:{int(item['mask'], 16):03x}"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--movie", type=Path, default=ARCHIVE)
    ap.add_argument("--meta", type=Path, default=METADATA)
    ap.add_argument("--first-movie-frame", type=int, required=True)
    ap.add_argument("--frames", type=int, required=True)
    ap.add_argument("--race-entry-frame", type=int,
                    help="caller-measured target race entry for optional input export")
    ap.add_argument("--input-out", type=Path)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    if (args.input_out is None) != (args.race_entry_frame is None):
        ap.error("--input-out and --race-entry-frame must be supplied together")
    data, member = read_movie(args.movie)
    meta = json.loads(args.meta.read_text(encoding="utf-8"))
    report = window(data, meta, args.first_movie_frame, args.frames)
    report["source_path"] = args.movie.as_posix()
    report["source_container_member"] = member
    report["source_movie_sha256"] = hashlib.sha256(data).hexdigest()
    if args.input_out is not None:
        args.input_out.parent.mkdir(parents=True, exist_ok=True)
        args.input_out.write_text(shifted_input_file(report, args.race_entry_frame),
                                  encoding="utf-8")
    out = json.dumps(report, indent=2) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(out, encoding="utf-8")
    else:
        print(out, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
