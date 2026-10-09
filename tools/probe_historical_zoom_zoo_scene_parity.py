#!/usr/bin/env python3
"""Reference/native Zoom Zoo semantic probe using original 2014 movie INPUT.

This is deliberately scene-relative and read-only for the guest. The movie
provides a P1 input seed, not a savestate or guaranteed reproduction of the
2014 player's starting conditions. Both targets boot original menu routes
from the same supplied SRAM; their independently observed guest entry
frames are used to rebase all subsequent input samples. A recorded +/-1
phase hypothesis permits diagnosing the uncertain movie-frame convention.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import struct
from pathlib import Path

import probe_jumpover_fallthrough_native as jf
import probe_original_non_dragster_course_entry as entry
import extract_historical_smv_scene_window as movie
import verify_historical_zoom_zoo_scene_anchor as anchor
from analyze_rnc_streams import find_streams
from rnc_method1 import unpack_method1
from probe_runtime_course_payload import is_fully_loaded_course
from summarize_zoo_scene_event_transitions import paired_event_diagnostics

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_MOVIE_START = 3190
ORIGINAL_WINDOW_FRAMES = 1811  # 3190..5000, both endpoints included.
PINNED_INPUT_FRAMES = 1810  # 3190..4999; includes every observed guest input frame.
PINNED_INPUT_SHA256 = "e77f10e4d652dfb2ed9afcf4c252e3e9f14e551a30edbbaa2a69ec50996f90b6"
# Movie-frame 3400/3800 (+210/+610 relative to the 3190 scene
# anchor) have the nearest *sampled* original Zoom Zoo rider positions
# to ROM candidate 0x24 cells: 91 and 54 world-X units respectively.
# A one-frame transient can disappear between sparse snapshots.
ORIGINAL_ANCHOR_SAMPLES = (
    128, 210, 256, 384, 512, 610, 768, 1010, 1024,
    1280, 1410, 1536, 1800,
)
DENSE_CONTACT_WINDOWS = ((190, 230), (590, 630))  # old near-cell tests
# Independent ORIGINAL Snes9x WRAM trace from run 37184022134:
# P1 checkpoint/gate/lap writes at 3408, 3794, 4031, 4722, 4911,
# with course scene entry at 3190. First two are already inside the
# original contact windows above. These extra windows cover the
# previously unsampled original events including second lap decrement.
ORIGINAL_PROGRESSION_WRITE_FRAMES = (3408, 3794, 4031, 4722, 4911)
ORIGINAL_PROGRESSION_RELATIVE_FRAMES = tuple(
    frame - ORIGINAL_MOVIE_START for frame in ORIGINAL_PROGRESSION_WRITE_FRAMES
)
ADDITIONAL_EVENT_WINDOWS = ((833, 849), (1524, 1540), (1713, 1729))
EXTRA_SAMPLES = tuple(sorted(set(ORIGINAL_ANCHOR_SAMPLES).union(
    *(range(first, last + 1) for first, last in
      (*DENSE_CONTACT_WINDOWS, *ADDITIONAL_EVENT_WINDOWS))
)))
CHECKPOINTS = (*entry.SAMPLES, *EXTRA_SAMPLES)


class SceneReplayError(ValueError):
    pass


def verified_archived_scene_input(data: bytes, metadata: dict) -> dict:
    """Reject modified 2014 controller samples even with a copied valid UID.

    The 1,810-source-frame SHA covers original frames 3190..4999; this
    includes the last compared checkpoint at +1800. The returned 1,811
    sample window retains existing archival chronology/report compatibility.
    The extra final input sample 5000 is after the last compared checkpoint
    and is not evidence of state parity at that frame.
    """
    prefix = movie.window(
        data, metadata, ORIGINAL_MOVIE_START, PINNED_INPUT_FRAMES
    )
    actual = prefix["raw_controller_window_sha256"]
    if actual != PINNED_INPUT_SHA256:
        raise SceneReplayError(
            "archived Zoo controller input differs from pinned 2014 SMV "
            f"window: expected {PINNED_INPUT_SHA256}, got {actual}"
        )
    return movie.window(data, metadata, ORIGINAL_MOVIE_START, ORIGINAL_WINDOW_FRAMES)


def replay_script() -> str:
    text = entry.original_menu_script("zoom-zoo")
    if not text.endswith("quit\n"):
        raise SceneReplayError("original Zoo menu route changed")
    lines = text[:-len("quit\n")].rstrip().splitlines()
    previous = entry.SAMPLES[-1]
    for frame in EXTRA_SAMPLES:
        if frame <= previous or frame >= ORIGINAL_WINDOW_FRAMES:
            raise SceneReplayError("extended guest checkpoint outside bounded movie")
        lines.extend((f"wait {frame - previous}", f"dump race-plus-{frame:04d}"))
        previous = frame
    return "\n".join(lines + ["quit", ""])


def movie_events(window_report: dict, target_entry_frame: int, phase: int = 0
                 ) -> list[tuple[int, int, int]]:
    if type(target_entry_frame) is not int or target_entry_frame < 0:
        raise SceneReplayError("race entry must be an observed nonnegative frame")
    if type(phase) is not int or phase not in (-1, 0, 1):
        raise SceneReplayError("movie phase must be -1, 0 or 1")
    if (window_report.get("movie_frame_range") != [3190, 5000]
            or window_report.get("frames") != ORIGINAL_WINDOW_FRAMES):
        raise SceneReplayError("original movie input window is unverified")
    events = []
    for segment in window_report["relative_input_segments"]:
        start = target_entry_frame + phase + segment["start"]
        length = segment["duration"]
        if start < 0 or length < 1:
            raise SceneReplayError("event requires a negative frame or zero duration")
        events.append((start, length, int(segment["mask"], 16)))
    for old, new in zip(events, events[1:]):
        if old[0] + old[1] > new[0]:
            raise SceneReplayError("overlapping movie controller event runs")
    return events


def read_guest(path: Path, frame: int, decoded: bytes | None = None) -> dict:
    if not path.is_file():
        raise SceneReplayError(f"missing event-relative WRAM frame {frame}: {path}")
    image = path.read_bytes()
    if len(image) != entry.WRAM_BYTES:
        raise SceneReplayError(f"invalid 128 KiB WRAM frame {frame}: {path}")
    if (decoded is not None and image[0x0313] == 1
            and not is_fully_loaded_course(decoded, image[entry.COURSE_RAM_OFFSET:])):
        raise SceneReplayError(f"frame {frame} has no fully installed canonical Zoom Zoo course")
    row = {"relative_frame": frame, "menu": image[0x009F],
           "in_race": image[0x0313], "track_id": image[0x00CE]}
    if row["in_race"] == 1:
        if row["track_id"] != 1:
            raise SceneReplayError(f"race frame {frame} has wrong track ID {row['track_id']}")
        u = lambda offset: struct.unpack_from("<H", image, offset)[0]
        s = lambda offset: struct.unpack_from("<h", image, offset)[0]
        row.update({
            "p1_x": u(0x0411), "p1_y": u(0x0415),
            "p1_vx": s(0x04B7), "p1_vy": s(0x04BB),
            "p1_stored_contact": u(0x0E95),
            "p1_next_checkpoint": u(0x1199),
            "p1_finish_gate": u(0x119D),
            "p1_laps_remaining": u(0x0EF1),
            "p1_boost": u(0x11CF),
        })
    return row


def load_rows(directory: Path, decoded: bytes | None = None) -> list[dict]:
    rows = []
    for frame in CHECKPOINTS:
        name = "race-entered" if frame == 0 else (
            f"race-plus-{frame:03d}" if frame in entry.SAMPLES
            else f"race-plus-{frame:04d}"
        )
        rows.append(read_guest(directory / f"{name}.wram.bin", frame, decoded))
    return rows


def compare(reference: list[dict], native: list[dict]) -> dict | None:
    if len(reference) != len(CHECKPOINTS) or len(native) != len(CHECKPOINTS):
        raise SceneReplayError("incomplete course input replay snapshots")
    for ref, nat in zip(reference, native):
        if ref["relative_frame"] != nat["relative_frame"]:
            raise SceneReplayError("native/reference guest-frame alignment broken")
        fields = sorted(k for k in set(ref) | set(nat) if ref.get(k) != nat.get(k))
        if fields:
            return {"relative_frame": ref["relative_frame"], "fields": fields,
                    "reference": {k: ref.get(k) for k in fields},
                    "native": {k: nat.get(k) for k in fields}}
    return None


def expected_active_window(rows: list[dict]) -> dict:
    """Prevent matched premature exits from claiming full active-window parity.

    The archived original Zoom Zoo run remains active through movie frame 5000.
    A matched transition to another menu is observable but is not a passed
    1811-frame active-circuit comparison.
    """
    if len(rows) != len(CHECKPOINTS):
        raise SceneReplayError("incomplete course input replay snapshots")
    for expected_frame, row in zip(CHECKPOINTS, rows):
        if row.get("relative_frame") != expected_frame:
            raise SceneReplayError("guest-relative active-window phases do not align")
        if row.get("in_race") != 1 or row.get("track_id") != 1:
            return {
                "status": "left_original_active_zoom_zoo_window",
                "first_nonactive_relative_frame": expected_frame,
                "race_active": row.get("in_race"),
                "track_id": row.get("track_id"),
                "menu": row.get("menu"),
            }
    return {"status": "full_original_active_zoom_zoo_window"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--snesref", type=Path, required=True)
    ap.add_argument("--core", type=Path, required=True)
    ap.add_argument("--native", type=Path, required=True)
    ap.add_argument("--rom", type=Path, default=entry.ROOT / "reference/roms/retail/Uniracers_USA.sfc")
    ap.add_argument("--sram", type=Path, default=jf.DEFAULT_SRAM)
    ap.add_argument("--work-dir", type=Path, required=True)
    ap.add_argument("--phase", type=int, choices=(-1, 0, 1), default=0)
    ap.add_argument("--require-original-sram", action="store_true")
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    for key in ("snesref", "core", "native", "rom", "sram", "work_dir"):
        setattr(args, key, getattr(args, key).resolve())
    if sha256_file(args.rom) != entry.USA_ROM_SHA256:
        ap.error("requires exact canonical USA retail ROM")
    course_streams = list(find_streams(args.rom.read_bytes()))
    if len(course_streams) != 45:
        ap.error("canonical ROM must have 45 decoded course streams")
    decoded_zoo = unpack_method1(course_streams[1][1])
    meta = json.loads(movie.METADATA.read_text(encoding="utf-8"))
    anchor.build(
        meta, json.loads(anchor.REFERENCE.read_text(encoding="utf-8")),
        json.loads(anchor.REPLAY.read_text(encoding="utf-8"))
    )
    source, _ = movie.read_movie(movie.ARCHIVE)
    window_report = verified_archived_scene_input(source, meta)
    source_sram_equal = sha256_file(args.sram) == meta.get("emitted_sram_sha256")
    if args.require_original_sram and not source_sram_equal:
        ap.error("supplied SRAM differs from recorded movie's original 8 KiB SRAM")
    work = args.work_dir / "zoom-zoo-2014-scene"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    calibrate = work / "calibrate"
    calibrate.mkdir()
    calibration_script = calibrate / "entry.script"
    calibration_script.write_text(entry.original_menu_script("zoom-zoo"), encoding="utf-8")
    ref_log = jf.run_reference(calibrate, args, calibration_script, [])
    nat_log = jf.run_native(calibrate, args, calibration_script, [], 0)
    rf, nf = jf.race_entry_frame(ref_log), jf.race_entry_frame(nat_log)
    if rf is None or nf is None:
        raise SceneReplayError("both fresh original/native runs must reach Zoo race entry")
    replay = work / "replay"
    replay.mkdir()
    script = replay / "scene.script"
    script.write_text(replay_script(), encoding="utf-8")
    events = movie_events(window_report, rf, args.phase)
    replay_ref_log = jf.run_reference(replay, args, script, events)
    replay_nat_log = jf.run_native(replay, args, script, events, nf - rf)
    if jf.race_entry_frame(replay_ref_log) != rf or jf.race_entry_frame(replay_nat_log) != nf:
        raise SceneReplayError("replayed run shifted its previously calibrated race-entry frame")
    reference = load_rows(replay / "ref", decoded_zoo)
    native = load_rows(replay / "native", decoded_zoo)
    first = compare(reference, native)
    event_diagnostics = paired_event_diagnostics(reference, native)
    reference_window = expected_active_window(reference)
    native_window = expected_active_window(native)
    complete_active_window = all(
        row["status"] == "full_original_active_zoom_zoo_window"
        for row in (reference_window, native_window)
    )
    report = {
        "schema_version": 1, "kind": "historical-2014-zoo-scene-relative-input-probe",
        "rom_sha256": sha256_file(args.rom),
        "reference_core_sha256": sha256_file(args.core),
        "native_executable_sha256": sha256_file(args.native),
        "run_sram_sha256": sha256_file(args.sram),
        "movie_embedded_sram_8k_matches_run": source_sram_equal,
        "pinned_original_input_1810_sha256": PINNED_INPUT_SHA256,
        "archived_input_window_sha256": window_report["raw_controller_window_sha256"],
        "archived_frame_range": window_report["movie_frame_range"],
        "scene_input_phase_hypothesis": args.phase,
        "reference_race_entry": rf, "native_race_entry": nf,
        "guest_entry_offset": nf - rf,
        "relative_checkpoints": list(CHECKPOINTS),
        "dense_contact_windows": [list(w) for w in DENSE_CONTACT_WINDOWS],
        "original_snes9x_source_event_frames": list(ORIGINAL_PROGRESSION_WRITE_FRAMES),
        "additional_dense_event_windows": [list(w) for w in ADDITIONAL_EVENT_WINDOWS],
        "observation_count": len(CHECKPOINTS),
        "first_divergence": first,
        "event_state_diagnostics": event_diagnostics,
        "reference_active_window": reference_window,
        "native_active_window": native_window,
        "valid_1811_frame_active_window": complete_active_window,
        "reference": reference, "native": native,
        "scope_limit": (
            "This pairs archived 2014 original input on two newly booted "
            "engines after scene entry, NOT the complete archived original "
            "savestate. Nonmatching SRAM further reduces historical equivalence. "
            "Original input phase convention +/-1 remains a hypothesis."
        ),
    }
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "first_divergence": first, "movie_phase": args.phase,
        "first_progression_state_disagreement": (
            event_diagnostics["first_progression_state_disagreement"]
        ),
        "reference_progression_change_interval_count": (
            event_diagnostics["reference_observed"]["progression_change_interval_count"]
        ),
        "native_progression_change_interval_count": (
            event_diagnostics["native_observed"]["progression_change_interval_count"]
        ),
        "source_sram_match": source_sram_equal, "guest_entry_offset": nf - rf,
        "valid_1811_frame_active_window": complete_active_window,
    }))
    return 0 if first is None and complete_active_window else 1


if __name__ == "__main__":
    raise SystemExit(main())
