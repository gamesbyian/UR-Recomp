#!/usr/bin/env python3
"""Common camera-frame crop for authoring readable 32/64px UNAPPROVED rig previews.

Use the union of genuine fixed-camera silhouettes once for the entire pose
family. Never fit per frame, alter the underlying OpenSCAD camera, introduce
unmeasured guest sprite pivots, or claim original-source 3D likeness.
"""
from __future__ import annotations
from math import ceil
from typing import Iterable


def common_pose_crop(bounds: Iterable[list[int]], width: int, height: int,
                     margin_fraction: float = 0.08) -> tuple[int, int, int, int]:
    """Square fixed crop containing ALL observed silhouettes, constant per family.

    Bounds are Pillow-style [left, top, right, bottom], right/bottom exclusive.
    Geometry is intentionally constrained to the original full rendered frame.
    Missing/invalid extrema fail closed instead of zooming into guessed art.
    """
    if type(width) is not int or type(height) is not int or width < 16 or height < 16:
        raise ValueError("review raster must have a positive measured shape")
    if type(margin_fraction) is not float or not 0.0 <= margin_fraction <= 0.25:
        raise ValueError("invalid common framing margin")
    measured = list(bounds)
    if not measured:
        raise ValueError("no observed silhouette family")
    for b in measured:
        if not isinstance(b, (list, tuple)) or len(b) != 4 or any(type(x) is not int for x in b):
            raise ValueError("silhouette bbox is not four exact integers")
        left, top, right, bottom = b
        if not (0 <= left < right <= width and 0 <= top < bottom <= height):
            raise ValueError("silhouette bbox is clipped or outside source frame")
    x0 = min(b[0] for b in measured)
    y0 = min(b[1] for b in measured)
    x1 = max(b[2] for b in measured)
    y1 = max(b[3] for b in measured)
    size = max(x1 - x0, y1 - y0)
    size += 2 * ceil(size * margin_fraction)
    if size > min(width, height):
        raise ValueError("common crop would exceed original fixed camera")
    cx = (x0 + x1) // 2
    cy = (y0 + y1) // 2
    left = min(max(0, cx - size // 2), width - size)
    top = min(max(0, cy - size // 2), height - size)
    crop = (left, top, left + size, top + size)
    if any(not (left <= b[0] and top <= b[1] and b[2] <= crop[2] and b[3] <= crop[3])
           for b in measured):
        raise ValueError("shared fixed-camera crop cannot contain every pose")
    return crop
