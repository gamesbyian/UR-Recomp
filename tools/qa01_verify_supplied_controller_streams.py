#!/usr/bin/env python3
"""Independently reopen actual QA01 replay-supplied controller files.

A source original movie-window digest alone never proves which physical pad
values a guest read. This ROM-free consumer verifies the exact on/off file
bytes, normalizes only each guest's *independently observed* race-entry clock,
and compares every resulting nonzero mask/duration event. It does not run
either emulator, parse the source SMV, or prove CPU joypad poll consumption.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

SCHEMA = "ur-qa01-independent-supplied-controller-streams/1"
AB = "ur-qa01-capture-ab-replay-control/1"
LINE = re.compile(rb"(0|[1-9][0-9]*):([1-9][0-9]*):([0-9a-f]{1,3})(:0)?\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
HEX40 = re.compile(r"[0-9a-f]{40}\Z")


def must(valid: bool, reason: str) -> None:
    if not valid:
        raise ValueError(reason)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def reopen(path: Path, *, native: bool, pinned: bool, origin: int) -> tuple[bytes, list[dict]]:
    must(path.is_file() and not path.is_symlink(),
         "missing/symlinked actual original/native input file: " + str(path))
    must(type(origin) is int and origin >= 0, "invalid real guest frame origin")
    raw = path.read_bytes()
    must(len(raw) <= 2_000_000 and (not raw or raw.endswith(b"\n")) and
         b"\r" not in raw, "noncanonical original/native supplied input text")
    decoded = []
    previous_end = -1
    for line in raw.splitlines():
        hit = LINE.fullmatch(line)
        must(hit is not None, "invalid source guest controller segment")
        additional = hit.group(4)
        must((additional is None if (not native or pinned) else additional == b":0"),
             "unexpected original/native guest input transport fields")
        start, duration, mask = (int(hit.group(1)), int(hit.group(2)),
                                 int(hit.group(3), 16))
        must(0 < mask <= 0x0FFF and 0 < duration <= 1_000_000,
             "invalid actual supplied source controller mask/duration")
        relative = start - origin
        must(relative >= 0 and relative >= previous_end,
             "guest source controller stream shifted, unordered or overlapping")
        must(start + duration < 10_000_000,
             "unbounded source controller event")
        previous_end = relative + duration
        decoded.append({"start_relative_to_actual_guest_entry": relative,
                        "duration_frames": duration,
                        "nonzero_mask_hex": f"{mask:03x}"})
    return raw, decoded


def audit(baseline: dict, captured: dict, sources: dict[str, Path]) -> dict:
    must(type(sources) is dict and set(sources) ==
         {"off_original", "off_native", "on_original", "on_native"},
         "require all four actual original/native on/off supplied input files")
    required = ("source_sha", "rom_sha256", "original_movie_sha256",
                "original_movie_window_sha256", "reference_core_sha256",
                "native_executable_sha256", "source_sram_sha256",
                "reference_entry", "native_entry", "native_backend")
    # The original/natively supplied input bytes are independently reopened;
    # top-level producer 'input_sha256' names the differing command script,
    # not these actual controller segments.
    for side, record in (("off", baseline), ("on", captured)):
        must(type(record) is dict and record.get("schema_version") == 1 and
             record.get("admission") ==
             "investigative candidate; not a release-ledger pass" and
             all(key in record for key in required if key != "source_sha"),
             side + " missing source-qualified replay producer receipt")
    for key in required:
        if key == "source_sha":
            continue
        must(baseline[key] == captured[key],
             "changed original/native producer identity or host frame: " + key)
    must(baseline["native_backend"] in ("pinned-baldosa", "native"),
         "unsupported original/native input transport")
    controls = (baseline.get("qa01_capture_ab_control"),
                captured.get("qa01_capture_ab_control"))
    for mode, record in zip(("off", "on"), controls):
        must(type(record) is dict and record.get("schema") == AB and
             type(record.get("repository_source_sha")) is str and
             HEX40.fullmatch(record["repository_source_sha"]) and
             type(record.get("controller_movie_window_sha256")) is str and
             HEX64.fullmatch(record["controller_movie_window_sha256"]) and
             record["controller_movie_window_sha256"] ==
             baseline["original_movie_window_sha256"],
             mode + " missing actual 2014 controller-window binding")
        must(record.get("capturing_continuous_frames") == (mode == "on"),
             "capture-on/off input receipts labelled incorrectly")
        must(record.get("cpu_joypad_reads_proven") is False and
             record.get("full_event_accepted") is False,
             "unsupported actual CPU controller read/gameplay acceptance claim")
    must(controls[0]["repository_source_sha"] ==
         controls[1]["repository_source_sha"],
         "capture changed producer source commit")
    pinned = baseline["native_backend"] == "pinned-baldosa"
    logs = {}
    for mode, report, control in zip(("off", "on"),
                                      (baseline, captured), controls):
        for side, prefix in (("original", "reference"),
                             ("native", "native")):
            raw, events = reopen(sources[mode + "_" + side],
                                 native=(side == "native"),
                                 pinned=pinned,
                                 origin=report[prefix + "_entry"]
                                 if prefix == "reference" else report["native_entry"])
            field = prefix + "_supplied_input_sha256"
            sizefield = prefix + "_supplied_input_bytes"
            must(type(control.get(field)) is str and HEX64.fullmatch(control[field])
                 and sha(raw) == control[field] and
                 type(control.get(sizefield)) is int and len(raw) == control[sizefield],
                 "actual guest controller file differs from producer SHA/length")
            logs[mode + "_" + side] = {"bytes": raw, "events": events}
    for side in ("original", "native"):
        must(logs["off_" + side]["bytes"] == logs["on_" + side]["bytes"],
             "same-guest on/off supplied controller bytes changed")
    for mode in ("off", "on"):
        must(logs[mode + "_original"]["events"] ==
             logs[mode + "_native"]["events"],
             "original/native source controller event segments differ after"
             " independently observed race-entry frame normalization")
    canonical = logs["on_original"]["events"]
    serialized = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return {
        "schema": SCHEMA,
        "repository_source_sha": controls[0]["repository_source_sha"],
        "source_movie_controller_window_sha256":
            controls[0]["controller_movie_window_sha256"],
        "original_actual_guest_frame_origin": baseline["reference_entry"],
        "native_actual_guest_frame_origin": baseline["native_entry"],
        "all_four_raw_guest_input_files_independently_reopened": True,
        "each_guest_on_off_exact_supplied_input_bytes_equal": True,
        "original_native_normalized_source_controller_segments_equal": True,
        "normalized_segment_population": len(canonical),
        "normalized_segment_sha256": sha(serialized.encode("ascii")),
        # Preserve every normalized segment for future source-input-to-actual-
        # bus-read joins. The SHA alone is not an independently inspectable
        # timeline; no fabricated zero-mask events are filled into gaps.
        "normalized_segments": canonical,
        "first_and_last_source_segment": [canonical[0], canonical[-1]]
            if canonical else [],
        "compiled_executables_independently_reopened": False,
        "source_SMV_bytes_independently_reopened": False,
        "actual_CPU_or_SPC_input_consumption_proven": False,
        "full_race_or_Windows_persistence_proven": False,
        "accepted_USA_events": 0,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    for item in ("baseline", "captured", "off-original-input", "off-native-input",
                 "on-original-input", "on-native-input", "output"):
        ap.add_argument("--" + item, required=True, type=Path)
    args = ap.parse_args()
    must(not args.output.exists(), "refuse overwrite of independent input receipt")
    out = audit(json.loads(args.baseline.read_text()),
                json.loads(args.captured.read_text()),
                {"off_original": args.off_original_input,
                 "off_native": args.off_native_input,
                 "on_original": args.on_original_input,
                 "on_native": args.on_native_input})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
    print("QA01 exact source-controller input files re-opened: CPU polls unknown, 0/45")


if __name__ == "__main__":
    main()
