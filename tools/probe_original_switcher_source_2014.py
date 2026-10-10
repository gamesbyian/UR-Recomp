#!/usr/bin/env python3
"""QA-01: check archived 2014 source for a *real* Switcher race result.

Original Snes9x only. Does not attempt native game acceptance, does not
reclassify a stable result menu from another course, and does not assume an
archived trace extends past the requested finite horizon.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import analyze_rnc_streams as rnc
import extract_historical_smv_scene_window as movie
import probe_original_event_complete as event
from rnc_method1 import unpack_method1

# Explicit human-requested original-only scan windows. These do NOT select a
# scene, prove completion or trigger any native build. Keep automatic CI off.
SOURCE_HORIZONS = (22000, 48000, 96000)
NONQUALIFICATION = "source movie never demonstrated this course/result pair"


def inspect_original(args: argparse.Namespace) -> dict:
    args.work_dir.mkdir(parents=True, exist_ok=True)
    if type(args.source_horizon) is not int or args.source_horizon not in SOURCE_HORIZONS:
        raise ValueError("source horizon must be one of 22000, 48000, 96000 original frames")
    if event.sha(args.rom) != event.entry.USA_ROM_SHA256:
        raise ValueError("not canonical USA original ROM")
    src, _ = movie.read_movie(args.movie)
    meta = json.loads(args.movie_meta.read_text(encoding="utf-8"))
    movie.window(src, meta, 3190, 1810)  # replay metadata and embedded ROM identity
    if type(meta.get("sample_count")) is not int or args.source_horizon > meta["sample_count"]:
        raise ValueError("original source horizon exceeds verified movie sample count")
    out = args.work_dir / "source-switcher"
    if out.exists():
        raise ValueError("source output exists: use a fresh workspace")
    out.mkdir()
    input_path = out / "movie.input"
    sram_path = out / "anchored.srm"
    subprocess.run([sys.executable, str(event.ROOT / "tools/extract_smv_input.py"),
                    str(args.movie), "--input-out", str(input_path),
                    "--sram-out", str(sram_path), "--sram-size", "8192",
                    "--json-out", str(out / "movie-meta.json")], check=True)
    streams = list(rnc.find_streams(args.rom.read_bytes()))
    if len(streams) != 45:
        raise ValueError("require exactly 45 retail ROM RNC course streams")
    decoded = unpack_method1(streams[3][1])  # USA course 04, Switcher Race B
    ns = SimpleNamespace(case="switcher", source_horizon=args.source_horizon,
                         snesref=args.snesref, core=args.core, rom=args.rom)
    try:
        found = event.scan_source(ns, out, sram_path, input_path, decoded)
        status = "source_event_and_entry_verified"
        diagnostic = json.loads(
            (out / "source" / "source-event-diagnostic.json").read_text())
        source_result = {k:v for k,v in found.items()
                         if k != "original_source_entry"}
    except event.CompleteEventError as exc:
        # scan_source can also raise this type when the original core crashes,
        # its trace is malformed, or the original entry witness cannot load.
        # Those failures are NEVER evidence that the movie lacks Switcher.
        if str(exc) != NONQUALIFICATION:
            raise
        diag_path = out / "source" / "source-event-diagnostic.json"
        if not diag_path.is_file():
            raise ValueError("missing original trace diagnostic; source nonqualification unproven") from exc
        diagnostic = json.loads(diag_path.read_text(encoding="utf-8"))
        frames = diagnostic.get("source_trace_frames") if isinstance(diagnostic, dict) else None
        if (not isinstance(diagnostic, dict)
                or diagnostic.get("schema") != "UR-QA01-SOURCE-RESULT-PROBE/1"
                or diagnostic.get("wanted_course_track") != 3
                or diagnostic.get("wanted_result_menu") != 0x99
                or not isinstance(frames, list) or len(frames) != 2
                or any(type(f) is not int for f in frames)
                or not 0 <= frames[0] < frames[1] <= args.source_horizon
                or diagnostic.get("complete_event_qa_credit") != 0):
            raise ValueError("invalid or incomplete original source diagnostic") from exc
        status = "source_event_not_qualified_within_bounded_horizon"
        source_result = {"reason": str(exc)}
    report = {
        "schema": "UR-QA01-ORIGINAL-SWITCHER-SOURCE-QUALIFICATION/1",
        "scope": "archived original Snes9x only; full native Race B parity not attempted",
        "original_source_horizon_frames": args.source_horizon,
        "original_core_sha256": event.sha(args.core),
        "rom_sha256": event.sha(args.rom),
        "archived_movie_sha256": hashlib.sha256(src).hexdigest(),
        "source_sram_sha256": event.sha(sram_path),
        "source_result": source_result,
        "source_event_diagnostic": diagnostic,
        "status": status,
        "release_complete_event_credit": 0,
        "next": ("If original Switcher source actually finishes, separately "
                 "calibrate original and Baldosa stock course entries before "
                 "replaying the source controller masks unchanged. Do not "
                 "admit a Race B from original-only evidence."),
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    return report


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--snesref", type=Path, required=True)
    p.add_argument("--core", type=Path, required=True)
    p.add_argument("--rom", type=Path, required=True)
    p.add_argument("--movie", type=Path, default=movie.ARCHIVE)
    p.add_argument("--movie-meta", type=Path, default=movie.METADATA)
    p.add_argument("--work-dir", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    p.add_argument("--source-horizon", type=int, default=22000,
                   choices=SOURCE_HORIZONS,
                   help="finite original-only movie scan; 22000 baseline, 48000 then 96000 optional")
    args = p.parse_args()
    for key in ("snesref","core","rom","movie","movie_meta","work_dir","report"):
        setattr(args,key,getattr(args,key).resolve())
    r = inspect_original(args)
    diag = r["source_event_diagnostic"]
    print(json.dumps({"status":r["status"], "source_result":r["source_result"],
                      "original_source_horizon_frames":r["original_source_horizon_frames"],
                      "source_active_switcher_frames":diag.get("active_track_frames"),
                      "source_switcher_candidate_entries":diag.get("source_event_candidate_entries"),
                      "source_stable_result_runs":diag.get("stable_original_results"),
                      "release_complete_event_credit":0},indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
