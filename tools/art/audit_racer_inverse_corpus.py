#!/usr/bin/env python3
"""Read-only, ROM-free audit of source-registered racer pose groups.

This is a metadata coverage/split diagnostic, NOT a source-pixel or 3D
reconstruction validator. No source art, ROM or neural dependencies.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

SCHEMA = "UR-RACER-INVERSE-CORPUS-AUDIT/1"
DEFAULT = Path(__file__).resolve().parents[2] / "analysis/data/racer-hd-replacement-prototype.json"


def audit(data: dict, source_sha256: str) -> dict:
    if data.get("schema_version") != 1 or not isinstance(data.get("entries"), list):
        raise ValueError("unexpected source registry")
    entries = data["entries"]
    ids = [item.get("representation_id") for item in entries]
    if any(not isinstance(x, str) or not x for x in ids) or len(set(ids)) != len(ids):
        raise ValueError("missing or duplicate representation identity")
    by_id = {row["representation_id"]: row for row in entries}
    sequences = {"first-1205-1220": data.get("motion_review_sequence")}
    sequences.update(data.get("motion_review_sequences") or {})
    groups = []
    occurrence = defaultdict(set)
    for name, sequence in sorted(sequences.items()):
        if not isinstance(sequence, dict):
            raise ValueError("invalid sequence")
        frames = sequence.get("frames")
        if not isinstance(frames, list) or not frames:
            raise ValueError("missing sequence frames")
        previous = None
        counts = {"p1": set(), "p2": set()}
        for record in frames:
            frame = record.get("frame")
            if type(frame) is not int or (previous is not None and frame <= previous):
                raise ValueError("frames must be strictly increasing")
            previous = frame
            present = 0
            for player in ("p1", "p2"):
                rid = record.get(player + "_representation_id")
                if rid is None:
                    continue  # One-player broader-frequency witness.
                if rid not in by_id or by_id[rid].get("player") != player:
                    raise ValueError("unknown or wrong-player representation: " + str(rid))
                present += 1
                counts[player].add(rid)
                occurrence[rid].add(name)
            if present == 0:
                raise ValueError("frame has no registered player representation")
        start, end = sequence.get("window_start"), sequence.get("window_end")
        if frames[0]["frame"] != start or frames[-1]["frame"] != end:
            raise ValueError("sequence range does not match frame contents")
        groups.append({
            "id": name, "first_frame": start, "last_frame": end,
            "observed_frame_count": len(frames),
            "unique_p1_representations": len(counts["p1"]),
            "unique_p2_representations": len(counts["p2"]),
            "representation_ids": sorted(counts["p1"] | counts["p2"]),
        })
    shared = {rid: sorted(seq) for rid, seq in occurrence.items() if len(seq) > 1}
    # Do not promote a suggested holdout to an independent test unless its
    # representation identities are disjoint and source pixel hashes verify.
    for group in groups:
        group["shares_identity_with_other_groups"] = any(
            rid in shared for rid in group["representation_ids"]
        )
        group["source_pixel_hashes_verified"] = False
        group["independent_camera_verified"] = False
        group["eligible_for_authentic_3d_holdout"] = False
    return {
        "schema": SCHEMA, "source_manifest_sha256": source_sha256,
        "registered_entry_count": len(entries), "sequence_count": len(groups),
        "distinct_representations_in_sequences": len(occurrence),
        "cross_sequence_reused_representation_count": len(shared),
        "cross_sequence_reused_representations": shared,
        "groups": groups,
        "source_pixels_loaded": False,
        "original_3d_geometry_recovered": False,
        "heldout_pose_family_independently_verified": False,
        "character_likeness_approved": False,
        "shipping_art_approved": False,
        "next_step": "Recover exact source raster SHA and independently deduplicate semantic/visual aliases before freezing training and holdout partitions.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT)
    parser.add_argument("--out", type=Path, help="Optional machine-readable metadata receipt")
    args = parser.parse_args()
    raw = args.source.read_bytes()
    report = audit(json.loads(raw), hashlib.sha256(raw).hexdigest())
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
