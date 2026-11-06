#!/usr/bin/env python3
"""Frozen candidate longitudinal saddle shape ablation on one real 2026 GLB.

The original authoring mesh is underdetermined. Apply exact ±10% relative
mesh-local X scale to the two source-owned saddle material meshes, retaining
the real pivot, other meshes, nodes, colours, camera and all pose controllers.
"""
from __future__ import annotations
from contextlib import contextmanager
import math

SADDLE_SPANS=(.9,1.1)

def span_vertices(vertices,ratio):
    if type(ratio) not in (int,float) or ratio not in SADDLE_SPANS:
        raise ValueError("only predeclared 0.9/1.1 saddle shape scale")
    try:
        pts=tuple(tuple(float(x) for x in xyz) for xyz in vertices)
    except (TypeError,ValueError,OverflowError) as exc:
        raise ValueError("finite three-axis saddle vertices required") from exc
    if not pts or any(len(p)!=3 or not all(math.isfinite(x) for x in p) for p in pts):
        raise ValueError("finite nonempty saddle xyz required")
    return tuple((p[0]*ratio,p[1],p[2]) for p in pts)

@contextmanager
def temporary_saddle_span(scene,ratio):
    import numpy as np
    import trimesh
    from tools.art.experimental_direct_drive_phase import PARTS,CHILD_COUNTS
    if type(ratio) not in (int,float) or ratio not in SADDLE_SPANS:
        raise ValueError("predeclared 2026 saddle span control required")
    if not isinstance(scene,trimesh.Scene) or scene.graph.base_frame!="world":
        raise ValueError("one authentic source-owned 2026 GLB required")
    parent=scene.graph.transforms.parents.get("saddle")
    root=scene.graph.base_frame
    if (parent is None or (parent!=root and
            scene.graph.transforms.parents.get(parent)!=root) or
            any(scene.graph.transforms.parents.get(p)!=parent for p in PARTS) or
            set(scene.graph.nodes_geometry)!={
                f"{part}__material_{i}" for part,n in CHILD_COUNTS.items()
                for i in range(n)}):
        raise ValueError("source five-parent/16-material GLB changed")
    original_nodes=set(scene.graph.nodes)
    original_geometries=set(scene.geometry)
    before={p:np.asarray(scene.graph.get(p)[0]).copy() for p in PARTS}
    saved={}
    for i in range(CHILD_COUNTS["saddle"]):
        node=f"saddle__material_{i}"
        world,geometry_name=scene.graph.get(node)
        if (not np.allclose(world,before["saddle"],atol=1e-8,rtol=0)
                or geometry_name in saved or geometry_name not in scene.geometry):
            raise ValueError("unexpected original authored saddle child transform")
        mesh=scene.geometry[geometry_name]
        vertices=np.asarray(mesh.vertices).copy()
        if (vertices.ndim!=2 or vertices.shape[1]!=3 or
                not np.isfinite(vertices).all()):
            raise ValueError("invalid original 2026 saddle vertices")
        saved[geometry_name]=(vertices,np.asarray(mesh.faces).copy(),
                              np.asarray(mesh.visual.vertex_colors).copy())
    try:
        for name,(points,_,_) in saved.items():
            edited=points.copy()
            edited[:,0]*=ratio
            scene.geometry[name].vertices=edited
        if (set(scene.graph.nodes)!=original_nodes or
                set(scene.geometry)!=original_geometries or
                any(not np.allclose(scene.graph.get(p)[0],before[p],
                                    atol=1e-8,rtol=0) for p in PARTS) or
                any(not np.array_equal(scene.geometry[name].faces,faces) or
                        not np.array_equal(scene.geometry[name].visual.vertex_colors,colors)
                        for name,(_,faces,colors) in saved.items())):
            raise ValueError("candidate saddle span altered source rig identity")
        yield
    finally:
        for name,(points,_,_) in saved.items():
            scene.geometry[name].vertices=points
        if (set(scene.graph.nodes)!=original_nodes or
                set(scene.geometry)!=original_geometries or
                any(not np.allclose(scene.graph.get(p)[0],before[p],
                                    atol=1e-8,rtol=0) for p in PARTS) or
                any(not np.array_equal(scene.geometry[name].vertices,points) or
                        not np.array_equal(scene.geometry[name].faces,faces) or
                        not np.array_equal(scene.geometry[name].visual.vertex_colors,colors)
                        for name,(points,faces,colors) in saved.items())):
            raise ValueError("authored 2026 saddle shape did not restore exactly")
