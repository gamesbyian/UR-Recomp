#!/usr/bin/env python3
"""Reversible volume-only 2026 eight-spoke -> broader blade-like support probe.

Official printed manual p15 shows broad metallic supports, but is NOT
registered original 1994 gameplay mesh or calibrated camera. Keep existing
unapproved 2026 five-parent/16-material source GLB and exact eight spokes,
and modify ONLY the source spokes material's wheel-plane tangent breadth.
"""
from __future__ import annotations

from contextlib import contextmanager
import math

SOURCE_GL_B_SHA256="d83a39b805107eb309d3f56db8d5aeb77f435038170005fd5d15c0c45ed4c94a"
SOURCE_GL_B_VERTEX_COUNT=1788
SOURCE_GL_B_FACE_COUNT=3572
SPOKE_NODE="rim_and_hub__material_2"
SPOKE_SET_COUNT=8
ORIGINAL_RADIAL_OFFSET_DEGREES=11
BLADE_WIDTH_FACTOR=2.0
UNMODIFIED_ROOT_RADIUS=0.12
FULL_BLADE_START_RADIUS=0.72


def wider_blade_vertices(vertices,factor=BLADE_WIDTH_FACTOR):
    """Keep source spoke count, material, 3D Y, wheel radius and crank separate.

    Broadening begins only beyond the source hub's radial r=.12 and rises
    quadratically toward the existing spoke attachment r=.72. This is
    mathematically ONE fixed, manual-inspired 2026 model sculpt candidate,
    not fitted original 1994 3D dimensions or a parameter sweep.
    """
    if type(factor) not in (int,float) or float(factor)!=BLADE_WIDTH_FACTOR:
        raise ValueError("only one frozen source 2026 blade-breadth proposal")
    try:
        rows=tuple(tuple(float(v) for v in row) for row in vertices)
    except (ValueError,TypeError,OverflowError) as exc:
        raise ValueError("finite original source spoke mesh required") from exc
    if (not rows or any(len(row)!=3 or any(not math.isfinite(v) for v in row)
                        for row in rows)):
        raise ValueError("nonempty finite 3D original source spoke vertices required")
    pitch=2*math.pi/SPOKE_SET_COUNT
    offset=math.radians(ORIGINAL_RADIAL_OFFSET_DEGREES)
    result=[]
    for x,y,z in rows:
        radius=math.hypot(x,z)
        if radius<=UNMODIFIED_ROOT_RADIUS:
            result.append((x,y,z))
            continue
        theta=math.atan2(x,z)
        axis=offset+round((theta-offset)/pitch)*pitch
        delta=math.atan2(math.sin(theta-axis),math.cos(theta-axis))
        u=min(1.,max(0.,(radius-UNMODIFIED_ROOT_RADIUS)/
                           (FULL_BLADE_START_RADIUS-UNMODIFIED_ROOT_RADIUS)))
        opened_angle=axis+delta*(1+(float(factor)-1)*u*u)
        result.append((radius*math.sin(opened_angle),y,
                       radius*math.cos(opened_angle)))
    return tuple(result)


@contextmanager
def temporary_wider_spoke_blades(scene):
    """Temporarily deform only authentic 2026 authored spokes, rollback exactly."""
    import numpy as np
    import trimesh
    from tools.art.experimental_direct_drive_phase import PARTS,CHILD_COUNTS

    if not isinstance(scene,trimesh.Scene) or scene.graph.base_frame!="world":
        raise ValueError("single source-authored five-part 2026 GLB scene required")
    parent=scene.graph.transforms.parents.get("rim_and_hub")
    if (parent is None or
            any(scene.graph.transforms.parents.get(part)!=parent for part in PARTS)
            or set(scene.graph.nodes_geometry)!={
                f"{part}__material_{i}"
                for part,count in CHILD_COUNTS.items() for i in range(count)}):
        raise ValueError("authored five-parent/16-material hierarchy changed")
    t,name=scene.graph.get(SPOKE_NODE)
    if name not in scene.geometry or not np.isfinite(np.asarray(t)).all():
        raise ValueError("missing source-authored 2026 spoke material graph")
    mesh=scene.geometry[name]
    original=np.asarray(mesh.vertices).copy()
    faces=np.asarray(mesh.faces).copy()
    paint=np.asarray(mesh.visual.vertex_colors).copy()
    if (original.shape!=(SOURCE_GL_B_VERTEX_COUNT,3)
            or faces.shape!=(SOURCE_GL_B_FACE_COUNT,3)
            or paint.shape!=(SOURCE_GL_B_VERTEX_COUNT,4)
            or not np.array_equal(paint[:,:3],
                np.tile(np.array([184,204,217]),(len(paint),1)))):
        raise ValueError("not the single original 2026 source eight-spoke GLB")
    source_names=set(scene.geometry)
    source_nodes=set(scene.graph.nodes)
    parents={part:np.asarray(scene.graph.get(part)[0]).copy() for part in PARTS}
    try:
        mesh.vertices=np.asarray(wider_blade_vertices(original),dtype=float)
        if (set(scene.geometry)!=source_names or set(scene.graph.nodes)!=source_nodes
                or any(not np.array_equal(scene.graph.get(part)[0],parents[part])
                       for part in PARTS)
                or not np.array_equal(mesh.faces,faces)
                or not np.array_equal(mesh.visual.vertex_colors,paint)):
            raise ValueError("unapproved 2026 source mesh ownership changed")
        yield
    finally:
        mesh.vertices=original
        if (set(scene.geometry)!=source_names or set(scene.graph.nodes)!=source_nodes
                or not np.array_equal(mesh.vertices,original)
                or not np.array_equal(mesh.faces,faces)
                or not np.array_equal(mesh.visual.vertex_colors,paint)
                or any(not np.array_equal(scene.graph.get(part)[0],parents[part])
                       for part in PARTS)):
            raise ValueError("original 2026 five-part GLB failed exact spoke rollback")
