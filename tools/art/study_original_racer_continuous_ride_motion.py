#!/usr/bin/env python3
"""Source-authenticated, unpaired motion potential of five real ride-cycle GLBs.

Four *predeclared* 2026 rig-time steps are evaluated independently against each
genuine original 1994 P1/P2 frame edge. No source guest frame is assigned a rig
time; this is descriptive transition coverage, not a fitted 1994 trajectory.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path

try:
    from tools.art.audit_original_racer_pose_transition_pixels import pixel_change
    from tools.art.compare_original_chroma_axes_to_glb_poses import CAMERA_SHA
    from tools.art.evaluate_original_racer_wheel_holdout import (
        originals_from_corpus, translated_4x_source_mask,
    )
    from tools.art.freeze_racer_source_family_splits import validate_corpus
    from tools.art.render_racer_glb_projection import (
        camera_config, model_mesh, render_mask,
    )
    from tools.art.no_replace_report import publish_text_once
except ModuleNotFoundError:
    from audit_original_racer_pose_transition_pixels import pixel_change
    from compare_original_chroma_axes_to_glb_poses import CAMERA_SHA
    from evaluate_original_racer_wheel_holdout import (
        originals_from_corpus, translated_4x_source_mask,
    )
    from freeze_racer_source_family_splits import validate_corpus
    from render_racer_glb_projection import camera_config, model_mesh, render_mask
    from no_replace_report import publish_text_once

SCHEMA = "UR-ART4K-REAL-CONTINUOUS-RIDE-SOURCE-MOTION/1"
SOURCE_RIG_SHA = "e99ef45bfe72f09ee97f51b7d7449c501aee2ca2d93596106ede4b56caddc984"
TIMES = ("0.0", "0.25", "0.5", "0.75", "1.0")
# Real 2026 OpenSCAD GLB bytes verified from exact-head original authoring
# workflow run 41383635894, artifact ZIP and immutable exporter receipts.
PINNED_GRID_GLB_SHA = {
    "0.0": "482364ab9db69ed7ff4879a73cb10aab848442ad3adaf94b246ec0c87f5aad25",
    "0.25": "4c2ecc8f3a226486d363d5987a08f79bbbbf5606ab12de85a719c52cf35e6eac",
    "0.5": "a4af4c9dd3bdbf3985d2b8ff299b70eab413808a7a5595c83dd0cfb973607c85",
    "0.75": "9a05dabf58103c0f4495534a82f8737b576530f2750fc0f8e147c482c1b36a5e",
    "1.0": "12c5724e725b099d56238a461b06a286ffc03a2f551116decff5d1b1ac11ab96",
}
RECEIPT_SCHEMA = "UR-ART4K-REAL-CONTINUOUS-SOURCE-GLB-RECEIPT/1"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def validate_sample_receipt(qualified, current, last, requested_time):
    """ROM-free strict identity check before looking at candidate geometry."""
    if requested_time not in TIMES:
        raise ValueError("ride-grid sample not predeclared")
    if (not isinstance(qualified, dict)
            or qualified.get("schema") != RECEIPT_SCHEMA
            or qualified.get("rig_pose") != "ride"
            or type(qualified.get("rig_time")) not in (float, int)
            or not math.isfinite(qualified["rig_time"])
            or qualified["rig_time"] != float(requested_time)
            or qualified.get("model_source_sha256") != SOURCE_RIG_SHA
            or qualified.get("GLB_sha256") != PINNED_GRID_GLB_SHA[requested_time]
            or qualified.get("part_parent_count") != 5
            or qualified.get("part_material_mesh_count") != 16
            or qualified.get("source_owned_pivots_validated_against_real_GLB") is not True
            or qualified.get("authored_continuous_source_kinematics_recomputed") is not True
            or qualified.get("1994_source_cadence_or_pose_paired") is not False
            or qualified.get("1994_source_camera_or_rig_recovered") is not False
            or qualified.get("owner_character_likeness_approved") is not False
            or qualified.get("shipping_art_approved") is not False):
        raise ValueError("unverified actual continuous ride sample identity")
    if (not isinstance(current, dict) or not isinstance(last, dict)
            or last.get("status") != "succeeded"
            or last.get("current_output_usable") is not True
            or current.get("attempt_id") != last.get("attempt_id")
            or current.get("source_sha256") != SOURCE_RIG_SHA
            or last.get("source_sha256") != SOURCE_RIG_SHA
            or current.get("rig_pose") != "ride"
            or qualified.get("GLB_sha256") != current.get("glb_sha256")
            or qualified.get("GLB_sha256") != last.get("glb_sha256")):
        raise ValueError("inconsistent actual continuous ride exporter receipts")
    path = current.get("glb_path")
    if (type(path) is not str or
            not path.startswith("attempts/" + current["attempt_id"] + "/") or
            Path(path).is_absolute() or ".." in Path(path).parts or
            not path.endswith(".glb")):
        raise ValueError("invalid immutable GLB artifact path")
    return path


def original_edges(corpus, originals):
    """Only physical adjacent frames from the verified source registry."""
    frames_by_track = {}
    for frame in corpus["source_temporal_frame_observations"]:
        number, window = frame["guest_frame"], frame["window"]
        for player, representation in frame["representations"].items():
            if player not in ("p1", "p2"):
                raise ValueError("unexpected P1/P2 source identity")
            row = corpus["source_representations"][representation]
            if row["player"] != player:
                raise ValueError("wrong-player original source representation")
            sha = row["source_binary_mask_sha256"]
            if sha not in originals:
                raise ValueError("unverified original frame silhouette")
            frames_by_track.setdefault((window, player), []).append((number, sha))
    edges, total = [], 0
    for (window, player), rows in sorted(frames_by_track.items()):
        total += len(rows)
        for (number_a, sha_a), (number_b, sha_b) in zip(sorted(rows), sorted(rows)[1:]):
            if number_b <= number_a:
                raise ValueError("invalid original source chronology")
            if number_b != number_a + 1:
                continue  # Real missing guest frames are NOT motion edges.
            edges.append((window, player, number_a, number_b, sha_a, sha_b))
    if (len(edges) != 109 or total != 144 or
            len({window for window, _ in frames_by_track}) != 27):
        raise ValueError("actual ROM player/window/frame temporal census changed")
    return edges


def summarize_candidate(rows):
    if len(rows) != 109:
        raise ValueError("missing original motion edges")
    source = sum(x["source_changed_pixel_count"] for x in rows)
    pose = sum(x["model_pose_only_changed_pixel_count"] for x in rows)
    overlap = sum(x["source_changed_pixels_overlapping_pose_only_model_change"]
                  for x in rows)
    placed = sum(x["model_placed_changed_pixel_count"] for x in rows)
    placed_overlap = sum(x["source_changed_pixels_explained_by_placed_model"]
                         for x in rows)
    changed = sum(x["original_source_binary_silhouette_changed"] for x in rows)
    holds = len(rows) - changed
    if (source != 1631 or changed != 19 or holds != 90):
        raise ValueError("authentic original ROM moving/held pixel census changed")
    return {
        "actual_original_source_edges": 109,
        "source_changed_edges": 19, "source_held_edges": 90,
        "source_changed_pixels": source,
        "model_pose_only_changed_pixels": pose,
        "model_pose_only_matching_source_changed_pixels": overlap,
        "pose_only_source_changed_pixel_recall":
            round(overlap / source, 8),
        "pose_only_source_changed_pixel_precision":
            round(overlap / pose, 8) if pose else None,
        "placed_model_changed_pixels": placed,
        "placed_model_matching_source_changed_pixels": placed_overlap,
        "placed_source_changed_pixel_recall": round(placed_overlap / source, 8),
        "source_held_edges_with_spurious_pose_change":
            sum(not x["original_source_binary_silhouette_changed"]
                and x["model_pose_only_raster_changed"] for x in rows),
        "source_held_edges_with_spurious_placed_change":
            sum(not x["original_source_binary_silhouette_changed"]
                and x["model_placed_raster_changed"] for x in rows),
    }


def evaluate(corpus_path: Path, sample_roots: dict[str, Path],
             camera_path: Path) -> dict:
    if set(sample_roots) != set(TIMES):
        raise ValueError("exact five predeclared ride sample times required")
    corpus, verified = validate_corpus(corpus_path)
    originals = originals_from_corpus(corpus_path, corpus)
    if len(originals) != 35 or set(originals) != verified["all_masks"]:
        raise ValueError("wrong authentic original source silhouette census")
    edges = original_edges(corpus, originals)
    raw_camera = camera_path.read_bytes()
    if digest(raw_camera) != CAMERA_SHA:
        raise ValueError("original provisional 7:6 camera SHA mismatch")
    camera = json.loads(raw_camera)
    camera_config(camera)
    samples, projections = {}, {}
    for time in TIMES:
        root = sample_roots[time].resolve()
        root_continuous = root / "art4k-continuous"
        qpath = root / "art4k-continuous-qualified.json"
        qualified = json.loads(qpath.read_bytes())
        current = json.loads((root_continuous / "articulated_blockout_current.json").read_bytes())
        last = json.loads((root_continuous / "articulated_blockout_last_attempt.json").read_bytes())
        relative = validate_sample_receipt(qualified, current, last, time)
        glb = (root_continuous / relative).resolve()
        if not glb.is_relative_to(root_continuous.resolve()) or not glb.is_file():
            raise ValueError("source GLB escapes verified immutable artifact")
        verts, faces, sha, nodes = model_mesh(glb, qualified["GLB_sha256"])
        if sha != qualified["GLB_sha256"] or nodes < 21:
            raise ValueError("real five-parent 16-child GLB scene graph missing")
        projections[time] = render_mask(verts, faces, camera)
        samples[time] = {
            "rig_time": float(time), "source_model_sha256": SOURCE_RIG_SHA,
            "actual_glb_sha256": sha,
            "independently_checked_qualified_receipt_sha256": digest(qpath.read_bytes()),
            "authored_2026_motion_source": True,
            "original_1994_pose_frame_paired": False,
        }
    anchors = {sha: originals[sha]["source_alpha_anchor_x2_y2"]
               for sha in originals}
    placed = {(time, sha): translated_4x_source_mask(projections[time], anchor)
              for time in TIMES for sha, anchor in sorted(anchors.items())}
    pairs = list(zip(TIMES, TIMES[1:]))
    results = []
    for from_time, to_time in pairs:
        rows = []
        for window, player, frame_a, frame_b, sha_a, sha_b in edges:
            # The 2026 interval is kept identical across all authentic
            # source edges: no source-label/time fitting or oracle cherry-pick.
            source_a, source_b = originals[sha_a]["mask"], originals[sha_b]["mask"]
            stats = pixel_change(
                source_a, source_b,
                placed[from_time, sha_a], placed[to_time, sha_b],
                placed[to_time, sha_a],
            )
            rows.append(stats)
        results.append({
            "authored_2026_rig_time_from": float(from_time),
            "authored_2026_rig_time_to": float(to_time),
            "1994_guest_frame_to_2026_rig_time_paired": False,
            "source_pixel_statistics": summarize_candidate(rows),
        })
    first, last = projections[TIMES[0]], projections[TIMES[-1]]
    if first.shape != (256, 256) or last.shape != (256, 256):
        raise ValueError("invalid experimental render grid")
    import numpy as np
    close_pixel_difference = int(np.count_nonzero(first != last))
    return {
        "schema": SCHEMA,
        "source_original_rom_sha256": corpus["source_rom_sha256"],
        "source_original_corpus_sha256": verified["corpus_sha256"],
        "source_original_64px_pngs_independently_revalidated": True,
        "frozen_provisional_camera_sha256": CAMERA_SHA,
        "source_original_actual_frame_edges": len(edges),
        "source_original_unique_binary_silhouettes": len(originals),
        "source_model_sha256": SOURCE_RIG_SHA,
        "exact_ride_grid": list(TIMES),
        "real_verified_glb_samples": samples,
        "first_last_authored_cycle_4x_pixel_xor": close_pixel_difference,
        "all_transition_pairs_predeclared_without_frame_matching": True,
        "source_masks_previously_inspected_no_untouched_pose_holdout": True,
        "original_1994_camera_or_pose_or_cadence_recovered": False,
        "owner_likeness_approved": False, "shipping_art_approved": False,
        "uniform_2026_phase_transition_diagnostics": results,
        "baseline_historical_five_static_pose_only_recall": 0.02023299,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--camera", type=Path, required=True)
    parser.add_argument("--ride-sample", nargs=2, action="append",
                        metavar=("TIME", "ARTIFACT_DIRECTORY"), required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    samples = dict((time, Path(path)) for time, path in args.ride_sample)
    if len(args.ride_sample) != len(samples):
        parser.error("duplicate ride times")
    data = json.dumps(evaluate(args.corpus, samples, args.camera),
                      indent=2, sort_keys=True) + "\n"
    if args.out:
        publish_text_once(args.out, data)
    else:
        print(data, end="")


if __name__ == "__main__":
    main()
