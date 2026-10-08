#!/usr/bin/env python3
"""Compare real packaged Windows Restart PCM under two temporary Start bindings.

The ordinary keyboard maps Return to SNES Start. Win32 Return also activates
Modern Restart. Holding the same game build and script constant while changing
only the disposable keybinds.ini Start row can test for a guest Start leak.
This is descriptive, not statistical proof or a reason to weaken a red gate.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

ARMS = ("start-return", "start-unbound")
TRIALS = 3


def _finite_nonnegative(value: object) -> bool:
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and value >= 0)


def reduce_keymap_trials(trials: dict[str, list[dict]]) -> dict:
    if set(trials) != set(ARMS):
        raise ValueError("exactly the canonical Return/Unbound keyboard cohorts required")
    summary: dict[str, dict] = {}
    for arm in ARMS:
        records = trials[arm]
        if not isinstance(records, list) or len(records) != TRIALS:
            raise ValueError(f"{arm}: exactly {TRIALS} full native trials required")
        converted = []
        for index, entry in enumerate(records):
            if (not isinstance(entry, dict)
                or entry.get("schema_version") != 1
                or entry.get("authority") !=
                    "packaged Windows real pause-menu Restart Win32 Down/Enter"
                or entry.get("device_origin") != "sdl3-disk-playback"
                or entry.get("sample_rate") != 44100
                or any(entry.get(marker) != 1 for marker in (
                    "restart_selected", "host_resumed",
                    "guest_resumed_after_restart"))):
                raise ValueError(f"{arm}[{index}]: untrusted or missing Restart semantics")
            pre = entry.get("paused_one_second")
            post = entry.get("restarted_final_one_second")
            envelope = entry.get("last_eight_seconds_envelope")
            if (not isinstance(pre, dict) or not isinstance(post, dict)
                or pre.get("frames") != 44100 or post.get("frames") != 44100
                or pre.get("combined_rms") != 0
                or pre.get("channel_rms") != [0, 0]
                or pre.get("channel_nonzero_fraction") != [0, 0]
                or not isinstance(envelope, dict)
                or envelope.get("audio_origin") != "sdl3-disk-playback"
                or envelope.get("sample_rate") != 44100
                or envelope.get("window_ms") != 100
                or envelope.get("captured_tail_seconds") != 8
                or not isinstance(envelope.get("windows"), list)
                or len(envelope["windows"]) != 80):
                raise ValueError(f"{arm}[{index}]: incomplete real stereo PCM evidence")
            levels = post.get("channel_rms")
            fracs = post.get("channel_nonzero_fraction")
            if (not isinstance(levels, list) or len(levels) != 2
                or not isinstance(fracs, list) or len(fracs) != 2
                or any(not _finite_nonnegative(x) for x in levels + fracs)
                or any(x > 1 for x in fracs)):
                raise ValueError(f"{arm}[{index}]: invalid final stereo samples")
            bucket_rms = [window.get("combined_rms")
                          for window in envelope["windows"]]
            if any(not _finite_nonnegative(x) for x in bucket_rms):
                raise ValueError(f"{arm}[{index}]: invalid SDL device envelope")
            audible = min(levels) >= 50 and min(fracs) >= 0.001
            trailing_silence = 0
            for rms in reversed(bucket_rms):
                if rms != 0:
                    break
                trailing_silence += 1
            converted.append({
                "trial": index + 1,
                "audible_stereo_after_restart": audible,
                "final_one_second_channel_rms": levels,
                "trailing_literal_silence_100ms_buckets": trailing_silence,
                "guest_resume_frame": entry.get("restart_guest_resume_frame"),
            })
        summary[arm] = {
            "trials": converted,
            "audible_stereo_count": sum(x["audible_stereo_after_restart"] for x in converted),
            "fully_silent_tail_count": sum(all(v == 0 for v in x["final_one_second_channel_rms"])
                                           for x in converted),
        }
    return {
        "schema_version": 1,
        "authority": "same Windows packaged exe and original guest script; separate fresh processes",
        "controlled_dimension": "guest P1 SNES Start: Return vs None; Win32 Modern menu still receives Return",
        "cohorts": summary,
        "difference_in_audible_counts": (summary["start-unbound"]["audible_stereo_count"]
                                         - summary["start-return"]["audible_stereo_count"]),
        "interpretation": "descriptive causal discriminator, not statistical significance or shipping pass",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory", type=Path)
    p.add_argument("--json-out", required=True, type=Path)
    a = p.parse_args()
    trials = {
        arm: [
            json.loads((a.directory / f"restart-keymap-{arm}-{index}.json")
                       .read_text(encoding="utf-8"))
            for index in range(1, TRIALS + 1)
        ]
        for arm in ARMS
    }
    report = reduce_keymap_trials(trials)
    a.json_out.parent.mkdir(parents=True, exist_ok=True)
    a.json_out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                          encoding="utf-8")
    print("WINDOWS_RESTART_KEYMAP_AB_ANALYSIS PASS "
          f"return_audible={report['cohorts']['start-return']['audible_stereo_count']}/{TRIALS} "
          f"unbound_audible={report['cohorts']['start-unbound']['audible_stereo_count']}/{TRIALS} "
          "interpretation=diagnostic_only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
