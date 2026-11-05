#!/usr/bin/env python3
"""Audit whether five REAL 2026 experimental static GLBs can be mesh-morphed.

Only examines source-hash-pinned original five-pose 2026 *blockout*. glTF
material node names do not prove stable vertex correspondence, joint rigging,
or original 1994 3D source animation. Requires optional numpy/trimesh.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path

try:
    from tools.art.no_replace_report import publish_text_once
except ModuleNotFoundError:
    from no_replace_report import publish_text_once

SCHEMA="UR-ART4K-EXPERIMENTAL-POSE-GLB-TOPOLOGY/1"
COMMIT="d061cddcdbac9b2b5ac137d0d721b63f92dc3ec1"
SOURCE_GLB_SHA={
 "upright":"efdc8425f252b4a0218d140d087c6cc923689589e0cf74cc6333d722182595f5",
 "pedal":"f692277bb9bf215ccc97bc89f44d28378a43ddc9aa45843c4f0ab30e8747db53",
 "wheelie":"859b985d8fc51f994e5e42fd64bc871d493249285454ec836b415ec833f33c27",
 "stunt":"d3375cf4d44d973ca7b4308bfff5b3646087a37d206a2746792c8083483f3212",
 "bank":"50d56b4f702ad655929c17e5cbc4e281386cf6b2fb2cd80e71d0a2e6b672fd59",
}
MATERIAL_COUNTS={
 "tire":2,"rim_and_hub":5,"fork_and_frame":4,"pedals":3,"saddle":2
}

def digest(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()

def compare_mesh_pose_tables(tables:dict[str,dict[str,dict]])->dict:
    """Pure topology policy against source-owned material identifiers.

    Stable face ordering is a NECESSARY condition for direct vertex blending,
    not proof that equal indices represent equal 3D semantic vertices.
    """
    if set(tables)!=set(SOURCE_GLB_SHA):
        raise ValueError("not the canonical five experimental 2026 poses")
    expected={f"{part}__material_{i}" for part,n in MATERIAL_COUNTS.items()
              for i in range(n)}
    if any(set(nodes)!=expected for nodes in tables.values()):
        raise ValueError("missing, duplicate or alien source part material")
    baseline=tables["upright"]
    output=[]
    for name in sorted(expected):
        ref=baseline[name]
        vertices_equal=faces_equal=vertex_count_stable=world_transform_equal=True
        per_pose={}
        for pose,nodes in tables.items():
            row=nodes[name]
            for key in ("vertex_count","face_count","vertex_bytes_sha256",
                        "face_indices_sha256","world_transform_sha256"):
                if key not in row:
                    raise ValueError("incomplete source mesh topology witness")
            if (type(row["vertex_count"]) is not int or row["vertex_count"]<3 or
                    type(row["face_count"]) is not int or row["face_count"]<1 or
                    any(not isinstance(row[k],str) or len(row[k])!=64
                        for k in ("vertex_bytes_sha256","face_indices_sha256",
                                  "world_transform_sha256"))):
                raise ValueError("invalid source mesh geometry data")
            vertex_count_stable &= row["vertex_count"]==ref["vertex_count"]
            vertices_equal &= row["vertex_bytes_sha256"]==ref["vertex_bytes_sha256"]
            faces_equal &= row["face_indices_sha256"]==ref["face_indices_sha256"]
            world_transform_equal &= row["world_transform_sha256"]==ref["world_transform_sha256"]
            per_pose[pose]={"vertex_count":row["vertex_count"],
                            "triangle_count":row["face_count"]}
        output.append({
            "material_mesh_name":name,
            "source_part":name.split("__material_")[0],
            "vertex_counts_equal_in_all_five_poses":bool(vertex_count_stable),
            "local_positions_equal_in_all_five_poses":bool(vertices_equal),
            "face_index_arrays_equal_in_all_five_poses":bool(faces_equal),
            "world_matrices_equal_in_all_five_poses":bool(world_transform_equal),
            "necessary_topology_conditions_met":bool(vertex_count_stable and faces_equal),
            "direct_vertex_index_blending_requires_authored_correspondence":True,
            "per_pose_counts":per_pose,
        })
    return {
        "source_material_mesh_count":len(output),
        "source_parent_parts":len(MATERIAL_COUNTS),
        "all_five_vertex_counts_stable_meshes":
            sum(x["vertex_counts_equal_in_all_five_poses"] for x in output),
        "all_five_local_positions_identical_meshes":
            sum(x["local_positions_equal_in_all_five_poses"] for x in output),
        "all_five_face_index_arrays_stable_meshes":
            sum(x["face_index_arrays_equal_in_all_five_poses"] for x in output),
        "all_five_world_matrices_identical_meshes":
            sum(x["world_matrices_equal_in_all_five_poses"] for x in output),
        "all_material_meshes_meet_necessary_topology_conditions":
            all(x["necessary_topology_conditions_met"] for x in output),
        "all_material_meshes_safe_for_naive_glb_vertex_morph":False,
        "material_meshes":output,
        "matched_3d_semantic_vertex_correspondence_proven":False,
        "1994_original_pose_or_camera_identified":False,
    }

def load_source_model_tables(model_root:Path)->dict:
    import numpy as np
    import trimesh
    root=model_root.resolve()
    tables={}
    for pose,sha in SOURCE_GLB_SHA.items():
        path=(root/"assets"/COMMIT/f"{pose}-{sha[:16]}.glb").resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError("missing source-hash-bound real five-pose GLB")
        raw=path.read_bytes()
        if digest(raw)!=sha:
            raise ValueError("actual source GLB differs from authenticated 2026 export")
        scene=trimesh.load(file_obj=io.BytesIO(raw),file_type="glb",
                           force="scene",process=False)
        if not isinstance(scene,trimesh.Scene):
            raise ValueError("source model GLB lost named scene")
        table={}
        for node in scene.graph.nodes_geometry:
            if node in table:
                raise ValueError("duplicated source material node")
            world,geometry=scene.graph.get(node)
            mesh=scene.geometry[geometry]
            vertices=np.asarray(mesh.vertices,dtype="<f8")
            faces=np.asarray(mesh.faces,dtype="<i8")
            if (vertices.ndim!=2 or vertices.shape[1]!=3 or
                    faces.ndim!=2 or faces.shape[1]!=3 or
                    not np.isfinite(vertices).all() or
                    (faces<0).any() or (faces>=len(vertices)).any() or
                    not np.isfinite(world).all()):
                raise ValueError("malformed original 2026 candidate GLB geometry")
            table[node]={
                "vertex_count":len(vertices),
                "face_count":len(faces),
                "vertex_bytes_sha256":digest(vertices.tobytes()),
                "face_indices_sha256":digest(faces.tobytes()),
                "world_transform_sha256":
                    digest(np.asarray(world,dtype="<f8").tobytes()),
            }
        tables[pose]=table
    return tables

def audit(model_root:Path)->dict:
    data=compare_mesh_pose_tables(load_source_model_tables(model_root))
    return {
        "schema":SCHEMA,
        "experimental_source_model_commit":COMMIT,
        "exact_five_source_glb_sha256":SOURCE_GLB_SHA,
        "experimental_pose_labels_are_original_1994_sprite_states":False,
        "original_1994_rig_or_animation_recovered":False,
        "direct_3d_mesh_morphing_is_source_supported":False,
        "original_character_likeness_approved":False,
        "shipping_art_approved":False,
        "comparison":data,
    }

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model-review-dir",required=True,type=Path)
    ap.add_argument("--out",type=Path)
    args=ap.parse_args()
    payload=json.dumps(audit(args.model_review_dir),sort_keys=True,indent=2)+"\n"
    if args.out:
        publish_text_once(args.out,payload)
    else:
        print(payload,end="")

if __name__=="__main__":
    main()
