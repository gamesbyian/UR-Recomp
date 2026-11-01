#!/usr/bin/env python3
"""Independently verify one real source-authored continuous ART-4K GLB export.

Accepts the one canonical five-part OpenSCAD study and its existing immutable
exporter receipt contract. Does not invent source-1994 pose correspondences,
animation cadence, character likeness, or a second rig.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile

try:
    from tools.art.continuous_pose_recipe import continuous_pose_recipe
    from tools.art.glb_roundtrip_guard import validate_glb_roundtrip
    from tools.art.export_articulated_unicycle import PLAYER_PALETTES
    from tools.art.scad_materials import materials_for_part
except ModuleNotFoundError:
    from continuous_pose_recipe import continuous_pose_recipe
    from glb_roundtrip_guard import validate_glb_roundtrip
    from export_articulated_unicycle import PLAYER_PALETTES
    from scad_materials import materials_for_part

SCHEMA = "UR-ART4K-REAL-CONTINUOUS-SOURCE-GLB-RECEIPT/1"
POSES = ("ride", "stunt_cycle")
PART_MATERIAL_COUNTS = {
    "tire": 2, "rim_and_hub": 5, "fork_and_frame": 4,
    "pedals": 3, "saddle": 2,
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def publish_receipt_no_replace(path: Path, payload: dict) -> None:
    """Publish complete evidence atomically without replacing foreign files.

    A prior exists() check followed by write_text() follows dangling symlinks
    and can overwrite an unrelated target. Same-directory hard-link creation
    is atomic and refuses existing files, directories and symlinks.
    """
    content = json.dumps(payload, sort_keys=True, indent=2) + "\n"
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    staged = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        os.link(staged, path)
    finally:
        staged.unlink(missing_ok=True)


def _verified_child(parent: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or relative.startswith("/"):
        raise ValueError("invalid immutable artifact relative path")
    root = parent.resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError("artifact path missing or escapes bounded export")
    return path


def _same_number(actual, expected, label: str) -> None:
    if (type(actual) not in (int, float) or not math.isfinite(actual)
            or not math.isclose(actual, expected, rel_tol=0, abs_tol=1e-7)):
        raise ValueError("actual source-continuous control diverges: " + label)


def validate_one(source_path: Path, out_dir: Path, pose: str, time: float,
                 player_palette: str = "source") -> dict:
    if pose not in POSES or type(time) not in (int, float) or not math.isfinite(time) or not 0 <= time <= 1:
        raise ValueError("unsupported original authoring pose/time sample")
    if not isinstance(player_palette, str) or player_palette not in PLAYER_PALETTES:
        raise ValueError("unsupported source-owned player palette")
    source_bytes = source_path.read_bytes()
    source = source_bytes.decode("utf-8")
    expected_pedal, expected_lean, expected_matrix, expected_meta = (
        continuous_pose_recipe(source, pose, time))
    root = out_dir.resolve()
    last = json.loads((root / "articulated_blockout_last_attempt.json").read_text())
    pointer = json.loads((root / "articulated_blockout_current.json").read_text())
    if (last.get("schema") != "ur-art4k-export-attempt/1"
            or last.get("status") != "succeeded"
            or last.get("current_output_usable") is not True
            or pointer.get("schema") != "ur-art4k-export-current/1"
            or pointer.get("attempt_id") != last.get("attempt_id")
            or pointer.get("source_sha256") != sha256(source_bytes)
            or last.get("source_sha256") != sha256(source_bytes)
            or pointer.get("rig_pose") != pose):
        raise ValueError("stale, failed, or source-divergent continuous GLB export pointer")
    glb = _verified_child(root, pointer.get("glb_path"))
    receipt_file = _verified_child(root, pointer.get("receipt_path"))
    if (glb.parent != receipt_file.parent or
            glb.parent != (root / "attempts" / last["attempt_id"]).resolve()):
        raise ValueError("GLB and receipt do not belong to same immutable attempt")
    glb_bytes = glb.read_bytes()
    receipt_bytes = receipt_file.read_bytes()
    if (sha256(glb_bytes) != pointer.get("glb_sha256")
            or sha256(glb_bytes) != last.get("glb_sha256")
            or sha256(receipt_bytes) != pointer.get("receipt_sha256")):
        raise ValueError("published GLB or receipt bytes changed")
    receipt = json.loads(receipt_bytes)
    if (receipt.get("schema") != "ur-art4k-articulated-blockout/1"
            or receipt.get("attempt_id") != last["attempt_id"]
            or receipt.get("source_sha256") != sha256(source_bytes)
            or receipt.get("rig_pose") != pose
            or receipt.get("glb_sha256") != sha256(glb_bytes)
            or receipt.get("glb_size") != len(glb_bytes)
            or receipt.get("pose_source_registered_to_original_game") is not False
            or receipt.get("original_character_likeness_approved") is not False
            or receipt.get("shipping_art_approved") is not False
            or receipt.get("animation_cadence_source_registered") is not False):
        raise ValueError("source model receipt claims unverified 1994 art or wrong export")
    # The exporter now supports provisional P1/P2 material selection. An
    # immutable GLB's colours can be internally consistent while its palette
    # identity is forged in the mutable current pointer or the receipt.
    # Bind both to the caller's expected versioned palette before loading GLB.
    _, rgba = PLAYER_PALETTES[player_palette]
    expected_palette = {
        "schema_version": 1,
        "id": player_palette,
        "override_rgba": list(rgba) if rgba else None,
        "original_raster_color_registered": False,
        "owner_material_approved": False,
    }
    if (pointer.get("player_palette") != expected_palette
            or receipt.get("player_palette") != expected_palette):
        raise ValueError("source-bound player palette receipt/pointer mismatch")
    controls = receipt.get("pose_controls")
    meta = receipt.get("continuous_pose")
    if not isinstance(controls, dict) or not isinstance(meta, dict):
        raise ValueError("missing authored continuous GLB controls")
    _same_number(controls.get("pedal_phase_degrees"), expected_pedal, "pedal")
    _same_number(controls.get("saddle_lean_degrees"), expected_lean, "saddle")
    for key, value in expected_meta.items():
        if type(value) is bool:
            if meta.get(key) is not value:
                raise ValueError("false authored continuous-pose formula claim")
        else:
            _same_number(meta.get(key), value, key)
    if set(meta) != set(expected_meta):
        raise ValueError("unrecognized additional continuous-pose claims")
    transform = receipt.get("source_pose_transform")
    if not isinstance(transform, list) or len(transform) != 4:
        raise ValueError("missing source-authored transform")
    for i, row in enumerate(transform):
        if not isinstance(row, list) or len(row) != 4:
            raise ValueError("malformed source transform row")
        for j, v in enumerate(row):
            _same_number(v, expected_matrix[i][j], f"transform[{i}][{j}]")
    components = receipt.get("components")
    if not isinstance(components, list) or len(components) != 5:
        raise ValueError("source model must preserve five parent parts")
    if {x.get("name") for x in components} != set(PART_MATERIAL_COUNTS):
        raise ValueError("source-owned parent part identity changed")
    palette_expression, _ = PLAYER_PALETTES[player_palette]
    for row in components:
        if (row.get("material_count") != PART_MATERIAL_COUNTS[row["name"]]
                or len(row.get("materials", [])) != row["material_count"]
                or row.get("editable_node") is not True):
            raise ValueError("source-owned material geometry identity changed")
        # GLB roundtrip checks the bytes against the receipt. Independently
        # recompute the receipt's material colours from the actual SCAD source
        # and selected palette, so a self-consistent forged GLB/receipt pair
        # cannot claim the wrong P1/P2 colours.
        expected_colors = [
            list(color) for color in materials_for_part(
                source, row["name"], rig_color_override=palette_expression)
        ]
        if [material.get("rgba") for material in row["materials"]] != expected_colors:
            raise ValueError("source-owned player palette material RGBA mismatch")
    independently_checked = validate_glb_roundtrip(glb, receipt)
    if receipt.get("glb_roundtrip") != independently_checked:
        raise ValueError("stored GLB round-trip acceptance differs from actual source geometry")
    return {
        "schema": SCHEMA,
        "model_source_sha256": sha256(source_bytes),
        "rig_pose": pose,
        "rig_time": time,
        "player_palette": expected_palette,
        "immutable_attempt_id": last["attempt_id"],
        "GLB_sha256": sha256(glb_bytes),
        "GLB_receipt_sha256": sha256(receipt_bytes),
        "part_parent_count": len(components),
        "part_material_mesh_count": sum(x["material_count"] for x in components),
        "authored_continuous_source_kinematics_recomputed": True,
        "source_owned_pivots_validated_against_real_GLB": True,
        "1994_source_cadence_or_pose_paired": False,
        "1994_source_camera_or_rig_recovered": False,
        "owner_character_likeness_approved": False,
        "shipping_art_approved": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--pose", choices=POSES, required=True)
    parser.add_argument("--time", type=float, required=True)
    parser.add_argument("--player-palette", choices=tuple(PLAYER_PALETTES),
                        default="source",
                        help="expected versioned provisional palette; not original colour approval")
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    payload = validate_one(args.source, args.output_dir, args.pose, args.time,
                           player_palette=args.player_palette)
    publish_receipt_no_replace(args.receipt, payload)
    print(json.dumps(payload, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
