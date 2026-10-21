#!/usr/bin/env python3
"""Measure Original-raster hero gesture continuity, without creating motion.

Consumes already-source-validated original RGBA frames in chronological
registered order. Every measurement is descriptive: even byte-identical end
poses cannot qualify a cyclic menu idle, source timestamp or visual approval.
No ROM loading, game clock, SDL renderer, guest state or authored HD art.
"""
from __future__ import annotations

import hashlib
from typing import Sequence


def _validate_frame(frame: bytes, width: int, height: int) -> None:
    if width <= 0 or height <= 0 or width > 1024 or height > 1024:
        raise ValueError("invalid source-raster dimensions")
    if not isinstance(frame, bytes) or len(frame) != width * height * 4:
        raise ValueError("incomplete original RGBA frame")
    if not any(frame[offset] for offset in range(3, len(frame), 4)):
        raise ValueError("original racer frame contains no visible pixels")


def _contact_x2_y2(frame: bytes, width: int, height: int) -> list[int]:
    # Same half-pixel convention as the Original stock sprite compositor.
    for y in range(height - 1, -1, -1):
        xs = [x for x in range(width)
              if frame[4 * (y * width + x) + 3] > 0]
        if xs:
            return [xs[0] + xs[-1], y * 2]
    raise ValueError("original racer has no alpha contact")


def compare_visible_rasters(before: bytes, after: bytes, *,
                            width: int = 64, height: int = 64) -> dict:
    """Pair metrics, preserving alpha semantics and visible-only differences.

    Changing invisible RGB in transparent pixels is irrelevant to presentation.
    Alpha overlap/union uses nonzero alpha (not premultiplication assumptions).
    All fractions are exact integers in basis points for stable JSON/evidence.
    """
    _validate_frame(before, width, height)
    _validate_frame(after, width, height)
    changed = alpha_changed = opaque_intersection = opaque_union = 0
    changed_min_x = width
    changed_min_y = height
    changed_max_x = changed_max_y = -1
    for index in range(width * height):
        pos = index * 4
        old = before[pos:pos + 4]
        new = after[pos:pos + 4]
        old_visible = old[3] != 0
        new_visible = new[3] != 0
        if old_visible and new_visible:
            opaque_intersection += 1
        if old_visible or new_visible:
            opaque_union += 1
        if old[3] != new[3]:
            alpha_changed += 1
        if not (old_visible or new_visible):
            continue
        if old != new:
            changed += 1
            x = index % width
            y = index // width
            changed_min_x = min(changed_min_x, x)
            changed_min_y = min(changed_min_y, y)
            changed_max_x = max(changed_max_x, x)
            changed_max_y = max(changed_max_y, y)

    a = _contact_x2_y2(before, width, height)
    b = _contact_x2_y2(after, width, height)
    return {
        "visible_changed_pixels": changed,
        "alpha_changed_pixels": alpha_changed,
        "opaque_alpha_intersection": opaque_intersection,
        "opaque_alpha_union": opaque_union,
        "alpha_iou_basis_points": (opaque_intersection * 10000 // opaque_union),
        "change_bbox_xyxy": (
            [changed_min_x, changed_min_y, changed_max_x, changed_max_y]
            if changed else None),
        "contact_shift_x2_y2": [b[0] - a[0], b[1] - a[1]],
        "visually_static": changed == 0,
    }


def analyze_original_hero_temporal_clip(
    frames: Sequence[bytes], registered_guest_frames: Sequence[int], *,
    width: int = 64, height: int = 64
) -> dict:
    """Describe registered chronological frames, and refuse loop certification."""
    if (not frames or len(frames) != len(registered_guest_frames) or
            len(frames) > 1024):
        raise ValueError("missing or mismatched original-raster frame sequence")
    if len(frames) < 2:
        raise ValueError("a temporal assessment needs at least two frames")
    if (any(type(n) is not int or n < 0 for n in registered_guest_frames) or
            list(registered_guest_frames) !=
            list(range(registered_guest_frames[0],
                       registered_guest_frames[0] + len(frames)))):
        raise ValueError("registered guest-frame labels must be consecutive")
    for frame in frames:
        _validate_frame(frame, width, height)
    edges = []
    for index in range(1, len(frames)):
        measurement = compare_visible_rasters(
            frames[index - 1], frames[index], width=width, height=height)
        edges.append({
            "from_registered_guest_frame": registered_guest_frames[index - 1],
            "to_registered_guest_frame": registered_guest_frames[index],
            **measurement
        })
    loop_measurement = compare_visible_rasters(
        frames[-1], frames[0], width=width, height=height)
    # Edge always describes the *counterfactual* jump from the last pose to
    # the first. It is never added to chronological edges or judged safe.
    unique_hashes = {
        hashlib.sha256(frame).hexdigest() for frame in frames
    }
    max_real_change = max(e["visible_changed_pixels"] for e in edges)
    return {
        "schema_version": 1,
        "frame_count": len(frames),
        "first_registered_guest_frame": registered_guest_frames[0],
        "last_registered_guest_frame": registered_guest_frames[-1],
        "distinct_rgba_frames": len(unique_hashes),
        "observed_static_edges": sum(e["visually_static"] for e in edges),
        "observed_dynamic_edges": sum(not e["visually_static"] for e in edges),
        "max_observed_visible_change_pixels": max_real_change,
        "observed_max_abs_contact_shift_x2": max(
            abs(e["contact_shift_x2_y2"][0]) for e in edges),
        "observed_max_abs_contact_shift_y2": max(
            abs(e["contact_shift_x2_y2"][1]) for e in edges),
        "consecutive_registered_edges": edges,
        "counterfactual_last_to_first_edge": {
            "from_registered_guest_frame": registered_guest_frames[-1],
            "to_registered_guest_frame": registered_guest_frames[0],
            **loop_measurement,
            "is_observed_chronological_edge": False,
        },
        "loop_certified": False,
        "source_guest_timing_independently_certified": False,
        "artistic_approval": "pending",
        "metric_interpretation": (
            "Source-pose visual deltas only. Original raster fidelity, "
            "native final-pixel output and loop/motion aesthetics need "
            "independent acceptance. A still/zero-distance seam is no proof "
            "that cycling these original race poses is source-faithful."
        ),
    }
