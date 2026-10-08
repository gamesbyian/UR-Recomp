#!/usr/bin/env python3
"""Scout Walker/Ping Pong's unmarked second-loop shortcut on both engines.

Historical lead: GameFAQs Uniracers NTSC scores (thread 41488930) reports
that the SECOND large loop on Ping Pong can be bypassed by timing, without a
yellow shortcut marker. No recovered input movie pins the jump frame.
This tool therefore captures a right-only traversal and a controlled jump
candidate WITHOUT calling a trajectory a successful skip. Manual harness:
the source, libretro reference, native executable and original ROM are needed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import struct
from pathlib import Path

import probe_jumpover_fallthrough_native as common

ROOT = Path(__file__).resolve().parents[1]
TRACK_ID = 21               # course:22, Walker Ping Pong; ROM selector is index - 1
TRACK_NAME = "Ping Pong"
WRAM_SIZE = 0x20000
FIELDS = {
    "x": (0x0411, False),
    "y": (0x0415, False),
    "vx": (0x04B7, True),
    "vy": (0x04BB, True),
    "air": (0x0545, False),
    "contact": (0x0E95, False),
    "checkpoint": (0x1199, False),
    "laps_remaining": (0x0EF1, False),
    "boost": (0x11CF, False),
    "finish_gate": (0x119D, False),
}
# Tour index 4 = Walker (two Down presses from Crawler), track index 1 =
# Ping Pong (one Down). Bind both selectors before confirming.
MENU = """\
until 009F == D7 3600
wait 60
press a 2
until 009F == 3C 1200
wait 60
press a 2
until 009F == 6D 1200
wait 60
press down 2
wait 16
press down 2
wait 20
until 009B == 04 120
press a 2
until 009F == F6 1200
wait 60
press down 2
wait 20
until 009B == 01 120
press a 2
until 009F == 16 1200
wait 60
press a 2
until 0313 == 01 1800
dump race-entered
"""


class ScoutError(ValueError):
    """Missing or non-Ping-Pong race evidence, or an invalid intervention."""


def route_events(entry: int, frames: int, jump_at: int | None = None,
                 jump_frames: int = 0) -> list[tuple[int, int, int]]:
    """Frame-exact right-only input, optionally B+Right for one bounded window."""
    if type(entry) is not int or entry < 0 or type(frames) is not int or not 1 <= frames <= 4000:
        raise ScoutError("invalid race entry or bounded scan duration")
    if jump_at is None:
        if jump_frames:
            raise ScoutError("jump_frames requires jump_at")
        return [(entry, frames + 1, 0x0080)]
    if (type(jump_at) is not int or type(jump_frames) is not int or
            not 1 <= jump_at < frames or not 1 <= jump_frames <= 120 or
            jump_at + jump_frames >= frames):
        raise ScoutError("jump intervention must fit inside sampled race window")
    return [
        (entry, jump_at, 0x0080),
        (entry + jump_at, jump_frames, 0x0081),
        (entry + jump_at + jump_frames, frames + 1 - jump_at - jump_frames, 0x0080),
    ]


def fixture_script(frames: int, stride: int) -> str:
    if (type(frames) is not int or type(stride) is not int or
            not 10 <= frames <= 4000 or not 1 <= stride <= 60):
        raise ScoutError("invalid bounded frame sampling configuration")
    points = sorted(set(range(0, frames + 1, stride)) | {frames})
    lines = [MENU.rstrip("\n")]
    current = 0
    for frame in points:
        if frame > current:
            lines.append(f"wait {frame - current}")
            current = frame
        lines.append(f"dump s{frame:04d}")
    lines.append("quit")
    return "\n".join(lines) + "\n"


def samples(frames: int, stride: int) -> list[int]:
    return sorted(set(range(0, frames + 1, stride)) | {frames})


def decode(wram: bytes) -> dict:
    row = {}
    for key, (addr, signed) in FIELDS.items():
        # Air-time is a word in guest memory (historic TAS bot used low byte).
        row[key] = struct.unpack_from("<h" if signed else "<H", wram, addr)[0]
    return row


def load_series(directory: Path, frames: int, stride: int) -> dict[int, dict]:
    out = {}
    for frame in samples(frames, stride):
        path = directory / f"s{frame:04d}.wram.bin"
        if not path.is_file():
            raise ScoutError(f"missing sampled WRAM frame {frame}: {path}")
        wram = path.read_bytes()
        if len(wram) != WRAM_SIZE:
            raise ScoutError(f"WRAM frame {frame} is {len(wram)} bytes, not 131072")
        if wram[0x00CE] != TRACK_ID or wram[0x0313] != 1:
            raise ScoutError(f"frame {frame} is not an active Ping Pong circuit "
                             f"(track {wram[0x00CE]}, inRace {wram[0x0313]})")
        out[frame] = decode(wram)
    return out


def compare(reference: dict[int, dict], native: dict[int, dict]) -> dict:
    if not reference or set(reference) != set(native):
        raise ScoutError("native/reference captures need identical, nonempty frame sets")
    mismatch = next(((f, [k for k in FIELDS if reference[f][k] != native[f][k]])
                     for f in sorted(reference)
                     if reference[f] != native[f]), None)
    def digest(rows):
        return hashlib.sha256(
            json.dumps([(f, rows[f]) for f in sorted(rows)], sort_keys=True).encode()
        ).hexdigest()
    return {
        "compared_frames": len(reference),
        "first_divergence": ({"relative_frame": mismatch[0], "fields": mismatch[1]}
                             if mismatch else None),
        "reference_sha256": digest(reference),
        "native_sha256": digest(native),
        "reference_checkpoint_states": sorted({r["checkpoint"] for r in reference.values()}),
        "reference_laps_remaining": sorted({r["laps_remaining"] for r in reference.values()}),
        "classification": "scouting_only_no_shortcut_claim",
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--snesref", type=Path, required=True)
    ap.add_argument("--core", type=Path, required=True)
    ap.add_argument("--native", type=Path, required=True)
    ap.add_argument("--rom", type=Path, required=True)
    ap.add_argument("--sram", type=Path, default=common.DEFAULT_SRAM)
    ap.add_argument("--work-dir", type=Path, required=True)
    ap.add_argument("--frames", type=int, default=720)
    ap.add_argument("--stride", type=int, default=10)
    ap.add_argument("--jump-at", type=int, help="guest frames after race entry")
    ap.add_argument("--jump-frames", type=int, default=12)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args(argv)
    for key in ("snesref", "core", "native", "rom", "sram", "work_dir"):
        setattr(args, key, getattr(args, key).resolve())
    try:
        script = fixture_script(args.frames, args.stride)
        route_events(0, args.frames, args.jump_at,
                     args.jump_frames if args.jump_at is not None else 0)
    except ScoutError as exc:
        ap.error(str(exc))

    # Discover each engine's race-entry frame via stock, scene-keyed menus.
    # This avoids treating native/reference frontend cadence differences as
    # controller timing. No guest writes or state transplants are used.
    work = args.work_dir
    work.mkdir(parents=True, exist_ok=True)
    boot_script = work / "boot.script"
    boot_script.write_text(MENU + "quit\n", encoding="utf-8")
    ref_entry = common.race_entry_frame(common.run_reference(work, args, boot_script, []))
    native_entry = common.race_entry_frame(common.run_native(work, args, boot_script, [], 0))
    if ref_entry is None or native_entry is None:
        raise SystemExit("Failed to reach both stock Ping Pong race-entry states")
    delta = native_entry - ref_entry
    cases = [( "right-only", None)]
    if args.jump_at is not None:
        cases.append(("jump-candidate", args.jump_at))
    outputs = {}
    for name, candidate in cases:
        case = work / name
        shutil.rmtree(case, ignore_errors=True)
        case.mkdir(parents=True)
        script_path = case / "probe.script"
        script_path.write_text(script, encoding="utf-8")
        events = route_events(ref_entry, args.frames, candidate,
                              args.jump_frames if candidate is not None else 0)
        ref_log = common.run_reference(case, args, script_path, events)
        nat_log = common.run_native(case, args, script_path, events, delta)
        if common.race_entry_frame(ref_log) != ref_entry:
            raise SystemExit(f"{name}: reference race entry shifted")
        if common.race_entry_frame(nat_log) != native_entry:
            raise SystemExit(f"{name}: native race entry shifted")
        reference = load_series(case / "ref", args.frames, args.stride)
        native = load_series(case / "native", args.frames, args.stride)
        result = compare(reference, native)
        result["reference_first"] = reference[min(reference)]
        result["reference_last"] = reference[max(reference)]
        result["native_last"] = native[max(native)]
        result["jump_at"] = candidate
        outputs[name] = result
    report = {
        "schema_version": 1,
        "course": {"name": TRACK_NAME, "course_id": "course:22", "track_id": TRACK_ID},
        "source": "https://gamefaqs.gamespot.com/boards/588824-uniracers/41488930",
        "claim_under_test": "unmarked second large loop bypass by timed jump",
        "qualification": "all cases are input-only from stock boot; no seed or guest mutation",
        "reference_entry_frame": ref_entry,
        "native_entry_frame": native_entry,
        "sampling_stride_frames": args.stride,
        "cases": outputs,
        "conclusion": "Input-only diagnostic parity only; timed shortcut has not been admitted.",
    }
    payload = json.dumps(report, indent=2) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if all(case["first_divergence"] is None for case in outputs.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
