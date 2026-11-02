#!/usr/bin/env python3
"""Conservative discrete pose-label experiment on source-indexed costs.

Source 2D chronology and camera / model authenticity must be validated
separately. This tool cannot identify the 1994 3D pose or change game art.
"""
from __future__ import annotations
import argparse
import json
import math


def _cost(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def fit(data):
    if not isinstance(data, dict):
        raise ValueError("expected JSON object")
    poses, frames = data.get("poses"), data.get("frames")
    penalty = data.get("change_penalty", 0.0)
    if (not isinstance(poses, list) or not 1 <= len(poses) <= 32
            or any(type(p) is not str or not p for p in poses)
            or len(set(poses)) != len(poses)):
        raise ValueError("expected 1..32 distinct nonempty poses")
    if not isinstance(frames, list) or not 1 <= len(frames) <= 10000:
        raise ValueError("expected 1..10000 source-indexed frames")
    if not _cost(penalty):
        raise ValueError("invalid change penalty")
    transitions = data.get("transition_penalties")
    if transitions is not None:
        if (not isinstance(transitions, dict) or set(transitions) != set(poses)
                or any(not isinstance(transitions[p], dict)
                       or set(transitions[p]) != set(poses) for p in poses)
                or any(not _cost(transitions[p][q]) for p in poses for q in poses)):
            raise ValueError("invalid or incomplete transition matrix")

    # No fictitious transitions: window/player identities and actual guest-frame
    # adjacency are mandatory. No reordering or interpolation is performed.
    groups, seen, last_by_track = [], set(), {}
    for frame in frames:
        if not isinstance(frame, dict):
            raise ValueError("invalid source frame")
        window, player, number = frame.get("window"), frame.get("player"), frame.get("guest_frame")
        costs = frame.get("costs")
        if (type(window) is not str or not window or player not in ("p1", "p2")
                or type(number) is not int or number < 0
                or not isinstance(costs, dict) or set(costs) != set(poses)
                or any(not _cost(x) for x in costs.values())):
            raise ValueError("invalid original source identity or costs")
        identity, track = (window, player, number), (window, player)
        if identity in seen:
            raise ValueError("duplicate source frame")
        seen.add(identity)
        if track in last_by_track and number <= last_by_track[track]:
            raise ValueError("nonmonotonic original source chronology")
        last_by_track[track] = number
        previous = groups[-1][-1] if groups else None
        if (previous is None or (previous["window"], previous["player"]) != track
                or number != previous["guest_frame"] + 1):
            groups.append([])
        groups[-1].append(frame)

    sequences = []
    for seq in groups:
        dp = {p: (seq[0]["costs"][p], (p,)) for p in poses}
        for frame in seq[1:]:
            # Tuple ordering supplies deterministic lexical tie-breaking.
            dp = {
                q: min((dp[p][0] + frame["costs"][q]
                        + (transitions[p][q] if transitions is not None
                           else penalty if p != q else 0),
                        dp[p][1] + (q,)) for p in poses)
                for q in poses
            }
        total, labels = min(dp.values())
        independent = [min(poses, key=lambda p: (f["costs"][p], p)) for f in seq]
        emission = sum(f["costs"][p] for f, p in zip(seq, labels))
        sequences.append({
            "window": seq[0]["window"], "player": seq[0]["player"],
            "guest_frames": [f["guest_frame"] for f in seq],
            "sequence_poses": list(labels), "independent_poses": independent,
            "sequence_cost": total, "sequence_emission_cost": emission,
            "sequence_transition_cost": total - emission,
            "independent_emission_cost": sum(f["costs"][p] for f, p in zip(seq, independent)),
            "sequence_transition_count": sum(a != b for a, b in zip(labels, labels[1:])),
            "independent_transition_count": sum(a != b for a, b in zip(independent, independent[1:])),
            "constant_label_sequence": len(set(labels)) == 1,
        })
    return {
        "method": "original-racer-discrete-temporal-label-baseline/2",
        "original_pose_identity_verified": False,
        "camera_or_3d_joint_motion_recovered": False,
        "interpretation": "source-indexed costs; coherence is not authentic 3D pose recovery",
        "sequences": sequences,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input")
    parser.add_argument("--output")
    args = parser.parse_args()
    with open(args.input, encoding="utf-8") as stream:
        result = fit(json.load(stream))
    report = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8") as stream:
            stream.write(report)
    else:
        print(report, end="")


if __name__ == "__main__":
    main()
