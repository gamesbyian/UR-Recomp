#!/usr/bin/env python3
"""Correlate persistent Modern framework Volume selection with actual SDL output.

Production volume is owned by SNESRecomp config.ini; the title's Modern
Options screen only delegates step actions to it. Compare two fresh-process
SDL device captures around a third process's existing in-product adjustment.
Do not assume exact DSP gain, sample timing or absolute volume parity.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

START = re.compile(r"(?m)^UR_VOLUME_ACCEPTANCE START percent=(\d+)\s*$")
SELECTED = re.compile(r"(?m)^UR_VOLUME SELECTED percent=(\d+)\s*$")


def _read_event(log: str, pattern: re.Pattern, label: str, *, count: int) -> list[int]:
    result = [int(n) for n in pattern.findall(log)]
    if len(result) != count or any(n < 0 or n > 100 for n in result):
        raise ValueError(f"{label}: expected exactly {count} bounded framework Volume events")
    return result


def _require_audio(metrics: dict, label: str) -> dict:
    if (metrics.get("schema_version") != 1
        or metrics.get("audio_origin") != "sdl3-disk-playback"
        or metrics.get("device_format") not in ("S16LE", "S16")
        or metrics.get("channels") != 2
        or metrics.get("sample_rate") != 44100):
        raise ValueError(f"{label}: invalid native Windows SDL3 stereo playback provenance")
    for key in ("rms", "tail_rms", "duration_seconds", "tail_duration_seconds"):
        value = metrics.get(key)
        if (not isinstance(value, (int, float)) or isinstance(value, bool)
            or not math.isfinite(value) or value <= 0):
            raise ValueError(f"{label}: missing or invalid audible PCM metric {key}")
    if not 0.95 <= metrics["tail_duration_seconds"] <= 1.05:
        raise ValueError(f"{label}: not a one-second device tail")
    channels = metrics.get("tail_channel_rms")
    if (not isinstance(channels, list) or len(channels) != 2
        or any(not isinstance(x, (int, float)) or isinstance(x, bool)
               or not math.isfinite(x) or x <= 0 for x in channels)):
        raise ValueError(f"{label}: missing audible left/right channel evidence")
    return metrics


def volume_output_report(
    before_log: str, adjust_log: str, after_log: str,
    before: dict, after: dict,
    repeat_log: str | None = None, repeat: dict | None = None,
) -> dict:
    initial = _read_event(before_log, START, "before", count=1)[0]
    adjusting = _read_event(adjust_log, START, "adjust", count=1)[0]
    loaded = _read_event(after_log, START, "after", count=1)[0]
    if _read_event(before_log, SELECTED, "before", count=0):
        raise AssertionError("unreachable")
    _read_event(after_log, SELECTED, "after", count=0)
    selections = _read_event(adjust_log, SELECTED, "adjust", count=3)
    if initial != adjusting or not 10 <= adjusting <= 100:
        raise ValueError("adjustment did not start from the independently verified framework value")
    if selections[-1] != initial - 5 or loaded != selections[-1]:
        raise ValueError("fresh Windows process did not load the selected framework volume")
    if "UR_VOLUME_ACCEPTANCE ROW_NOT_REACHED" in adjust_log:
        raise ValueError("product Volume options row was not reached")
    if "UR_PAUSE_OPTIONS OPENED" not in adjust_log:
        raise ValueError("real Modern pause Options navigation was not exercised")
    b = _require_audio(before, "before")
    a = _require_audio(after, "after")
    if (repeat_log is None) != (repeat is None):
        raise ValueError("the same-volume control needs both log and PCM evidence")
    repeat_report = None
    if repeat_log is not None and repeat is not None:
        repeat_loaded = _read_event(repeat_log, START, "after-repeat", count=1)[0]
        _read_event(repeat_log, SELECTED, "after-repeat", count=0)
        if repeat_loaded != loaded:
            raise ValueError("same-volume control loaded a different framework Volume")
        control = _require_audio(repeat, "after-repeat")
        repeat_report = {
            "framework_volume_percent": repeat_loaded,
            "tail_rms_ratio": round(control["tail_rms"] / a["tail_rms"], 6),
            "full_rms_ratio": round(control["rms"] / a["rms"], 6),
            "original_tail_nonzero_fraction": a.get("tail_nonzero_fraction"),
            "repeat_tail_nonzero_fraction": control.get("tail_nonzero_fraction"),
            "original_duration_seconds": a["duration_seconds"],
            "repeat_duration_seconds": control["duration_seconds"],
            "meaning": "A/A same-setting device output variability, not gain causality",
        }
    return {
        "schema_version": 1,
        "authority": "SNESRecomp [Sound] Volume, via Modern Options",
        "pcm_clock": "two independent fresh-process SDL3 disk device streams",
        "framework_volume_percent": {
            "before": initial,
            "selected": selections[-1],
            "fresh_process_loaded": loaded,
            "step_observations": selections,
        },
        "device_output": {
            "before_tail_rms": b["tail_rms"],
            "after_tail_rms": a["tail_rms"],
            "tail_rms_ratio": round(a["tail_rms"] / b["tail_rms"], 6),
            "before_tail_channel_rms": b["tail_channel_rms"],
            "after_tail_channel_rms": a["tail_channel_rms"],
            "channel_tail_ratios": [
                round(x / y, 6)
                for x, y in zip(a["tail_channel_rms"], b["tail_channel_rms"])
            ],
            "before_full_rms": b["rms"],
            "after_full_rms": a["rms"],
            "full_rms_ratio": round(a["rms"] / b["rms"], 6),
            "before_duration_seconds": b["duration_seconds"],
            "after_duration_seconds": a["duration_seconds"],
        },
        "same_volume_control": repeat_report,
        "limits": "A/B and same-setting A/A descriptive; no assumed exact gain or guest/sample alignment",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("directory", type=Path)
    ap.add_argument("--json-out", required=True, type=Path)
    args = ap.parse_args()
    root = args.directory
    logs = [
        (root / f"audio-volume-{phase}.log").read_text(encoding="utf-8", errors="replace")
        for phase in ("before", "adjust", "after")
    ]
    metrics = [
        json.loads((root / f"audio-volume-output-{phase}.json").read_text(encoding="utf-8"))
        for phase in ("before", "after")
    ]
    repeat_log = (root / "audio-volume-after-repeat.log").read_text(
        encoding="utf-8", errors="replace"
    )
    repeat_metric = json.loads(
        (root / "audio-volume-output-after-repeat.json").read_text(encoding="utf-8")
    )
    result = volume_output_report(*logs, *metrics, repeat_log, repeat_metric)
    args.json_out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    p = result["framework_volume_percent"]
    d = result["device_output"]
    print(
        "WINDOWS_VOLUME_AUDIO_REPORT PASS "
        f"framework_before={p['before']} selected={p['selected']} "
        f"fresh_loaded={p['fresh_process_loaded']} "
        f"tail_rms_ratio={d['tail_rms_ratio']:.5f} "
        f"full_rms_ratio={d['full_rms_ratio']:.5f}"
    )
    print(
        "WINDOWS_VOLUME_SAME_SETTING_CONTROL "
        f"volume_percent={result['same_volume_control']['framework_volume_percent']} "
        f"tail_rms_ratio={result['same_volume_control']['tail_rms_ratio']:.5f} "
        f"full_rms_ratio={result['same_volume_control']['full_rms_ratio']:.5f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
