#!/usr/bin/env python3
"""Fixed-pivot whole-character 2026 GLB rotation, after existing direct-drive controls.

One canonical unapproved five-parent GLB, unchanged 16 material meshes.
Original ROM orientation indices are NOT calibrated source 3D physical angles.
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

from tools.art.experimental_continuous_five_parent_pose import (
    PARTS, SOURCE_GLB_SHA256, apply_scene as apply_axle_controls,
    parameters as axle_parameters,
)

SCHEMA = "UR-ART4K-EXPERIMENTAL-SINGLE-GLB-FIXED-ROOT-ORBIT/1"
# The 2026 OpenSCAD authoring source is pinned. Its valid GLB exports are\n# byte-variable across actual GHA runs, so authorize current inputs through\n# the existing successful exporter receipt and exact-file SHA verifier.\n
MODES = ("wheel_axle", "historical_midbody")
MIDBODY_OFFSET_ABOVE_AXLE_WORLD_Z = 0.8
# Original 2026 OpenSCAD shared_rig puts the axle at Z=1.00;
# its existing continuous_rig spin pivots at Z=1.80.
HISTORICAL_SCAD_SHA = "e99ef45bfe72f09ee97f51b7d7449c501aee2ca2d93596106ede4b56caddc984"


def root_matrix(original_orientation_index: int, pivot: tuple[float, float, float]):
    """Rigid source-world Y rotation about a fixed world point, row-major."""
    if type(original_orientation_index) is not int or not 0 <= original_orientation_index < 64:
        raise ValueError("original 0..63 source orientation index required")
    if (not isinstance(pivot, (tuple, list)) or len(pivot) != 3 or
            any(type(x) not in (int, float) or not math.isfinite(x) for x in pivot)):
        raise ValueError("finite fixed original 2026 world pivot required")
    x, y, z = map(float, pivot)
    theta = 2 * math.pi * original_orientation_index / 64
    c, s = math.cos(theta), math.sin(theta)
    # Explicit T(pivot) @ Ry(theta) @ T(-pivot).
    return ((c, 0., s, x - c*x - s*z),
            (0., 1., 0., 0.),
            (-s, 0., c, z + s*x - c*z),
            (0., 0., 0., 1.))


def apply_root_scene(scene, index: int, pivot_mode: str,
                     wheel_crank_delta_deg: float = 0,
                     frame_pitch_deg: float = 0) -> dict:
    """Absolute pose: existing two axle controls plus one shared global orbit.

    Reuses the original axle controller's exact-rest cache and fail-closed
    external-edit validation. Updates its last-world-pose receipt only after
    confirming the combined transform, enabling repeated A -> B -> neutral.
    """
    import numpy as np
    import trimesh
    if pivot_mode not in MODES:
        raise ValueError("only two pre-authored 2026 root pivot choices allowed")
    root_matrix(index, (0., 0., 0.))  # fail before changing a scene
    axle_parameters(wheel_crank_delta_deg, frame_pitch_deg)
    if not isinstance(scene, trimesh.Scene):
        raise ValueError("actual source GLB scene graph required")
    nodes_before = set(scene.graph.nodes)
    mesh_nodes = set(scene.graph.nodes_geometry)
    geometry_names = set(scene.geometry)
    record = apply_axle_controls(scene, wheel_crank_delta_deg, frame_pitch_deg)
    root = scene.graph.base_frame
    parent = scene.graph.transforms.parents.get("tire")
    if (parent is None or any(scene.graph.transforms.parents.get(p) != parent for p in PARTS)
            or (parent != root and scene.graph.transforms.parents.get(parent) != root)):
        raise ValueError("the original five GLB part parents no longer share a root")
    parent_world = (np.asarray(scene.graph.get(parent)[0], dtype=float)
                    if parent != root else np.eye(4))
    if (parent_world.shape != (4, 4) or not np.isfinite(parent_world).all()
            or not np.allclose(parent_world[:3,:3].T @ parent_world[:3,:3],
                               np.eye(3), atol=1e-7, rtol=0)):
        raise ValueError("invalid original GLB parent transform")
    before = {p: np.array(scene.graph.get(p)[0], dtype=float, copy=True)
              for p in PARTS}
    axle_xyz = np.asarray(record["source_axle_world_xyz"], dtype=float)
    if axle_xyz.shape != (3,) or not np.isfinite(axle_xyz).all():
        raise ValueError("source-authored 2026 model axle was not proven")
    pivot = np.array(axle_xyz, copy=True)
    if pivot_mode == "historical_midbody":
        pivot[2] += MIDBODY_OFFSET_ABOVE_AXLE_WORLD_Z
    K = np.asarray(root_matrix(index, tuple(float(x) for x in pivot)), dtype=float)
    inv_parent = np.linalg.inv(parent_world)
    expected = {p: K @ before[p] for p in PARTS}
    for p in PARTS:
        scene.graph.update(frame_to=p, frame_from=parent,
                           matrix=inv_parent @ expected[p])
    actual = {p: np.asarray(scene.graph.get(p)[0], dtype=float)
              for p in PARTS}
    if (nodes_before != set(scene.graph.nodes) or
            mesh_nodes != set(scene.graph.nodes_geometry) or
            geometry_names != set(scene.geometry) or
            any(not np.allclose(actual[p], expected[p], atol=1e-8, rtol=0)
                for p in PARTS)):
        raise ValueError("whole-rig rotation modified source geometry or hierarchy")
    # Existing axle operator knows its immutable original rest pose. Keep
    # the last receipt coherent with this additive shared-root transform.
    # An unexpected outside node edit still fails its next call.
    scene._ur_art4k_continuous_last = {
        p: np.array(actual[p], copy=True) for p in PARTS
    }
    return {
        "schema": SCHEMA,
        "source_original_ROM_orientation_index": index,
        "original_orientation_to_2026_angle_IS_UNCALIBRATED_hypothesis": True,
        "assumed_2d_index_fraction_of_turn": index / 64,
        "historical_2026_pivot_mode": pivot_mode,
        "historical_2026_pivot_world_xyz": pivot.tolist(),
        "historical_2026_openSCAD_sha256": HISTORICAL_SCAD_SHA,
        "input_GLb_digest_bound_during_authenticated_build": False,
        "wheel_crank_delta_degrees_2026_hypothesis": float(wheel_crank_delta_deg),
        "frame_pitch_degrees_2026_hypothesis": float(frame_pitch_deg),
        "one_common_root_rotation_all_five_parts": True,
        "sixteen_original_material_meshes_unchanged": True,
        "original_1994_3D_angle_camera_or_joint_pivot_recovered": False,
        "owner_likeness_approved": False,
        "shipping_art_approved": False,
    }


def build(source: bytes, source_orientation_index: int, pivot_mode: str,
          wheel_crank_delta_deg: float, frame_pitch_deg: float, *,
          verified_export_root: Path | None = None):
    import numpy as np
    import trimesh
    actual_sha = hashlib.sha256(source).hexdigest() if type(source) is bytes else ""
    if type(source) is not bytes or source[:4] != b"glTF":
        raise ValueError("source must be an authenticated actual 2026 upright GLB")
    if verified_export_root is None:
        if actual_sha != SOURCE_GLB_SHA256:
            raise ValueError("source must be the exact SHA-pinned real 2026 upright GLB")
        input_source_class = "historical_immutable_viewer_artifact"
    else:
        # The OpenSCAD-to-Trimesh exporter emits variable GLB bytes across
        # builds of the same source. The established Pages staging verifier
        # checks original source SCAD SHA, attempt/current pointer integrity,
        # actual GLB bytes, exact receipt and unapproved-art flags.
        from runpy import run_path
        validate = run_path(str(Path(__file__).resolve().parent /
                                "model-review/stage_pages.py"))["validate"]
        ptr, outputs = validate(verified_export_root, "upright")
        if (ptr["source_sha256"] != HISTORICAL_SCAD_SHA or
                ptr["glb_sha256"] != actual_sha or
                outputs["glb"].read_bytes() != source):
            raise ValueError("current source GLB failed verified export receipt")
        input_source_class = "current_successful_source_scad_export_receipt"
    scene = trimesh.load(io.BytesIO(source), file_type="glb", force="scene", process=False)
    old_nodes, old_geom_nodes = set(scene.graph.nodes), set(scene.graph.nodes_geometry)
    old_parents = dict(scene.graph.transforms.parents)
    original = {name:(np.array(mesh.vertices, copy=True),np.array(mesh.faces,copy=True))
                for name,mesh in scene.geometry.items()}
    result = apply_root_scene(scene, source_orientation_index, pivot_mode,
                              wheel_crank_delta_deg, frame_pitch_deg)
    expected = {p:np.array(scene.graph.get(p)[0],copy=True) for p in PARTS}
    output = scene.export(file_type="glb")
    if not isinstance(output,bytes) or output[:4] != b"glTF":
        raise ValueError("failed to serialize authentic derived source GLB")
    reread = trimesh.load(io.BytesIO(output),file_type="glb",
                          force="scene",process=False)
    if (set(reread.graph.nodes) != old_nodes or
            set(reread.graph.nodes_geometry) != old_geom_nodes or
            dict(reread.graph.transforms.parents) != old_parents or
            set(reread.geometry) != set(original)):
        raise ValueError("original five-parent sixteen-material topology lost")
    for name,(vertices,faces) in original.items():
        mesh = reread.geometry[name]
        if (not np.array_equal(mesh.faces, faces) or
                not np.allclose(mesh.vertices, vertices, atol=1e-6, rtol=0)):
            raise ValueError("original source local material geometry modified")
    for p in PARTS:
        if not np.allclose(reread.graph.get(p)[0], expected[p], atol=1e-6, rtol=0):
            raise ValueError("GLB roundtrip lost whole-rig parent pose")
    result.update({
        "source_2026_upright_GLb_sha256": actual_sha,
        "input_GLb_digest_bound_during_authenticated_build": True,
        "source_2026_GLb_provenance_class": input_source_class,
        "source_historical_2026_SCAD_sha256": HISTORICAL_SCAD_SHA,
        "derived_GLB_sha256": hashlib.sha256(output).hexdigest(),
        "derived_GLB_bytes": len(output),
        "material_geometry_and_all_parent_matrices_survived_roundtrip": True,
    })
    return output,result


def process(source:Path,index:int,pivot_mode:str,wheel:float,
            pitch:float,out:Path,receipt:Path):
    if (len({source.resolve(),out.resolve(),receipt.resolve()}) != 3 or
            any(p.exists() or p.is_symlink() for p in (out,receipt))):
        raise ValueError("source, output and receipt must differ; no overwrite")
    output,record = build(source.read_bytes(),index,pivot_mode,wheel,pitch)
    out.parent.mkdir(parents=True,exist_ok=True)
    receipt.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".art4k-root-glb-",dir=out.parent) as folder, \
            tempfile.TemporaryDirectory(prefix=".art4k-root-receipt-",dir=receipt.parent) as proofdir:
        temp_glb=Path(folder)/"candidate.glb"
        temp_receipt=Path(proofdir)/"candidate.json"
        temp_glb.write_bytes(output)
        temp_receipt.write_text(json.dumps(record,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        os.link(temp_glb,out)
        os.link(temp_receipt,receipt)
    return record


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-glb",type=Path,required=True)
    p.add_argument("--source-orientation-index",type=int,required=True)
    p.add_argument("--pivot-mode",choices=MODES,required=True)
    p.add_argument("--wheel-crank-delta-deg",type=float,default=0.)
    p.add_argument("--frame-pitch-deg",type=float,default=0.)
    p.add_argument("--out-glb",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(process(a.source_glb,a.source_orientation_index,
                             a.pivot_mode,a.wheel_crank_delta_deg,a.frame_pitch_deg,
                             a.out_glb,a.receipt),indent=2,sort_keys=True))


if __name__=="__main__":
    main()
