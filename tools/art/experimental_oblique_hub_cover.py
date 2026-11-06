"""One reversible 2026 hub-cover 3D volume, motivated by a visible 1994 print face.

The original p15 printed image has a large partially visible dark central
casing, but no authenticated full 1994 hub, artist camera, 3D housing depth,
or part-material identity. This code affects ONLY the existing dark source
2026 hub material and never changes game source or shipped model assets.
"""
from __future__ import annotations

from contextlib import contextmanager
import math

CURRENT_2026_SOURCE_GLB_SHA256="634aa0280ec1a8a322c34d1598680e854980f317965b3a848a2cf6b240c50c08"
SOURCE_MATERIAL="rim_and_hub__material_4"
ORIGINAL_SOURCE_VERTEX_COUNT=100
ORIGINAL_SOURCE_FACE_COUNT=196
ORIGINAL_SOURCE_RGBA=(82,94,110,255)
# One fixed authored research hypothesis. These ARE NOT original 1994 measures.
HUB_COVER_HALF_X=.26
HUB_COVER_HALF_Z=.32
HUB_COVER_CHAMFER=.04
HUB_COVER_Y_START=.18
HUB_COVER_Y_END=.38
HUB_COVER_CENTER_X=-.04
HUB_COVER_CENTER_Z=-.05
NEW_HUB_COVER_VERTICES=16
NEW_HUB_COVER_FACES=28

def authored_oblique_hub_cover():
    """Closed chamfered near-side X/Z plate volume in 2026 wheel-local XYZ."""
    x,z,b=HUB_COVER_HALF_X,HUB_COVER_HALF_Z,HUB_COVER_CHAMFER
    points=[(-x+b,-z),(x-b,-z),(x,-z+b),(x,z-b),
            (x-b,z),(-x+b,z),(-x,z-b),(-x,-z+b)]
    vertices=tuple((HUB_COVER_CENTER_X+px,y,HUB_COVER_CENTER_Z+pz)
                   for y in (HUB_COVER_Y_START,HUB_COVER_Y_END)
                   for px,pz in points)
    faces=[]
    for i in range(1,7):
        faces.extend(((0,i,i+1),(8,8+i+1,8+i)))
    for i in range(8):
        j=(i+1)%8
        faces.extend(((i,8+j,j),(i,8+i,8+j)))
    if len(vertices)!=NEW_HUB_COVER_VERTICES or len(faces)!=NEW_HUB_COVER_FACES:
        raise ValueError("single authored 2026 cover polygon triangulation changed")
    return vertices,tuple(faces)

def counterspun_hub_cover_vertices(phase_degrees):
    """Pre-inverse wheel-Y rotation: same cover fixed to axle under wheel spin.

    Authored 2026 geometry only. The wheel parent receives Ry(-phase) per
    actual GLB direct-drive, so undo its parent motion in local cover vertices
    using Ry(+phase). This is an in-memory kinematic *hypothesis*, not a new
    joint or assertion about the 1994 production rig.
    """
    if (type(phase_degrees) not in (int,float) or
            not math.isfinite(phase_degrees) or
            not -360 <= phase_degrees <= 360):
        raise ValueError("finite existing 2026 wheel phase within ±360 required")
    vertices,_=authored_oblique_hub_cover()
    if phase_degrees==0:
        return vertices
    # Direct-drive's parent rotation is Ry(-phase):
    # [ cos,0,-sin; 0,1,0; sin,0,cos ].
    # The exact inverse in its wheel-local frame cancels parent wheel spin.
    theta=math.radians(float(phase_degrees))
    c,q=math.cos(theta),math.sin(theta)
    return tuple((c*x+q*z,y,-q*x+c*z) for x,y,z in vertices)


@contextmanager
def temporary_hub_cover_volume(scene, *, counterspin_degrees=0.):

    """Source-SHA-external-verified real GLB; exact rollback on success/error.

    At zero, reuse the existing 2026 wheel-rotating research shell.
    Counterspin is the single predeclared axle-locked alternative. It changes
    *only* this proposed shell, preserving all authored source material data.
    """
    vertices=counterspun_hub_cover_vertices(counterspin_degrees)
    import numpy as np
    import trimesh
    from tools.art.experimental_direct_drive_phase import PARTS,CHILD_COUNTS

    if not isinstance(scene,trimesh.Scene) or scene.graph.base_frame!="world":
        raise ValueError("real original 2026 GLB scene required")
    expected={f"{parent}__material_{i}" for parent,count in CHILD_COUNTS.items()
              for i in range(count)}
    if (set(scene.graph.nodes_geometry)!=expected
            or len(expected)!=16 or len(PARTS)!=5
            or len(scene.geometry)!=16 or set(scene.geometry)!=expected):
        raise ValueError("single source-authored five-parent/16-material GLB required")
    t,geometry_name=scene.graph.get(SOURCE_MATERIAL)
    if (geometry_name!=SOURCE_MATERIAL or
            scene.graph.transforms.parents.get(SOURCE_MATERIAL)!="rim_and_hub"
            or not np.isfinite(np.asarray(t)).all()):
        raise ValueError("source dark hub part and parent not verified")
    hub=scene.geometry[SOURCE_MATERIAL]
    old_vertices=np.asarray(hub.vertices).copy()
    old_faces=np.asarray(hub.faces).copy()
    old_colors=np.asarray(hub.visual.vertex_colors).copy()
    if (old_vertices.shape!=(ORIGINAL_SOURCE_VERTEX_COUNT,3)
            or old_faces.shape!=(ORIGINAL_SOURCE_FACE_COUNT,3)
            or old_colors.shape!=(ORIGINAL_SOURCE_VERTEX_COUNT,4)
            or not np.isfinite(old_vertices).all()
            or not np.array_equal(old_colors,np.tile(np.array(ORIGINAL_SOURCE_RGBA),
                                                    (ORIGINAL_SOURCE_VERTEX_COUNT,1)))
            or not hub.is_watertight):
        raise ValueError("expected original source dark coaxial 2026 hub cylinder")
    others={k:(np.asarray(mesh.vertices).copy(),np.asarray(mesh.faces).copy(),
               np.asarray(mesh.visual.vertex_colors).copy())
            for k,mesh in scene.geometry.items() if k!=SOURCE_MATERIAL}
    parent_transforms={part:np.asarray(scene.graph.get(part)[0]).copy()
                       for part in PARTS}
    before_nodes=set(scene.graph.nodes)
    before_volume=float(hub.volume)
    _,faces=authored_oblique_hub_cover()
    try:
        hub.vertices=np.vstack([old_vertices,np.asarray(vertices,dtype=float)])
        hub.faces=np.vstack([old_faces,
                             np.asarray(faces,dtype=int)+len(old_vertices)])
        hub.visual.vertex_colors=np.vstack([
            old_colors,np.tile(old_colors[0],(NEW_HUB_COVER_VERTICES,1))])
        if (not hub.is_watertight or hub.volume<=before_volume
                or len(hub.vertices)!=116 or len(hub.faces)!=224
                or not np.array_equal(hub.vertices[:100],old_vertices)
                or not np.array_equal(hub.faces[:196],old_faces)
                or not np.array_equal(hub.visual.vertex_colors[:100],old_colors)):
            raise ValueError("research-only 2026 hub cover violates original geometry invariant")
        yield
    finally:
        hub.vertices=old_vertices
        hub.faces=old_faces
        hub.visual.vertex_colors=old_colors
        if (not np.array_equal(hub.vertices,old_vertices)
                or not np.array_equal(hub.faces,old_faces)
                or not np.array_equal(hub.visual.vertex_colors,old_colors)
                or set(scene.graph.nodes)!=before_nodes
                or any(not np.array_equal(scene.graph.get(p)[0],parent_transforms[p])
                       for p in PARTS)
                or any(not np.array_equal(scene.geometry[n].vertices,old[0])
                       or not np.array_equal(scene.geometry[n].faces,old[1])
                       or not np.array_equal(scene.geometry[n].visual.vertex_colors,old[2])
                       for n,old in others.items())):
            raise ValueError("2026 source dark hub or other material did not rollback")
