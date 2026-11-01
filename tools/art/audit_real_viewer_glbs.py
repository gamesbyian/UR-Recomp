#!/usr/bin/env python3
"""Audit the actual five-pose model-review Pages artifact against original P1.

This consumes the existing viewer's published, SHA-bound GLBs. It is a
research-only diagnostic: P1 frame 1205 has no verified correspondence to
the other four experimental rig poses, and camera calibration is provisional.
Never modify the viewer, its manifests, or original sprite artwork.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory

try:
    from tools.art.render_racer_glb_projection import (
        model_mesh, render_mask, render_to_png, camera_config,
    )
    from tools.art.score_racer_candidate import score_retained_original
    from tools.art.racer_source_pixels import decode_rgba_png
    from tools.art.build_racer_source_pixel_corpus import build as original_corpus
except ModuleNotFoundError:
    from render_racer_glb_projection import model_mesh, render_mask, render_to_png, camera_config
    from score_racer_candidate import score_retained_original
    from racer_source_pixels import decode_rgba_png
    from build_racer_source_pixel_corpus import build as original_corpus

POSES = ("upright", "pedal", "wheelie", "stunt", "bank")
SCHEMA = "UR-RACER-REAL-VIEWER-GLB-AUDIT/1"
CAMERA = Path(__file__).resolve().parents[2] / "analysis/data/racer-inverse-side-provisional-1205.json"
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_existing_path(root: Path, relative: str, suffix: str) -> Path:
    if not isinstance(relative, str) or "\\" in relative:
        raise ValueError("unsafe viewer manifest path")
    part = Path(relative)
    if (part.is_absolute() or part.suffix != suffix or
            any(x in ("", ".", "..") for x in part.parts)):
        raise ValueError("unsafe viewer manifest path")
    full = (root / part).resolve()
    if not full.is_relative_to(root.resolve()) or not full.is_file():
        raise ValueError("missing or escaped viewer artifact")
    return full


def inspect_viewer(site: Path) -> tuple[dict, dict, dict]:
    """Validate the viewer's **existing** model+reference publication contract."""
    if site.is_symlink() or not site.is_dir():
        raise ValueError("model-review directory must be ordinary directory")
    mpath = site / "manifest.json"
    spath = site / "sprites.json"
    model = json.loads(mpath.read_text(encoding="utf-8"))
    sprites = json.loads(spath.read_text(encoding="utf-8"))
    commit = model.get("source_commit")
    if (model.get("schema") != "ur-racer-model-review/1" or
            not isinstance(commit, str) or not HEX40.fullmatch(commit) or
            model.get("source_sprite_pose_registration") is not False or
            model.get("likeness_approved") is not False or
            not isinstance(model.get("source_model_sha256"), str) or
            not HEX64.fullmatch(model["source_model_sha256"])):
        raise ValueError("unverified or misleading viewer model manifest")
    if (sprites.get("schema") != "ur-racer-original-sprite-reference/1" or
            sprites.get("sprite_3d_pose_mapping_verified") is not False or
            not isinstance(sprites.get("frames"), list)):
        raise ValueError("unverified original-sprite rail")
    # The stage's self-declared image SHA isn't source authentication.
    # Independently check ALL 32 original frame identities against the
    # existing ROM-composed source corpus and its retained image hashes.
    corpus = original_corpus()
    if sprites.get("source_sha256") != corpus["historical_manifest_declared_rom_sha256"]:
        raise ValueError("viewer source ROM identity differs from original corpus")
    expected = {(x["player"], x["guest_frame"]): x
                for x in corpus["observations"]}
    if len(expected) != 32 or len(sprites["frames"]) != len(expected):
        raise ValueError("viewer original sprite rail must contain exactly 32 source observations")
    refs = {}
    for item in sprites["frames"]:
        key = (item.get("player"), item.get("guest_frame"))
        if key in refs or key not in expected:
            raise ValueError("duplicate or unrecognized viewer sprite source frame")
        authentic = expected[key]
        if (item.get("sha256") != authentic["png_file_sha256"] or
                item.get("representation_id") != authentic["representation_id"]):
            raise ValueError("viewer sprite is not original-source authenticated")
        path = safe_existing_path(site, item.get("image"), ".png")
        if digest(path) != authentic["png_file_sha256"]:
            raise ValueError("retained original sprite SHA mismatch")
        w, h, _, _ = decode_rgba_png(path)
        if (w, h) != (64, 64):
            raise ValueError("reference must be original 64x64 source raster")
        refs[key] = item
    if set(refs) != set(expected):
        raise ValueError("missing original sprite reference")
    reference = refs["p1", 1205]
    pose_files = {}
    if not isinstance(model.get("poses"), dict) or set(model["poses"]) != set(POSES):
        raise ValueError("viewer missing exact five experimental model poses")
    for pose in POSES:
        row = model["poses"][pose]
        if not isinstance(row, dict) or not isinstance(row.get("sha256"), str) or not HEX64.fullmatch(row["sha256"]):
            raise ValueError("missing exact GLB SHA")
        path = safe_existing_path(site, row.get("url"), ".glb")
        if digest(path) != row["sha256"]:
            raise ValueError("viewer GLB SHA mismatch for " + pose)
        pose_files[pose] = path
    if (model.get("candidate_sha256") != model["poses"]["upright"]["sha256"] or
            model.get("model_url") != model["poses"]["upright"]["url"]):
        raise ValueError("viewer default model is not verified upright pose")
    return model, reference, pose_files


def measure(site: Path, camera_path: Path = CAMERA) -> dict:
    model, source, poses = inspect_viewer(site)
    raw_camera = camera_path.read_bytes()
    camera = json.loads(raw_camera)
    camera_config(camera)
    if (camera.get("camera_calibration_status") != "provisional" or
            camera.get("source_witness", {}).get("guest_frame") != 1205 or
            camera.get("source_witness", {}).get("player") != "p1"):
        raise ValueError("only provisional, explicit P1 frame1205 camera is supported")
    results = {}
    with TemporaryDirectory(prefix="ur-real-viewer-model-audit-") as temp:
        for pose in POSES:
            vertices, faces, glb_sha, nodes = model_mesh(
                poses[pose], model["poses"][pose]["sha256"]
            )
            projected = render_mask(vertices, faces, camera)
            candidate = Path(temp) / (pose + ".png")
            candidate_sha = render_to_png(projected, candidate)
            scores = score_retained_original("p1", 1205, candidate, candidate_sha, 4)
            results[pose] = {
                "glb_sha256": glb_sha,
                "triangle_count": len(faces),
                "glb_scene_graph_node_count": nodes,
                "projection_png_sha256": candidate_sha,
                "binary_mask_iou_against_original_p1_1205": scores["mask_iou"],
                "boundary_chamfer_physical_px": scores["boundary_chamfer_mean_physical_px"],
                "mask_xor_pixels": scores["mask_xor_pixels"],
                "candidate_opaque_pixels": scores["candidate_opaque"],
                "candidate_bbox_xyxy": scores["candidate_bbox_xyxy"],
                "source_pose_mapping_verified": False,
            }
    return {
        "schema": SCHEMA,
        "existing_viewer_schema": model["schema"],
        "source_model_commit": model["source_commit"],
        "source_model_scad_sha256": model["source_model_sha256"],
        "source_sprite_frame": "p1:1205",
        "source_sprite_png_sha256": source["sha256"],
        "camera_manifest_sha256": hashlib.sha256(raw_camera).hexdigest(),
        "camera_status": "provisional",
        "original_1994_camera_recovered": False,
        "original_3d_pose_mapping_verified": False,
        "comparisons_other_than_upright_are_illustrative_unpaired": True,
        "five_GLBS_verified_against_viewer_manifest": True,
        "viewer_files_modified": False,
        "owner_likeness_approved": False,
        "shipping_art_approved": False,
        "poses": results,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model-review-dir", required=True, type=Path)
    ap.add_argument("--camera", default=CAMERA, type=Path)
    args = ap.parse_args()
    print(json.dumps(measure(args.model_review_dir, args.camera), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
