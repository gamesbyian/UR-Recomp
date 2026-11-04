#!/usr/bin/env python3
"""Canonical oriented-surface fingerprint for the ONE authored 2026 racer GLB.

The source-identical OpenSCAD/Trimesh exporter has emitted different binary
GLB hashes from real Actions runs because of volatile temp metadata and
equivalent vertex/face enumeration. This tool distinguishes *actual mesh
surface/colour/parent pose* drift from serialization-only drift. It does not
authenticate a claimed SCAD authoring source or prove original 1994 likeness;
a separate exact GLB SHA plus the real exporter receipt are still mandatory.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import re
import struct

SCHEMA="UR-ART4K-ORIENTED-2026-GLB-TRIANGLE-MULTISET/1"
AUTHORED_SCAD_SHA="e99ef45bfe72f09ee97f51b7d7449c501aee2ca2d93596106ede4b56caddc984"
PART_COUNTS={"tire":2,"rim_and_hub":5,"fork_and_frame":4,"pedals":3,"saddle":2}
VALID_NODES={f"{part}__material_{i}"
             for part,count in PART_COUNTS.items() for i in range(count)}


def digest(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def canonical_triangle_sha(vertices,faces)->str:
    """Invariant to vertex IDs, face iteration and cyclic face start.

    Preserves actual float32 triangle coordinates, winding, degeneracies and
    multiplicity. Reversing a triangle changes the record. All sampling here
    comes from *actual* glTF float32 buffer positions, not recomputed CSG.
    """
    import numpy as np
    vertices=np.asarray(vertices,dtype="<f4")
    faces=np.asarray(faces)
    if (vertices.ndim!=2 or vertices.shape[1]!=3 or
            faces.ndim!=2 or faces.shape[1]!=3 or
            not len(vertices) or not len(faces) or
            not np.isfinite(vertices).all() or
            not np.issubdtype(faces.dtype,np.integer) or
            np.any(faces<0) or np.any(faces>=len(vertices))):
        raise ValueError("invalid actual GLB positions or oriented triangles")
    records=[]
    for f in faces:
        tri=[tuple(float(x) for x in vertices[int(index)]) for index in f]
        # Cyclic start choice does not change a triangle's winding.
        tri=min((tri,tri[1:]+tri[:1],tri[2:]+tri[:2]))
        records.append(struct.pack("<9f",*(x for p in tri for x in p)))
    return digest(b"".join(sorted(records)))


def inspect_glb(raw:bytes,*,expected_sha256:str|None=None)->dict:
    """Require source-style 5-parent/16-child, single-colour material parts."""
    import numpy as np
    import trimesh
    if (type(raw) is not bytes or len(raw)<16 or raw[:4]!=b"glTF" or
            (expected_sha256 is not None and
             (not re.fullmatch("[0-9a-f]{64}",expected_sha256) or
              digest(raw)!=expected_sha256))):
        raise ValueError("exact authentic 2026 GLB byte/SHA identity required")
    scene=trimesh.load(io.BytesIO(raw),file_type="glb",force="scene",process=False)
    if (not isinstance(scene,trimesh.Scene) or
            set(scene.graph.nodes_geometry)!=VALID_NODES or
            len(scene.geometry)!=16 or
            not set(PART_COUNTS).issubset(scene.graph.nodes)):
        raise ValueError("unexpected 2026 GLB five-parent sixteen-material graph")
    nodes={}
    for name in sorted(VALID_NODES):
        part=name.split("__material_",1)[0]
        if scene.graph.transforms.parents.get(name)!=part:
            raise ValueError("GLB material child not attached to its own authored parent")
        transform,geom_name=scene.graph.get(name)
        mesh=scene.geometry[geom_name]
        if not isinstance(mesh,trimesh.Trimesh) or mesh.is_empty:
            raise ValueError("empty source 2026 material geometry")
        matrix=np.asarray(transform,dtype=float)
        if matrix.shape!=(4,4) or not np.isfinite(matrix).all():
            raise ValueError("nonfinite authored 2026 material parent transform")
        rgba=np.asarray(mesh.visual.vertex_colors,dtype=np.uint8)
        if rgba.shape!=(len(mesh.vertices),4) or not np.all(rgba==rgba[0]):
            raise ValueError("one source-owned solid RGBA colour per authored material")
        nodes[name]={
            "parent":part,
            "triangles":int(len(mesh.faces)),
            "source_colour_RGBA":rgba[0].tolist(),
            "oriented_triangle_SHA256":canonical_triangle_sha(
                mesh.vertices,mesh.faces),
            "parent_child_world_matrix":matrix.round(9).ravel().tolist(),
        }
    core={"schema":SCHEMA,"mesh_nodes":nodes}
    canonical=digest(json.dumps(core,sort_keys=True,
                                separators=(",",":")).encode("utf-8"))
    return {
        "schema":SCHEMA,
        "input_GLb_sha256":digest(raw),
        "input_GLb_bytes":len(raw),
        "source_SCAD_sha256_expected_but_must_verify_exporter_receipt":AUTHORED_SCAD_SHA,
        "authored_2026_geometry_colour_parent_pose_fingerprint_sha256":canonical,
        "exact_material_children":16,
        "exact_parent_parts":5,
        "binary_metadata_vertex_face_order_ignored":True,
        "orientation_winding_and_triangle_multiplicity_preserved":True,
        "normal_vectors_pbr_material_shader_and_metadata_not_fingerprinted":True,
        "original_1994_mesh_camera_pose_material_recovered":False,
        "owner_likeness_approved":False,
        "source_materials":nodes,
    }


def main()->None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--glb",type=Path,required=True)
    parser.add_argument("--glb-sha256",required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    record=inspect_glb(args.glb.read_bytes(),
                       expected_sha256=args.glb_sha256)
    from tools.art.no_replace_report import publish_text_once
    publish_text_once(args.out,json.dumps(record,sort_keys=True,indent=2)+"\n")
    print("ART4K_ACTUAL_SOURCE_GLB_SEMANTIC_SURFACE_SHA",
          json.dumps({
              "GLb_byte_sha256":record["input_GLb_sha256"],
              "oriented_surface_sha256":record[
                  "authored_2026_geometry_colour_parent_pose_fingerprint_sha256"],
              "triangle_count":sum(x["triangles"]
                                   for x in record["source_materials"].values())
          },sort_keys=True))


if __name__=="__main__":
    main()
