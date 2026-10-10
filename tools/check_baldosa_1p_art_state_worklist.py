#!/usr/bin/env python3
"""Rank actual source-derived missing 1P racer art/composition states.

Read-only guest WRAM census, never a license to draw synthetic HD riders.
All counts refer to actual guest frames, not desktop screenshot frames.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re

LINE = re.compile(
    r"^UR_RACER_HD_1P_STATE frame=(\d+) semantic=([0-9A-F]{4}) "
    r"primary=([0-9A-F]{4}) companion=([0-9A-F]{4}) "
    r"selector=([0-9A-F]{4}) gate=([0-9A-F]{4}) "
    r"registered=([01]) art=([01]) selected=([012]) fallback=([0-4])$"
)
GATE = re.compile(r"^UR_RACER_HD_CENSUS frame=(\d+) phase=gate ")
RACE = re.compile(r"^script f=(\d+) until 00E1F ok after \d+ frames$")
END = re.compile(r"^script f=(\d+) dump end ok$")


def assess(baseline: Path, traced_crc: Path, log: Path) -> dict:
    a, b = baseline.read_bytes().splitlines(), traced_crc.read_bytes().splitlines()
    if len(a) != 5447 or a != b:
        raise ValueError("missing independent full 5447-frame 1P guest CRC match")
    lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
    race = [int(m[1]) for line in lines if (m := RACE.fullmatch(line))]
    end = [int(m[1]) for line in lines if (m := END.fullmatch(line))]
    if len(race) != 1 or len(end) != 1 or race[0] >= end[0] or end[0] != len(a):
        raise ValueError("source-script 1P race milestone/terminal provenance absent")
    seen = {}
    native_gates = {int(m[1]) for line in lines if (m := GATE.match(line))}
    for line in lines:
        if not line.startswith("UR_RACER_HD_1P_STATE "):
            continue
        match = LINE.fullmatch(line)
        if not match:
            raise ValueError("malformed source-origin 1P semantic state trace")
        frame = int(match[1])
        if frame in seen or frame not in native_gates or not (1700 <= frame <= 5150):
            raise ValueError("1P semantic trace has duplicate/non-native/outside-window guest frame")
        semantic, primary, companion, selector, gate = (int(v, 16) for v in match.groups()[1:6])
        registered, art, selected, fallback = map(int, match.groups()[6:])
        seen[frame] = {
            "semantic_frame": semantic,
            "primary": primary,
            "companion": companion,
            "selector": selector,
            "gate": gate,
            "selected_registration": registered,
            "authored_asset": art,
            "selected_pack": selected,
            "selection_fallback": fallback,
        }
    if not seen or not any(f > race[0] for f in seen):
        raise ValueError("no real post-race-milestone 1P source states observed")
    scoped = [v for f, v in sorted(seen.items()) if race[0] < f <= end[0]]
    reasons = Counter(str(v["selection_fallback"]) for v in scoped)
    missing_asset = Counter()
    unmatched_state = Counter()
    covered = Counter()
    for x in scoped:
        if x["semantic_frame"] == 0:
            continue
        name = f"{x['semantic_frame']:04X}:{x['primary']:04X}:{x['companion']:04X}:{x['selector']:04X}:{x['gate']:04X}"
        if not x["authored_asset"]:
            missing_asset[name] += 1
        elif not x["selected_registration"] or x["selected_pack"] == 0:
            unmatched_state[name] += 1
        else:
            covered[name] += 1
    return {
        "schema_version": 1,
        "status": "measured-source-1p-semantic-worklist",
        "native_guest_crc_equal": len(a),
        "race_script_milestone": race[0],
        "native_trace_guest_frames": len(seen),
        "post_milestone_trace_guest_frames": len(scoped),
        "registered_state_samples": sum(covered.values()),
        "missing_authored_asset_samples": sum(missing_asset.values()),
        "registered_art_state_mismatch_samples": sum(unmatched_state.values()),
        "semantic_zero_samples": sum(x["semantic_frame"] == 0 for x in scoped),
        "selected_fallback_distribution": dict(sorted(reasons.items())),
        "top_missing_art_exact_states": [
            {"state": state, "guest_frames": count}
            for state, count in missing_asset.most_common(25)
        ],
        "top_authored_but_not_registered_exact_states": [
            {"state": state, "guest_frames": count}
            for state, count in unmatched_state.most_common(25)
        ],
        "top_selected_authored_exact_states": [
            {"state": state, "guest_frames": count}
            for state, count in covered.most_common(12)
        ],
        "release_art_approval": False,
        "widescreen_hd_admission": False,
        "limits": (
            "P1 semantic/selector/guard statistics from actual guest WRAM "
            "after race milestone. These ranks do not establish source-OBJ "
            "visibility, BG priority, all-camera coverage, asset fidelity, "
            "safe 342-wide replacement or any finished Windows release."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--baseline-crc", required=True, type=Path)
    p.add_argument("--candidate-crc", required=True, type=Path)
    p.add_argument("--log", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    a = p.parse_args()
    report = assess(a.baseline_crc, a.candidate_crc, a.log)
    a.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("UR_RACER_HD_1P_WORKLIST "
          f"guest={report['post_milestone_trace_guest_frames']} "
          f"missing_art={report['missing_authored_asset_samples']} "
          f"unregistered={report['registered_art_state_mismatch_samples']} "
          f"covered={report['registered_state_samples']} "
          "release_admitted=0")


if __name__ == "__main__":
    main()
