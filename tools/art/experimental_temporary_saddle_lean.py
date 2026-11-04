#!/usr/bin/env python3
"""Temporary exact 2026 GLB saddle-parent pitch, without changing source mesh.

Uses the actual source-owned saddle mounting pivot, not a guessed 1994 joint.
Rollback is mandatory before existing whole-rig controller is used again.
"""
from __future__ import annotations
from contextlib import contextmanager
import math


def saddle_local_y_matrix(degrees:float):
    import numpy as np
    if type(degrees) not in (int,float) or not math.isfinite(degrees) or not -30<=degrees<=30:
        raise ValueError("bounded 2026 saddle local pitch (-30..30) required")
    theta=math.radians(degrees)
    c,s=math.cos(theta),math.sin(theta)
    transform=np.eye(4)
    transform[:3,:3]=[[c,0.,s],[0.,1.,0.],[-s,0.,c]]
    return transform


@contextmanager
def temporary_saddle_pitch(scene,degrees:float):
    """Pitch only the EXISTING 2026 saddle mounting node; exact TRS restore.

    Every other 2026 parent, GLB mesh, material and original scene node stays
    bitwise untouched, and the existing parent root/axle controller keeps
    its source-verified last-state cache coherent after the rollback.
    """
    import numpy as np
    import trimesh
    R=saddle_local_y_matrix(degrees)
    if not isinstance(scene,trimesh.Scene):
        raise ValueError("one actual five-parent 2026 GLB scene required")
    parent=scene.graph.transforms.parents.get("saddle")
    if parent is None or set(scene.graph.nodes_geometry)!={
        f"{part}__material_{i}"
        for part,n in (("tire",2),("rim_and_hub",5),
                       ("fork_and_frame",4),("pedals",3),("saddle",2))
        for i in range(n)}:
        raise ValueError("source-verified five-parent/sixteen-child hierarchy required")
    if any(scene.graph.transforms.parents.get(
            f"saddle__material_{i}")!="saddle" for i in range(2)):
        raise ValueError("original saddle material detached from mounting point")
    original_world=np.asarray(scene.graph.get("saddle")[0],dtype=float).copy()
    origin=scene.graph.base_frame
    parent_world=(np.eye(4) if parent==origin
                  else np.asarray(scene.graph.get(parent)[0],dtype=float))
    local=np.linalg.inv(parent_world)@original_world
    before={part:np.asarray(scene.graph.get(part)[0]).copy()
            for part in ("tire","rim_and_hub","fork_and_frame","pedals","saddle")}
    scene.graph.update(frame_to="saddle",frame_from=parent,matrix=local@R)
    try:
        after=np.asarray(scene.graph.get("saddle")[0],dtype=float)
        if (not np.allclose(after[:3,3],original_world[:3,3],
                            atol=1e-9,rtol=0) or
            any(not np.array_equal(np.asarray(scene.graph.get(part)[0]),old)
                for part,old in before.items() if part!="saddle")):
            raise ValueError("temporary saddle lean changed root, wheel, fork or mount")
        yield
    finally:
        scene.graph.update(frame_to="saddle",frame_from=parent,matrix=local)
        for part,old in before.items():
            if not np.allclose(scene.graph.get(part)[0],old,atol=1e-9,rtol=0):
                raise ValueError("2026 saddle local rotation did not restore original GLB pose")
