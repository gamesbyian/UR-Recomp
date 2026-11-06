#!/usr/bin/env python3
"""Reversible source-mesh-local fork/crown volume ablation on ONE 2026 GLB.

The exact 1994 original physical fork crown was not recovered. These bounded
symmetrical local transverse scales are hypothetical review candidates. The
single existing five-parent 16-material source model, saddle mount, tyre,
crank, camera and full original source timeline are held fixed.
"""
from __future__ import annotations
from contextlib import contextmanager
import math

# Frozen authoring coordinates come directly from the ONE source SCAD fork:
# [-.10,y,.83] -> [-.17,0,1.39] -> [-.25,0,2.09].
# Only the central fork/crown band .86 <= local Z <= 1.98 is changed.
CROWN_SCALES = (.90,1.10)
CROWN_CENTER_Z = 1.42
CROWN_HALF_BAND = .56
SOURCE_STEM_XZ = ((.83,-.10),(1.39,-.17),(2.09,-.25))


def validate_scale(scale):
    if type(scale) not in (int,float) or float(scale) not in CROWN_SCALES:
        raise ValueError("only frozen ±10% local 2026 fork crown radial controls")


def source_stem_x(z: float) -> float:
    """Existing 2026 SCAD centreline, not source-game 1994 anatomical truth."""
    if not isinstance(z,(int,float)) or not math.isfinite(z):
        raise ValueError("finite source local z required")
    a,b = (SOURCE_STEM_XZ[0],SOURCE_STEM_XZ[1]) if z <= 1.39 else (
        SOURCE_STEM_XZ[1], SOURCE_STEM_XZ[2])
    return a[1] + (float(z)-a[0])*(b[1]-a[1])/(b[0]-a[0])


def scale_crown_vertices(vertices,scale):
    """Preserve local Z, source part attachment, both band ends and paint seam.

    Identical local-Z transformation is applied to every original source
    fork material, not only the blue one. A smooth quartic taper vanishes
    exactly at each band end, avoiding a hard ridge and preserving stem and
    hub vertices outside the band. No per-original-racer adjustments.
    """
    validate_scale(scale)
    try:
        rows=tuple(tuple(float(x) for x in point) for point in vertices)
    except (TypeError,ValueError,OverflowError) as exc:
        raise ValueError("source GLB fork vertices must be three-axis") from exc
    if not rows or any(len(row)!=3 or
                       any(not math.isfinite(v) for v in row)
                       for row in rows):
        raise ValueError("nonempty finite original 2026 GLB geometry required")
    result=[]
    for x,y,z in rows:
        phase=abs((z-CROWN_CENTER_Z)/CROWN_HALF_BAND)
        weight=(1-phase*phase)**2 if phase<1 else 0.
        factor=1+(float(scale)-1)*weight
        center=source_stem_x(z)
        result.append((center+(x-center)*factor,y*factor,z))
    return tuple(result)


@contextmanager
def temporary_fork_crown_volume(scene,scale):
    """Transform ONLY original fork child vertex buffers, restore on every exit."""
    import numpy as np
    import trimesh
    from tools.art.experimental_direct_drive_phase import PARTS,CHILD_COUNTS

    validate_scale(scale)
    if not isinstance(scene,trimesh.Scene) or scene.graph.base_frame!="world":
        raise ValueError("original five-parent 2026 scene GLB required")
    root=scene.graph.base_frame
    parent=scene.graph.transforms.parents.get("fork_and_frame")
    if (parent is None or
            (parent!=root and scene.graph.transforms.parents.get(parent)!=root) or
            any(scene.graph.transforms.parents.get(part)!=parent for part in PARTS) or
            set(scene.graph.nodes_geometry)!={
                f"{part}__material_{i}"
                for part,number in CHILD_COUNTS.items() for i in range(number)}):
        raise ValueError("source five-parent/16-material node hierarchy differs")
    nodes,geometry_names=set(scene.graph.nodes),set(scene.geometry)
    parents={part:np.asarray(scene.graph.get(part)[0]).copy() for part in PARTS}
    if any(t.shape!=(4,4) or not np.isfinite(t).all() for t in parents.values()):
        raise ValueError("original authored source parent transform invalid")
    saved={}
    for i in range(CHILD_COUNTS["fork_and_frame"]):
        node=f"fork_and_frame__material_{i}"
        transform,name=scene.graph.get(node)
        if (not np.allclose(transform,parents["fork_and_frame"],atol=1e-8,rtol=0)
                or name in saved or name not in scene.geometry):
            raise ValueError("authored real fork child transforms/materials changed")
        mesh=scene.geometry[name]
        points=np.asarray(mesh.vertices).copy()
        faces=np.asarray(mesh.faces).copy()
        colors=np.asarray(mesh.visual.vertex_colors).copy()
        if (points.ndim!=2 or points.shape[1]!=3 or len(points)==0
                or not np.isfinite(points).all()):
            raise ValueError("invalid original fork geometry vertices")
        saved[name]=(points,faces,colors)
    try:
        for name,(points,_,_) in saved.items():
            scene.geometry[name].vertices=np.asarray(
                scale_crown_vertices(points,scale),dtype=float)
        if (set(scene.graph.nodes)!=nodes or set(scene.geometry)!=geometry_names
                or any(not np.array_equal(scene.graph.get(p)[0],parents[p])
                       for p in PARTS)
                or any(not np.array_equal(scene.geometry[name].faces,faces) or
                           not np.array_equal(scene.geometry[name].visual.vertex_colors,colors)
                       for name,(_,faces,colors) in saved.items())):
            raise ValueError("fork crown ablation altered original 2026 rig identity")
        yield
    finally:
        for name,(points,_,_) in saved.items():
            scene.geometry[name].vertices=points
        if (set(scene.graph.nodes)!=nodes or set(scene.geometry)!=geometry_names
                or any(not np.array_equal(scene.graph.get(p)[0],parents[p])
                       for p in PARTS)
                or any(not np.array_equal(scene.geometry[name].vertices,points) or
                           not np.array_equal(scene.geometry[name].faces,faces) or
                           not np.array_equal(scene.geometry[name].visual.vertex_colors,colors)
                       for name,(points,faces,colors) in saved.items())):
            raise ValueError("temporary authored fork crown mesh failed exact rollback")
