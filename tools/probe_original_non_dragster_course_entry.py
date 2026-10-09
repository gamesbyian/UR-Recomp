#!/usr/bin/env python3
"""Input-only fresh-process original/native course-entry comparison.

First targets are intentionally NOT Dragster: Zoom Zoo (circuit, stream 2)
and Jumps (timed stunt, stream 13). Use the same stock-menu scripted
controller route on original Snes9x and native Authentic. No guest memory
writes or save-state transplants. Assert *full* decompressed course identity
before interpreting player positions and any event-phase observations.

This is a bounded start-state oracle. It cannot certify a completed lap,
finish, stunt score or result without a separate full-event capture.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import struct
from pathlib import Path

from analyze_rnc_streams import find_streams
from rnc_method1 import unpack_method1
from probe_runtime_course_payload import (
    is_fully_loaded_course, rank_spawn_assignment_candidates,
)
import probe_jumpover_fallthrough_native as jf

ROOT = Path(__file__).resolve().parents[1]
USA_ROM_SHA256 = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
# (stream ordinal, track id, menu tour selection, track row, classification)
CASES = {
    "zoom-zoo": (2, 1, 0, 1, "circuit-a"),
    "jumps": (13, 12, 2, 2, "stunt"),
}
SAMPLES = (0, 1, 2, 4, 8, 16, 32, 64)
WRAM_BYTES = 0x20000
COURSE_RAM_OFFSET = 0x10000
MENU_PREFIX = """
until 009F == D7 3600
wait 60
press a 2
until 009F == 3C 1200
wait 60
press a 2
until 009F == 6D 1200
wait 60
"""
# These original menu cursor steps reuse tested tour2 and Jumpover stock
# routes; confirmation is guarded by selectedOption (7E:009B).
# No guest pointer or tournament/frontend API is used.


class CourseEntryEvidenceError(ValueError):
    pass


def original_menu_script(case_name: str) -> str:
    if case_name not in CASES:
        raise CourseEntryEvidenceError("unrecognized original course case")
    _, _, tour, row, _ = CASES[case_name]
    lines = MENU_PREFIX.strip().splitlines()
    if tour:
        # Tour index 2 / Shuffler is reached with one Down edge
        # in the existing tour2 script; do not generalize this grid
        # mapping into a formula for all nine tours.
        if tour != 2:
            raise CourseEntryEvidenceError("tour navigation lacks a validated original route")
        lines += ["press down 2", "until 009B == 02 600", "wait 30"]
    lines += ["press a 2", "until 009F == F6 1200", "wait 60"]
    for _ in range(row):
        lines += ["press down 2", "wait 12"]
    lines += [f"until 009B == {row:02X} 600", "wait 30",
              "press a 2", "until 009F == 16 1200",
              "wait 60", "press a 2", "until 0313 == 01 1800",
              "dump race-entered"]
    current = 0
    for frame in SAMPLES[1:]:
        lines += [f"wait {frame - current}", f"dump race-plus-{frame:03d}"]
        current = frame
    lines.append("quit")
    return "\n".join(lines) + "\n"


def sample_state(wram: bytes, case_name: str, decoded: bytes) -> dict:
    if len(wram) != WRAM_BYTES:
        raise CourseEntryEvidenceError("expected exactly 128 KiB WRAM")
    stream, track_id, _, _, kind = CASES[case_name]
    if wram[0x00CE] != track_id or wram[0x0313] != 1:
        raise CourseEntryEvidenceError(
            f"not active original {case_name}: track {wram[0x00CE]} race {wram[0x0313]}"
        )
    if not is_fully_loaded_course(decoded, wram[COURSE_RAM_OFFSET:]):
        raise CourseEntryEvidenceError(
            f"{case_name} stream {stream} is not fully installed at 7F:0000"
        )
    u = lambda off: struct.unpack_from("<H", wram, off)[0]
    s = lambda off: struct.unpack_from("<h", wram, off)[0]
    fields = {
        "p1_x": u(0x0411), "p1_y": u(0x0415),
        "p2_x": u(0x0413), "p2_y": u(0x0417),
        "p1_speed_x": s(0x04B7), "p1_speed_y": s(0x04BB),
        "p1_contact_stored": u(0x0E95), "p2_contact_stored": u(0x0E97),
        "p1_laps_remaining": u(0x0EF1),
        "p1_boost": u(0x11CF),
        # USA bank-81 live timer digits: distinct minutes, tens, seconds,
        # tenths and six-step subtick phase. Numeric decoding is deferred
        # until an actual input-only reference/native trace is retained.
        "timer_minutes_raw": u(0x0E0F),
        "timer_tens_raw": u(0x0E13),
        "timer_seconds_raw": u(0x0E17),
        "timer_tenths_raw": u(0x0E1B),
        "timer_subtick_raw": u(0x0E1F),
    }
    return fields


def samples_from_directory(directory: Path, case_name: str, decoded: bytes) -> list[dict]:
    rows = []
    for frame in SAMPLES:
        name = "race-entered" if frame == 0 else f"race-plus-{frame:03d}"
        path = directory / f"{name}.wram.bin"
        if not path.is_file():
            raise CourseEntryEvidenceError(f"required guest snapshot absent: {path}")
        rows.append({"relative_frame": frame, **sample_state(path.read_bytes(), case_name, decoded)})
    return rows


def first_difference(reference: list[dict], native: list[dict]) -> dict | None:
    if len(reference) != len(SAMPLES) or len(native) != len(SAMPLES):
        raise CourseEntryEvidenceError("incomplete reference/native sample window")
    for ref, nat in zip(reference, native):
        if ref["relative_frame"] != nat["relative_frame"]:
            raise CourseEntryEvidenceError("guest-relative frame phases do not align")
        mismatched = sorted(key for key in ref if ref[key] != nat[key])
        if mismatched:
            return {
                "relative_frame": ref["relative_frame"],
                "fields": mismatched,
                "reference_values": {k: ref[k] for k in mismatched},
                "native_values": {k: nat[k] for k in mismatched},
            }
    return None


def summarize_pair(decoded: bytes, rows: list[dict]) -> dict:
    if len(rows) != len(SAMPLES):
        raise CourseEntryEvidenceError("incomplete phase window")
    first = rows[0]
    pair_a = [int.from_bytes(decoded[i:i + 2], "little") for i in (3, 5)]
    pair_b = [int.from_bytes(decoded[i:i + 2], "little") for i in (7, 9)]
    return {
        "header_pair_a": pair_a, "header_pair_b": pair_b,
        "spawn_assignment": rank_spawn_assignment_candidates(
            pair_a, pair_b,
            {"slot1_x": first["p1_x"], "slot1_y": first["p1_y"],
             "slot2_x": first["p2_x"], "slot2_y": first["p2_y"]},
        ),
        "samples": rows,
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=tuple(CASES), required=True)
    parser.add_argument("--snesref", type=Path, required=True)
    parser.add_argument("--core", type=Path, required=True)
    parser.add_argument("--native", type=Path, required=True)
    parser.add_argument("--rom", type=Path, default=ROOT / "reference/roms/retail/Uniracers_USA.sfc")
    parser.add_argument("--sram", type=Path, default=jf.DEFAULT_SRAM)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args(argv)
    for name in ("snesref", "core", "native", "rom", "sram", "work_dir"):
        setattr(args, name, getattr(args, name).resolve())
    if sha256_file(args.rom) != USA_ROM_SHA256:
        parser.error("exact canonical USA retail ROM required; PAL uses different register addresses")
    stream, track_id, _, _, kind = CASES[args.case]
    records = list(find_streams(args.rom.read_bytes()))
    if len(records) != 45:
        parser.error("canonical ROM must contain exactly 45 valid course streams")
    decoded = unpack_method1(records[stream - 1][1])
    work = args.work_dir / args.case
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    script = work / "course-entry.script"
    script.write_text(original_menu_script(args.case), encoding="utf-8")
    ref_log = jf.run_reference(work, args, script, [])
    rf = jf.race_entry_frame(ref_log)
    if rf is None:
        raise CourseEntryEvidenceError(f"reference never reached {args.case}: {ref_log[-2400:]}")
    nat_log = jf.run_native(work, args, script, [], 0)
    nf = jf.race_entry_frame(nat_log)
    if nf is None:
        raise CourseEntryEvidenceError(f"native never reached {args.case}: {nat_log[-2400:]}")
    # Scripts are scene-keyed. No absolute input frame alignment is required.
    reference = samples_from_directory(work / "ref", args.case, decoded)
    native = samples_from_directory(work / "native", args.case, decoded)
    difference = first_difference(reference, native)
    result = {
        "schema_version": 1,
        "qualification": "fresh boot, stock menu input only, no guest WRAM writes",
        "course": {"id": f"course:{stream:02d}", "stream_index": stream,
                   "track_id": track_id, "kind": kind, "case": args.case},
        "rom_sha256": sha256_file(args.rom),
        "sram_sha256": sha256_file(args.sram),
        "native_executable_sha256": sha256_file(args.native),
        "reference_core_sha256": sha256_file(args.core),
        "script_sha256": sha256_file(script),
        "reference_race_entry_frame": rf,
        "native_race_entry_frame": nf,
        "entry_frame_offset": nf - rf,
        "reference": summarize_pair(decoded, reference),
        "native": summarize_pair(decoded, native),
        "first_divergence": difference,
        "parity": "passed_entry_window" if difference is None else "discrepant_entry_window",
        "scope_limit": (
            "Full decoded USA course identity and first 64 active frames only. "
            "No finish, complete lap, 45-second stunt timeout, score or result certified."
        ),
    }
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                                 encoding="utf-8")
    print(json.dumps({"course": result["course"], "parity": result["parity"],
                      "first_divergence": difference,
                      "reference_spawn": result["reference"]["spawn_assignment"]["discriminator"],
                      "native_spawn": result["native"]["spawn_assignment"]["discriminator"]}))
    return 0 if difference is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
