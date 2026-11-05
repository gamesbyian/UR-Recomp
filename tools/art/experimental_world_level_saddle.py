#!/usr/bin/env python3
"""Temporary, source-owned 2026 saddle attitude ablation on the real GLB.

After existing whole-rig root motion and +15 deg local saddle pitch, keep its
mounting-point world translation exactly, but return its world 3x3 attitude to
the unique 2026 neutral-root +15-deg reference. No source ROM part identity,
physical 1994 saddle joint or owner art approval is inferred.
"""
from __future__ import annotations
from contextlib import contextmanager
import math


def world_level_target(current_world, reference_attitude):
    """Pure stdlib, strictly rigid 4x4 target retaining *current* position."""
    try:
        current=tuple(tuple(float(v) for v in row) for row in current_world)
        attitude=tuple(tuple(float(v) for v in row) for row in reference_attitude)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("finite rigid source 2026 GLB matrices required") from exc
    if (len(current)!=4 or any(len(row)!=4 for row in current) or
            len(attitude)!=3 or any(len(row)!=3 for row in attitude) or
            any(not math.isfinite(v) for row in current for v in row) or
            any(not math.isfinite(v) for row in attitude for v in row) or
            any(abs(current[3][j]-(1. if j==3 else 0.))>1e-8 for j in range(4))):
        raise ValueError("finite proper 2026 GLB root and saddle attitudes required")
    for rotation in (tuple(tuple(row[j] for j in range(3)) for row in current[:3]),
                     attitude):
        if any(abs(sum(rotation[k][i]*rotation[k][j] for k in range(3))-
                   (1. if i==j else 0.))>1e-7
               for i in range(3) for j in range(3)):
            raise ValueError("source-GLB world saddle matrix must be rigid")
        a,b,c=rotation
        determinant=(a[0]*(b[1]*c[2]-b[2]*c[1])-
                     a[1]*(b[0]*c[2]-b[2]*c[0])+
                     a[2]*(b[0]*c[1]-b[1]*c[0]))
        if abs(determinant-1.)>1e-7:
            raise ValueError("source saddle attitude must preserve right-handed material geometry")
    target=tuple(tuple(attitude[i][j] if j<3 and i<3 else current[i][j]
                       for j in range(4)) for i in range(4))
    return target


@contextmanager
def temporary_saddle_world_attitude(scene, reference_attitude):
    """Hold saddle attitude at one fixed authored reference; restore exactly.

    Must execute *inside* the existing temporary_saddle_pitch context, after
    apply_root_scene, and never alter the existing controller's pose cache.
    """
    import numpy as np
    import trimesh
    from tools.art.experimental_direct_drive_phase import PARTS, CHILD_COUNTS
    if not isinstance(scene,trimesh.Scene) or scene.graph.base_frame!="world":
        raise ValueError("real authenticated five-parent GLB scene required")
    parent=scene.graph.transforms.parents.get("saddle")
    root=scene.graph.base_frame
    if (parent is None or
            (parent!=root and scene.graph.transforms.parents.get(parent)!=root) or
            any(scene.graph.transforms.parents.get(p)!=parent for p in PARTS) or
            set(scene.graph.nodes_geometry)!={
                f"{part}__material_{i}"
                for part,n in CHILD_COUNTS.items() for i in range(n)}):
        raise ValueError("source five-parent saddle hierarchy changed")
    before={part:np.asarray(scene.graph.get(part)[0]).copy() for part in PARTS}
    names=set(scene.graph.nodes)
    geometry=set(scene.geometry)
    original=before["saddle"]
    target=np.asarray(world_level_target(original,reference_attitude))
    parent_world=(np.eye(4) if parent==root
                  else np.asarray(scene.graph.get(parent)[0]).copy())
    inv=np.linalg.inv(parent_world)
    original_local=inv@original
    scene.graph.update(frame_to="saddle",frame_from=parent,matrix=inv@target)
    try:
        actual=np.asarray(scene.graph.get("saddle")[0])
        if (not np.allclose(actual,target,atol=1e-8,rtol=0) or
                set(scene.graph.nodes)!=names or set(scene.geometry)!=geometry or
                any(not np.allclose(scene.graph.get(part)[0],before[part],
                                    atol=1e-8,rtol=0)
                    for part in PARTS if part!="saddle")):
            raise ValueError("saddle attitude ablation altered mount or other 2026 GLB parts")
        yield
    finally:
        scene.graph.update(frame_to="saddle",frame_from=parent,
                           matrix=original_local)
        if (set(scene.graph.nodes)!=names or set(scene.geometry)!=geometry or
                any(not np.allclose(scene.graph.get(part)[0],before[part],
                                    atol=1e-8,rtol=0) for part in PARTS)):
            raise ValueError("temporary 2026 saddle world attitude failed to restore original rig")
