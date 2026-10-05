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
    if equivalence.get("schema_version") != 1:
        raise ValueError("unsupported pose-equivalence schema version")
    if decisions.get("schema_version") != 1:
        raise ValueError("unsupported art-approval schema version")

    equivalence_family = equivalence.get("family")
    decision_family = decisions.get("family")
    if not isinstance(equivalence_family, str) or not equivalence_family:
        raise ValueError("equivalence surface lacks a family")
    if decision_family != equivalence_family:
        raise ValueError(
            f"approval family {decision_family!r} does not match "
            f"equivalence family {equivalence_family!r}"
        )

    source_window = equivalence.get("source_temporal_window")
    review_basis = decisions.get("review_basis")
    if not isinstance(source_window, dict):
        raise ValueError("equivalence surface lacks a source temporal window")
    if not isinstance(review_basis, dict):
        raise ValueError("approval ledger lacks a review basis")
    start = source_window.get("start")
    end = source_window.get("end")
    if (
        not isinstance(start, int)
        or isinstance(start, bool)
        or not isinstance(end, int)
        or isinstance(end, bool)
        or end < start
    ):
        raise ValueError("equivalence surface has invalid temporal bounds")
    reviewed_window = review_basis.get("temporal_window")
    expected_window = [start, end]
    if reviewed_window != expected_window:
        raise ValueError(
            f"approval temporal window {reviewed_window!r} does not match "
            f"equivalence window {expected_window!r}"
        )
    for field in ("workflow_run", "artifact_id"):
        value = review_basis.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ValueError(f"approval review basis lacks a positive {field}")
    review_surface = review_basis.get("review_surface")
    if not isinstance(review_surface, str) or not review_surface.strip():
        raise ValueError("approval review basis lacks a review_surface")

    family_blockers = decisions.get("family_blockers", [])
    if not isinstance(family_blockers, list):
        raise ValueError("family_blockers must be a list")

    decision_rows = decisions.get("decisions", [])
    if not isinstance(decision_rows, list):
        raise ValueError("decisions must be a list")
    by_source: dict[str, dict[str, Any]] = {}
    for row in decision_rows:
        if not isinstance(row, dict):
            raise ValueError("each art decision must be an object")
        source = row["authored_source_representation_id"]
        if source in by_source:
            raise ValueError(f"duplicate art decision for {source}")
        status = row["status"]
        if status not in ALLOWED_STATUSES:
            raise ValueError(f"unsupported art decision status {status!r} for {source}")
        reviewed_hash = row.get("reviewed_authored_rgba_sha256")
        if (
            not isinstance(reviewed_hash, str)
            or len(reviewed_hash) != 64
            or any(ch not in "0123456789abcdef" for ch in reviewed_hash)
        ):
            raise ValueError(
                f"{source} lacks a lowercase hexadecimal reviewed authored RGBA SHA-256"
            )
        approved = bool(row.get("shipping_art_approved", False))
        if approved != (status == "approved"):
            raise ValueError(
                f"{source} shipping_art_approved disagrees with status {status}"
            )
        blocker_codes = row.get("blocker_codes", [])
        if not isinstance(blocker_codes, list):
            raise ValueError(f"{source} blocker_codes must be a list")
        if status == "approved" and blocker_codes:
            raise ValueError(
                f"{source} is approved but still carries blocker codes"
            )
        by_source[source] = row

    pose_groups = equivalence.get("pose_groups", [])
    if not isinstance(pose_groups, list):
        raise ValueError("pose_groups must be a list")

    poses = []
    expected_sources: list[str] = []
    for pose in pose_groups:
        if not isinstance(pose, dict):
            raise ValueError("each pose group must be an object")
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
        and not family_blockers
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
        "family": equivalence_family,
        "source_temporal_window": source_window,
        "review_basis": review_basis,
        "family_blockers": family_blockers,
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
