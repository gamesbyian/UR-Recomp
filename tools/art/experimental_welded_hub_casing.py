"""Experimental ONE connected 2026 dark axle sleeve + beveled housing.

The official 1994 printed p15 dark patch is a partly occluded *2D* reference.
This single-manifold 2026 mesh is a topology/rigging improvement of the
unapproved modern proposal, NOT recovered original production 3D geometry.
Never mutate another source part or claim original 1994 attachment.
"""
from __future__ import annotations

from contextlib import contextmanager
import math

from tools.art.experimental_oblique_hub_cover import (
    ORIGINAL_SOURCE_RGBA, SOURCE_MATERIAL,
    ORIGINAL_SOURCE_VERTEX_COUNT, ORIGINAL_SOURCE_FACE_COUNT,
    HUB_COVER_Y_START, HUB_COVER_Y_END,
    HUB_COVER_CENTER_X, HUB_COVER_CENTER_Z,
    authored_oblique_hub_cover,
)

SECTION_COUNT=50
RING_COUNT=58   # 50 source cylinder azimuths plus 8 original polygon corners
WELDED_VERTICES=4*RING_COUNT+2
WELDED_FACES=8*RING_COUNT
SINGLE_SOLID_IS_ORIGINAL_1994_GEOMETRY=False


def cross2(a,b):
    return a[0]*b[1]-a[1]*b[0]


def ray_convex_outline(theta,polygon):
    """First positive, finite ray hit on the eight-sided physical outline."""
    d=(math.cos(theta),math.sin(theta))
    roots=[]
    for a,b in zip(polygon,polygon[1:]+polygon[:1]):
        edge=(b[0]-a[0],b[1]-a[1])
        det=cross2(d,edge)
        if abs(det)<1e-12:
            continue
        distance=cross2(a,edge)/det
        t=cross2(a,d)/det
        if distance>0 and -1e-8<=t<=1+1e-8:
            roots.append(distance)
    if not roots:
        raise ValueError("authored 2026 beveled housing not star-shaped around source axle")
    r=min(roots)
    return (r*d[0],r*d[1])


def welded_source_hub_casing(source_vertices):
    """Produce a single closed genus-zero 2026 shell, from exact 100-vertex sleeve.

    The source cylinder ends at Y ±0.21; the proposed plate begins at Y +0.18.
    Instead of two coincident closed volumes, cap the original axle at -0.21,
    bridge its near-side circle at +0.18 to the beveled polygon through one
    planar annulus, and close the polygon at +0.38. Every original exterior
    face is reproduced analytically to float32 precision, except the hidden
    0.03 model-unit interval inside the original overlapping cover.
    """
    if len(source_vertices)!=ORIGINAL_SOURCE_VERTEX_COUNT:
        raise ValueError("exact original 2026 axle sleeve 100 vertices required")
    points=[]
    for p in source_vertices:
        if len(p)!=3 or not all(type(float(v)) is float and math.isfinite(float(v)) for v in p):
            raise ValueError("finite original 2026 cylindrical vertex required")
        points.append(tuple(map(float,p)))
    levels=sorted({round(p[1],5) for p in points})
    if levels!=[-.21,.21]:
        raise ValueError("original 2026 source axle y bounds changed")
    lower=[p for p in points if abs(p[1]-levels[0])<1e-5]
    upper=[p for p in points if abs(p[1]-levels[1])<1e-5]
    if len(lower)!=SECTION_COUNT or len(upper)!=SECTION_COUNT:
        raise ValueError("exact source 50-section cylinder topology required")
    radii=[math.hypot(p[0],p[2]) for p in lower]
    if any(abs(r-.086)>2e-5 for r in radii):
        raise ValueError("original 2026 coaxial cylinder radius changed")
    radius=sum(radii)/len(radii)
    cover,_=authored_oblique_hub_cover()
    polygon=[(p[0],p[2]) for p in cover[:8]]
    angles=sorted(set(round(math.atan2(p[2],p[0]),12) for p in lower)
                  |set(round(math.atan2(z,x),12) for x,z in polygon))
    if len(angles)!=RING_COUNT:
        raise ValueError("source cylinder or authored housing corner angular registry changed")
    rings=[
        [(radius*math.cos(a),levels[0],radius*math.sin(a)) for a in angles],
        [(radius*math.cos(a),HUB_COVER_Y_START,radius*math.sin(a)) for a in angles],
        [(lambda xz:(xz[0],HUB_COVER_Y_START,xz[1]))(
            ray_convex_outline(a,polygon)) for a in angles],
        [(lambda xz:(xz[0],HUB_COVER_Y_END,xz[1]))(
            ray_convex_outline(a,polygon)) for a in angles],
    ]
    vertices=[p for ring in rings for p in ring]
    vertices.extend([(0.,levels[0],0.),(HUB_COVER_CENTER_X,HUB_COVER_Y_END,HUB_COVER_CENTER_Z)])
    faces=[]
    n=RING_COUNT
    # Cylinder side, rear annulus and exterior cover walls share weld edges.
    # Increasing x/z azimuth has outward normals for the vertical walls.
    for band in range(3):
        below,above=band*n,(band+1)*n
        for i in range(n):
            j=(i+1)%n
            faces.extend([(below+i,above+i,below+j),(above+i,above+j,below+j)])
    # Interior cap vertices avoid zero-area fan triangles on octagon edges.
    for i in range(n):
        j=(i+1)%n
        faces.extend([(4*n,i,j),(4*n+1,3*n+j,3*n+i)])
    if len(vertices)!=WELDED_VERTICES or len(faces)!=WELDED_FACES:
        raise ValueError("one source 2026 watertight topological casing changed")
    return tuple(vertices),tuple(faces)


def assert_closed_positive_one_solid(vertices,faces):
    """Dependency-free genuine geometry check, not an image silhouette proxy."""
    n=len(vertices)
    if n!=WELDED_VERTICES or len(faces)!=WELDED_FACES:
        raise ValueError("one connected 2026 mesh with frozen vertex/face count required")
    edge_map={}
    connections={i:set() for i in range(n)}
    six_volume=0.
    for face in faces:
        if len(face)!=3 or len(set(face))!=3 or any(type(k) is not int or k<0 or k>=n for k in face):
            raise ValueError("invalid 2026 housing triangle")
        a,b,c=[vertices[k] for k in face]
        u=[b[k]-a[k] for k in range(3)]
        v=[c[k]-a[k] for k in range(3)]
        cross=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
        if math.hypot(*cross)<1e-12:
            raise ValueError("degenerate 2026 physical hub housing triangle")
        six_volume+=a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0])
        for i,j in ((face[0],face[1]),(face[1],face[2]),(face[2],face[0])):
            key=(min(i,j),max(i,j))
            edge_map.setdefault(key,[]).append(1 if i<j else -1)
            connections[i].add(j);connections[j].add(i)
    if len(edge_map)!=n+len(faces)-2 or any(v!=[1,-1] and v!=[-1,1] for v in edge_map.values()):
        raise ValueError("expected one consistently oriented closed 2-manifold genus-zero shell")
    visited={0};front=[0]
    while front:
        i=front.pop()
        for j in connections[i]-visited:
            visited.add(j);front.append(j)
    if len(visited)!=n:
        raise ValueError("disconnected multiple shells are forbidden")
    if six_volume<=0 or not math.isfinite(six_volume):
        raise ValueError("invalid signed volume for physically welded source casing")
    return six_volume/6.


@contextmanager
def temporary_welded_source_hub_casing(scene):
    """Keep all five parent transforms and sixteen source materials untouched."""
    import numpy as np
    import trimesh
    from tools.art.experimental_direct_drive_phase import PARTS,CHILD_COUNTS

    if not isinstance(scene,trimesh.Scene) or scene.graph.base_frame!="world":
        raise ValueError("original five-parent 2026 GLB scene required")
    expected={f"{parent}__material_{i}" for parent,count in CHILD_COUNTS.items()
              for i in range(count)}
    if (len(PARTS)!=5 or len(expected)!=16 or
            set(scene.geometry)!=expected or
            set(scene.graph.nodes_geometry)!=expected or
            scene.graph.transforms.parents.get(SOURCE_MATERIAL)!="rim_and_hub"):
        raise ValueError("original 2026 five-part sixteen-material GLB identity changed")
    hub=scene.geometry[SOURCE_MATERIAL]
    original_vertices=np.asarray(hub.vertices).copy()
    original_faces=np.asarray(hub.faces).copy()
    original_colours=np.asarray(hub.visual.vertex_colors).copy()
    if (original_vertices.shape!=(100,3) or original_faces.shape!=(196,3)
            or original_colours.shape!=(100,4) or
            not np.array_equal(original_colours,
                               np.tile(np.asarray(ORIGINAL_SOURCE_RGBA),(100,1))) or
            not hub.is_watertight):
        raise ValueError("real original 2026 hub sleeve is not verified")
    others={name:(np.asarray(mesh.vertices).copy(),np.asarray(mesh.faces).copy(),
                  np.asarray(mesh.visual.vertex_colors).copy())
            for name,mesh in scene.geometry.items() if name!=SOURCE_MATERIAL}
    parent_matrices={part:np.asarray(scene.graph.get(part)[0]).copy() for part in PARTS}
    nodes=set(scene.graph.nodes)
    welded,faces=welded_source_hub_casing(original_vertices)
    volume=assert_closed_positive_one_solid(welded,faces)
    try:
        hub.vertices=np.asarray(welded,dtype=float)
        hub.faces=np.asarray(faces,dtype=int)
        hub.visual.vertex_colors=np.tile(original_colours[0],(len(welded),1))
        if (not hub.is_watertight or not hub.is_winding_consistent or
                hub.euler_number!=2 or
                not math.isclose(hub.volume,volume,rel_tol=1e-8,abs_tol=1e-10)):
            raise ValueError("actual original 2026 source GLB welded casing not one watertight body")
        yield
    finally:
        hub.vertices=original_vertices
        hub.faces=original_faces
        hub.visual.vertex_colors=original_colours
        if (not np.array_equal(hub.vertices,original_vertices) or
                not np.array_equal(hub.faces,original_faces) or
                not np.array_equal(hub.visual.vertex_colors,original_colours) or
                set(scene.graph.nodes)!=nodes or
                any(not np.array_equal(scene.graph.get(n)[0],matrix)
                        for n,matrix in parent_matrices.items()) or
                any(not np.array_equal(scene.geometry[n].vertices,saved[0])
                        or not np.array_equal(scene.geometry[n].faces,saved[1])
                        or not np.array_equal(scene.geometry[n].visual.vertex_colors,saved[2])
                        for n,saved in others.items())):
            raise ValueError("original source 2026 GLB part geometry or rig not restored")
