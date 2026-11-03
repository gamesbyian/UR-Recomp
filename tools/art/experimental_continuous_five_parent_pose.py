#!/usr/bin/env python3
"""Experimental, topology-stable continuous parent pose of the ONE 2026 GLB rig.

One source-authored upright model, not five different meshes. Drive rotates
tire/rim/pedals together at the original axle; frame pitch rotates fork/saddle
together at the same axle. Neither parameter is a recovered 1994 animation.
The part-local meshes and original 16 material identities never change.
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

from tools.art.experimental_direct_drive_phase import (
    SOURCE_GLBS, SOURCE_PHASE, PARTS, CHILD_COUNTS, rotation as drive_rotation,
)
from tools.art.experimental_frame_hinge import rotation_y as frame_rotation

SOURCE_GLB_SHA256 = SOURCE_GLBS["upright"]
SOURCE_CRANK_REFERENCE_DEG = SOURCE_PHASE["upright"]
SCHEMA = "UR-ART4K-EXPERIMENTAL-SINGLE-GLB-CONTINUOUS-COUPLED-PARENT-POSE/1"
DRIVE = ("tire", "rim_and_hub", "pedals")
FRAME = ("fork_and_frame", "saddle")


def parameters(wheel_crank_delta_deg: float, frame_pitch_deg: float) -> tuple[float, float]:
    """No arbitrary per-source GLB shape or camera settings are permitted."""
    if (type(wheel_crank_delta_deg) not in (int, float) or
            type(frame_pitch_deg) not in (int, float) or
            not math.isfinite(wheel_crank_delta_deg) or
            not math.isfinite(frame_pitch_deg) or
            not -360 <= wheel_crank_delta_deg <= 360 or
            not -45 <= frame_pitch_deg <= 45):
        raise ValueError("finite wheel/crank +/-360 and frame pitch +/-45 required")
    return float(wheel_crank_delta_deg), float(frame_pitch_deg)


def apply_scene(scene, wheel_crank_delta_deg: float, frame_pitch_deg: float) -> dict:
    """Move only the five original part parents, never local material meshes.

    The existing upright GLB's wheel/rim/pedal axle parents must coincide.
    Its fork/saddle keep their initial relative pose through the shared frame
    transform. Drive/crank and frame pitch are independent two-DOF controls.
    """
    import numpy as np
    import trimesh

    phase, pitch = parameters(wheel_crank_delta_deg, frame_pitch_deg)
    if (not isinstance(scene, trimesh.Scene) or
            scene.graph.base_frame != "world" or
            not set(PARTS).issubset(scene.graph.nodes) or
            len(scene.graph.nodes_geometry) != 16):
        raise ValueError("requires the canonical original five-parent 16-mesh rig")
    root = scene.graph.base_frame
    all_nodes = set(scene.graph.nodes)
    all_geom = set(scene.geometry)
    if any(scene.graph.transforms.parents.get(p) != root for p in PARTS):
        raise ValueError("source part parents have changed")
    for p, n in CHILD_COUNTS.items():
        child_nodes = [
            x for x in scene.graph.nodes_geometry
            if scene.graph.transforms.parents.get(x) == p
        ]
        if len(child_nodes) != n:
            raise ValueError("source material part identities changed")

    before = {p: np.array(scene.graph.get(p)[0], dtype=float, copy=True) for p in PARTS}
    if any(T.shape != (4, 4) or not np.isfinite(T).all() for T in before.values()):
        raise ValueError("nonfinite source parent matrix")
    axle = before["tire"]
    if any(not np.allclose(before[p], axle, atol=1e-8, rtol=0) for p in DRIVE):
        raise ValueError("wheel, rim and pedal parents do not share source axle")
    axis = axle[:3, :3]
    if (not np.allclose(axis.T @ axis, np.eye(3), atol=1e-7, rtol=0) or
            not np.isclose(np.linalg.det(axis), 1, atol=1e-7, rtol=0) or
            not np.allclose(axle[3, :], [0, 0, 0, 1], atol=1e-8, rtol=0)):
        raise ValueError("source wheel axle transform is not rigid")
    source_frame_saddle = np.linalg.inv(before["fork_and_frame"]) @ before["saddle"]

    drive = axle @ np.asarray(drive_rotation(phase), dtype=float) @ np.linalg.inv(axle)
    frame = axle @ np.asarray(frame_rotation(pitch), dtype=float) @ np.linalg.inv(axle)
    for p in PARTS:
        transform = drive if p in DRIVE else frame
        scene.graph.update(frame_to=p, frame_from=root, matrix=transform @ before[p])
    if all_nodes != set(scene.graph.nodes) or all_geom != set(scene.geometry):
        raise ValueError("source node and material identity changed")

    after = {p: np.asarray(scene.graph.get(p)[0], dtype=float) for p in PARTS}
    for p in PARTS:
        expected = (drive if p in DRIVE else frame) @ before[p]
        if not np.allclose(after[p], expected, atol=1e-8, rtol=0):
            raise ValueError("incorrect coupled parent transform")
    if (any(not np.allclose(after[p], after["tire"], atol=1e-8, rtol=0)
            for p in DRIVE) or
            not np.allclose(np.linalg.inv(after["fork_and_frame"]) @ after["saddle"],
                            source_frame_saddle, atol=1e-8, rtol=0)):
        raise ValueError("direct drive or rigid frame coupling broken")

    return {
        "schema": SCHEMA,
        "source_original_rig_part_parents": list(PARTS),
        "source_original_material_children": 16,
        "source_axle_world_xyz": list(map(float, axle[:3, 3])),
        "wheel_crank_delta_deg_from_upright_2026": phase,
        "source_authored_upright_crank_phase_deg": SOURCE_CRANK_REFERENCE_DEG,
        "frame_pitch_deg_from_upright_2026": pitch,
        "rotated_drive_parts": list(DRIVE),
        "rotated_upper_frame_parts": list(FRAME),
        "original_local_meshes_changed": False,
        "1994_source_camera_or_animation_mapping_recovered": False,
        "original_3d_geometry_recovered": False,
        "owner_likeness_approved": False,
        "shipping_art_approved": False,
    }


def build(source: bytes, wheel_crank_delta_deg: float, frame_pitch_deg: float):
    """Export an optional derived GLB with preserved source-local material meshes."""
    import numpy as np
    import trimesh

    if (type(source) is not bytes or
            hashlib.sha256(source).hexdigest() != SOURCE_GLB_SHA256 or
            source[:4] != b"glTF"):
        raise ValueError("source must be the SHA-pinned existing 2026 upright GLB")
    scene = trimesh.load(io.BytesIO(source), file_type="glb",
                         force="scene", process=False)
    geom = {
        key: (np.array(mesh.vertices, copy=True), np.array(mesh.faces, copy=True),
              np.array(mesh.vertex_normals, copy=True),
              np.array(mesh.visual.vertex_colors, copy=True))
        for key, mesh in scene.geometry.items()
    }
    node_names = set(scene.graph.nodes)
    mesh_nodes = set(scene.graph.nodes_geometry)
    parents = dict(scene.graph.transforms.parents)
    result = apply_scene(scene, wheel_crank_delta_deg, frame_pitch_deg)
    part_transforms = {p: np.array(scene.graph.get(p)[0], copy=True) for p in PARTS}
    output = scene.export(file_type="glb")
    if type(output) is not bytes or output[:4] != b"glTF":
        raise ValueError("derived continuous GLB serialization failed")
    actual = trimesh.load(io.BytesIO(output), file_type="glb",
                          force="scene", process=False)
    if (set(actual.graph.nodes) != node_names or
            set(actual.graph.nodes_geometry) != mesh_nodes or
            set(actual.geometry) != set(geom) or
            dict(actual.graph.transforms.parents) != parents):
        raise ValueError("derived GLB changed part hierarchy or material nodes")
    for key, (vertices, faces, normals, colors) in geom.items():
        mesh = actual.geometry[key]
        if (not np.array_equal(mesh.faces, faces) or
                not np.allclose(mesh.vertices, vertices, atol=1e-6, rtol=0) or
                not np.allclose(mesh.vertex_normals, normals, atol=1e-6, rtol=0) or
                not np.array_equal(mesh.visual.vertex_colors, colors)):
            raise ValueError("derived GLB changed source local geometry or colours")
    for p in PARTS:
        if not np.allclose(actual.graph.get(p)[0], part_transforms[p],
                           atol=1e-6, rtol=0):
            raise ValueError("GLB roundtrip corrupted coupled parent transform")
    result.update({
        "source_2026_upright_glb_sha256": SOURCE_GLB_SHA256,
        "derived_glb_sha256": hashlib.sha256(output).hexdigest(),
        "derived_glb_bytes": len(output),
        "source_part_meshes_and_materials_preserved_after_real_roundtrip": True,
        "experimentally_authored_2026_pose_not_1994_ground_truth": True,
    })
    return output, result


def process(source: Path, wheel_crank_delta_deg: float, frame_pitch_deg: float,
            output: Path, receipt: Path) -> dict:
    if (len({source.resolve(), output.resolve(), receipt.resolve()}) != 3 or
            any(p.exists() or p.is_symlink() for p in (output, receipt))):
        raise ValueError("input, GLB and receipt paths must differ and outputs be new")
    binary, record = build(source.read_bytes(), wheel_crank_delta_deg, frame_pitch_deg)
    output.parent.mkdir(parents=True, exist_ok=True)
    receipt.parent.mkdir(parents=True, exist_ok=True)
    # Atomic no-replace publishing per destination filesystem, receipt LAST.
    with tempfile.TemporaryDirectory(prefix=".art4k-continuous-glb-", dir=output.parent) as x, \
         tempfile.TemporaryDirectory(prefix=".art4k-continuous-receipt-", dir=receipt.parent) as y:
        glb_stage = Path(x) / "candidate.glb"
        json_stage = Path(y) / "candidate.json"
        glb_stage.write_bytes(binary)
        json_stage.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n",
                              encoding="utf-8")
        os.link(glb_stage, output)
        # On failure retain an orphan rather than risk deleting foreign files.
        os.link(json_stage, receipt)
    return record


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-glb", type=Path, required=True)
    p.add_argument("--wheel-crank-delta-deg", type=float, required=True)
    p.add_argument("--frame-pitch-deg", type=float, required=True)
    p.add_argument("--out-glb", type=Path, required=True)
    p.add_argument("--receipt", type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(process(a.source_glb, a.wheel_crank_delta_deg,
                             a.frame_pitch_deg, a.out_glb, a.receipt),
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
