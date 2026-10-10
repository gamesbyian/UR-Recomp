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


def inspect_original(args: argparse.Namespace) -> dict:
    args.work_dir.mkdir(parents=True, exist_ok=True)
    if args.source_horizon < 12000 or args.source_horizon > 24000:
        raise ValueError("source horizon outside bounded 12000..24000 movie range")
    if event.sha(args.rom) != event.entry.USA_ROM_SHA256:
        raise ValueError("not canonical USA original ROM")
    src, _ = movie.read_movie(args.movie)
    meta = json.loads(args.movie_meta.read_text(encoding="utf-8"))
    movie.window(src, meta, 3190, 1810)  # replay metadata and embedded ROM identity
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
        status = "source_event_not_qualified_within_bounded_horizon"
        diag_path = out / "source" / "source-event-diagnostic.json"
        diagnostic = json.loads(diag_path.read_text()) if diag_path.exists() else {}
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
    p.add_argument("--source-horizon", type=int, default=22000)
    args = p.parse_args()
    for key in ("snesref","core","rom","movie","movie_meta","work_dir","report"):
        setattr(args,key,getattr(args,key).resolve())
    r = inspect_original(args)
    print(json.dumps({"status":r["status"],"source_result":r["source_result"],
                      "release_complete_event_credit":0},indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
