#!/usr/bin/env python3
"""Reduce three bounded SDL3 guest-Start pause envelopes into CI-visible shape.

All time values are relative to each fresh process's *device-stream end*,
never to exact simulated guest frames. Literal silence here means exactly
zero decoded PCM energy in a bucket, not a calibrated acoustic noise floor.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

PHASES = ("ui-pause-before", "ui-pause-after-start", "ui-pause-after-resume")


def _valid_nonnegative(value: object) -> bool:
    return (
        isinstance(value, (int, float)) and not isinstance(value, bool)
        and math.isfinite(value) and value >= 0
    )


def summarize_phase(report: dict, case: str) -> dict:
    if report.get("schema_version") != 1 or report.get("audio_origin") != "sdl3-disk-playback":
        raise ValueError(f"{case}: untrusted PCM envelope source")
    if report.get("device_format") not in ("S16LE", "S16") or report.get("channels") != 2:
        raise ValueError(f"{case}: invalid source stereo format")
    rate = report.get("sample_rate")
    if not isinstance(rate, int) or not 8000 <= rate <= 192000:
        raise ValueError(f"{case}: invalid device sample rate")
    if report.get("window_ms") != 100 or report.get("captured_tail_seconds") != 3:
        raise ValueError(f"{case}: required three-second, 100 ms envelope")
    windows = report.get("windows")
    if not isinstance(windows, list) or len(windows) != 30:
        raise ValueError(f"{case}: incomplete bounded stereo envelope")

    zero_indices = []
    max_step = [0, 0]
    max_peak = [0, 0]
    rms_values = []
    for i, window in enumerate(windows):
        if not isinstance(window, dict):
            raise ValueError(f"{case}: invalid envelope bucket {i}")
        left, right, combined = (
            window.get("rms"), window.get("peak"), window.get("peak_adjacent_step")
        )
        if (not isinstance(left, list) or not isinstance(right, list)
            or not isinstance(combined, list)
            or len(left) != 2 or len(right) != 2 or len(combined) != 2
            or any(not _valid_nonnegative(v) for v in left)
            or any(not isinstance(v, int) or isinstance(v, bool)
                   or not 0 <= v <= 32768 for v in right)
            or any(not isinstance(v, int) or isinstance(v, bool)
                   or not 0 <= v <= 65535 for v in combined)):
            raise ValueError(f"{case}: invalid stereo RMS/peak/step in bucket {i}")
        total = window.get("combined_rms")
        if not _valid_nonnegative(total) or abs(
            total - math.sqrt(sum(v * v for v in left) / 2)
        ) > 0.002:
            raise ValueError(f"{case}: inconsistent combined RMS in bucket {i}")
        start, end = (
            window.get("start_seconds_before_end"),
            window.get("end_seconds_before_end"),
        )
        frames = window.get("frames")
        if (not _valid_nonnegative(start) or not _valid_nonnegative(end)
            or not isinstance(frames, int) or isinstance(frames, bool)
            or frames != round(rate * 0.1)
            or abs(start - (3 - i * 0.1)) > 0.0001
            or abs(end - (2.9 - i * 0.1)) > 0.0001):
            raise ValueError(f"{case}: invalid device-relative timing in bucket {i}")
        zeros = window.get("zero_fraction")
        if not isinstance(zeros, list) or len(zeros) != 2 or any(
            not _valid_nonnegative(v) or v > 1 for v in zeros
        ):
            raise ValueError(f"{case}: invalid zero fraction in bucket {i}")
        if total == 0:
            if zeros != [1, 1] or right != [0, 0] or any(left):
                raise ValueError(f"{case}: contradictory reported silent bucket {i}")
            zero_indices.append(i)
        rms_values.append(total)
        max_step = [max(max_step[ch], combined[ch]) for ch in range(2)]
        max_peak = [max(max_peak[ch], right[ch]) for ch in range(2)]

    first_audible = next((i for i, rms in enumerate(rms_values) if rms > 0), None)
    last_audible = next((i for i in range(29, -1, -1) if rms_values[i] > 0), None)
    leading = first_audible if first_audible is not None else 30
    trailing = 29 - last_audible if last_audible is not None else 30
    return {
        "literal_silent_buckets": zero_indices,
        "leading_silence_seconds": round(leading * 0.1, 1),
        "trailing_silence_seconds": round(trailing * 0.1, 1),
        "first_nonzero_bucket": first_audible,
        "last_nonzero_bucket": last_audible,
        "peak_adjacent_sample_step": max_step,
        "peak_sample": max_peak,
        "bucket_rms": [round(v, 2) for v in rms_values],
    }


def reduce_envelopes(reports: dict) -> dict:
    if set(reports) != set(PHASES):
        raise ValueError("exactly three canonical stock guest pause phases are required")
    return {
        "schema_version": 1,
        "reference_clock": "SDL3 device stream end, not guest timestamp",
        "time_window": "final 3.0 s, 100 ms buckets",
        "literal_silence": "zero PCM energy, no noise-floor assumption",
        "phases": {case: summarize_phase(reports[case], case) for case in PHASES},
        "limits": "descriptive only; no click, onset latency or fade-fidelity gate",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args()
    reports = {
        case: json.loads((args.directory / f"audio-envelope-{case}.json").read_text(encoding="utf-8"))
        for case in PHASES
    }
    reduced = reduce_envelopes(reports)
    args.json_out.write_text(json.dumps(reduced, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for case, profile in reduced["phases"].items():
        print(
            "SDL_PAUSE_ENVELOPE_SHAPE "
            f"case={case} leading_silence_s={profile['leading_silence_seconds']:.1f} "
            f"trailing_silence_s={profile['trailing_silence_seconds']:.1f} "
            f"max_step_left={profile['peak_adjacent_sample_step'][0]} "
            f"max_step_right={profile['peak_adjacent_sample_step'][1]}"
        )
    print("SDL_PAUSE_ENVELOPE_SHAPE PASS phases=3 raw_pcm_uploaded=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
