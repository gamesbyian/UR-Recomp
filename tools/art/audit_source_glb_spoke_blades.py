#!/usr/bin/env python3
"""Read-only 2026 GLB spokes -> fixed blade mass proof, no source-ROM fitting."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from tools.art.experimental_spoke_blade_volume import (
    SOURCE_GL_B_SHA256,SOURCE_GL_B_VERTEX_COUNT,SOURCE_GL_B_FACE_COUNT,
    SPOKE_NODE,SPOKE_SET_COUNT,BLADE_WIDTH_FACTOR,
    temporary_wider_spoke_blades,
)
from tools.art.no_replace_report import publish_text_once


def analyze(path:Path)->dict:
    import numpy as np
    import trimesh
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=SOURCE_GL_B_SHA256:
        raise ValueError("exact original 2026 upright GLB source SHA required")
    scene=trimesh.load(path,force="scene",process=False)
    if not isinstance(scene,trimesh.Scene):
        raise ValueError("source GLB must retain full material and rig graph")
    original_nodes=set(scene.graph.nodes_geometry)
    original_colors={key:np.asarray(m.visual.vertex_colors).copy()
                     for key,m in scene.geometry.items()}
    original_geom={key:np.asarray(m.vertices).copy()
                   for key,m in scene.geometry.items()}
    _,target_name=scene.graph.get(SPOKE_NODE)
    mesh=scene.geometry[target_name]
    original=np.asarray(mesh.vertices).copy()
    before_volume=float(mesh.volume)
    if not mesh.is_watertight:
        raise ValueError("source mesh must be a closed original 2026 spoke solid")
    with temporary_wider_spoke_blades(scene):
        updated=np.asarray(mesh.vertices)
        displacement=np.linalg.norm(updated-original,axis=1)
        before_radius=np.hypot(original[:,0],original[:,2])
        after_radius=np.hypot(updated[:,0],updated[:,2])
        if (not np.array_equal(updated[:,1],original[:,1])
                or np.max(np.abs(before_radius-after_radius))>1e-10
                or not mesh.is_watertight
                or any(not np.array_equal(m.visual.vertex_colors,original_colors[name])
                       for name,m in scene.geometry.items())
                or any(not np.array_equal(m.vertices,original_geom[name])
                       for name,m in scene.geometry.items() if name!=target_name)):
            raise ValueError("authored source spoke probe changed wheel or other source geometry")
        after_volume=float(mesh.volume)
        changed=int(np.count_nonzero(displacement>1e-5))
        maximum=float(np.max(displacement))
        mean=float(np.mean(displacement))
    if (set(scene.graph.nodes_geometry)!=original_nodes
            or any(not np.array_equal(m.vertices,original_geom[name])
                   for name,m in scene.geometry.items())):
        raise ValueError("temporary 3D spoke blade did not restore original GLB")
    if not(1000<changed<1788 and .01<maximum<.03 and after_volume>before_volume):
        raise ValueError("original eight-spoke GLB broadening failed bounded geometry review")
    return {
        "schema":"UR-ART4K-2026-REAL-GLB-PRINT-INSPIRED-SPOKE-VOLUME/1",
        "source_2026_upright_GLb_sha256":SOURCE_GL_B_SHA256,
        "original_source_GLb_byte_count":len(raw),
        "single_original_2026_rig_five_parents_sixteen_material_meshes":True,
        "original_rim_spoke_material_node":SPOKE_NODE,
        "original_fixed_spoke_count":SPOKE_SET_COUNT,
        "only_original_2026_spoke_vertices_modified":True,
        "source_spoke_vertices":SOURCE_GL_B_VERTEX_COUNT,
        "source_spoke_faces":SOURCE_GL_B_FACE_COUNT,
        "blade_width_factor_research_only":BLADE_WIDTH_FACTOR,
        "changed_original_vertices_over_1e_5_model_units":changed,
        "max_vertex_displacement_model_units":round(maximum,8),
        "mean_vertex_displacement_model_units":round(mean,8),
        "original_spoke_mesh_signed_volume_model_units3":round(before_volume,9),
        "proposed_spoke_mesh_signed_volume_model_units3":round(after_volume,9),
        "changed_spoke_mesh_volume_percent":round((after_volume/before_volume-1)*100,6),
        "actual_material_node_triangle_count_unchanged":True,
        "source_spoke_y_depth_and_radial_endpoints_preserved":True,
        "all_original_2026_materials_parent_hierarchy_and_other_four_parts_unchanged":True,
        "original_source_2026_spoke_mesh_watertight_after_deformation":True,
        "original_2026_model_vertex_arrays_restored_exactly":True,
        "original_1994_3D_mesh_camera_spoke_count_or_rig_recovered":False,
        "authoritative_original_1994_spoke_profile_observed_in_print":False,
        "owner_2026_character_likeness_approved":False,
        "shipping_art_approved":False,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--glb",type=Path,required=True)
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    report=analyze(args.glb)
    value=json.dumps(report,sort_keys=True,indent=2)+"\n"
    if args.out:
        publish_text_once(args.out,value)
    print(value,end="")


if __name__=="__main__":
    main()
