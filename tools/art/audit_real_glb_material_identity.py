#!/usr/bin/env python3
"""Hash-bind the current five-pose 16-material GLB colourway as research evidence.

This reads the EXISTING experimental Pages viewer's verified five GLBs. It
does not recolour, re-export, redraw or approve the canonical #2832 rig.
Original P1/P2 source palettes are a separate, independently verified 2D
dataset; numerical similarity is NOT source-authenticated 3D material mapping.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SCHEMA = "UR-RACER-EXPERIMENTAL-GLB-MATERIAL-IDENTITY/1"
POSES = ("upright", "pedal", "wheelie", "stunt", "bank")
EXPECTED_PART_MATERIALS = {
    "tire": 2, "rim_and_hub": 5, "fork_and_frame": 4,
    "pedals": 3, "saddle": 2,
}
MESH_NAMES = frozenset(
    f"{part}__material_{number}"
    for part, count in EXPECTED_PART_MATERIALS.items()
    for number in range(count)
)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def validate_rgb_materials(materials: dict) -> dict:
    """Validate all 16 named homogeneous vertex-colour material patches."""
    if not isinstance(materials, dict) or set(materials) != MESH_NAMES:
        raise ValueError("source rig must have exactly 16 published material mesh identities")
    normalized = {}
    for name in sorted(MESH_NAMES):
        value = materials[name]
        if (not isinstance(value, (list, tuple)) or len(value) != 4 or
                any(type(c) is not int or not 0 <= c <= 255 for c in value) or
                value[3] != 255):
            raise ValueError("part material must have one valid opaque RGBA colour")
        normalized[name] = [int(x) for x in value]
    return normalized


def read_glb_materials(path: Path, declared_sha: str) -> dict:
    """Check actual exported binary GLB bytes and material vertex colours."""
    if sha(path.read_bytes()) != declared_sha:
        raise ValueError("published source GLB SHA256 mismatch")
    try:
        import trimesh
    except ImportError as exc:
        raise RuntimeError("optional offline Trimesh dependency required for real GLB material audit") from exc
    scene = trimesh.load(path, force="scene", process=False)
    if not isinstance(scene, trimesh.Scene):
        raise ValueError("source GLB is not a scene")
    if set(scene.geometry) != MESH_NAMES:
        raise ValueError("wrong original five-parent, sixteen material mesh identities")
    colours = {}
    for name, mesh in scene.geometry.items():
        if (len(mesh.faces) < 1 or len(mesh.vertices) < 3 or
                mesh.visual.kind != "vertex"):
            raise ValueError("missing source material geometry or authored vertex colour")
        pixels = mesh.visual.vertex_colors
        if len(pixels) != len(mesh.vertices) or not len(pixels):
            raise ValueError("original GLB material vertex-colour count differs from geometry")
        first = [int(v) for v in pixels[0]]
        if any(tuple(int(c) for c in px) != tuple(first) for px in pixels[1:]):
            raise ValueError("per-mesh vertex colour differs, no homogeneous material proof")
        colours[name] = first
    return validate_rgb_materials(colours)


def reduce_five_materials(source: dict, *, manifest_sha: str,
                          sprite_rail_sha: str, camera_witness_sha: str | None = None) -> dict:
    """Require equal geometry material colourway for each provisional pose.

    An intentional future per-pose/per-player material change requires an
    explicit schema upgrade and separate source mapping, not silent drift.
    """
    if not isinstance(source, dict) or set(source) != set(POSES):
        raise ValueError("all five current authored pose colourways are required")
    if any(not isinstance(x, str) or len(x) != 64 or
           any(c not in "0123456789abcdef" for c in x)
           for x in (manifest_sha, sprite_rail_sha)):
        raise ValueError("original viewer manifest and sprite rail SHA identities required")
    palette = {}
    for pose in POSES:
        palette[pose] = validate_rgb_materials(source[pose])
    origin = palette["upright"]
    drift = {pose: [
        name for name in sorted(MESH_NAMES) if palette[pose][name] != origin[name]
    ] for pose in POSES}
    if any(drift.values()):
        raise ValueError("existing experimental GLB material colours drift between pose exports")
    raw = (json.dumps(origin, sort_keys=True, separators=(",", ":"))+"\n").encode()
    return {
        "schema": SCHEMA,
        "viewer_manifest_sha256": manifest_sha,
        "viewer_sprite_rail_sha256": sprite_rail_sha,
        "five_experimental_pose_material_sets_identical": True,
        "single_experimental_colourway_not_player_specific": True,
        "distinct_material_mesh_identities": len(origin),
        "common_pose_material_fingerprint_sha256": sha(raw),
        "fork_primary_material_rgb": origin["fork_and_frame__material_0"][:3],
        "fork_primary_material_rgb_hex": "#" + "".join(
            f"{v:02x}" for v in origin["fork_and_frame__material_0"][:3]),
        "authored_material_rgba_by_mesh": origin,
        "source_P1_P2_separate_colourways_validated_in_this_GLB": False,
        "original_1994_material_albedo_recovered": False,
        "source_original_sprite_to_GLb_pose_mapping_verified": False,
        "owner_likeness_approved": False,
        "shipping_art_approved": False,
    }


def inspect(site: Path) -> dict:
    """Authenticate the existing viewer's model+sprite publication contract."""
    if site.is_symlink():
        raise ValueError("source model-review site must not be a symlink")
    try:
        from tools.art.audit_real_viewer_glbs import inspect_viewer
    except ModuleNotFoundError:
        from audit_real_viewer_glbs import inspect_viewer
    site = site.resolve()
    before_model = (site / "manifest.json").read_bytes()
    before_sprite = (site / "sprites.json").read_bytes()
    model, _, glb_files = inspect_viewer(site)
    palette = {}
    for pose in POSES:
        palette[pose] = read_glb_materials(
            glb_files[pose], model["poses"][pose]["sha256"])
    # Never bind a palette from one manifest to an apparently new same-path
    # sprite rail/model revision during an unattended five-GLB export.
    if ((site / "manifest.json").read_bytes() != before_model or
            (site / "sprites.json").read_bytes() != before_sprite):
        raise ValueError("model-review source metadata changed during material audit")
    report = reduce_five_materials(
        palette, manifest_sha=sha(before_model), sprite_rail_sha=sha(before_sprite))
    report["model_authoring_source_commit"] = model["source_commit"]
    report["model_authoring_scad_sha256"] = model["source_model_sha256"]
    report["verified_glb_sha256_by_experimental_pose"] = {
        p: model["poses"][p]["sha256"] for p in POSES
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-review-dir", required=True, type=Path)
    parser.add_argument("--out", type=Path,
                        help="new immutable private JSON report, never overwrite")
    args = parser.parse_args()
    report = inspect(args.model_review_dir)
    raw = json.dumps(report, indent=2, sort_keys=True)+"\n"
    if args.out:
        if args.out.resolve().is_relative_to(args.model_review_dir.resolve()):
            parser.error("do not write research receipts into the website directory")
        try:
            from tools.art.no_replace_report import publish_text_once
        except ModuleNotFoundError:
            from no_replace_report import publish_text_once
        publish_text_once(args.out, raw)
    else:
        print(raw, end="")


if __name__ == "__main__":
    main()
