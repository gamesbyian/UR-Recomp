#!/usr/bin/env python3
"""QA-08: measure *actually presented* Racer HD availability from native logs.

UR_RACER_HD_CENSUS=1 traces admission once per guest simulation frame and
final host presenter use per render. This counts actual replacement outputs,
not just registration matches. Missing renders remain explicit uncertainty,
not silently counted as Original. No GPU screenshot/occlusion parity is inferred.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re

CENSUS = re.compile(
    r"UR_RACER_HD_CENSUS frame=(\d+) phase=(gate|present) "
    r"status=([a-z][a-z0-9-]*) reason=([a-z][a-z0-9-]*)\\s*$"
)

ALLOWED = {
    "gate": {"original", "armed"},
    "present": {"original", "hd"},
}
ORIGINS = {"full-pair", "p1-only"}


def episode_lengths(frames: list[int]) -> list[int]:
    result: list[int] = []
    last = None
    for frame in sorted(frames):
        if frame < 0 or frame == last:
            raise ValueError("episode frame numbers must be unique and nonnegative")
        if last is None or frame != last + 1:
            result.append(1)
        else:
            result[-1] += 1
        last = frame
    return result


def analyze(log: str, *, source: str = "") -> dict:
    gates: dict[int, tuple[str, str]] = {}
    presents: dict[int, list[tuple[str, str]]] = {}
    for lineno, line in enumerate(log.splitlines(), 1):
        if "UR_RACER_HD_CENSUS" not in line:
            continue
        match = CENSUS.search(line)
        if not match:
            raise ValueError(f"malformed census line {lineno}")
        frame, phase, status, reason = match.groups()
        frame = int(frame)
        if status not in ALLOWED[phase]:
            raise ValueError(f"invalid {phase} status at line {lineno}: {status}")
        if phase == "gate":
            if frame in gates:
                raise ValueError(f"duplicate gate for frame {frame}")
            if status == "armed" and reason not in ORIGINS:
                raise ValueError(f"invalid armed capture mode at frame {frame}: {reason}")
            gates[frame] = (status, reason)
        else:
            if status == "hd" and reason not in ORIGINS:
                raise ValueError(f"invalid HD render mode at frame {frame}: {reason}")
            presents.setdefault(frame, []).append((status, reason))
    if not gates:
        raise ValueError("no native Racer HD per-frame gate observations")
    if not presents:
        raise ValueError("no native Racer HD per-present observations")

    gate_reasons = Counter(reason for status, reason in gates.values() if status == "original")
    presented_classes: dict[int, str] = {}
    present_reasons = Counter()
    rendered_player_frames = 0
    hd_present_calls = 0
    for frame, observations in sorted(presents.items()):
        gate = gates.get(frame)
        if gate is None:
            raise ValueError(f"present at unobserved guest frame {frame}")
        for status, reason in observations:
            if gate[0] == "armed" and status != "hd":
                raise ValueError(
                    f"capture-armed frame {frame} fell through without HD: "
                    "stock OBJ may have been removed before presentation"
                )
            if gate[0] == "original" and status == "hd":
                raise ValueError(f"HD draw after Original-only gate at frame {frame}")
            if gate[0] == "armed" and status == "hd" and gate[1] != reason:
                raise ValueError(f"gate/render mode disagreement at frame {frame}")
            present_reasons[(status, reason)] += 1
            if status == "hd":
                hd_present_calls += 1
        statuses = {status for status, _ in observations}
        if len(statuses) > 1:
            raise ValueError(f"frame {frame} has mixed HD and Original presentations")
        status = next(iter(statuses))
        presented_classes[frame] = status
        if status == "hd":
            # One HD P1 in both viewports != two HD racers.
            rendered_player_frames += 1 if gate[1] == "p1-only" else 2

    hd_frames = sorted(f for f, status in presented_classes.items() if status == "hd")
    original_frames = sorted(f for f, status in presented_classes.items() if status == "original")
    consecutive = [
        (a, b)
        for a, b in zip(sorted(presented_classes), sorted(presented_classes)[1:])
        if b == a + 1
    ]
    fallback_to_hd = sum(a in original_frames and b in hd_frames for a, b in consecutive)
    hd_to_fallback = sum(a in hd_frames and b in original_frames for a, b in consecutive)
    runs = episode_lengths(hd_frames)
    original_runs = episode_lengths(original_frames)
    armed = {f for f, (status, _) in gates.items() if status == "armed"}
    undrawn_armed = sorted(armed.difference(hd_frames))
    nonpresented = sorted(set(gates).difference(presented_classes))
    denom = len(presented_classes)
    return {
        "schema_version": 1,
        "classification": "native-per-present-raster-outcome; not pixel-fidelity/occlusion proof",
        "source": source,
        "measurement": {
            "guest_frames_observed": len(gates),
            "guest_frames_with_host_presents": denom,
            "guest_frames_without_host_presents": len(nonpresented),
            "host_present_calls": sum(map(len, presents.values())),
            "hd_present_calls": hd_present_calls,
            "hd_drawn_guest_frames": len(hd_frames),
            "original_presented_guest_frames": len(original_frames),
            "hd_presented_fraction": len(hd_frames) / denom,
            "stock_fallback_fraction": len(original_frames) / denom,
            "hd_drawn_player_frames": rendered_player_frames,
            "player_frame_denominator": 2 * denom,
            "hd_player_frame_fraction": rendered_player_frames / (2 * denom),
            "capture_armed_guest_frames": len(armed),
            "armed_without_hd_draw_guest_frames": len(undrawn_armed),
            "consecutive_presented_guest_frame_pairs": len(consecutive),
            "original_to_hd_edges": fallback_to_hd,
            "hd_to_original_edges": hd_to_fallback,
            "draw_mode_switches": fallback_to_hd + hd_to_fallback,
            "hd_run_count": len(runs),
            "hd_run_lengths": runs,
            "one_frame_hd_runs": runs.count(1),
            "longest_hd_run_frames": max(runs, default=0),
            "longest_stock_run_frames": max(original_runs, default=0),
            "gate_fallback_reasons": dict(sorted(gate_reasons.items())),
            "present_outcomes": {
                f"{status}/{reason}": count
                for (status, reason), count in sorted(present_reasons.items())
            },
            "hd_guest_frames": hd_frames,
            "armed_without_hd_draw_guest_frame_ids": undrawn_armed,
            "nonpresented_guest_frame_ids": nonpresented,
        },
        "limitations": [
            "Counts host draw callback returns, not proof of correct pixels or background priority.",
            "Does not treat absent host presentation as a stock frame or join across frame gaps.",
            "P1-only diagnostic draws count as one HD player-frame; Original P2 remains stock.",
            "Current presenter only accepts fixed 256x224 geometry; widescreen is expected to fall back.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("log", type=Path)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    report = analyze(
        args.log.read_text(encoding="utf-8", errors="replace"), source=str(args.log)
    )
    result = json.dumps(report, sort_keys=True, indent=2) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(result, encoding="utf-8")
    print(result, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
