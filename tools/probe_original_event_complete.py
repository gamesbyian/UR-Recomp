#!/usr/bin/env python3
"""QA-01/07: archived *completed* original inputs transplanted into fresh guests.

Only an observed 2014 Snes9x scene-entry/result pair can select an input
window. The same controller masks are rebased independently to the observed
reference/native guest entry. No WRAM pokes, savestate transplants or guessed
absolute native frames. A failed/partial attempt emits diagnostics, never an
accepted 45-course census row. See docs/ORIGINAL-COURSE-EVENT-CENSUS.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import analyze_rnc_streams as rnc
import extract_historical_smv_scene_window as movie
import extract_menu_visual_language as visual
import probe_attract_cycle as trace
import probe_jumpover_fallthrough_native as engine
import probe_original_non_dragster_course_entry as entry
import probe_tier_opponents as textdecode
from probe_runtime_course_payload import is_fully_loaded_course
from rnc_method1 import unpack_method1

# Stock Crawler track-select rows, independently known result-menu values.
# Switcher is the required first non-Dragster Race; source scan must actually
# observe its result before replay. No claimed historical Switcher result yet.
CASES = {
    "zoom-zoo": (2, 1, 0xBC, "circuit-a"),
    "bowl": (3, 2, 0x18, "stunt"),
    "switcher": (4, 3, 0x99, "race-b"),
}
SOURCE_HORIZON = 22000
INITIAL_FRAMES = (0, 1, 2, 4, 8, 16, 32, 64)
ZOO_PROGRESS_FRAMES = (217, 218, 219, 603, 604, 605, 840, 841, 842,
                       1531, 1532, 1533, 1720, 1721, 1722)


class CompleteEventError(ValueError):
    pass


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stock_crawler_script(slot: int) -> str:
    if slot not in (2, 3, 4):
        raise CompleteEventError("only independently established Crawler track routes")
    lines = entry.MENU_PREFIX.strip().splitlines()
    lines += ["press a 2", "until 009F == F6 1200", "wait 60"]
    for _ in range(slot - 1):
        lines += ["press down 2", "wait 12"]
    lines += [f"until 009B == {slot - 1:02X} 600", "wait 30",
              "press a 2", "until 009F == 16 1200", "wait 60",
              "press a 2", "until 0313 == 01 1800", "dump race-entered"]
    return "\n".join(lines) + "\n"


def source_event(states: dict[int, dict], track: int, result_menu: int) -> dict:
    """Detect source-original course entry and terminal result, never infer
    either from an approximate movie timestamp."""
    frames = sorted(states)
    entries = [f for f in frames if states[f]["track"] == track
               and states[f]["in_race"] == 1
               and (f == frames[0] or states.get(f - 1, {}).get("in_race") != 1
                    or states.get(f - 1, {}).get("track") != track)]
    results = [f for f in frames if states[f]["menu"] == result_menu
               and states.get(f - 1, {}).get("menu") != result_menu]
    for start in entries:
        stop = next((f for f in results if f > start and
                     states[f]["track"] == track), None)
        if stop is None:
            continue
        if any(states[f]["track"] != track or states[f]["in_race"] != 1
               for f in range(start, stop) if f in states
               and states[f]["menu"] not in (0x84, 0x2F)):
            # The event may fade or enter the results sequence before
            # the final result. Do not require in_race=1 across a fade.
            pass
        if stop - start < 250:
            raise CompleteEventError("implausibly short source event")
        tally = next((f for f in frames if start < f < stop
                      and states[f]["menu"] == 0x2F), None)
        if result_menu == 0x18 and tally is None:
            raise CompleteEventError("Stunt result missing prior 0x2F tally")
        return {"original_entry_frame": start, "original_result_frame": stop,
                "source_stunt_tally_frame": tally,
                "source_active_frames_to_result": stop - start}
    raise CompleteEventError("source movie never demonstrated this course/result pair")


def sample_frames(case: str, source_duration: int) -> list[int]:
    if source_duration <= 600:
        raise CompleteEventError("source event too short for bounded test")
    cap = min(2400, source_duration - 300)
    extra = ZOO_PROGRESS_FRAMES if case == "zoom-zoo" else ()
    return sorted(set(INITIAL_FRAMES) | set(range(120, cap + 1, 120))
                  | {f for f in extra if f <= cap})


def replay_script(slot: int, result_menu: int, frames: list[int],
                  stunt: bool) -> str:
    lines = stock_crawler_script(slot).rstrip().splitlines()
    last = 0
    for f in frames[1:]:
        lines += [f"wait {f - last}", f"dump scene-{f:05d}"]
        last = f
    if stunt:
        lines += ["until 009F == 2F 9000", "dump result-tally"]
    lines += [f"until 009F == {result_menu:02X} 9000",
              "dump result-onset", "wait 2", "dump result-stable", "quit"]
    return "\n".join(lines) + "\n"


def load_state(path: Path, decoded: bytes, track: int, active: bool) -> dict:
    if not path.is_file():
        raise CompleteEventError(f"missing guest frame {path}")
    w = path.read_bytes()
    if len(w) != 0x20000 or w[0x00CE] != track:
        raise CompleteEventError(f"wrong WRAM size or course at {path}")
    if active and (w[0x0313] != 1 or not is_fully_loaded_course(decoded, w[0x10000:])):
        raise CompleteEventError(f"premature result or wrong decoded course at {path}")
    u = lambda a: int.from_bytes(w[a:a + 2], "little")
    signed = lambda a: int.from_bytes(w[a:a + 2], "little", signed=True)
    return {"menu": w[0x009F], "in_race": w[0x0313],
            "p1_x": u(0x0411), "p1_y": u(0x0415),
            "p2_x": u(0x0413), "p2_y": u(0x0417),
            "p1_vx": signed(0x04B7), "p1_vy": signed(0x04BB),
            "p1_contact": u(0x0E95), "p2_contact": u(0x0E97),
            "p1_checkpoint": u(0x1199), "p1_finish_gate": u(0x119D),
            "p1_laps": u(0x0EF1), "p2_laps": u(0x0EF3),
            "boost": u(0x11CF), "stunt_queue_cursor": u(0x0CE3),
            "clock_raw": [w[a] for a in (0x0E0F, 0x0E13, 0x0E17,
                                           0x0E1B, 0x0E1F)]}


def load_capture(directory: Path, frames: list[int], decoded: bytes,
                 track: int, stunt: bool) -> dict:
    rows = []
    for f in frames:
        tag = "race-entered" if f == 0 else f"scene-{f:05d}"
        rows.append({"relative_frame": f,
                     **load_state(directory / f"{tag}.wram.bin", decoded, track, True)})
    final = load_state(directory / "result-stable.wram.bin", decoded, track, False)
    onset = load_state(directory / "result-onset.wram.bin", decoded, track, False)
    # Screen text is decoded from ORIGINAL PPU memory (also emitted by native
    # guest dumps), so it includes the actual finish time/lap and stunt score.
    screens = {
        "final": textdecode.screen_texts(visual.Dump(directory, "result-stable")),
        "onset": textdecode.screen_texts(visual.Dump(directory, "result-onset")),
    }
    if stunt:
        tally = load_state(directory / "result-tally.wram.bin", decoded, track, False)
        if tally["menu"] != 0x2F:
            raise CompleteEventError("not a real stunt tally screen")
        screens["tally"] = textdecode.screen_texts(visual.Dump(directory, "result-tally"))
    return {"samples": rows, "result": final, "onset": onset,
            "result_text": screens}


def diagnose(original: dict, native: dict, result_menu: int, stunt: bool) -> dict:
    r_rows, n_rows = original["samples"], native["samples"]
    if [r["relative_frame"] for r in r_rows] != [r["relative_frame"] for r in n_rows]:
        raise CompleteEventError("different original/native sampling windows")
    first = None
    for r, n in zip(r_rows, n_rows):
        differences = sorted(k for k in r if r[k] != n[k])
        if differences:
            first = {"relative_frame": r["relative_frame"], "fields": differences,
                     "reference": {k: r[k] for k in differences},
                     "native": {k: n[k] for k in differences}}
            break
    complete = all(x["result"]["menu"] == result_menu and
                   x["onset"]["menu"] == result_menu
                   for x in (original, native))
    texts_match = original["result_text"] == native["result_text"]
    scored = True
    if stunt:
        # A zero-score idle run cannot count as the requested scored Stunt.
        score_lines = " ".join(original["result_text"]["final"])
        scored = bool(re.search(r":\s*[1-9][0-9]*", score_lines))
    return {"first_sample_disagreement": first,
            "both_reached_terminal_menu": complete,
            "rendered_result_and_score_text_matched": texts_match,
            "stunt_positive_score_visible": scored,
            "paired_event_candidate": bool(complete and texts_match and scored and first is None),
            "qualification": "candidate only; source/original and native complete-event evidence still requires independent review"}


def scan_source(args, work: Path, sram: Path, source_input: Path) -> dict:
    scan = work / "source"
    scan.mkdir(parents=True)
    (scan / "scan.script").write_text(f"wait {args.source_horizon}\nquit\n")
    env = dict(os.environ, SNESREF_HEADLESS="1", SNESREF_FAST="1",
               SNESREF_WRAM_FILL="0", SNESREF_SRAM_IN=str(sram),
               SNESREF_SCRIPT=str(scan / "scan.script"),
               SNESREF_INPUT_FILE=str(source_input),
               SNESREF_TRACE_FILE=str(scan / "trace.jsonl"),
               SNESREF_DUMP_DIR=str(scan))
    p = subprocess.run([str(args.snesref), str(args.core), str(args.rom)],
                       env=env, cwd=scan, capture_output=True, text=True,
                       timeout=900)
    if p.returncode:
        raise CompleteEventError("source-original replay failed: " + (p.stdout + p.stderr)[-1200:])
    states = trace.frame_states((scan / "trace.jsonl").read_text().splitlines())
    stream, track, menu, _ = CASES[args.case]
    event = source_event(states, track, menu)
    if args.case == "zoom-zoo" and event["original_entry_frame"] != 3190:
        raise CompleteEventError("2014 Zoom Zoo entry disagrees with pinned original 3190")
    return event


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case", choices=tuple(CASES), required=True)
    ap.add_argument("--snesref", type=Path, required=True)
    ap.add_argument("--core", type=Path, required=True)
    ap.add_argument("--native", type=Path, required=True)
    ap.add_argument("--rom", type=Path, default=ROOT / "reference/roms/retail/Uniracers_USA.sfc")
    ap.add_argument("--movie", type=Path, default=movie.ARCHIVE)
    ap.add_argument("--movie-meta", type=Path, default=movie.METADATA)
    ap.add_argument("--source-horizon", type=int, default=SOURCE_HORIZON)
    ap.add_argument("--work-dir", type=Path, required=True)
    ap.add_argument("--json-out", type=Path, required=True)
    args = ap.parse_args(argv)
    for name in ("snesref", "core", "native", "rom", "movie", "movie_meta",
                 "work_dir", "json_out"):
        setattr(args, name, getattr(args, name).resolve())
    if sha(args.rom) != entry.USA_ROM_SHA256:
        ap.error("only canonical USA retail ROM is admitted")
    if args.source_horizon < 12500 or args.source_horizon > 24000:
        ap.error("source horizon must be 12500..24000")
    streams = list(rnc.find_streams(args.rom.read_bytes()))
    if len(streams) != 45:
        ap.error("requires exactly 45 original ROM course streams")
    stream, track, menu, kind = CASES[args.case]
    decoded = unpack_method1(streams[stream - 1][1])
    args.work_dir.mkdir(parents=True, exist_ok=True)
    work = args.work_dir / args.case
    if work.exists():
        raise CompleteEventError("nonempty prior event workspace; use a fresh path")
    work.mkdir()
    # Reuse original reset-movie SRAM rather than the unrelated all-silver fixture.
    source_input, sram = work / "movie.input", work / "anchored.srm"
    subprocess.run([sys.executable, str(ROOT / "tools/extract_smv_input.py"),
                    str(args.movie), "--input-out", str(source_input),
                    "--sram-out", str(sram), "--sram-size", "8192",
                    "--json-out", str(work / "original-movie-meta.json")], check=True)
    original_event = scan_source(args, work, sram, source_input)
    original_bytes, _ = movie.read_movie(args.movie)
    pinned_meta = json.loads(args.movie_meta.read_text())
    source_length = original_event["source_active_frames_to_result"] + 40
    source_window = movie.window(original_bytes, pinned_meta,
                                 original_event["original_entry_frame"], source_length)
    frames = sample_frames(args.case, original_event["source_active_frames_to_result"])
    # Both calibrations boot afresh with exactly the same original SRAM.
    args.sram = sram
    calibration = work / "calibration"
    calibration.mkdir()
    script = calibration / "entry.script"
    script.write_text(stock_crawler_script(stream) + "quit\n")
    rl = engine.run_reference(calibration, args, script, [])
    nl = engine.run_native(calibration, args, script, [], 0)
    rf, nf = engine.race_entry_frame(rl), engine.race_entry_frame(nl)
    if rf is None or nf is None:
        raise CompleteEventError("could not calibrate both stock Crawler race entries")
    replay = work / "replay"
    replay.mkdir()
    script = replay / "complete.script"
    script.write_text(replay_script(stream, menu, frames, kind == "stunt"))
    events = [(rf + part["start"], part["duration"], int(part["mask"], 16))
              for part in source_window["relative_input_segments"]]
    rl = engine.run_reference(replay, args, script, events)
    nl = engine.run_native(replay, args, script, events, nf - rf)
    if engine.race_entry_frame(rl) != rf or engine.race_entry_frame(nl) != nf:
        raise CompleteEventError("race entry changed after scene-relative transplant")
    if "dump result-stable" not in rl or "dump result-stable" not in nl:
        raise CompleteEventError("one engine failed to reach the stock terminal result")
    reference = load_capture(replay / "ref", frames, decoded, track, kind == "stunt")
    native = load_capture(replay / "native", frames, decoded, track, kind == "stunt")
    comparison = diagnose(reference, native, menu, kind == "stunt")
    report = {
        "schema_version": 1, "admission": "investigative candidate; not a release-ledger pass",
        "course_id": f"course:{stream:02d}", "name": args.case, "family": kind,
        "rom_sha256": sha(args.rom), "original_movie_sha256": sha(args.movie),
        "source_sram_sha256": sha(sram), "native_executable_sha256": sha(args.native),
        "reference_core_sha256": sha(args.core), "input_sha256": sha(script),
        "original_source_event": original_event,
        "original_movie_window_sha256": source_window["raw_controller_window_sha256"],
        "reference_entry": rf, "native_entry": nf, "native_frame_shift": nf-rf,
        "relative_sample_frames": frames, "comparison": comparison,
        "reference": reference, "native": native,
        "scope": "original archived scene inputs, fresh reference/native stock menu; event results text from guest PPU dumps; instruction-time contact causality unproven"
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"course": report["course_id"], "source": original_event,
                      "comparison": comparison}, sort_keys=True))
    return 0 if comparison["paired_event_candidate"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
