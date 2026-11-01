#!/usr/bin/env python3
"""Original-USA-ROM source raster *temporal* witness, not 3D animation recovery.

Reads only the already-authenticated source-corpus.json and its original PNGs.
Preserves actual registered guest frame order, exact frame gaps, repeated holds,
alpha shape/paint transitions, visible bottom-alpha anchor and 2D painted axis.
No guessed 1994 timeline cadence or original sprite-to-2026 GLB pose binding.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

try:
    from tools.art.freeze_racer_source_family_splits import validate_corpus
    from tools.art.racer_source_pixels import decode_rgba_png, alpha_metrics
    from tools.art.audit_original_racer_chroma_axes import painted_axis
    from tools.art.build_real_viewer_pose_matrix import original_lowest_alpha_anchor
    from tools.art.no_replace_report import publish_text_once
except ModuleNotFoundError:
    from freeze_racer_source_family_splits import validate_corpus
    from racer_source_pixels import decode_rgba_png, alpha_metrics
    from audit_original_racer_chroma_axes import painted_axis
    from build_real_viewer_pose_matrix import original_lowest_alpha_anchor
    from no_replace_report import publish_text_once

SCHEMA = "UR-RACER-ORIGINAL-ROM-TEMPORAL-2D-MOTION-WITNESS/1"
ROM_SHA = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
PLAYERS = ("p1", "p2")


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def classify_pair(before: dict, after: dict) -> str:
    if before["source_rgba_sha256"] == after["source_rgba_sha256"]:
        if before["source_binary_mask_sha256"] != after["source_binary_mask_sha256"]:
            raise ValueError("identical original RGB representation has a different alpha")
        return "same_rgba_hold"
    if before["source_binary_mask_sha256"] == after["source_binary_mask_sha256"]:
        return "colour_change_same_silhouette"
    return "source_silhouette_changed"


def frame_edges(frames: list[dict], measurements: dict[str, dict]) -> dict:
    """Preserve source gaps and only compare neighbours within one window.

    Adjacency in the *registered list* is not always a contiguous game frame.
    Never bridge a missing-player observation or infer a 1994 3D motion pivot.
    """
    if not frames or not isinstance(measurements, dict):
        raise ValueError("empty original motion witness")
    by_window = defaultdict(list)
    for frame in frames:
        window, number, reps = (frame.get("window"), frame.get("guest_frame"),
                                frame.get("representations"))
        if (not isinstance(window, str) or not window or type(number) is not int
                or not isinstance(reps, dict) or not reps or
                any(p not in PLAYERS or rid not in measurements
                    for p, rid in reps.items())):
            raise ValueError("invalid registered source motion frame")
        by_window[window].append(frame)
    results = []
    all_edges = []
    for window, rows in sorted(by_window.items()):
        if [r["guest_frame"] for r in rows] != sorted({
                r["guest_frame"] for r in rows}):
            raise ValueError("registered source frame order duplicated or nonmonotonic")
        observations = []
        for player in PLAYERS:
            last = None
            for f in rows:
                n = f["guest_frame"]
                rid = f["representations"].get(player)
                if rid is None:
                    last = None
                    continue
                curr = measurements[rid]
                if curr["player"] != player:
                    raise ValueError("wrong player source representation in temporal sequence")
                if last is not None:
                    number, prior_id, prior = last
                    kind = classify_pair(prior, curr)
                    step = n-number
                    if step <= 0:
                        raise ValueError("non-forward original frame chronology")
                    a = prior["visible_bottom_alpha_anchor_x2_y2"]
                    b = curr["visible_bottom_alpha_anchor_x2_y2"]
                    delta_angle = round(curr["source_painted_axis_angle_deg"]-
                                        prior["source_painted_axis_angle_deg"], 6)
                    obs = {
                        "window": window, "player": player,
                        "from_guest_frame": number, "to_guest_frame": n,
                        "guest_frame_step": step,
                        "actually_adjacent_guest_frames": step == 1,
                        "from_registered_representation_id": prior_id,
                        "to_registered_representation_id": rid,
                        "original_2d_source_transition_kind": kind,
                        "source_binary_mask_changed": kind == "source_silhouette_changed",
                        "visible_bottom_alpha_anchor_delta_x2_y2":
                            [b[0]-a[0], b[1]-a[1]],
                        "painted_axis_angle_delta_deg": delta_angle,
                        "painted_axis_changed": delta_angle != 0,
                        "true_1994_3d_joint_or_camera_transition_identified": False,
                    }
                    observations.append(obs)
                    all_edges.append(obs)
                last = (n, rid, curr)
        results.append({
            "window": window,
            "registered_guest_frame_count": len(rows),
            "registered_frame_first": rows[0]["guest_frame"],
            "registered_frame_last": rows[-1]["guest_frame"],
            "per_player": {
                p: {
                    "registered_player_frames": sum(p in f["representations"] for f in rows),
                    "observed_pairs": sum(e["player"] == p for e in observations),
                    "one_guest_frame_step_pairs": sum(e["player"] == p and
                                    e["actually_adjacent_guest_frames"] for e in observations),
                    "identical_rgba_holds": sum(e["player"] == p and
                                    e["original_2d_source_transition_kind"] == "same_rgba_hold"
                                    for e in observations),
                    "silhouette_transitions": sum(e["player"] == p and
                                    e["source_binary_mask_changed"] for e in observations),
                    "paint_only_transitions": sum(e["player"] == p and
                                    e["original_2d_source_transition_kind"] ==
                                        "colour_change_same_silhouette"
                                    for e in observations),
                } for p in PLAYERS,
            },
            "observed_original_source_transitions": observations,
        })
    if not all_edges:
        raise ValueError("source lacks any registered temporal edge")
    return {
        "registered_source_windows": len(results),
        "source_observed_player_frame_pairs": len(all_edges),
        "actually_consecutive_original_guest_frame_pairs":
            sum(e["actually_adjacent_guest_frames"] for e in all_edges),
        "identical_source_rgba_holds": sum(e["original_2d_source_transition_kind"] ==
                                          "same_rgba_hold" for e in all_edges),
        "source_binary_silhouette_changes": sum(e["source_binary_mask_changed"]
                                                 for e in all_edges),
        "source_paint_only_changes": sum(e["original_2d_source_transition_kind"] ==
                                        "colour_change_same_silhouette" for e in all_edges),
        "original_2d_painted_axis_changes": sum(e["painted_axis_changed"]
                                                for e in all_edges),
        "windows": results,
    }


def audit(corpus_path: Path) -> dict:
    corpus, validated = validate_corpus(corpus_path)
    if corpus["source_rom_sha256"] != ROM_SHA:
        raise ValueError("not the canonical original USA ROM source")
    root = corpus_path.resolve().parent
    measurements = {}
    for rid, info in sorted(corpus["source_representations"].items()):
        path = (root / info["local_file"]).resolve()
        if not path.is_relative_to(root):
            raise ValueError("source raster escaped authenticated corpus")
        w, h, rgba, png_sha = decode_rgba_png(path)
        alpha = alpha_metrics(rgba, w, h)
        if ((w,h) != (64,64) or png_sha != info["local_png_sha256"]
                or alpha["source_rgba_sha256"] != info["source_rgba_sha256"]
                or alpha["binary_mask_sha256"] != info["source_binary_mask_sha256"]
                or alpha["source_alpha_sha256"] != info["source_alpha_sha256"]):
            raise ValueError("original source pixel identity changed since corpus validation")
        mask = bytes(1 if a else 0 for a in rgba[3::4])
        measurements[rid] = {
            "player": info["player"],
            "source_rgba_sha256": info["source_rgba_sha256"],
            "source_binary_mask_sha256": info["source_binary_mask_sha256"],
            "visible_bottom_alpha_anchor_x2_y2":
                list(original_lowest_alpha_anchor(mask)),
            "source_painted_axis_angle_deg":
                painted_axis(rgba, info["player"])["signed_axis_angle_from_image_vertical_deg"],
        }
    witness = frame_edges(corpus["source_temporal_frame_observations"], measurements)
    if (witness["registered_source_windows"] != len(corpus["registered_source_windows"])
            or len(measurements) != corpus["unique_representations"]):
        raise ValueError("original source temporal census changed")
    return {
        "schema": SCHEMA,
        "source_rom_sha256": ROM_SHA,
        "source_corpus_sha256": digest(corpus_path.read_bytes()),
        "source_registry_sha256": corpus["source_registry_sha256"],
        "source_original_frame_observations":
            len(corpus["source_temporal_frame_observations"]),
        "distinct_original_binary_masks": len(validated["all_masks"]),
        "original_source_representation_count": len(measurements),
        "original_source_pixel_aspect": "7:6",
        "definition": "registered guest frame pairs per player within each source window; no cross-gap interpolation; bottom visible alpha midpoint x2/y2, existing strict P1 red/P2 blue painted-axis descriptor",
        "original_1994_3d_pose_or_camera_recovered": False,
        "original_frame_cadence_or_model_time_inferred": False,
        "original_frame_to_experimental_2026_GLb_poses_mapped": False,
        "owner_character_likeness_approved": False,
        "shipping_art_approved": False,
        "temporal_source_witness": witness,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corpus", required=True, type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    result = json.dumps(audit(args.corpus), sort_keys=True, indent=2) + "\n"
    if args.out:
        publish_text_once(args.out, result)
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
