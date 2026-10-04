#!/usr/bin/env python3
"""Join Racer HD visual-pose evidence to explicit shipping-art review decisions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ALLOWED_STATUSES = {"approved", "needs-refinement", "rejected"}


def build_shipping_readiness(
    equivalence: dict[str, Any],
    decisions: dict[str, Any],
) -> dict[str, Any]:
    decision_rows = decisions.get("decisions", [])
    by_source: dict[str, dict[str, Any]] = {}
    for row in decision_rows:
        source = row["authored_source_representation_id"]
        if source in by_source:
            raise ValueError(f"duplicate art decision for {source}")
        status = row["status"]
        if status not in ALLOWED_STATUSES:
            raise ValueError(f"unsupported art decision status {status!r} for {source}")
        approved = bool(row.get("shipping_art_approved", False))
        if approved != (status == "approved"):
            raise ValueError(
                f"{source} shipping_art_approved disagrees with status {status}"
            )
        by_source[source] = row

    poses = []
    expected_sources: list[str] = []
    for pose in equivalence.get("pose_groups", []):
        source = pose.get("authored_source_representation_id")
        if source is None:
            status = "unauthored"
            decision = None
        else:
            expected_sources.append(source)
            decision = by_source.get(source)
            if decision is None:
                status = "unreviewed"
            elif decision.get("reviewed_authored_rgba_sha256") != pose.get(
                "authored_asset_rgba_sha256"
            ):
                status = "changed-since-review"
            else:
                status = decision["status"]
        poses.append({
            "pose_id": pose["pose_id"],
            "player": pose["player"],
            "authored_source_representation_id": source,
            "representation_ids": pose["representation_ids"],
            "observed_frames": pose["observed_frames"],
            "needs_authored_asset": pose["needs_authored_asset"],
            "authored_asset_conflict": pose.get("authored_asset_conflict", False),
            "review_status": status,
            "shipping_art_approved": status == "approved",
            "authored_asset_rgba_sha256": pose.get("authored_asset_rgba_sha256"),
            "reviewed_authored_rgba_sha256": (
                decision.get("reviewed_authored_rgba_sha256")
                if decision is not None else None
            ),
            "blocker_codes": (
                list(decision.get("blocker_codes", []))
                if decision is not None else []
            ),
        })

    expected = set(expected_sources)
    supplied = set(by_source)
    extra = sorted(supplied - expected)
    if extra:
        raise ValueError(
            "art decisions reference poses outside the current equivalence surface: "
            + ", ".join(extra)
        )

    counts = {
        "approved": sum(p["review_status"] == "approved" for p in poses),
        "needs_refinement": sum(
            p["review_status"] == "needs-refinement" for p in poses
        ),
        "rejected": sum(p["review_status"] == "rejected" for p in poses),
        "unreviewed": sum(p["review_status"] == "unreviewed" for p in poses),
        "changed_since_review": sum(
            p["review_status"] == "changed-since-review" for p in poses
        ),
        "unauthored": sum(p["review_status"] == "unauthored" for p in poses),
        "authored_conflicts": sum(p["authored_asset_conflict"] for p in poses),
    }
    shipping_ready = (
        len(poses) > 0
        and counts["approved"] == len(poses)
        and counts["needs_refinement"] == 0
        and counts["rejected"] == 0
        and counts["unreviewed"] == 0
        and counts["changed_since_review"] == 0
        and counts["unauthored"] == 0
        and counts["authored_conflicts"] == 0
    )
    return {
        "schema_version": 1,
        "family": equivalence.get("family"),
        "source_temporal_window": equivalence.get("source_temporal_window"),
        "review_basis": decisions.get("review_basis"),
        "family_blockers": decisions.get("family_blockers", []),
        "unique_pose_count": len(poses),
        "counts": counts,
        "shipping_ready": shipping_ready,
        "poses": poses,
        "rule": (
            "Shipping-art approval is owned once per unique byte-identical visual pose "
            "and is bound to the exact authored RGBA hash reviewed. Distinct semantic/"
            "runtime guards retain independent identity and inherit the approved or "
            "blocked visual asset only through the pose-equivalence proof. Any authored "
            "byte change invalidates the previous review disposition for that pose."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("equivalence", type=Path)
    parser.add_argument(
        "--decisions",
        type=Path,
        default=Path("analysis/data/racer-hd-art-approval.json"),
    )
    parser.add_argument("--out", type=Path)
    parser.add_argument("--require-shipping-ready", action="store_true")
    args = parser.parse_args()

    result = build_shipping_readiness(
        json.loads(args.equivalence.read_text(encoding="utf-8")),
        json.loads(args.decisions.read_text(encoding="utf-8")),
    )
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    if args.require_shipping_ready and not result["shipping_ready"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
