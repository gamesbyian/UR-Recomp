#!/usr/bin/env python3
"""Optional axle-centred fork/saddle pitch of the existing unapproved ART-4K GLB.

Purely mechanical 2026-rig hypothesis. Not original-game 3D reconstruction,
camera calibration, animation timing, source pose pairing or shipping art.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import math
import os
from pathlib import Path
import tempfile

SOURCE_GLB_SHA256 = "efdc8425f252b4a0218d140d087c6cc923689589e0cf74cc6333d722182595f5"
PARTS = ("tire", "rim_and_hub", "pedals", "fork_and_frame", "saddle")
MOVING = ("fork_and_frame", "saddle")
STATIC = ("tire", "rim_and_hub", "pedals")
SCHEMA = "UR-ART4K-EXPERIMENTAL-HUB-PIVOT-FRAME-PITCH/1"


def rotation_y(degrees):
    """Pure-Python axle-local rotation (optional 3D dependencies not needed)."""
    if type(degrees) not in (float, int) or not math.isfinite(degrees) or not -8 <= degrees <= 8:
        raise ValueError("experimental frame pitch must be finite within +/-8 degrees")
    a = math.radians(degrees)
    c, s = math.cos(a), math.sin(a)
    return ((c, 0., s, 0.), (0., 1., 0., 0.),
            (-s, 0., c, 0.), (0., 0., 0., 1.))


def pitch_scene(scene, degrees):
    """Modify exactly two existing parent nodes around the real GLB axle pivot."""
    import numpy as np
    import trimesh
    R = np.asarray(rotation_y(degrees), dtype=float)
    if not isinstance(scene, trimesh.Scene) or scene.graph.base_frame != "world":
        raise ValueError("unexpected GLB scene origin")
    if not set(PARTS).issubset(set(scene.graph.nodes)) or len(scene.graph.nodes_geometry) != 16:
        raise ValueError("missing original five parents and sixteen child meshes")
    if any(scene.graph.transforms.parents.get(p) != "world" for p in PARTS):
        raise ValueError("a source part is no longer a top-level world node")
    node_names, geometry_names = set(scene.graph.nodes), set(scene.geometry)
    original = {p: np.asarray(scene.graph.get(p)[0], dtype=float).copy() for p in PARTS}
    if any(T.shape != (4, 4) or not np.isfinite(T).all() for T in original.values()):
        raise ValueError("invalid original part transform")
    axle = original["tire"]
    if any(not np.allclose(original[p], axle, rtol=0, atol=1e-9) for p in STATIC):
        raise ValueError("source tire/rim/crank pivots do not coincide")
    basis = axle[:3, :3]
    if (not np.allclose(basis.T @ basis, np.eye(3), atol=1e-7, rtol=0)
            or not np.isclose(np.linalg.det(basis), 1., atol=1e-7, rtol=0)):
        raise ValueError("source axle transform is not rigid")
    K = axle @ R @ np.linalg.inv(axle)
    for p in MOVING:
        scene.graph.update(frame_to=p, frame_from="world", matrix=K @ original[p])
    if node_names != set(scene.graph.nodes) or geometry_names != set(scene.geometry):
        raise ValueError("scene graph/geometry changed during parent-only adjustment")
    for p in PARTS:
        expected = K @ original[p] if p in MOVING else original[p]
        observed = np.asarray(scene.graph.get(p)[0], dtype=float)
        if not np.allclose(observed, expected, rtol=0, atol=1e-9):
            raise ValueError("stationary wheel or active frame parent invariant violated")
    return {
        "experimental_frame_pitch_degrees": float(degrees),
        "source_wheel_axle_pivot_world_xyz": [float(v) for v in axle[:3, 3]],
        "moving_parent_parts": list(MOVING),
        "unmodified_parent_parts": list(STATIC),
        "five_original_part_parents_preserved": True,
        "sixteen_original_child_material_meshes_preserved": True,
        "original_1994_joint_pose_or_animation_recovered": False,
    }


def build(source: bytes, degrees: float):
    """Prepare immutable derived real GLB bytes and independently checked receipt."""
    import numpy as np
    import trimesh
    if hashlib.sha256(source).hexdigest() != SOURCE_GLB_SHA256 or source[:4] != b"glTF":
        raise ValueError("only the SHA-pinned unapproved 2026 upright GLB is supported")
    scene = trimesh.load(file_obj=io.BytesIO(source), file_type="glb",
                         force="scene", process=False)
    all_nodes, materials = set(scene.graph.nodes), set(scene.graph.nodes_geometry)
    record = pitch_scene(scene, degrees)
    derived = scene.export(file_type="glb")
    if not isinstance(derived, bytes) or derived[:4] != b"glTF":
        raise ValueError("failed to export actual derived GLB")
    checked = trimesh.load(file_obj=io.BytesIO(derived), file_type="glb",
                           force="scene", process=False)
    if (set(checked.graph.nodes) != all_nodes or
            set(checked.graph.nodes_geometry) != materials or
            len(checked.graph.nodes_geometry) != 16):
        raise ValueError("derived GLB lost original material or part nodes")
    for child in materials:
        _, old_key = scene.graph.get(child)
        _, new_key = checked.graph.get(child)
        old_mesh, new_mesh = scene.geometry[old_key], checked.geometry[new_key]
        if (old_mesh.vertices.shape != new_mesh.vertices.shape
                or old_mesh.faces.shape != new_mesh.faces.shape
                or not np.array_equal(old_mesh.faces, new_mesh.faces)
                or not np.allclose(old_mesh.vertices, new_mesh.vertices, atol=1e-6, rtol=0)):
            raise ValueError("derived GLB changes original untransformed mesh geometry")
    record.update({
        "schema": SCHEMA,
        "historical_unapproved_source_glb_sha256": SOURCE_GLB_SHA256,
        "derived_glb_sha256": hashlib.sha256(derived).hexdigest(),
        "derived_glb_bytes": len(derived),
        "2026_rig_existing_geometry_only": True,
        "original_rom_source_mask_matched_to_this_pitch": False,
        "original_game_frame_chronology_verified": False,
        "original_game_camera_or_contact_recovered": False,
        "owner_likeness_approved": False,
        "shipping_art_approved": False,
    })
    return derived, record


def process(glb: Path, pitch: float, output: Path, receipt: Path):
    """Publish complete immutable GLB first; publish valid receipt LAST."""
    if len({glb.resolve(), output.resolve(), receipt.resolve()}) != 3:
        raise ValueError("input/GLB/receipt paths must differ")
    if output.exists() or receipt.exists():
        raise FileExistsError("refuse to replace an earlier candidate or receipt")
    derived, record = build(glb.read_bytes(), pitch)
    output.parent.mkdir(parents=True, exist_ok=True)
    receipt.parent.mkdir(parents=True, exist_ok=True)
    # Each staged file lives on the destination's own filesystem. Hard links
    # are exclusive: a concurrent writer cannot be silently overwritten.
    with tempfile.TemporaryDirectory(prefix=".art4k-hinge-glb-", dir=output.parent) as left, \
            tempfile.TemporaryDirectory(prefix=".art4k-hinge-receipt-", dir=receipt.parent) as right:
        staged = Path(left) / "complete.glb"
        staged_receipt = Path(right) / "complete.json"
        staged.write_bytes(derived)
        staged_receipt.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        linked_output = False
        try:
            os.link(staged, output)
            linked_output = True
            os.link(staged_receipt, receipt)
        except BaseException:
            if linked_output:
                output.unlink()
            raise
    return record


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-glb", type=Path, required=True)
    p.add_argument("--frame-pitch-degrees", type=float, required=True)
    p.add_argument("--out-glb", type=Path, required=True)
    p.add_argument("--receipt", type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(process(a.source_glb, a.frame_pitch_degrees, a.out_glb, a.receipt), indent=2))


if __name__ == "__main__":
    main()
