#!/usr/bin/env python3
"""Audit real *temporal* original racer sprite changes without inventing 3D poses.

Tracks SHA-authenticated 64x64 original P1/P2 guest-frame 1205..1220
silhouettes. Separates exact alpha-shape holds, raw 2D raster changes and
source-registered, contact-aligned shape changes under identical pixel-aspect.
Source contact is the lowest visible alpha midpoint, never inferred physics
ground contact. Does not assign source frames to experimental 2026 GLB poses.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

try:
    from tools.art.build_racer_source_pixel_corpus import build, ROOT, STRIP, REGISTRY
    from tools.art.build_real_viewer_pose_matrix import (
        original_registered_contacts, original_lowest_alpha_anchor,
        translated_binary_mask,
    )
    from tools.art.racer_source_pixels import alpha_metrics, decode_rgba_png
    from tools.art.no_replace_report import publish_text_once
except ModuleNotFoundError:
    from build_racer_source_pixel_corpus import build, ROOT, STRIP, REGISTRY
    from build_real_viewer_pose_matrix import (
        original_registered_contacts, original_lowest_alpha_anchor,
        translated_binary_mask,
    )
    from racer_source_pixels import alpha_metrics, decode_rgba_png
    from no_replace_report import publish_text_once

SCHEMA = "UR-RACER-ORIGINAL-SOURCE-TEMPORAL-CADENCE/1"
PLAYERS = ("p1", "p2")
FRAMES = range(1205, 1221)
ANCHOR = (67, 76)
CANONICAL_ROM_SHA = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def valid_hash(value) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(
        c in "0123456789abcdef" for c in value
    )


def raw_mask_comparison(left: bytes, right: bytes) -> dict:
    if len(left) != 4096 or len(right) != 4096 or any(v not in (0, 1) for v in left+right):
        raise ValueError("original binary silhouette comparison requires two 64x64 alpha masks")
    both = sum(a and b for a, b in zip(left, right))
    union = sum(a or b for a, b in zip(left, right))
    return {
        "mask_xor_pixels": sum(a != b for a, b in zip(left, right)),
        "mask_intersection_pixels": both,
        "mask_union_pixels": union,
        "mask_iou": round(both / union, 8) if union else 1.0,
    }


def audit_rows(rows: list[dict], *, registry_sha256: str,
               rom_sha256: str, witness_anchor=ANCHOR) -> dict:
    """Pure validator and temporal reducer; source PNGs checked by loader.

    Rows carry transient decoded 64x64 binary masks and immutable source SHA.
    No mask pixels are written to the returned JSON receipt.
    """
    if (rom_sha256 != CANONICAL_ROM_SHA or not valid_hash(registry_sha256) or
            witness_anchor != ANCHOR):
        raise ValueError("original ROM/registry identity or witness anchor changed")
    by_key = {}
    for row in rows:
        key = (row.get("player"), row.get("guest_frame"))
        mask = row.get("mask")
        anchor = row.get("registered_contact_x2_y2")
        if (key[0] not in PLAYERS or type(key[1]) is not int or key[1] not in FRAMES or
                key in by_key):
            raise ValueError("duplicate or invalid original player/frame identity")
        if (not isinstance(mask, bytes) or len(mask) != 4096 or
                any(v not in (0, 1) for v in mask) or not any(mask) or
                not valid_hash(row.get("source_rgba_sha256")) or
                row.get("binary_mask_sha256") != sha(mask) or
                not isinstance(row.get("representation_id"), str) or
                not row["representation_id"] or not valid_hash(row.get("source_png_sha256"))):
            raise ValueError("original sprite pixel provenance/mask is missing or false")
        if (not isinstance(anchor, tuple) or len(anchor) != 2 or
                any(type(x) is not int for x in anchor) or
                original_lowest_alpha_anchor(mask) != anchor):
            raise ValueError("original registered contact disagrees with authentic alpha pixels")
        delta = (witness_anchor[0] - anchor[0], witness_anchor[1] - anchor[1])
        if any(v % 2 for v in delta):
            raise ValueError("original half-pixel parity requires a 4x rerender, not rounding")
        aligned = translated_binary_mask(mask, delta[0] // 2, delta[1] // 2)
        by_key[key] = {**row, "aligned_mask": aligned}
    if set(by_key) != {(player, frame) for player in PLAYERS for frame in FRAMES}:
        raise ValueError("original sequence must contain all 16 frames for both players")
    out_players = {}
    changed_at_frame = {}
    grouped_ids = {}
    for player in PLAYERS:
        timeline = []
        transitions = []
        runs = []
        last = None
        run = None
        for frame in FRAMES:
            row = by_key[player, frame]
            mask_sha = row["binary_mask_sha256"]
            timeline.append({
                "guest_frame": frame,
                "representation_id": row["representation_id"],
                "source_rgba_sha256": row["source_rgba_sha256"],
                "source_png_sha256": row["source_png_sha256"],
                "original_binary_mask_sha256": mask_sha,
                "registered_bottom_alpha_midpoint_x2_y2": list(row["registered_contact_x2_y2"]),
                "reference_to_witness_translation_logical_xy": [
                    (ANCHOR[k] - row["registered_contact_x2_y2"][k]) // 2
                    for k in (0, 1)
                ],
            })
            if run is None or run["original_binary_mask_sha256"] != mask_sha:
                run = {
                    "start_guest_frame": frame,
                    "end_guest_frame": frame,
                    "frame_count": 1,
                    "original_binary_mask_sha256": mask_sha,
                    "original_representation_ids": [row["representation_id"]],
                }
                runs.append(run)
            else:
                run["end_guest_frame"] = frame
                run["frame_count"] += 1
                if row["representation_id"] not in run["original_representation_ids"]:
                    run["original_representation_ids"].append(row["representation_id"])
            if last is not None:
                raw = raw_mask_comparison(last["mask"], row["mask"])
                aligned = raw_mask_comparison(last["aligned_mask"], row["aligned_mask"])
                change = raw["mask_xor_pixels"] != 0
                changed_at_frame[player, frame] = change
                transitions.append({
                    "from_guest_frame": frame - 1,
                    "to_guest_frame": frame,
                    "source_registered_anchor_delta_x2_y2": [
                        row["registered_contact_x2_y2"][k] -
                        last["registered_contact_x2_y2"][k] for k in (0, 1)
                    ],
                    "exact_source_shape_changed": change,
                    "raw_original_binary_mask_xor_pixels": raw["mask_xor_pixels"],
                    "raw_original_binary_mask_iou": raw["mask_iou"],
                    "contact_aligned_binary_mask_xor_pixels": aligned["mask_xor_pixels"],
                    "contact_aligned_binary_mask_iou": aligned["mask_iou"],
                    "original_2d_alpha_placement_separated_from_shape_only": True,
                    "original_3d_pose_correspondence_established": False,
                })
            last = row
        unique = set(x["original_binary_mask_sha256"] for x in timeline)
        grouped_ids[player] = unique
        out_players[player] = {
            "guest_frame_count": len(timeline),
            "consecutive_frame_transition_count": len(transitions),
            "distinct_original_binary_masks": len(unique),
            "original_shape_change_edges": sum(t["exact_source_shape_changed"] for t in transitions),
            "unchanged_original_shape_edges": sum(not t["exact_source_shape_changed"] for t in transitions),
            "distinct_contiguous_source_shape_holds": len(runs),
            "longest_contiguous_source_shape_hold_frames": max(x["frame_count"] for x in runs),
            "source_frame_sequence": timeline,
            "source_shape_holds": runs,
            "source_frame_transitions": transitions,
        }
    paired = []
    for frame in list(FRAMES)[1:]:
        changing = [p for p in PLAYERS if changed_at_frame[p, frame]]
        paired.append({
            "transition_to_guest_frame": frame,
            "player_source_shapes_changed": changing,
            "both_players_changed": len(changing) == 2,
            "both_players_held": len(changing) == 0,
            "coincident_change_is_synchronized_3d_animation_proof": False,
        })
    return {
        "schema": SCHEMA,
        "original_source_registry_sha256": registry_sha256,
        "original_source_rom_sha256": rom_sha256,
        "source_image_provenance": "independent retained ROM-composed 64x64 PNGs, verified by build_racer_source_pixel_corpus",
        "guest_frame_range": [FRAMES.start, FRAMES.stop - 1],
        "source_pixel_aspect": "7:6",
        "logical_witness_bottom_alpha_midpoint_x2_y2": list(ANCHOR),
        "original_bottom_alpha_midpoint_is_physical_contact": False,
        "all_original_2d_offsets_are_source_registered_not_iou_optimized": True,
        "original_frame_observations": len(rows),
        "distinct_original_binary_silhouettes": len(set().union(*grouped_ids.values())),
        "players": out_players,
        "paired_player_frame_transition_observations": paired,
        "original_p1_p2_temporal_coupling_or_shared_3d_phase_verified": False,
        "source_1994_3d_pose_mapping_verified": False,
        "source_1994_camera_recovered": False,
        "independent_3d_camera_or_heldout_family_evaluated": False,
        "owner_likeness_approved": False,
        "shipping_art_approved": False,
    }


def authentic_rows() -> tuple[list[dict], dict]:
    """Require independently checked original PNG bytes, frame and registered ID."""
    corpus = build()
    if corpus.get("historical_manifest_declared_rom_sha256") != CANONICAL_ROM_SHA:
        raise ValueError("source retained corpus ROM provenance is wrong")
    contacts = original_registered_contacts(REGISTRY, corpus["source_registry_current_sha256"])
    rows = []
    loaded = {}
    for item in corpus["observations"]:
        path = (ROOT / item["source_image"]).resolve()
        if (not path.is_relative_to(STRIP.resolve()) or not path.is_file() or
                path.suffix != ".png"):
            raise ValueError("original source image escaped retained first-family strip")
        if path not in loaded:
            loaded[path] = decode_rgba_png(path)
        w, h, rgba, png_sha = loaded[path]
        metrics = alpha_metrics(rgba, w, h)
        if ((w, h) != (64, 64) or png_sha != item["png_file_sha256"] or
                metrics["source_rgba_sha256"] != item["source_rgba_sha256"] or
                metrics["binary_mask_sha256"] != item["binary_mask_sha256"]):
            raise ValueError("retained original source bytes differ from independent audit")
        match = contacts.get(item["representation_id"])
        if match is None or match[0] != item["player"]:
            raise ValueError("original source representation has no correct registered player")
        mask = bytes(1 if value else 0 for value in rgba[3::4])
        rows.append({
            "player": item["player"],
            "guest_frame": item["guest_frame"],
            "representation_id": item["representation_id"],
            "mask": mask,
            "binary_mask_sha256": metrics["binary_mask_sha256"],
            "source_rgba_sha256": metrics["source_rgba_sha256"],
            "source_png_sha256": png_sha,
            "registered_contact_x2_y2": match[1],
        })
    return rows, corpus


def run() -> dict:
    rows, corpus = authentic_rows()
    report = audit_rows(
        rows,
        registry_sha256=corpus["source_registry_current_sha256"],
        rom_sha256=corpus["historical_manifest_declared_rom_sha256"],
    )
    report["retained_original_source_manifest_sha256_by_player"] = (
        corpus["showcase_manifest_sha256"]
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="new immutable report JSON; stdout default")
    args = parser.parse_args()
    result = json.dumps(run(), indent=2, sort_keys=True) + "\n"
    if args.out:
        publish_text_once(args.out, result)
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
