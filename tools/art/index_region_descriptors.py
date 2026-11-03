#!/usr/bin/env python3
"""ROM-free 64px source 4bpp topology, without asserting any original 3D part labels."""
from __future__ import annotations
from collections import defaultdict, deque
import hashlib
import math

WIDTH = HEIGHT = 64
SCHEMA = "UR-ART4K-SOURCE-INDEX-REGIONS/1"

def sha(data):
    return hashlib.sha256(data).hexdigest()

def neighbours(q):
    x, y = q % 64, q // 64
    if x: yield q - 1
    if x < 63: yield q + 1
    if y: yield q - 64
    if y < 63: yield q + 64

def describe_index_regions(indices: bytes, touched: bytes, centres: list) -> dict:
    """Make complete disjoint topology of 15 indices, written zero and untouched zero.

    All tied raster wheel-centres remain separate hypotheses. Exact 4-neighbour
    edges and components, not RGB threshold masks or semantic part labels.
    """
    if (not isinstance(indices, bytes) or not isinstance(touched, bytes) or
            len(indices) != 4096 or len(touched) != 4096 or
            any(x > 15 for x in indices) or any(t not in (0, 1) for t in touched) or
            any(i and not t for i, t in zip(indices, touched))):
        raise ValueError("invalid authenticated 64x64 4bpp/visited planes")
    if (not isinstance(centres, list) or not centres or
            any(not isinstance(c, (list,tuple)) or len(c) != 3 or
                any(type(v) is not int for v in c) or
                not (0 <= c[0] < 64 and 0 <= c[1] < 64 and c[2] == 7)
                for c in centres)):
        raise ValueError("invalid tied seven-pixel source wheel centres")
    labels = [i if i else (16 if t else 17) for i,t in zip(indices,touched)]
    groups = defaultdict(list)
    for q,k in enumerate(labels): groups[k].append(q)
    regions = {}
    for k in sorted(groups):
        pixels = groups[k]
        x = [q % 64 for q in pixels]
        y = [q // 64 for q in pixels]
        n = len(pixels)
        mx, my = sum(x)/n, sum(y)/n
        cxx = sum((v-mx)**2 for v in x)/n
        cyy = sum((v-my)**2 for v in y)/n
        cxy = sum((a-mx)*(b-my) for a,b in zip(x,y))/n
        remaining = set(pixels)
        components = []
        while remaining:
            root = min(remaining)
            remaining.remove(root)
            queue = deque([root]); area = 0
            while queue:
                q = queue.popleft(); area += 1
                for other in neighbours(q):
                    if other in remaining:
                        remaining.remove(other);queue.append(other)
            components.append(area)
        neighbours_by_label = defaultdict(int)
        perimeter = 0
        for q in pixels:
            for other in neighbours(q):
                if labels[other] != k:
                    neighbours_by_label[str(labels[other])] += 1
                    perimeter += 1
            perimeter += 4 - sum(1 for _ in neighbours(q))
        wheel = []
        for cx,cy,r in centres:
            dist = [(a-cx)**2+(b-cy)**2 for a,b in zip(x,y)]
            wheel.append({
                "centre_xy_radius": [cx,cy,r],
                "in_source_disc": sum(d <= r*r for d in dist),
                "radial_squared_bins": [sum(lo <= d < hi for d in dist)
                                        for lo,hi in ((0,9),(9,25),(25,49),(49,10**9))]
            })
        regions[str(k)] = {
            "original_palette_index": k if k <= 15 else 0,
            "region_kind": ("opaque_index" if k <= 15 else
                            "explicit_transparent_zero" if k == 16 else "unwritten_background"),
            "pixels": n,
            "bounds_xyxy": [min(x),min(y),max(x),max(y)],
            "centroid_xy": [mx,my],
            "covariance_xx_xy_yy": [cxx,cxy,cyy],
            "principal_axis_undirected_degrees":
                (math.degrees(.5*math.atan2(2*cxy,cxx-cyy)) if n > 1 else None),
            "component_areas": sorted(components,reverse=True),
            "four_connected_perimeter": perimeter,
            "adjacency_edges": dict(sorted(neighbours_by_label.items(),key=lambda a:int(a[0]))),
            "source_wheel_centre_hypotheses": wheel,
        }
    if sum(v["pixels"] for v in regions.values()) != 4096:
        raise AssertionError("index/visited/background partition incomplete")
    return {"schema":SCHEMA,"source_index_sha256":sha(indices),
            "source_tile_written_sha256":sha(touched),
            "region_pixels_partition_is_exhaustive":True,
            "original_1994_3d_part_identity_verified":False,
            "original_1994_camera_verified":False,"regions":regions}
