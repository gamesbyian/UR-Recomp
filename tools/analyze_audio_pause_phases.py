#!/usr/bin/env python3
"""Compare device-output tails around observed stock guest Start edges.

There is no proven mapping from SDL queued device samples to exact guest
frames, nor any reference for whether the stock pause should be silent.
This report is diagnostic, not a substitute for Modern host pause acceptance.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

CHECKPOINTS = ("ui-pause-before", "ui-pause-after-start", "ui-pause-after-resume")


def pause_phase_report(
    metrics: dict, queues: dict, *,
    max_paused_to_before: float | None = None,
    min_resumed_to_before: float | None = None,
) -> dict:
    limits = {
        "max_paused_to_before": max_paused_to_before,
        "min_resumed_to_before": min_resumed_to_before,
    }
    if any(limit is not None and (
        not isinstance(limit, (int, float)) or isinstance(limit, bool)
        or not math.isfinite(limit) or limit < 0
    ) for limit in limits.values()):
        raise ValueError("pause attenuation limits must be non-negative finite numbers")
    if set(metrics) != set(CHECKPOINTS) or set(queues) != set(CHECKPOINTS):
        raise ValueError("missing or extra stock pause checkpoint")
    phases = {}
    for name in CHECKPOINTS:
        pcm = metrics[name]
        stats = queues[name]
        if pcm.get("schema_version") != 1 or pcm.get("audio_origin") != "sdl3-disk-playback":
            raise ValueError(f"{name}: invalid playback-device origin")
        if pcm.get("channels") != 2 or pcm.get("device_format") not in ("S16LE", "S16"):
            raise ValueError(f"{name}: invalid stereo format")
        if stats.get("schema_version") != 1 or stats.get("audio_origin") != "snesrecomp-production-audio-stats":
            raise ValueError(f"{name}: invalid production queue origin")
        tail_rms = pcm.get("tail_rms")
        tail_duration = pcm.get("tail_duration_seconds")
        stereo = pcm.get("tail_channel_rms")
        if any(not isinstance(value, (int, float)) or isinstance(value, bool)
               or not math.isfinite(float(value)) or value < 0
               for value in (tail_rms, tail_duration)):
            raise ValueError(f"{name}: nonfinite or negative tail audio")
        if not 0.95 <= tail_duration <= 1.05:
            raise ValueError(f"{name}: one-second device tail required")
        if not isinstance(stereo, list) or len(stereo) != 2 or any(
            not isinstance(value, (int, float)) or isinstance(value, bool)
            or not math.isfinite(float(value)) or value < 0 for value in stereo
        ):
            raise ValueError(f"{name}: missing or invalid stereo tail")
        deltas = stats.get("deltas", {})
        post = stats.get("post_startup_deltas", {})
        required = ("dropped_audible", "underflows", "missing_frames")
        if any(not isinstance(deltas.get(field), int) or deltas[field] < 0
               or not isinstance(post.get(field), int) or post[field] < 0
               for field in required):
            raise ValueError(f"{name}: missing production continuity counters")
        if deltas["dropped_audible"] > 0:
            raise ValueError(f"{name}: audible source-ring samples were lost")
        phases[name] = {
            "tail_rms": round(float(tail_rms), 6),
            "tail_channel_rms": [round(float(value), 6) for value in stereo],
            "tail_duration_seconds": tail_duration,
            "tail_nonzero_fraction": pcm["tail_nonzero_fraction"],
            "underflows": deltas["underflows"],
            "missing_frames": deltas["missing_frames"],
            "post_startup_underflows": post["underflows"],
            "post_startup_missing_frames": post["missing_frames"],
            "audible_samples_dropped": deltas["dropped_audible"],
        }
    baseline = phases["ui-pause-before"]["tail_rms"]
    paused = phases["ui-pause-after-start"]["tail_rms"]
    resumed = phases["ui-pause-after-resume"]["tail_rms"]
    if any(value is not None for value in limits.values()) and baseline == 0:
        raise ValueError("cannot enforce pause attenuation without audible pre-pause baseline")
    if max_paused_to_before is not None and paused / baseline > max_paused_to_before:
        raise ValueError(
            f"stock pause RMS ratio {paused / baseline:.6f} exceeds "
            f"measured limit {max_paused_to_before}"
        )
    if min_resumed_to_before is not None and resumed / baseline < min_resumed_to_before:
        raise ValueError(
            f"stock resume RMS ratio {resumed / baseline:.6f} below "
            f"measured limit {min_resumed_to_before}"
        )
    relative = {
        name: (round(phases[name]["tail_rms"] / baseline, 6) if baseline > 0 else None)
        for name in CHECKPOINTS
    }
    # -infinity dB for literal silence is represented as null, not invalid
    # JSON or an arbitrary numeric floor. Ratios are process-local evidence.
    relative_db = {
        name: (round(20 * math.log10(value), 4) if value is not None and value > 0 else None)
        for name, value in relative.items()
    }
    return {
        "schema_version": 1,
        "meaning": "Stock guest Start pause and resume, not Modern host pause",
        "window": "Approximate 1-second SDL playback tail after guest-observed 30-frame hold",
        "phase_order": list(CHECKPOINTS),
        "phases": phases,
        "relative_to_before": relative,
        "relative_to_before_db": relative_db,
        "limits": {
            "source_audible_drops": 0,
            **{key: value for key, value in limits.items() if value is not None},
        },
        "limit_policy": "Ratio limits are opt-in until repeat Windows measurements establish tolerance; no exact device latency claim",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("directory", type=Path)
    ap.add_argument("--json-out", type=Path, required=True)
    ap.add_argument("--max-paused-to-before", type=float)
    ap.add_argument("--min-resumed-to-before", type=float)
    args = ap.parse_args()
    metrics = {name: json.loads((args.directory / f"audio-output-{name}.json").read_text())
               for name in CHECKPOINTS}
    queues = {name: json.loads((args.directory / f"audio-ring-{name}.json").read_text())
              for name in CHECKPOINTS}
    report = pause_phase_report(
        metrics, queues, max_paused_to_before=args.max_paused_to_before,
        min_resumed_to_before=args.min_resumed_to_before,
    )
    args.json_out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    for name in CHECKPOINTS:
        item = report["phases"][name]
        print(
            "STOCK_PAUSE_AUDIO_PHASE "
            f"checkpoint={name} tail_rms={item['tail_rms']:.2f} "
            f"post_underflows={item['post_startup_underflows']} "
            f"post_missing={item['post_startup_missing_frames']}"
        )
    print(
        "STOCK_PAUSE_AUDIO_ATTENUATION "
        f"paused_db={report['relative_to_before_db']['ui-pause-after-start']} "
        f"resumed_db={report['relative_to_before_db']['ui-pause-after-resume']}"
    )
    print("STOCK_PAUSE_AUDIO_MATRIX PASS phases=3 source_drops=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
