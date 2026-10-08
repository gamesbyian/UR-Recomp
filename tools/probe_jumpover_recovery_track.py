#!/usr/bin/env python3
"""Extend the admitted Jumpover fall-through trajectories toward recovery contact.

The original Uniracers manual describes the red/yellow track as preventing a
racer from falling forever. The existing two-route Jumpover reference/native
fixture proves the first fall-through, but stops at movie frame 110. This
bounded extension keeps the admitted approach and boost seed, holds the last
recorded controller mask afterward, and surveys both fall-throughs and
direction-matched controls. It cannot assign a track color from WRAM alone.

Manual: requires snesref, snes9x libretro, canonical ROM, and native executable.
No stock-physics changes or new CI workflow.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

import probe_jumpover_fallthrough_native as jf

START_MOVIE_FRAME = 100
DEFAULT_END_FRAME = 280
DEFAULT_STRIDE = 4
WRAM_SIZE = jf.WRAM_SIZE
FALL_Y = jf.FALL_Y


class RecoveryEvidenceError(ValueError):
    """Missing, misidentified, or incomplete recovery survey."""


def sample_frames(end: int, stride: int) -> list[int]:
    if type(end) is not int or type(stride) is not int or not 110 <= end <= 600 or not 1 <= stride <= 30:
        raise RecoveryEvidenceError("end must be 110..600; stride must be 1..30")
    return sorted(set(range(START_MOVIE_FRAME, end + 1, stride)) | {end})


def long_movie(route: str, end: int, *, control: bool) -> list[int]:
    if route not in jf.ROUTES:
        raise RecoveryEvidenceError("unknown Jumpover route")
    masks = jf.movie_masks(route, jf.CONTROL_SAMPLE if control else None)
    if len(masks) <= end:
        masks.extend([masks[-1]] * (end + 1 - len(masks)))
    return masks


def extension_script(entry: int, splice: int, lead: int, boost: int,
                     end: int, stride: int) -> str:
    frames = sample_frames(end, stride)
    seed = splice - 1 - lead
    if seed <= entry or splice <= entry:
        raise RecoveryEvidenceError("boost seed must be after race entry and before splice")
    lines = [jf.MENU_SCRIPT.rstrip("\n"), f"wait {seed - entry}",
             f"poke {jf.BOOST_ADDR:04X} {boost & 0xFF:02x}{boost >> 8:02x}"]
    cur = seed + 2  # Poke adds one frame plus one trailing idle frame.
    for frame in frames:
        target = splice + frame
        if target < cur:
            raise RecoveryEvidenceError("sample precedes boost seed")
        if target > cur:
            lines.append(f"wait {target - cur}")
            cur = target
        lines.append(f"dump s{frame:03d}")
    return "\n".join(lines + ["quit", ""])


def read_series(root: Path, end: int, stride: int) -> dict[int, dict]:
    series = {}
    for frame in sample_frames(end, stride):
        file = root / f"s{frame:03d}.wram.bin"
        if not file.is_file():
            raise RecoveryEvidenceError(f"missing sample {frame}: {file}")
        wram = file.read_bytes()
        if len(wram) != WRAM_SIZE:
            raise RecoveryEvidenceError(f"sample {frame}: expected {WRAM_SIZE} WRAM bytes")
        if wram[0x00CE] != jf.JUMPOVER_TRACK_ID or wram[0x0313] != 1:
            raise RecoveryEvidenceError(f"sample {frame}: not active Jumpover (track/race)")
        series[frame] = jf.read_p1(wram)
    return series


def classify_scout(series: dict[int, dict]) -> dict:
    if not series:
        raise RecoveryEvidenceError("empty scout capture")
    contact_after_floor = [f for f, row in sorted(series.items())
                           if row["y"] > FALL_Y and row["air_time"] == 0]
    grounded_anywhere = [f for f, row in sorted(series.items()) if row["air_time"] == 0]
    return {
        "sampled_frames": len(series),
        "max_y": max(x["y"] for x in series.values()),
        "contact_below_old_floor_sample_frames": contact_after_floor,
        "all_grounded_sample_frames": grounded_anywhere,
        "last": series[max(series)],
        "series_sha256": hashlib.sha256(
            json.dumps([(f, series[f]) for f in sorted(series)], sort_keys=True).encode()
        ).hexdigest(),
        "recovery_surface_classification": "unknown: WRAM contact does not establish red/yellow pixel identity",
    }


def compare(ref: dict[int, dict], native: dict[int, dict]) -> dict:
    if not ref or set(ref) != set(native):
        raise RecoveryEvidenceError("both engines must supply exactly matching nonempty sample frames")
    first = next(({"sample": f, "fields": sorted(k for k in jf.FIELDS if ref[f][k] != native[f][k])}
                  for f in sorted(ref) if ref[f] != native[f]), None)
    return {
        "first_divergence": first,
        "reference": classify_scout(ref),
        "native": classify_scout(native),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ("snesref", "core", "native", "rom"):
        ap.add_argument(f"--{name}", type=Path, required=True)
    ap.add_argument("--sram", type=Path, default=jf.DEFAULT_SRAM)
    ap.add_argument("--work-dir", type=Path, required=True)
    ap.add_argument("--end", type=int, default=DEFAULT_END_FRAME)
    ap.add_argument("--stride", type=int, default=DEFAULT_STRIDE)
    ap.add_argument("--routes", default="right,left")
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args(argv)
    try:
        sample_frames(args.end, args.stride)
    except RecoveryEvidenceError as exc:
        ap.error(str(exc))
    for name in ("snesref", "core", "native", "rom", "sram", "work_dir"):
        setattr(args, name, getattr(args, name).resolve())
    chosen = args.routes.split(",")
    if not chosen or any(x not in jf.ROUTES for x in chosen) or len(set(chosen)) != len(chosen):
        ap.error("--routes must be one or both of right,left")

    args.work_dir.mkdir(parents=True, exist_ok=True)
    boot = args.work_dir / "boot.script"
    boot.write_text(jf.MENU_SCRIPT + "quit\n", encoding="utf-8")
    reference_entry = jf.race_entry_frame(jf.run_reference(args.work_dir, args, boot, []))
    native_entry = jf.race_entry_frame(jf.run_native(args.work_dir, args, boot, [], 0))
    if reference_entry is None or native_entry is None:
        raise SystemExit("could not reach the named Jumpover race from stock boot")
    shift = native_entry - reference_entry

    cases = {}
    ok = True
    for route in chosen:
        cfg = jf.ROUTES[route]
        for control in (False, True):
            name = f"{route}-" + ("shoulder-control" if control else "fall-through")
            work = args.work_dir / name
            shutil.rmtree(work, ignore_errors=True)
            work.mkdir(parents=True)
            splice = reference_entry + cfg["splice_offset"]
            # Keep the admitted PHYS-02 lead which produces the fall-through.
            lead = 36 if route == "right" else 21
            script = work / "probe.script"
            script.write_text(extension_script(reference_entry, splice, lead,
                                               cfg["boost"], args.end, args.stride),
                              encoding="utf-8")
            masks = long_movie(route, args.end, control=control)
            events = jf.input_events(masks, reference_entry, splice, cfg["approach"])
            rlog = jf.run_reference(work, args, script, events)
            nlog = jf.run_native(work, args, script, events, shift)
            if jf.race_entry_frame(rlog) != reference_entry or jf.race_entry_frame(nlog) != native_entry:
                raise SystemExit(f"{name}: race entry did not reproduce")
            ref = read_series(work / "ref", args.end, args.stride)
            native = read_series(work / "native", args.end, args.stride)
            match = compare(ref, native)
            cases[name] = match
            if match["first_divergence"] is not None:
                ok = False
    report = {
        "schema_version": 1,
        "source_fixture": "analysis/generated/jumpover-fallthrough-native.json",
        "manual_source": "https://www.world-of-nintendo.com/manuals/super_nes/uniracers.shtml",
        "qualification": "controlled boost seed and synthetic hold extension after recovered movie",
        "scope": "post-fall-through contact survey, not proven red/yellow visual classification",
        "sampled_movie_frames": sample_frames(args.end, args.stride),
        "reference_race_entry_frame": reference_entry,
        "native_race_entry_frame": native_entry,
        "cases": cases,
    }
    payload = json.dumps(report, indent=2) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
