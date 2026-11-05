#!/usr/bin/env python3
"""One reversible 2026 GLB frame-stretch research axis, never original 1994 speed law."""
from __future__ import annotations
from contextlib import contextmanager
import math

SCALES=(.96,1.04)
SADDLE_MOUNT_HEIGHT=2.27  # single 2026 authored SCAD axle-to-saddle stem height


def stretch_vertices(vertices,scale):
    """Dependency-free, rigid x/y with a nonrigid z of source-owned fork meshes."""
    if type(scale) not in (int,float) or float(scale) not in SCALES:
        raise ValueError("only two frozen 2026 upper-stretch scale controls allowed")
    try:
        rows=tuple(tuple(float(v) for v in row) for row in vertices)
    except (TypeError,ValueError,OverflowError) as exc:
        raise ValueError("source-owned 3D vertices required") from exc
    if not rows or any(len(row)!=3 or any(not math.isfinite(v) for v in row)
                       for row in rows):
        raise ValueError("nonempty finite 2026 xyz fork vertices required")
    return tuple((x,y,z*float(scale)) for x,y,z in rows)


@contextmanager
def temporary_upper_frame_stretch(scene,scale):
    """Stretch source fork mesh vertices; move original saddle mount coherently.

    Wheel/tire/rim/pedals, GLB parent graph, materials, actual parent attitudes,
    original source mesh triangle indexes and other geometries are unchanged.
    """
    import numpy as np
    import trimesh
    from tools.art.experimental_direct_drive_phase import PARTS,CHILD_COUNTS
    if type(scale) not in (int,float) or float(scale) not in SCALES:
        raise ValueError("only preregistered four-percent source frame stretch")
    if not isinstance(scene,trimesh.Scene) or scene.graph.base_frame!="world":
        raise ValueError("only actual source-owned five-parent 2026 GLB")
    root=scene.graph.base_frame
    parent=scene.graph.transforms.parents.get("saddle")
    if (parent is None or
            (parent!=root and scene.graph.transforms.parents.get(parent)!=root) or
            any(scene.graph.transforms.parents.get(part)!=parent for part in PARTS) or
            set(scene.graph.nodes_geometry)!={
                f"{part}__material_{i}"
                for part,n in CHILD_COUNTS.items() for i in range(n)}):
        raise ValueError("source-owned five-parent/16-material hierarchy changed")
    before={part:np.asarray(scene.graph.get(part)[0]).copy() for part in PARTS}
    parent_world=(np.eye(4) if parent==root
                  else np.asarray(scene.graph.get(parent)[0]).copy())
    for matrix in (parent_world,before["fork_and_frame"],before["saddle"]):
        if (not np.isfinite(matrix).all() or
                not np.allclose(matrix[3],[0,0,0,1],atol=1e-8,rtol=0) or
                not np.allclose(matrix[:3,:3].T@matrix[:3,:3],np.eye(3),
                                atol=1e-7,rtol=0) or
                not np.isclose(np.linalg.det(matrix[:3,:3]),1,atol=1e-7)):
            raise ValueError("authored model parents must be proper rigid")
    nodes,geometries=set(scene.graph.nodes),set(scene.geometry)
    saved={}
    for i in range(CHILD_COUNTS["fork_and_frame"]):
        node=f"fork_and_frame__material_{i}"
        transform,mesh_name=scene.graph.get(node)
        if (not np.allclose(transform,before["fork_and_frame"],atol=1e-8,rtol=0)
                or mesh_name in saved or mesh_name not in scene.geometry):
            raise ValueError("fork children must share source-owned local axle axis")
        mesh=scene.geometry[mesh_name]
        original=np.asarray(mesh.vertices).copy()
        if original.ndim!=2 or original.shape[1]!=3 or not np.isfinite(original).all():
            raise ValueError("malformed source mesh xyz")
        saved[mesh_name]=(original,np.asarray(mesh.faces).copy(),
                          np.asarray(mesh.visual.vertex_colors).copy())
    original_local=np.linalg.inv(parent_world)@before["saddle"]
    target=before["saddle"].copy()
    target[:3,3]+=parent_world[:3,:3]@np.array([0,0,SADDLE_MOUNT_HEIGHT*(float(scale)-1)])
    try:
        for name,(vertices,_,_) in saved.items():
            modified=vertices.copy()
            modified[:,2]*=float(scale)
            scene.geometry[name].vertices=modified
        scene.graph.update(frame_to="saddle",frame_from=parent,
                           matrix=np.linalg.inv(parent_world)@target)
        if (set(scene.graph.nodes)!=nodes or set(scene.geometry)!=geometries or
                not np.allclose(scene.graph.get("saddle")[0],target,atol=1e-8,rtol=0) or
                any(not np.allclose(scene.graph.get(part)[0],before[part],
                                    atol=1e-8,rtol=0) for part in PARTS if part!="saddle") or
                any(not np.array_equal(scene.geometry[name].faces,faces) or
                        not np.array_equal(scene.geometry[name].visual.vertex_colors,colors)
                        for name,(_,faces,colors) in saved.items())):
            raise ValueError("2026 upper stretch modified unrelated rig/material")
        yield
    finally:
        for name,(vertices,_,_) in saved.items():
            scene.geometry[name].vertices=vertices
        scene.graph.update(frame_to="saddle",frame_from=parent,matrix=original_local)
        if (set(scene.graph.nodes)!=nodes or set(scene.geometry)!=geometries or
                any(not np.allclose(scene.graph.get(part)[0],before[part],
                                    atol=1e-8,rtol=0) for part in PARTS) or
                any(not np.array_equal(scene.geometry[name].vertices,vertices) or
                        not np.array_equal(scene.geometry[name].faces,faces) or
                        not np.array_equal(scene.geometry[name].visual.vertex_colors,colors)
                        for name,(vertices,faces,colors) in saved.items())):
            raise ValueError("temporary 2026 frame stretch failed exact geometry rollback")
