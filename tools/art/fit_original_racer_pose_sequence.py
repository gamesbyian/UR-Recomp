#!/usr/bin/env python3
"""Deterministic temporal labeling of existing per-frame, per-pose silhouette costs.

Exploratory inference only: source animation identities and camera remain unverified.
"""
import argparse
import json
import math


def fit(data):
    poses, frames = data["poses"], data["frames"]
    weight = data.get("change_penalty", 0.0)
    if not isinstance(poses, list) or not poses or any(not isinstance(p, str) or not p for p in poses) or len(set(poses)) != len(poses):
        raise ValueError("poses must be distinct nonempty strings")
    if not isinstance(frames, list) or not frames:
        raise ValueError("frames required")
    def valid_cost(x):
        return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) and x >= 0
    if not valid_cost(weight):
        raise ValueError("invalid change penalty")
    transitions = data.get("transition_penalties")
    if transitions is not None:
        if set(transitions) != set(poses) or any(set(transitions[p]) != set(poses) for p in poses):
            raise ValueError("incomplete transition matrix")
        if any(not valid_cost(transitions[p][q]) for p in poses for q in poses):
            raise ValueError("invalid transition penalty")
    ids, sequences = set(), []
    for frame in frames:
        fid, family, costs = frame["id"], frame["family"], frame["costs"]
        if not isinstance(fid, str) or not fid or fid in ids:
            raise ValueError("duplicate/invalid frame id")
        ids.add(fid)
        if not isinstance(family, str) or not family or set(costs) != set(poses) or any(not valid_cost(v) for v in costs.values()):
            raise ValueError("invalid frame family or costs")
        if not sequences or sequences[-1][0]["family"] != family:
            sequences.append([])
        sequences[-1].append(frame)
    output = []
    for seq in sequences:
        dp = {p: (seq[0]["costs"][p], (p,)) for p in poses}
        for frame in seq[1:]:
            dp = {q: min((dp[p][0] + (transitions[p][q] if transitions is not None else (weight if p != q else 0)) + frame["costs"][q], dp[p][1] + (q,)) for p in poses) for q in poses}
        score, labels = min(dp.values())
        greedy = [min(poses, key=lambda p: (f["costs"][p], p)) for f in seq]
        output.append({"family": seq[0]["family"], "frame_ids": [f["id"] for f in seq],
                       "sequence_poses": list(labels), "independent_poses": greedy,
                       "sequence_cost": score, "sequence_emission_cost": sum(f["costs"][p] for f, p in zip(seq, labels)),
                       "independent_emission_cost": sum(f["costs"][p] for f, p in zip(seq, greedy))})
    return {"method": "temporal-pose-label-baseline", "original_pose_identity_verified": False,
            "sequences": output}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input")
    parser.add_argument("--output")
    args = parser.parse_args()
    with open(args.input, encoding="utf-8") as stream:
        result = fit(json.load(stream))
    report = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8") as stream:
            stream.write(report)
    else:
        print(report, end="")


if __name__ == "__main__":
    main()
