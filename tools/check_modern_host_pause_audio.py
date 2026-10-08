#!/usr/bin/env python3
"""Accept real Windows Modern host-frozen pause as audibly active, then silent.

The frozen guest must not be advanced to validate pause. Require the existing
host-owned pause event, actual pre-pause SDL3 stereo output in the whole file,
then complete digital silence in the last 3 seconds of device output. This
does not validate restart/resume, hardware speaker latency or APU DSP parity.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from tools.capture_modern_paused_audio import verify_modern_pause_log


def check_host_pause_audio(log: str, output: dict, envelope: dict) -> dict:
    pause = verify_modern_pause_log(log)
    if (
        output.get("schema_version") != 1
        or output.get("audio_origin") != "sdl3-disk-playback"
        or output.get("device_format") not in ("S16LE", "S16")
        or output.get("channels") != 2
        or output.get("sample_rate") != 44100
    ):
        raise ValueError("Modern pause output is not verified SDL3 stereo playback")
    duration = output.get("duration_seconds")
    overall = output.get("rms")
    fraction = output.get("nonzero_fraction")
    if (
        any(not isinstance(value, (int, float)) or isinstance(value, bool)
            or not math.isfinite(value) for value in (duration, overall, fraction))
        or duration < 15 or overall < 50 or fraction < 0.05 or fraction > 1
    ):
        raise ValueError("Modern pause capture lacks meaningful audible pre-pause output")
    if (
        output.get("tail_pcm_frames") != 44100
        or output.get("tail_duration_seconds") != 1.0
        or output.get("tail_rms") != 0
        or output.get("tail_nonzero_fraction") != 0
        or output.get("tail_channel_rms") != [0.0, 0.0]
        or output.get("tail_peak") != 0
    ):
        raise ValueError("Modern host-owned pause must produce a silent SDL device tail")
    if (
        envelope.get("schema_version") != 1
        or envelope.get("audio_origin") != "sdl3-disk-playback"
        or envelope.get("device_format") not in ("S16LE", "S16")
        or envelope.get("channels") != 2
        or envelope.get("sample_rate") != 44100
        or envelope.get("window_ms") != 100
        or envelope.get("captured_tail_seconds") != 3.0
        or not isinstance(envelope.get("windows"), list)
        or len(envelope["windows"]) != 30
    ):
        raise ValueError("Modern pause lacks complete SDL device envelope evidence")
    for index, item in enumerate(envelope["windows"]):
        if (
            not isinstance(item, dict)
            or item.get("frames") != 4410
            or item.get("combined_rms") != 0
            or item.get("rms") != [0.0, 0.0]
            or item.get("peak") != [0, 0]
            or item.get("zero_fraction") != [1.0, 1.0]
        ):
            raise ValueError(f"Modern pause had non-silent/corrupt SDL device envelope bucket {index}")
    return {
        "schema_version": 1,
        "authority": "Modern host-owned frozen guest pause, not stock guest Start",
        "guest_race_entered_frame": pause["guest_race_entered_frame"],
        "host_paused": pause["host_pause_state"],
        "device_origin": output["audio_origin"],
        "device_sample_rate": 44100,
        "pre_pause_whole_capture_rms": overall,
        "pre_pause_whole_capture_nonzero_fraction": fraction,
        "last_second_rms": 0,
        "last_three_seconds_silent_buckets": 30,
        "rule": "audible gameplay capture followed by 3.0 s of literal SDL digital silence",
        "limits": "no exact guest/audio onset alignment or graceful teardown claim",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("native_log", type=Path)
    parser.add_argument("output_report", type=Path)
    parser.add_argument("envelope_report", type=Path)
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args()
    result = check_host_pause_audio(
        args.native_log.read_text(encoding="utf-8", errors="replace"),
        json.loads(args.output_report.read_text(encoding="utf-8")),
        json.loads(args.envelope_report.read_text(encoding="utf-8")),
    )
    args.json_out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(
        "MODERN_HOST_PAUSE_AUDIO_SILENCE PASS "
        f"race_entered_frame={result['guest_race_entered_frame']} "
        "source=real-sdl3-device audible_pre_pause=1 "
        "silent_device_tail_seconds=3.0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
