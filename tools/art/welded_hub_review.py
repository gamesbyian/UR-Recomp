#!/usr/bin/env python3
"""One physically connected, non-shipping 2026 hub housing study.

Use the *current* 5-parent, 16-material OpenSCAD GLB as an input. Exactly one
material mesh is substituted, without adding a second rig. This does not
recover the lost original 1994 geometry or approve a new character likeness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

PART_MATERIAL_COUNTS = {'tire': 2, 'rim_and_hub': 5, 'fork_and_frame': 4,
                        'pedals': 3, 'saddle': 2}
EXPECTED_NODES = {f'{part}__material_{i}'
                  for part, n in PART_MATERIAL_COUNTS.items() for i in range(n)}
HUB_NODE = 'rim_and_hub__material_4'
RING_COUNT, VERTEX_COUNT, FACE_COUNT = 58, 234, 464
CENTER_X, CENTER_Z = -.04, -.05
HALFWIDTH, HALFHEIGHT, BEVEL = .26, .32, .04
REAR_Y, ANNULUS_Y, FACE_Y = -.21, .18, .38


def _cross(a, b):
    return a[0]*b[1] - a[1]*b[0]


def _ray_polygon(theta, polygon):
    direction = (math.cos(theta), math.sin(theta))
    intersections = []
    for a, b in zip(polygon, polygon[1:] + polygon[:1]):
        edge = (b[0]-a[0], b[1]-a[1])
        det = _cross(direction, edge)
        if abs(det) < 1e-12:
            continue
        r = _cross(a, edge)/det
        t = _cross(a, direction)/det
        if r > 0 and -1e-8 <= t <= 1+1e-8:
            intersections.append(r)
    if not intersections:
        raise ValueError('no valid closed case intersection')
    r = min(intersections)
    return r*direction[0], r*direction[1]


def welded_housing(source_vertices):
    """Weld original 2026 radius-0.086 sleeve to a beveled 2026 case.

    Source cylinder rear and near faces have 50 equal-spaced spokes/angles.
    Eight case corners are included exactly, giving 58 angular sections.
    """
    points = [tuple(map(float, vertex)) for vertex in source_vertices]
    if len(points) != 100 or any(len(p) != 3 or not all(map(math.isfinite,p)) for p in points):
        raise ValueError('expected 100 finite original 2026 sleeve vertices')
    elevations = sorted({round(p[1],5) for p in points})
    if elevations != [-.21,.21]:
        raise ValueError('original 2026 sleeve Y extent changed')
    rear = [p for p in points if abs(p[1]+.21)<1e-5]
    front = [p for p in points if abs(p[1]-.21)<1e-5]
    if len(rear) != 50 or len(front) != 50:
        raise ValueError('original sleeve has wrong angular sections')
    if any(abs(math.hypot(p[0],p[2])-.086) > 2e-5 for p in points):
        raise ValueError('original 2026 source sleeve radius changed')
    circle_radius = sum(math.hypot(p[0],p[2]) for p in rear)/len(rear)
    corners_local = [(-HALFWIDTH+BEVEL,-HALFHEIGHT),
                     (HALFWIDTH-BEVEL,-HALFHEIGHT),
                     (HALFWIDTH,-HALFHEIGHT+BEVEL),
                     (HALFWIDTH,HALFHEIGHT-BEVEL),
                     (HALFWIDTH-BEVEL,HALFHEIGHT),
                     (-HALFWIDTH+BEVEL,HALFHEIGHT),
                     (-HALFWIDTH,-HALFHEIGHT+BEVEL),
                     (-HALFWIDTH+BEVEL,-HALFHEIGHT)]
    polygon = [(CENTER_X+x,CENTER_Z+z) for x,z in corners_local]
    angles = sorted(set(round(math.atan2(p[2],p[0]),12) for p in rear)
                    | set(round(math.atan2(z,x),12) for x,z in polygon))
    if len(angles) != RING_COUNT:
        raise ValueError('2026 source cylinder/case angular registry changed')
    rings = [
        [(circle_radius*math.cos(a),REAR_Y,circle_radius*math.sin(a)) for a in angles],
        [(circle_radius*math.cos(a),ANNULUS_Y,circle_radius*math.sin(a)) for a in angles],
        [(x,ANNULUS_Y,z) for a in angles for x,z in [_ray_polygon(a,polygon)]],
        [(x,FACE_Y,z) for a in angles for x,z in [_ray_polygon(a,polygon)]],
    ]
    vertices=[v for ring in rings for v in ring]
    vertices.extend(((0.,REAR_Y,0.),(CENTER_X,FACE_Y,CENTER_Z)))
    faces=[]
    n=RING_COUNT
    for k in range(3):
        lo,hi=k*n,(k+1)*n
        for i in range(n):
            j=(i+1)%n
            faces.extend(((lo+i,hi+i,lo+j),(hi+i,hi+j,lo+j)))
    for i in range(n):
        j=(i+1)%n
        faces.extend(((4*n,i,j),(4*n+1,3*n+j,3*n+i)))
    return vertices,faces


def check_closed_shell(vertices,faces):
    """Test one nondegenerate connected orientable watertight genus-0 mesh."""
    if len(vertices)!=VERTEX_COUNT or len(faces)!=FACE_COUNT:
        raise ValueError('expected one 234-vertex 464-face 2026 housing')
    edge_uses={}
    adjacent={i:set() for i in range(len(vertices))}
    six_volume=0.
    for f in faces:
        if len(f)!=3 or len(set(f))!=3 or any(type(k)!=int or not 0<=k<len(vertices) for k in f):
            raise ValueError('invalid housing triangle')
        a,b,c=[vertices[k] for k in f]
        u=[b[k]-a[k] for k in range(3)];v=[c[k]-a[k] for k in range(3)]
        cross=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
        if math.sqrt(sum(q*q for q in cross))<1e-12:
            raise ValueError('degenerate housing triangle')
        six_volume+=(a[0]*(b[1]*c[2]-b[2]*c[1])+
                     a[1]*(b[2]*c[0]-b[0]*c[2])+
                     a[2]*(b[0]*c[1]-b[1]*c[0]))
        for i,j in ((f[0],f[1]),(f[1],f[2]),(f[2],f[0])):
            edge_uses.setdefault((min(i,j),max(i,j)),[]).append(1 if i<j else -1)
            adjacent[i].add(j);adjacent[j].add(i)
    if len(edge_uses)!=len(vertices)+len(faces)-2 or any(sorted(v)!=[-1,1] for v in edge_uses.values()):
        raise ValueError('non-manifold or inconsistent winding')
    seen={0};front=[0]
    while front:
        x=front.pop()
        for y in adjacent[x]-seen:
            seen.add(y);front.append(y)
    if len(seen)!=len(vertices):
        raise ValueError('disconnected shells')
    if not math.isfinite(six_volume) or six_volume<=0:
        raise ValueError('invalid outward shell volume')
    return six_volume/6.


def make_preview(source_glb:Path,out_glb:Path):
    """Preserve the five-part source GLB and replace only its dark hub sleeve."""
    import numpy as np
    import trimesh
    if out_glb.resolve()==source_glb.resolve():
        raise ValueError('preview cannot overwrite source GLB')
    scene=trimesh.load(source_glb,force='scene',process=False)
    if (not isinstance(scene,trimesh.Scene) or scene.graph.base_frame!='world'
        or set(scene.geometry)!=EXPECTED_NODES
        or set(scene.graph.nodes_geometry)!=EXPECTED_NODES
        or scene.graph.transforms.parents.get(HUB_NODE)!='rim_and_hub'):
        raise ValueError('expected canonical five-parent, sixteen-material 2026 GLB')
    original=scene.geometry[HUB_NODE]
    if (len(original.vertices)!=100 or len(original.faces)!=196
        or not original.is_watertight):
        raise ValueError('2026 source dark sleeve topology changed')
    rgba=np.asarray(original.visual.vertex_colors)
    if rgba.shape!=(100,4) or not np.array_equal(rgba,np.tile(rgba[0],(100,1))):
        raise ValueError('2026 source dark sleeve material inconsistent')
    vertices,faces=welded_housing(original.vertices)
    volume=check_closed_shell(vertices,faces)
    mesh=trimesh.Trimesh(vertices=vertices,faces=faces,process=False)
    if max(math.hypot(x,z) for x,y,z in vertices)>0.5:
        raise ValueError('study casing exceeds inner-rim clearance radius')
    if (not mesh.is_watertight or not mesh.is_winding_consistent
        or mesh.euler_number!=2 or abs(mesh.volume-volume)>1e-8):
        raise ValueError('rendered housing failed connected-watertight contract')
    mesh.visual.vertex_colors=np.tile(rgba[0],(len(mesh.vertices),1))
    scene.geometry[HUB_NODE]=mesh
    encoded=scene.export(file_type='glb')
    out_glb.parent.mkdir(parents=True,exist_ok=True)
    if out_glb.exists():
        raise FileExistsError('would overwrite existing preview')
    out_glb.write_bytes(encoded)
    check=trimesh.load(out_glb,force='scene',process=False)
    if set(check.geometry)!=EXPECTED_NODES or not check.geometry[HUB_NODE].is_watertight:
        out_glb.unlink(missing_ok=True)
        raise ValueError('exported preview lost original scene or manifold')
    source_check=trimesh.load(source_glb,force='scene',process=False)
    for name in EXPECTED_NODES-{HUB_NODE}:
        a=source_check.geometry[name];b=check.geometry[name]
        if (not np.array_equal(a.vertices,b.vertices) or
            not np.array_equal(a.faces,b.faces) or
            not np.array_equal(a.visual.vertex_colors,b.visual.vertex_colors)):
            out_glb.unlink(missing_ok=True)
            raise ValueError('other source material geometry or paint changed: '+name)
    for name in PART_MATERIAL_COUNTS:
        if not np.array_equal(source_check.graph.get(name)[0],check.graph.get(name)[0]):
            out_glb.unlink(missing_ok=True)
            raise ValueError('source-authored assembly transform changed: '+name)
    return {'schema':'UR-ART4K-AUTHORED-WELDED-HUB-REVIEW/1',
            'baseline_glb_sha256':hashlib.sha256(source_glb.read_bytes()).hexdigest(),
            'review_glb_sha256':hashlib.sha256(encoded).hexdigest(),
            'source_2026_nonhub_nodes_unchanged':True,
            'unapproved_likeness':True,
            'original_1994_geometry_recovered':False,
            'hub_vertices':len(vertices),'hub_faces':len(faces),'volume':volume}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('output',type=Path)
    a=parser.parse_args()
    print(json.dumps(make_preview(a.source,a.output),indent=2))


if __name__=='__main__':main()
