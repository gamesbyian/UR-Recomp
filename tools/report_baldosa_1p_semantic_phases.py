#!/usr/bin/env python3
"""Reproduce phase-biased 1P native art priorities from authenticated guest frames.

A long held result/idle-like semantic state can dominate counts even when it
is absent from the moving racing segment. No assumption about result identity,
original source alpha, frame visuals or authored asset approval is made.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

try:
    from tools.check_baldosa_1p_art_state_worklist import (
        assess as assess_semantic, LINE as STATE,
    )
except ModuleNotFoundError:
    from check_baldosa_1p_art_state_worklist import (
        assess as assess_semantic, LINE as STATE,
    )


def assess(stock_crc: Path, candidate_crc: Path, native_log: Path,
           min_hold: int = 120) -> dict:
    if not 60 <= min_hold <= 400:
        raise ValueError("held-state threshold must be explicit and bounded")
    upstream = assess_semantic(stock_crc, candidate_crc, native_log)
    trace: dict[int, dict] = {}
    for line in native_log.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.startswith("UR_RACER_HD_1P_STATE "):
            continue
        m = STATE.fullmatch(line)
        if m is None:
            raise ValueError("malformed 1P semantic source provenance")
        frame = int(m[1])
        if frame in trace:
            raise ValueError("duplicate 1P source guest frame in art telemetry")
        trace[frame] = {
            "semantic": m[2], "gate": m[6],
            "authored": m[8] == "1", "selected": m[9] != "0",
        }
    race = upstream["race_script_milestone"]
    scoped = {f: v for f, v in trace.items() if f > race}
    if len(scoped) != upstream["post_milestone_trace_guest_frames"]:
        raise ValueError("exact source guest census does not match accepted art report")
    if not scoped:
        raise ValueError("no authenticated in-race P1 semantic states")
    # Only contiguous native frames count as one held state. A long gap
    # cannot falsely turn two isolated same-semantic observations into a hold.
    runs = []
    for frame, v in sorted(scoped.items()):
        if (runs and runs[-1]["semantic"] == v["semantic"] and
                runs[-1]["end"] + 1 == frame):
            runs[-1]["end"] = frame
            runs[-1]["frames"] += 1
        else:
            runs.append({"semantic": v["semantic"], "start": frame,
                         "end": frame, "frames": 1})
    eligible = [x for x in runs if x["frames"] >= min_hold]
    if not eligible:
        return {
            "schema_version": 1, "status": "no-long-held-semantic",
            "native_guest_crc_equal": upstream["native_guest_crc_equal"],
            "native_post_milestone_frames": len(scoped),
            "ranked_motion_semantic": [],
            "new_art_approved": False,
            "limits": "No held state verified; automatic art ranking withheld.",
        }
    held = max(eligible, key=lambda x: (x["frames"], -x["start"]))
    prefix = {f: v for f, v in scoped.items() if f < held["start"]}
    candidates = Counter(v["semantic"] for v in prefix.values())
    # Ignore the late hold's source semantic while finding the actual
    # motion-rich cycle; the late animation transition can contain it too.
    candidates.pop(held["semantic"], None)
    if len(candidates) < 3:
        raise ValueError("fewer than three distinct pre-hold native semantic states")
    top3 = [name for name, _ in candidates.most_common(3)]
    last_motion = max(f for f, v in prefix.items() if v["semantic"] in top3)
    moving = {f: v for f, v in scoped.items() if f <= last_motion}
    transition = {f: v for f, v in scoped.items() if last_motion < f < held["start"]}
    hold = {f: v for f, v in scoped.items() if f >= held["start"]}
    moving_counts = Counter(v["semantic"] for v in moving.values())
    categories = {
        "missing_asset": sum(not v["authored"] for v in moving.values()),
        "authored_unregistered": sum(v["authored"] and not v["selected"] for v in moving.values()),
        "selected_authored": sum(v["selected"] for v in moving.values()),
    }
    if sum(categories.values()) != len(moving) or (
        sum([len(moving), len(transition), len(hold)]) != len(scoped)
    ):
        raise ValueError("temporal source census loses classified native guest frames")
    held_gates = Counter(v["gate"] for v in hold.values())
    return {
        "schema_version": 1,
        "status": "source-derived-1p-temporal-art-priorities",
        "native_guest_crc_equal": upstream["native_guest_crc_equal"],
        "source_script_race_milestone": race,
        "native_post_milestone_frames": len(scoped),
        "motion_rich_upper_bound_window": [min(moving), max(moving)],
        "motion_rich_source_frames": len(moving),
        "motion_rich_semantic_top3": [
            {"semantic_frame": k, "guest_frames": moving_counts[k]} for k in top3
        ],
        "motion_rich_top3_fraction": round(
            sum(moving_counts[k] for k in top3) / len(moving), 6),
        "motion_rich_authored_classification": categories,
        "transition_window": [min(transition), max(transition)] if transition else None,
        "transition_source_guest_frames": len(transition),
        "longest_held_semantic": held,
        "held_source_gate_counts": dict(sorted(held_gates.items())),
        "held_source_guest_frames": len(hold),
        "new_art_approved": False,
        "source_alpha_and_final_ppu_priority_proven": False,
        "limits": (
            "One independently CRC-verified bounded scripted native 1P "
            "guest route. A motion-rich semantic phase inferred from source "
            "cadence is NOT an original-emulator result event classifier, "
            "P1 sprite alpha, or permission to draw/change HD OAM."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--baseline-crc", required=True, type=Path)
    p.add_argument("--candidate-crc", required=True, type=Path)
    p.add_argument("--log", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    a = p.parse_args()
    r = assess(a.baseline_crc, a.candidate_crc, a.log)
    a.out.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n")
    print("UR_RACER_HD_1P_SEMANTIC_PHASES "
          f"status={r['status']} "
          f"held={r.get('longest_held_semantic', {}).get('semantic', 'none')} "
          f"source_guest={r['native_post_milestone_frames']}")


if __name__ == "__main__":
    main()
