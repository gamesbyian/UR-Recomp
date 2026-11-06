#!/usr/bin/env python3
"""Reversible, source-authored 2026 saddle stem displacement on the ONE real GLB.

Historical independent saddle motion is attested, but its 1994 numerical
stroke/temporal law is not recovered. Compare ±0.12 *authored 2026 units*
along the independently authored frame-to-saddle stem, never fitted to frames.
"""
from __future__ import annotations
from contextlib import contextmanager
import math

SOURCE_STEM_DELTA=(.29,0.,.88)  # SCAD upper-frame[-.25,0,1.39] -> saddle[+.04,0,2.27]
SOURCE_STEM_LENGTH=math.sqrt(sum(x*x for x in SOURCE_STEM_DELTA))
SOURCE_STEM_UNIT=tuple(x/SOURCE_STEM_LENGTH for x in SOURCE_STEM_DELTA)
ALLOWED_STROKES=(-.12,.12)


def rigid_matrix(raw):
    try:
        rows=tuple(tuple(float(v) for v in row) for row in raw)
    except (TypeError,ValueError,OverflowError) as exc:
        raise ValueError("finite proper real GLB 4x4 required") from exc
    if (len(rows)!=4 or any(len(row)!=4 for row in rows)
            or any(not math.isfinite(x) for row in rows for x in row)
            or any(abs(rows[3][j]-(1. if j==3 else 0.))>1e-8 for j in range(4))):
        raise ValueError("finite proper real GLB 4x4 required")
    r=tuple(row[:3] for row in rows[:3])
    if any(abs(sum(r[k][i]*r[k][j] for k in range(3))-
               (1. if i==j else 0.))>1e-7 for i in range(3) for j in range(3)):
        raise ValueError("real GLB matrix rotation must be proper rigid")
    a,b,c=r
    determinant=(a[0]*(b[1]*c[2]-b[2]*c[1])
                 -a[1]*(b[0]*c[2]-b[2]*c[0])
                 +a[2]*(b[0]*c[1]-b[1]*c[0]))
    if abs(determinant-1.)>1e-7:
        raise ValueError("real GLB matrix rotation must be proper rigid")
    return rows


def translate_parent_local_world(original_world,parent_world,stroke):
    """Pure stdlib: change 2026 mount position only, with fixed attitude."""
    if type(stroke) not in (int,float) or float(stroke) not in ALLOWED_STROKES:
        raise ValueError("only predeclared ±0.12 2026 stem offsets allowed")
    a,b=rigid_matrix(original_world),rigid_matrix(parent_world)
    translated=tuple(tuple(
        a[i][j]+float(stroke)*sum(b[i][k]*SOURCE_STEM_UNIT[k] for k in range(3))
        if j==3 and i<3 else a[i][j]
        for j in range(4)) for i in range(4))
    if any(translated[i][j]!=a[i][j] for i in range(3) for j in range(3)):
        raise ValueError("source-authored saddle attitude unexpectedly moved")
    return translated


@contextmanager
def temporary_saddle_stem_slide(scene,stroke):
    """Preserve 16 actual GLB meshes, other four parts and exact prior pose."""
    import numpy as np
    import trimesh
    from tools.art.experimental_direct_drive_phase import PARTS,CHILD_COUNTS
    if not isinstance(scene,trimesh.Scene) or scene.graph.base_frame!="world":
        raise ValueError("real authenticated 2026 five-parent scene required")
    parent=scene.graph.transforms.parents.get("saddle")
    root=scene.graph.base_frame
    if (parent is None or
            (parent!=root and scene.graph.transforms.parents.get(parent)!=root)
            or any(scene.graph.transforms.parents.get(part)!=parent for part in PARTS)
            or set(scene.graph.nodes_geometry)!={
                f"{part}__material_{i}"
                for part,n in CHILD_COUNTS.items() for i in range(n)}):
        raise ValueError("real 2026 parent/16 material hierarchy changed")
    before={part:np.asarray(scene.graph.get(part)[0],dtype=float).copy()
            for part in PARTS}
    parent_world=(np.eye(4) if parent==root else
                  np.asarray(scene.graph.get(parent)[0],dtype=float).copy())
    target=np.asarray(translate_parent_local_world(
        before["saddle"],parent_world,stroke))
    inv=np.linalg.inv(parent_world)
    original_local=inv@before["saddle"]
    nodes,geo=set(scene.graph.nodes),set(scene.geometry)
    scene.graph.update(frame_to="saddle",frame_from=parent,matrix=inv@target)
    try:
        if (not np.allclose(scene.graph.get("saddle")[0],target,atol=1e-8,rtol=0)
                or set(scene.graph.nodes)!=nodes or set(scene.geometry)!=geo
                or any(not np.allclose(scene.graph.get(part)[0],before[part],
                                        atol=1e-8,rtol=0)
                       for part in PARTS if part!="saddle")):
            raise ValueError("saddle slide changed another real GLB model parent")
        yield
    finally:
        scene.graph.update(frame_to="saddle",frame_from=parent,matrix=original_local)
        if (set(scene.graph.nodes)!=nodes or set(scene.geometry)!=geo
                or any(not np.allclose(scene.graph.get(part)[0],before[part],
                                        atol=1e-8,rtol=0) for part in PARTS)):
            raise ValueError("saddle slide failed to restore real source rig")
