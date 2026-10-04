#!/usr/bin/env python3
"""Collapse exact semantic registrations into byte-identical stock visual poses."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def build_equivalence(dossier: dict[str, Any]) -> dict[str, Any]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for rep in dossier.get("representations", []):
        stock_hash = rep["stock_evidence"]["rgba_sha256"]
        groups[(rep["player"], stock_hash)].append(rep)

    pose_groups = []
    unauthored = []
    duplicate_authored = []
    for index, ((player, stock_hash), reps) in enumerate(sorted(groups.items()), 1):
        reps = sorted(reps, key=lambda row: row["representation_id"])
        authored = [
            row for row in reps
            if row.get("art_review", {}).get("authored_candidate") is not None
        ]
        source = authored[0]["representation_id"] if authored else None
        row = {
            "pose_id": f"{player}-pose-{index:03d}",
            "player": player,
            "stock_rgba_sha256": stock_hash,
            "representation_ids": [rep["representation_id"] for rep in reps],
            "semantic_frame_ids": sorted({rep["semantic_frame_id"] for rep in reps}),
            "observed_frames": sorted({
                frame
                for rep in reps
                for frame in rep.get("observed_frames_in_window", [])
            }),
            "authored_source_representation_id": source,
            "reuse_candidates": [
                rep["representation_id"] for rep in reps
                if source is not None and rep["representation_id"] != source
            ],
            "needs_authored_asset": source is None,
        }
        pose_groups.append(row)
        if source is None:
            unauthored.append(row["pose_id"])
        if len(authored) > 1:
            duplicate_authored.append({
                "pose_id": row["pose_id"],
                "authored_representation_ids": [
                    rep["representation_id"] for rep in authored
                ],
            })

    count = len(dossier.get("representations", []))
    return {
        "schema_version": 1,
        "family": dossier.get("family"),
        "source_temporal_window": dossier.get("temporal_window"),
        "semantic_representation_count": count,
        "unique_stock_pose_count": len(pose_groups),
        "semantic_registrations_collapsed_by_visual_equivalence": count - len(pose_groups),
        "pose_groups": pose_groups,
        "worklist": {
            "unauthored_pose_ids": unauthored,
            "unauthored_pose_count": len(unauthored),
            "duplicate_authored_groups": duplicate_authored,
        },
        "rule": (
            "Exact semantic/composition guards remain distinct runtime identities. "
            "Only byte-identical stock RGBA poses for the same player are eligible "
            "to share authored visual assets."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dossier", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = build_equivalence(json.loads(args.dossier.read_text()))
    rendered = json.dumps(result, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered)
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
