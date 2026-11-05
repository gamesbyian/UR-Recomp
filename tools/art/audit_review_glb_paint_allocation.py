#!/usr/bin/env python3
"""Depth-visible 2026 GLB material reassignment, never a 1994 part identity.

Reuse the only verified authored five-parent/16-material GLB, fixed provisional
7:6 side camera and existing triangle z-buffer. Change *which already visible
source-authored material IDs count as blue*, without editing a model or picking
a physical camera based on closeness to the original 1994 image.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
from pathlib import Path
from zipfile import ZipFile

from tools.art.audit_original_racer_painted_frame_depth import (
    material_triangles, rasterize_depth,
)
from tools.art.evaluate_original_racer_chroma_guided_3d_hinge import CAMERA_SHA
from tools.art.no_replace_report import publish_text_once
from tools.art.render_racer_glb_projection import camera_config

SCHEMA = "UR-ART4K-2026-GLB-DEPTH-VISIBLE-PAINT-ALLOCATION/1"
MODEL_SHA = "d2a2beee85f63fa074f1fa7294c5cd7522f376f9d4b02354e97c0702dda3fa7f"
SOURCE_SCAD_SHA = "e99ef45bfe72f09ee97f51b7d7449c501aee2ca2d93596106ede4b56caddc984"
DRAFT_RIG_HEAD = "975920cafc87af120649cd6db2b81e740f4363f9"
MODEL_URL = f"assets/{DRAFT_RIG_HEAD}/upright-{MODEL_SHA[:16]}.glb"
MANIFEST = "real-model-site/model-review/manifest.json"
SOURCE_ROOT = "real-model-site/model-review/"
RADIUS = 7
# Mirror only the existing source-gated Pages paint-previews; no fitted palette.
BLUE = "fork_and_frame__material_0"
POLICIES = {
    "original": (),
    "area": ("rim_and_hub__material_1", "pedals__material_1"),
    "disc": ("rim_and_hub__material_2", "pedals__material_1"),
    "discPlus": ("rim_and_hub__material_2",
                 "pedals__material_0", "pedals__material_1"),
}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def evaluate_owner_labels(owners, ties, material_names, *, centre, radius=RADIUS):
    """Pure 64px material-mask counterfactual on **already** depth-visible owner.

    Tied different-material frontmost pixels are unknown, never optimistically
    reassigned. All variants share a single full-model depth test and axle.
    """
    names = list(material_names)
    if (len(names) != 16 or len(set(names)) != 16 or
            not all(isinstance(s, str) for s in names) or
            BLUE not in names or
            not set().union(*POLICIES.values()).issubset(set(names))):
        raise ValueError("wrong source-owned model material hierarchy")
    if (len(owners) != 4096 or len(ties) != 4096 or
            any(type(i) is not int or not -1 <= i < len(names) for i in owners) or
            any(type(v) is not bool for v in ties)):
        raise ValueError("expected exact 64px frontmost material/tie masks")
    if (type(radius) is not int or radius != 7 or
            not isinstance(centre, (list, tuple)) or len(centre) != 2 or
            any(type(v) not in (float, int) or not math.isfinite(v)
                or not 0 <= v < 64 for v in centre)):
        raise ValueError("invalid original-equivalent model axle-disc definition")
    cx, cy = centre
    result = {}
    for policy, additional in POLICIES.items():
        allowed = {names.index(BLUE)} | {names.index(x) for x in additional}
        selected = [i for i, (owner, tie) in enumerate(zip(owners, ties))
                    if not tie and owner in allowed]
        n = len(selected)
        if n < 12:
            raise ValueError("source-material paint disappeared from projected 2026 GLB")
        inside = sum((i % 64 - cx)**2 + (i // 64 - cy)**2 <= radius**2
                     for i in selected)
        below_top = sum(i // 64 >= cy - radius for i in selected)
        result[policy] = {
            "existing_visible_model_materials_counted_as_colour": [BLUE, *additional],
            "depth_visible_painted_pixels": n,
            "painted_pixels_inside_7px_wheel_disc": inside,
            "painted_fraction_inside_7px_wheel_disc": round(inside / n, 8),
            "painted_fraction_at_or_below_wheel_top": round(below_top / n, 8),
        }
    return result


def evaluate(glb_artifact: Path, camera_path: Path) -> dict:
    """Offline render of one exact source GLB. Never refit geometry to P1/P2."""
    try:
        import numpy as np
        import trimesh
    except ImportError as error:
        raise RuntimeError("read-only real GLB analysis requires NumPy and Trimesh") from error
    raw_camera = camera_path.read_bytes()
    if sha(raw_camera) != CAMERA_SHA:
        raise ValueError("frozen provisional 2026 7:6 camera changed")
    camera = json.loads(raw_camera)
    right, up, origin, scale, anchor = camera_config(camera)
    with ZipFile(glb_artifact) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("duplicate source model archive member")
        manifest = json.loads(archive.read(MANIFEST))
        if (manifest.get("schema") != "ur-racer-model-review/1"
                or manifest.get("source_commit") != DRAFT_RIG_HEAD
                or manifest.get("source_model_sha256") != SOURCE_SCAD_SHA
                or manifest.get("candidate_sha256") != MODEL_SHA
                or manifest.get("model_url") != MODEL_URL
                or manifest.get("likeness_approved") is not False
                or manifest.get("source_sprite_pose_registration") is not False):
            raise ValueError("unapproved source-authored model identity changed")
        target = SOURCE_ROOT + MODEL_URL
        if target not in names:
            raise ValueError("source-owned upright GLB not in real artifact")
        raw_glb = archive.read(target)
        if sha(raw_glb) != MODEL_SHA or raw_glb[:4] != b"glTF":
            raise ValueError("changed exact source-owned 2026 model GLB")
    scene = trimesh.load(io.BytesIO(raw_glb), file_type="glb",
                         force="scene", process=False)
    names = sorted(scene.graph.nodes_geometry)
    if (len(names) != 16 or set(names) != set([
            f"fork_and_frame__material_{i}" for i in range(4)] +
            [f"rim_and_hub__material_{i}" for i in range(5)] +
            [f"pedals__material_{i}" for i in range(3)] +
            [f"saddle__material_{i}" for i in range(2)] +
            [f"tire__material_{i}" for i in range(2)])):
        raise ValueError("wrong five-parent 16-material source model")
    axle = np.asarray(scene.graph.get("tire")[0])[:3, 3] - origin
    cx = float(axle @ right * scale * 6/7 + anchor[0]/2)
    cy = float(-axle @ up * scale + anchor[1]/2)
    if not all(math.isfinite(v) and 0 <= v < 64 for v in (cx,cy)):
        raise ValueError("2026 axle outside unchanged original 64px canvas")
    triangles, ids, blue_id = material_triangles(scene)
    if names[blue_id] != BLUE:
        raise ValueError("blue material z-buffer identity changed")
    view = {}
    for direction, label in ((1, "plus_world_y"), (-1, "minus_world_y")):
        owner, ties, hits = rasterize_depth(
            triangles, ids, camera, direction)
        if owner.shape != (64,64) or ties.shape != (64,64):
            raise ValueError("wrong 2026 source raster")
        per = evaluate_owner_labels(
            [int(i) for i in owner.flat],
            [bool(v) for v in ties.flat],
            names, centre=(cx,cy))
        view[label] = {
            "source_model_view_camera_direction_y": direction,
            "depth_visible_whole_model_pixels": int((owner >= 0).sum()),
            "frontmost_different_material_depth_ties": int(ties.sum()),
            "one_unchanged_source_axle_centre_logical_xy": [cx,cy],
            "source_paint_hypotheses": per,
        }
    ranges = {}
    for policy in POLICIES:
        values = [view[k]["source_paint_hypotheses"][policy]
                  ["painted_fraction_inside_7px_wheel_disc"] for k in view]
        ranges[policy] = [min(values), max(values)]
    return {
        "schema": SCHEMA,
        "verified_original_source_2026_Scad_sha256": SOURCE_SCAD_SHA,
        "verified_one_2026_GLb_sha256": MODEL_SHA,
        "provisional_2026_camera_sha256": CAMERA_SHA,
        "source_glb_exact_model_and_camera_unchanged": True,
        "predeclared_existing_Pages_paint_modes_only": list(POLICIES),
        "material_reassignment_is_model_only": True,
        "source_1994_camera_or_3d_part_identity_recovered": False,
        "original_P1_P2_pose_correspondence_verified": False,
        "owner_art_likeness_approved": False,
        "shipping_art_approved": False,
        "model_paint_inside_wheel_disc_fraction_by_two_camera_sides": ranges,
        "each_provisional_depth_side": view,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model-artifact-zip", required=True, type=Path)
    p.add_argument("--camera", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args()
    result = evaluate(args.model_artifact_zip, args.camera)
    publish_text_once(args.out, json.dumps(result, sort_keys=True, indent=2) + "\n")
    print("ART4K_VISIBLE_2026_GLB_PAINT_ALLOCATION", json.dumps(
        result["model_paint_inside_wheel_disc_fraction_by_two_camera_sides"],
        sort_keys=True))


if __name__ == "__main__":
    main()
