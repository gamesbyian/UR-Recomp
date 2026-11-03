#!/usr/bin/env python3
"""Fixed-camera UNPAIRED 20 authentic Mesen 2D sprites versus five real 2026 GLBs.

Never identifies actual 1994 3D pose categories, reconstructs a lost mesh,
changes the gameplay renderer, tunes source-held-out silhouettes, or awards
owner likeness approval. Optional offline numpy/trimesh/Pillow only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
import zipfile

from tools.art.audit_original_mesen_sparse_pose_correspondence import (
    TICKS, SOURCE_ZIP_SHA, audit_source, validate_receipt,
)
from tools.art.audit_original_mesen_oam_descriptors import decode_oam
from tools.art.audit_original_mesen_obj_screen_pixels import decode_source_obj
from tools.art.audit_real_viewer_glbs import inspect_viewer, POSES
from tools.art.build_real_viewer_pose_matrix import original_lowest_alpha_anchor
from tools.art.compare_original_chroma_axes_to_glb_poses import CAMERA_SHA, POSE_GLB_SHA
from tools.art.evaluate_original_racer_wheel_holdout import translated_4x_source_mask
from tools.art.render_racer_glb_projection import camera_config, model_mesh, render_mask
from tools.art.no_replace_report import publish_text_once

SCHEMA = "UR-ART4K-LIVE-TWENTY-UNPAIRED-REAL-FIVE-GLB-SILHOUETTES/1"
ROLE_PATH = Path("analysis/data/racer-original-strict-tile-disjoint-holdout-20261103.json")
ROM_SHA = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verified_roles(summary: dict) -> tuple[set[str], set[str], set[str]]:
    if (not isinstance(summary, dict) or
            summary.get("schema") != "UR-ART4K-FROZEN-ORIGINAL-TILE-DISJOINT-HOLDOUT-SUMMARY/1" or
            summary.get("original_USA_ROM_sha256") != ROM_SHA or
            summary.get("source_4bpp_planes_in_fit") != 16 or
            summary.get("source_4bpp_planes_in_withheld") != 19):
        raise ValueError("not frozen original fit/withheld authority")
    groups = []
    for name, count in (("fit_original_index_plane_sha256", 16),
                        ("withheld_original_index_plane_sha256", 19),
                        ("strictly_tile_disjoint_withheld_index_plane_sha256", 6)):
        entries = summary.get(name)
        if (not isinstance(entries, list) or len(entries) != count or
                len(set(entries)) != count or
                any(type(s) is not str or len(s) != 64 or
                    any(c not in "0123456789abcdef" for c in s) for s in entries)):
            raise ValueError("malformed frozen source index-plane set")
        groups.append(set(entries))
    fit, withheld, strict = groups
    if fit & withheld or not strict <= withheld:
        raise ValueError("original source fit/withheld leakage")
    return fit, withheld, strict


def assigned_role(index_sha: str, roles: tuple[set[str], set[str], set[str]]) -> str:
    fit, withheld, strict = roles
    if index_sha in strict:
        return "strict_withheld"
    if index_sha in withheld:
        return "withheld"
    if index_sha in fit:
        return "fit"
    return "unclassified_live_source"


def mirror_source_horizontal(mask: bytes) -> bytes:
    """Reorient the real red upper viewport's source 2D alpha as displayed.

    The original held OAM plane SHA and source-fit/withheld identities remain
    based on the *unreflected* actual 1994 memory, never this screen transform.
    """
    if not isinstance(mask, bytes) or len(mask) != 4096 or any(v not in (0,1) for v in mask):
        raise ValueError("source sprite horizontal mirror requires binary 64x64")
    return b"".join(mask[row*64:(row+1)*64][::-1] for row in range(64))


def silhouette_iou(source: bytes, candidate: bytes) -> float:
    if (len(source) != 4096 or len(candidate) != 4096 or
            any(x not in (0, 1) for x in source) or
            any(x not in (0, 1) for x in candidate)):
        raise ValueError("strict original and candidate 64x64 binary silhouette required")
    intersect = sum(a & b for a, b in zip(source, candidate))
    union = sum(a | b for a, b in zip(source, candidate))
    if union == 0:
        raise ValueError("empty original/model silhouettes")
    return round(intersect / union, 8)


def summarize_rows(rows: list[dict], *,
                   scores_key: str = "unpaired_iou",
                   winner_key: str = "unpaired_iou_winner",
                   ties_key: str = "unpaired_iou_tied_candidates") -> dict:
    if (not isinstance(rows, list) or
            [(r.get("tick"), r.get("racer")) for r in rows] !=
            [(tick, racer) for tick in TICKS for racer in ("blue", "red")]):
        raise ValueError("incomplete original two-racer sparse frame census")
    counts = Counter()
    totals = {pose: 0.0 for pose in POSES}
    for row in rows:
        scores = row.get(scores_key)
        if (not isinstance(scores, dict) or set(scores) != set(POSES) or
                any(type(x) not in (float, int) or not math.isfinite(x) or
                    not 0 <= x <= 1 for x in scores.values())):
            raise ValueError("invalid real GLB silhouette scores")
        top = max(scores.values())
        highest = [p for p in POSES if scores[p] == top]
        ranked = highest[0] if len(highest) == 1 else None
        tied = highest if len(highest) > 1 else []
        if (row.get(winner_key) != ranked or
                row.get(ties_key) != tied):
            raise ValueError("wrong unpaired pose rank or tie classification")
        if row.get("frozen_source_role") not in (
                "fit", "withheld", "strict_withheld", "unclassified_live_source"):
            raise ValueError("invalid precommitted source role")
        counts[ranked if ranked is not None else "ambiguous_exact_tie"] += 1
        for p in POSES:
            totals[p] += scores[p]
    return {
        "original_2D_observations": 40,
        "unpaired_iou_winner_counts": {p: counts[p] for p in POSES},
        "ambiguous_exact_iou_tie_count": counts["ambiguous_exact_tie"],
        "mean_iou_per_real_GLb_pose": {p: round(totals[p] / 40, 8) for p in POSES},
        "authentic_source_1994_pose_labels_verified": False,
    }


def compute(source_zip: Path, receipt_file: Path, site: Path,
            camera_path: Path, role_path: Path = ROLE_PATH) -> dict:
    receipt = json.loads(receipt_file.read_text())
    validate_receipt(receipt)
    source_check = audit_source(source_zip, receipt)
    if (source_check["actual_source_zip_sha256"] != SOURCE_ZIP_SHA or
            source_check["source_pixel_accounting"] !=
            {"opaque": 12937, "exact": 12416, "red_plus_13": 521} or
            source_check["unexplained_original_source_pixels"] != 0):
        raise ValueError("authentic original source audit did not pass")
    role_bytes = role_path.read_bytes()
    roles = verified_roles(json.loads(role_bytes))
    camera_bytes = camera_path.read_bytes()
    if sha(camera_bytes) != CAMERA_SHA:
        raise ValueError("provisional original camera SHA changed")
    camera = json.loads(camera_bytes)
    camera_config(camera)
    if (camera.get("camera_calibration_status") != "provisional" or
            camera.get("source_anchor_x2_y2") != [67, 76] or
            camera.get("logical_pixels_per_model_unit_vertical") != 9.5):
        raise ValueError("not the frozen source provisional camera")
    model, _, paths = inspect_viewer(site)
    projected = {}
    for pose in POSES:
        expected = model["poses"][pose]["sha256"]
        if expected != POSE_GLB_SHA[pose]:
            raise ValueError("substituted experimental GLB")
        vertices, faces, actual_sha, _ = model_mesh(paths[pose], expected)
        if actual_sha != expected:
            raise ValueError("source GLB changed")
        projected[pose] = render_mask(vertices, faces, camera)
    rows = []
    with zipfile.ZipFile(source_zip) as archive:
        for item in receipt["samples"]:
            tick = item["tick"]
            oam = decode_oam(archive.read(f"frame-{tick:06d}-oam.bin"))
            vram = archive.read(f"frame-{tick:06d}-vram.bin")
            cgram = archive.read(f"frame-{tick:06d}-cgram.bin")
            for racer, slot in (("blue", 96), ("red", 97)):
                obj = decode_source_obj(oam[slot], vram, cgram,
                    oam_mode=4, obj_base=0x6000, second_table_offset=0x1000)
                if obj["size"] != 64 or obj["opaque_count"] != item[racer]["opaque"]:
                    raise ValueError("authentic original OBJ content changed")
                anchor = original_lowest_alpha_anchor(obj["alpha_mask"])
                # Source-held and completed-screen orientations answer
                # distinct questions. The actual original red upper raster
                # appears reflected relative to held slot 97 OAM hflip=false.
                # Do NOT optimize mirror choice by maximizing model IoU.
                screen_mask = (mirror_source_horizontal(obj["alpha_mask"])
                               if racer == "red" else obj["alpha_mask"])
                screen_anchor = original_lowest_alpha_anchor(screen_mask)
                scores, screen_scores = {}, {}
                for pose in POSES:
                    model_mask = translated_4x_source_mask(projected[pose], anchor)
                    screen_model_mask = translated_4x_source_mask(projected[pose], screen_anchor)
                    scores[pose] = silhouette_iou(obj["alpha_mask"], model_mask)
                    screen_scores[pose] = silhouette_iou(screen_mask, screen_model_mask)
                def winners(values):
                    top = max(values.values())
                    highest = [p for p in POSES if values[p] == top]
                    return (highest[0] if len(highest) == 1 else None,
                            highest if len(highest) > 1 else [])
                winner, tied = winners(scores)
                screen_winner, screen_tied = winners(screen_scores)
                if racer == "blue" and (scores != screen_scores or anchor != screen_anchor):
                    raise ValueError("unreflected blue original display source moved")
                index_sha = sha(obj["plane"])
                rows.append({
                    "tick": tick, "racer": racer, "original_OAM_slot": slot,
                    "original_index_plane_sha256": index_sha,
                    "original_alpha_sha256": sha(obj["alpha_mask"]),
                    "original_screen_xy": item[racer]["screen_xy"],
                    "original_screen_mirror_from_held": racer == "red",
                    "original_lowest_alpha_anchor_x2_y2": list(anchor),
                    "completed_screen_facing_lowest_alpha_anchor_x2_y2": list(screen_anchor),
                    "frozen_source_role": assigned_role(index_sha, roles),
                    "unpaired_iou": scores, "unpaired_iou_winner": winner,
                    "unpaired_iou_tied_candidates": tied,
                    "screen_oriented_unpaired_iou": screen_scores,
                    "screen_oriented_iou_winner": screen_winner,
                    "screen_oriented_iou_tied_candidates": screen_tied,
                    "original_1994_pose_identity_known": False,
                })
    return {
        "schema": SCHEMA, "original_source_zip_sha256": SOURCE_ZIP_SHA,
        "original_source_screen_40_registration_audit_passed": True,
        "original_source_ticks": list(TICKS),
        "old_frozen_fit_withheld_summary_sha256": sha(role_bytes),
        "real_2026_GLb_sha256": {p: POSE_GLB_SHA[p] for p in POSES},
        "provisional_camera_sha256": CAMERA_SHA,
        "common_camera_all_40_sources": True,
        "per_source_camera_auto_alignment": False,
        "authentic_1994_3D_model_or_camera_recovered": False,
        "source_to_experimental_GLb_pose_mapping_verified": False,
        "owner_likeness_approved": False, "shipping_art_approved": False,
        "summary": summarize_rows(rows),
        "screen_oriented_summary": summarize_rows(
            rows, scores_key="screen_oriented_unpaired_iou",
            winner_key="screen_oriented_iou_winner",
            ties_key="screen_oriented_iou_tied_candidates"),
        "source_held_orientation_and_original_completed_screen_orientation_distinguished": True,
        "rows": rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-zip", required=True, type=Path)
    parser.add_argument("--original-receipt", type=Path, default=Path(
        "analysis/data/racer-original-mesen-twenty-live-2d-screen-registrations-20261103.json"))
    parser.add_argument("--model-review-dir", required=True, type=Path)
    parser.add_argument("--camera", type=Path, default=Path(
        "analysis/data/racer-inverse-side-provisional-1205.json"))
    parser.add_argument("--role-summary", type=Path, default=ROLE_PATH)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    result = compute(args.original_zip, args.original_receipt,
                     args.model_review_dir, args.camera, args.role_summary)
    publish_text_once(args.out, json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "original_source_2D_count": 40,
        "held_source_unpaired_winners": result["summary"]["unpaired_iou_winner_counts"],
        "completed_screen_oriented_unpaired_winners":
            result["screen_oriented_summary"]["unpaired_iou_winner_counts"],
        "original_source_3D_accepted": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
