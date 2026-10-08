#!/usr/bin/env python3
"""Summarize named native SDL audio phases beside independent SNES references.

The comparison uses level *ratios within each engine*, not cross-emulator PCM
identity, samples or absolute loudness. Native device-output tails approximate
but are not yet proven identical to guest-centered reference PCM windows.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

CHECKPOINTS = ("main-menu-ready", "now-playing-ready", "race-entered")


def require_level(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label}: audio level must be numeric")
    level = float(value)
    if not math.isfinite(level) or level <= 0:
        raise ValueError(f"{label}: audio level must be positive and finite")
    return level


def phase_levels(native: dict[str, dict], references: dict) -> dict:
    if set(native) != set(CHECKPOINTS):
        raise ValueError("expected exactly the three canonical native audio checkpoints")
    if references.get("schema_version") != 1:
        raise ValueError("unsupported reference audio summary schema")
    engines = references.get("engines")
    if not isinstance(engines, list) or len(engines) < 2:
        raise ValueError("require at least two independent reference engines")

    levels: dict[str, dict[str, float]] = {}
    native_rms = {}
    native_peaks = {}
    native_stereo_tail_rms = {}
    for checkpoint in CHECKPOINTS:
        metric = native[checkpoint]
        if metric.get("schema_version") != 1 or metric.get("audio_origin") != "sdl3-disk-playback":
            raise ValueError(f"{checkpoint}: invalid native disk-audio evidence")
        if metric.get("channels") != 2 or metric.get("device_format") not in ("S16", "S16LE"):
            raise ValueError(f"{checkpoint}: native evidence must be S16 stereo")
        tail = require_level(metric.get("tail_duration_seconds"), f"{checkpoint} tail duration")
        if not 0.95 <= tail <= 1.05:
            raise ValueError(f"{checkpoint}: expected ~1-second checkpoint-centered tail")
        native_rms[checkpoint] = require_level(metric.get("tail_rms"), f"{checkpoint} tail RMS")
        native_peaks[checkpoint] = require_level(metric.get("tail_peak"), f"{checkpoint} tail peak")
        stereo = metric.get("tail_channel_rms")
        if not isinstance(stereo, list) or len(stereo) != 2:
            raise ValueError(f"{checkpoint}: missing stereo tail channel evidence")
        native_stereo_tail_rms[checkpoint] = [
            round(require_level(value, f"{checkpoint} {name} tail RMS"), 6)
            for value, name in zip(stereo, ("left", "right"))
        ]
    levels["native-sdl-disk"] = native_rms

    names = set()
    for engine in engines:
        name = engine.get("engine")
        if not isinstance(name, str) or not name or name in names:
            raise ValueError("reference engines must have unique nonblank names")
        names.add(name)
        checkpoints = engine.get("checkpoints")
        if not isinstance(checkpoints, dict) or set(checkpoints) != set(CHECKPOINTS):
            raise ValueError(f"{name}: expected canonical reference checkpoints")
        levels[name] = {
            checkpoint: require_level(checkpoints[checkpoint].get("rms"), f"{name} {checkpoint} RMS")
            for checkpoint in CHECKPOINTS
        }
    if "native-sdl-disk" in names:
        raise ValueError("reference engine name collides with native audio source")

    profiles = {}
    for name, values in levels.items():
        menu = values["main-menu-ready"]
        profiles[name] = {
            "rms": {key: round(values[key], 6) for key in CHECKPOINTS},
            "relative_to_main_menu": {key: round(values[key] / menu, 6) for key in CHECKPOINTS},
            "rms_phase_order": sorted(CHECKPOINTS, key=lambda key: (values[key], key)),
            "race_to_menu_rms_ratio": round(values["race-entered"] / menu, 6),
        }

    reference_order = [profiles[name]["rms_phase_order"] for name in names]
    return {
        "schema_version": 1,
        "comparison_basis": (
            "relative RMS ratios within each engine; native device tail ~1 second "
            "after 30 guest post-frames versus reference guest-centered ~1 second; "
            "not aligned PCM equivalence"
        ),
        "checkpoint_order": list(CHECKPOINTS),
        "native_source": "sdl3-disk-playback",
        "profiles": profiles,
        "reference_phase_order_consensus": (
            len({tuple(order) for order in reference_order}) == 1
        ),
        "native_matches_reference_phase_order": (
            len({tuple(order) for order in reference_order}) == 1
            and profiles["native-sdl-disk"]["rms_phase_order"] == reference_order[0]
        ),
        "native_tail_peak": native_peaks,
        "native_tail_channel_rms": native_stereo_tail_rms,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--native-directory", required=True, type=Path)
    ap.add_argument("--reference", required=True, type=Path)
    ap.add_argument("--json-out", required=True, type=Path)
    args = ap.parse_args()
    native = {
        key: json.loads((args.native_directory / f"audio-output-{key}.json").read_text())
        for key in CHECKPOINTS
    }
    reference = json.loads(args.reference.read_text(encoding="utf-8"))
    report = phase_levels(native, reference)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for name, profile in report["profiles"].items():
        print(
            "AUDIO_PHASE_PROFILE "
            f"engine={name} "
            f"now_to_menu={profile['relative_to_main_menu']['now-playing-ready']:.3f} "
            f"race_to_menu={profile['race_to_menu_rms_ratio']:.3f} "
            f"order={','.join(profile['rms_phase_order'])}"
        )
    print(
        "AUDIO_PHASE_MATRIX PASS "
        f"reference_order_consensus={report['reference_phase_order_consensus']} "
        f"native_matches_order={report['native_matches_reference_phase_order']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
