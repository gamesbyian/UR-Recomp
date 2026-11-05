#!/usr/bin/env python3
"""Evaluate FROZEN wheel-x 1.00/1.10 hypotheses on novel original ROM masks.

This is an unpaired diagnostic, not source-1994 camera, pose or art approval.
Original sprites are checked against the canonical-ROM corpus receipt; the
real 2026 GLB is identified by its historical SHA-256; neither is modified.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import io
import json
from pathlib import Path

try:
    from tools.art.freeze_racer_source_family_splits import validate_corpus
    from tools.art.racer_source_pixels import decode_rgba_png, alpha_metrics
    from tools.art.render_racer_glb_projection import camera_config, render_mask
    from tools.art.ablate_original_racer_wheel_width import ablated_world_mesh
    from tools.art.build_real_viewer_pose_matrix import original_lowest_alpha_anchor
    from tools.art.score_racer_candidate import score
    from tools.art.no_replace_report import publish_text_once
except ModuleNotFoundError:
    from freeze_racer_source_family_splits import validate_corpus
    from racer_source_pixels import decode_rgba_png, alpha_metrics
    from render_racer_glb_projection import camera_config, render_mask
    from ablate_original_racer_wheel_width import ablated_world_mesh
    from build_real_viewer_pose_matrix import original_lowest_alpha_anchor
    from score_racer_candidate import score
    from no_replace_report import publish_text_once

SCHEMA = "UR-RACER-GENUINE-DIFFERENT-FAMILY-WHEEL-HYPOTHESIS/1"
FIRST = "first-1205-1220"
# The previously scored real 2026 *experimental* GLB from run 41259476190.
MODEL_SHA = "efdc8425f252b4a0218d140d087c6cc923689589e0cf74cc6333d722182595f5"
ROM_SHA = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
FACTORS = (1.0, 1.1)  # Frozen on first-family evidence BEFORE this test.
BASE_ANCHOR = (67, 76)
FIRST_BASELINE_MEAN = {1.0: 0.57255469, 1.1: 0.59883507}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def split_family_components(per_window: dict[str, set[str]],
                            first: str = FIRST) -> dict:
    """Leakage-free holdout: any shared binary silhouette connects windows.

    Deterministic, exact binary-shape hash identity. A different temporal
    window containing the original training sprite is not independent.
    """
    if first not in per_window or len(per_window) < 2:
        raise ValueError("first-family plus additional original windows required")
    all_names = sorted(per_window)
    if any(not isinstance(name, str) or not name or
           not isinstance(per_window[name], set) or not per_window[name] or
           any(not isinstance(h, str) or len(h) != 64 for h in per_window[name])
           for name in all_names):
        raise ValueError("malformed authenticated source window shapes")
    parent = {name: name for name in all_names}

    def root(n):
        while parent[n] != n:
            parent[n] = parent[parent[n]]
            n = parent[n]
        return n

    by_mask = defaultdict(list)
    for name in all_names:
        for mask in per_window[name]:
            by_mask[mask].append(name)
    for windows in by_mask.values():
        lead = windows[0]
        for name in windows[1:]:
            parent[root(name)] = root(lead)
    groups = defaultdict(list)
    for name in all_names:
        groups[root(name)].append(name)
    fit = next(set(members) for members in groups.values() if first in members)
    withheld = [sorted(members) for members in groups.values()
                if first not in members]
    withheld.sort()
    fit_masks = set().union(*(per_window[n] for n in fit))
    withheld_masks = set().union(*(per_window[n] for g in withheld for n in g)) if withheld else set()
    if fit_masks & withheld_masks:
        raise ValueError("original binary silhouette leaked from training to holdout")
    return {
        "fit_connected_windows": sorted(fit),
        "withheld_connected_window_components": withheld,
        "fit_binary_shas": sorted(fit_masks),
        "withheld_binary_shas": sorted(withheld_masks),
        "independent_holdout_mask_count": len(withheld_masks),
    }


def translated_4x_source_mask(mask4, source_anchor):
    """Shift candidate by a *source-derived* half-logical-pixel anchor.

    Prior renderer already records this anchor in 1/2 logical-pixel units.
    Thus 4x shift = 2 * (source_anchor_x2 - base_x2). Unlike an integer
    logical-pixel shift, half-pixel parity is retained without rounding.
    """
    import numpy as np
    if (getattr(mask4, "shape", None) != (256, 256) or
            any(type(x) is not int for x in source_anchor) or
            len(source_anchor) != 2):
        raise ValueError("invalid source registration or 4x mask")
    dx, dy = (2 * (source_anchor[0] - BASE_ANCHOR[0]),
              2 * (source_anchor[1] - BASE_ANCHOR[1]))
    yy, xx = np.nonzero(mask4)
    if not len(xx):
        raise ValueError("empty model silhouette")
    if (min(xx)+dx < 0 or max(xx)+dx >= 256 or
            min(yy)+dy < 0 or max(yy)+dy >= 256):
        raise ValueError("source-registered model silhouette would clip")
    moved = np.zeros_like(mask4)
    moved[yy+dy, xx+dx] = 1
    result = bytes(int(v) for v in moved[2::4, 2::4].reshape(-1))
    if not any(result):
        raise ValueError("source-registered model silhouette empty at 64px")
    return result


def originals_from_corpus(path: Path, receipt: dict) -> dict:
    """Re-read every original sprite after the corpus's independent audit."""
    if receipt.get("source_rom_sha256") != ROM_SHA or (
            receipt.get("source_rom_verified_and_used_for_composition") is not True):
        raise ValueError("original ROM source receipt not authentic")
    groups = {}
    for identity, info in sorted(receipt["source_representations"].items()):
        path_ref = path.parent / info["local_file"]
        w, h, rgba, file_sha = decode_rgba_png(path_ref)
        measured = alpha_metrics(rgba, w, h)
        if ((w, h) != (64, 64) or
                file_sha != info["local_png_sha256"] or
                measured["source_rgba_sha256"] != info["source_rgba_sha256"] or
                measured["binary_mask_sha256"] != info["source_binary_mask_sha256"]):
            raise ValueError("original source pixels changed after corpus preflight")
        mask = bytes(1 if a else 0 for a in rgba[3::4])
        key = digest(mask)
        if key != info["source_binary_mask_sha256"]:
            raise ValueError("source binary mask SHA changed")
        anchor = original_lowest_alpha_anchor(mask)
        current = groups.setdefault(key, {"mask": mask, "source_alpha_anchor_x2_y2": anchor,
                                          "source_representations": [], "players": set()})
        if current["mask"] != mask or current["source_alpha_anchor_x2_y2"] != anchor:
            raise ValueError("same original binary shape has inconsistent anchor")
        current["source_representations"].append(identity)
        current["players"].add(info["player"])
    return groups


def evaluate(corpus_path: Path, glb_path: Path, camera_path: Path) -> dict:
    import trimesh
    receipt, verified = validate_corpus(corpus_path)
    split = split_family_components(verified["per_window_masks"])
    if split["independent_holdout_mask_count"] == 0:
        raise ValueError("additional source windows contain no independent silhouette holdout")
    groups = originals_from_corpus(corpus_path, receipt)
    if set(groups) != verified["all_masks"]:
        raise ValueError("original corpus grouping differs from authenticated windows")
    camera_bytes = camera_path.read_bytes()
    camera = json.loads(camera_bytes)
    camera_config(camera)
    if (camera.get("camera_calibration_status") != "provisional"
            or camera.get("source_anchor_x2_y2") != list(BASE_ANCHOR)
            or camera.get("logical_pixels_per_model_unit_vertical") != 9.5
            or camera.get("right_world") != [1, 0, 0]
            or camera.get("up_world") != [0, 0, 1]):
        raise ValueError("camera changed from frozen first-family experiment")
    glb_bytes = glb_path.read_bytes()
    if digest(glb_bytes) != MODEL_SHA:
        raise ValueError("not the single verified original 2026 experimental GLB")
    scene = trimesh.load(file_obj=io.BytesIO(glb_bytes),
                         file_type="glb", force="scene", process=False)
    if not isinstance(scene, trimesh.Scene):
        raise ValueError("canonical 2026 rig must remain an articulated GLB scene")
    projected = {}
    for factor in FACTORS:
        vertices, faces = ablated_world_mesh(scene, float(factor))
        projected[factor] = render_mask(vertices, faces, camera)
    candidate = {}
    for mask_sha in sorted(groups):
        group = groups[mask_sha]
        scores = {}
        for factor in FACTORS:
            mask = translated_4x_source_mask(
                projected[factor], group["source_alpha_anchor_x2_y2"])
            stats = score(group["mask"], mask)
            scores[str(factor)] = {
                "mask_iou": stats["mask_iou"],
                "boundary_chamfer_mean_physical_px":
                    stats["boundary_chamfer_mean_physical_px"],
                "mask_xor_pixels": stats["mask_xor_pixels"],
            }
        candidate[mask_sha] = {
            "source_binary_mask_sha256": mask_sha,
            "players": sorted(group["players"]),
            "registered_source_alpha_anchor_x2_y2":
                list(group["source_alpha_anchor_x2_y2"]),
            "unpaired_candidate_scores": scores,
            "delta_iou_width_1_10_minus_1_00":
                round(scores["1.1"]["mask_iou"]-scores["1.0"]["mask_iou"], 8),
        }

    def summary(hashes):
        values = [candidate[h] for h in hashes]
        return {
            "independent_binary_mask_count": len(values),
            "mean_iou_width_1_00": round(sum(v["unpaired_candidate_scores"]["1.0"]["mask_iou"] for v in values)/len(values), 8),
            "mean_iou_width_1_10": round(sum(v["unpaired_candidate_scores"]["1.1"]["mask_iou"] for v in values)/len(values), 8),
            "mean_delta_iou": round(sum(v["delta_iou_width_1_10_minus_1_00"] for v in values)/len(values), 8),
            "shape_wins_for_1_10": sum(v["delta_iou_width_1_10_minus_1_00"] > 0 for v in values),
            "shape_losses_for_1_10": sum(v["delta_iou_width_1_10_minus_1_00"] < 0 for v in values),
            "shape_ties": sum(v["delta_iou_width_1_10_minus_1_00"] == 0 for v in values),
        }

    first_masks = sorted(verified["per_window_masks"][FIRST])
    baseline = summary(first_masks)
    if any(abs(baseline["mean_iou_width_"+label] - expected) > 1e-8
           for label, expected in (("1_00", FIRST_BASELINE_MEAN[1.0]),
                                   ("1_10", FIRST_BASELINE_MEAN[1.1]))):
        raise ValueError("historical first-family score controls no longer reproduce")
    holdout = split["withheld_binary_shas"]
    return {
        "schema": SCHEMA, "source_corpus_sha256": digest(corpus_path.read_bytes()),
        "source_rom_sha256": ROM_SHA,
        "source_original_composition_verified": True,
        "original_source_frame_observations": len(receipt["source_temporal_frame_observations"]),
        "original_independent_binary_silhouettes": len(groups),
        "model_glb_sha256": MODEL_SHA,
        "provisional_camera_sha256": digest(camera_bytes),
        "camera_7_6_pixel_aspect": True,
        "locked_hypotheses_world_x_tire_and_rim_only": list(FACTORS),
        "fit_family": FIRST, "leakage_free_window_split": split,
        "historical_first_family_reproduction": baseline,
        "genuinely_new_binary_mask_holdout": summary(holdout),
        "holdout_sources_are_not_proven_novel_3d_views": True,
        "old_original_3d_camera_recovered": False,
        "source_frame_to_experimental_3d_pose_mapped": False,
        "experimental_3d_upright_pose_is_unpaired_to_original_1994_holdout": True,
        "rig_geometry_modified_or_published": False,
        "owner_character_likeness_approved": False,
        "shipping_art_approved": False,
        "per_original_binary_mask": candidate,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--glb", type=Path, required=True)
    parser.add_argument("--camera", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    payload = json.dumps(evaluate(args.corpus, args.glb, args.camera),
                         indent=2, sort_keys=True) + "\n"
    if args.out:
        publish_text_once(args.out, payload)
    else:
        print(payload, end="")


if __name__ == "__main__":
    main()
