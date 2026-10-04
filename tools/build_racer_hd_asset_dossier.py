#!/usr/bin/env python3
"""Build an approval-oriented evidence dossier for a registered Racer HD window.

The dossier is derived only from authoritative/reproducible project evidence:
the canonical ROM, the composition-aware replacement registry, and an exact
semantic trace report produced by summarize_racer_semantic_trace.py.

It does not approve art. It packages the evidence needed to review art without
guessing animation order, geometry, composition identity, or source pixels.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from prototype_racer_hd_replacement import (
    W,
    H,
    alpha_bounds,
    alpha_contact_anchor_x2_y2,
    build_remastered_candidate,
    build_stock_rgba,
    encode_png_rgba,
    nearest_rgba,
    object_flip_pivot_x2_y2,
)


RESOLVED_VISUAL_LANGUAGE = {
    "geometry_basis": (
        "smooth high-resolution form consistent with the developer-confirmed "
        "3D source-render pipeline; do not preserve SNES pixel stair-steps as geometry"
    ),
    "lighting_space": (
        "baked/object-local per representation and mirrored by the same runtime "
        "H/V transform as the racer raster"
    ),
    "dynamic_world_lighting": (
        "not part of the faithful Remastered racer baseline"
    ),
    "edge_treatment": (
        "retain the stock dark silhouette/value hierarchy on smooth contours; "
        "do not add a uniform new cartoon outline"
    ),
    "material_classes": {
        "tire": "dark rubber with broad stable highlights, never chrome-like",
        "saddle": "dark vinyl/leather-like surface with restrained broad highlights",
        "colored_frame": "glossy colored painted/anodized metal-like surface",
        "neutral_hardware": "bright neutral metallic hub/fork/pedal hardware",
    },
    "cast_shadow_policy": (
        "do not add a new host-authored ground/drop shadow to the faithful "
        "Remastered racer baseline"
    ),
    "micro_detail_policy": (
        "source assets may contain mechanically plausible detail, but details that "
        "alias, flicker, alter the recovered silhouette, or disappear incoherently "
        "at normal and split-screen gameplay scale must be suppressed"
    ),
    "specular_highlight_policy": (
        "use broad baked highlights and the stock palette hierarchy as the relative "
        "contrast reference: the brightest colored-frame tone is a restrained "
        "minority accent above the dominant body tone; neutral metal may reach much "
        "brighter values; do not add point sparkle/star glints"
    ),
}

PENDING_ART_DECISIONS = []

FIRST_AUTHORED_REPRESENTATION_ID = "ordinary-racer-0x0541-p1-sync-reference"
SECOND_AUTHORED_REPRESENTATION_ID = "ordinary-racer-0x0541-p1-companion-0D2D-reference"
THIRD_AUTHORED_REPRESENTATION_ID = "ordinary-racer-0x0540-p1-predecessor-reference"
FOURTH_AUTHORED_REPRESENTATION_ID = (
    "ordinary-racer-0x0540-p1-companion-0D2C-with-p2-0542-reference"
)
FIFTH_AUTHORED_REPRESENTATION_ID = (
    "ordinary-racer-0x057f-p1-with-p2-0542-companion-0D4A-reference"
)
SIXTH_AUTHORED_REPRESENTATION_ID = (
    "ordinary-racer-0x057E-p1-with-p2-0543-reference"
)
SEVENTH_AUTHORED_REPRESENTATION_ID = (
    "ordinary-racer-0x057D-p1-adjacent-reference"
)
EIGHTH_AUTHORED_REPRESENTATION_ID = (
    "ordinary-racer-0x0540-p2-sync-reference"
)
NINTH_AUTHORED_REPRESENTATION_ID = (
    "ordinary-racer-0x0540-p2-with-p1-companion-0D2D-reference"
)
TENTH_AUTHORED_REPRESENTATION_ID = (
    "ordinary-racer-0x0541-p2-predecessor-reference"
)
ELEVENTH_AUTHORED_REPRESENTATION_ID = (
    "ordinary-racer-0x0542-p2-with-p1-companion-0D2C-reference"
)
TWELFTH_AUTHORED_REPRESENTATION_ID = (
    "ordinary-racer-0x0542-p2-with-p1-057F-companion-0D4A-reference"
)
THIRTEENTH_AUTHORED_REPRESENTATION_ID = (
    "ordinary-racer-0x0543-p2-adjacent-reference"
)
FOURTEENTH_AUTHORED_REPRESENTATION_ID = (
    "ordinary-racer-0x0543-p2-with-p1-057E-reference"
)


def _rgba32(r: int, g: int, b: int, a: int = 255) -> bytes:
    return bytes((r, g, b, a))


def authored_red_frame_rgba(x: int, y: int) -> bytes:
    light = (255 - x) + (255 - y)
    if light > 335:
        return _rgba32(232, 83, 83)
    if light > 300:
        return _rgba32(201, 52, 52)
    if light > 260:
        return _rgba32(163, 37, 37)
    return _rgba32(120, 24, 24)


def authored_blue_frame_rgba(x: int, y: int) -> bytes:
    light = (255 - x) + (255 - y)
    if light > 335:
        return _rgba32(83, 115, 232)
    if light > 300:
        return _rgba32(52, 77, 201)
    if light > 260:
        return _rgba32(37, 58, 163)
    return _rgba32(24, 40, 120)


def authored_metal_rgba(x: int, y: int) -> bytes:
    light = (255 - x) + (255 - y)
    if light > 305:
        return _rgba32(246, 244, 242)
    if light > 275:
        return _rgba32(217, 213, 208)
    return _rgba32(159, 153, 142)


def authored_segment_contains(
    x: int,
    y: int,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    half_width: int,
) -> bool:
    """Integer-only filled segment shared with the native authored sampler."""
    dx = x2 - x1
    dy = y2 - y1
    px = x - x1
    py = y - y1
    length2 = dx * dx + dy * dy
    dot = px * dx + py * dy
    if dot < 0 or dot > length2:
        return False
    cross = dx * py - dy * px
    return cross * cross <= half_width * half_width * length2

def authored_saddle_contains(
    x: int,
    y: int,
    seat_cx: int,
    seat_cy: int,
    radius_x: int,
    radius_y: int,
    min_y: int,
    max_y: int,
) -> bool:
    if y < min_y or y > max_y:
        return False
    dx = x - seat_cx
    dy = y - seat_cy
    lhs = (
        dx * dx * radius_y * radius_y
        + dy * dy * radius_x * radius_x
    )
    rhs = radius_x * radius_x * radius_y * radius_y
    if lhs > rhs:
        return False
    nose_start = radius_x // 3
    if dx > nose_start:
        run = radius_x - nose_start
        remaining = radius_x - dx
        nose_half_height = (
            radius_y // 4
            + (remaining * radius_y * 3) // (4 * run)
        )
        if dy < -nose_half_height or dy > nose_half_height:
            return False
    return True


def authored_rim_hardware_rgba(
    x: int,
    y: int,
    wheel_cx: int,
    wheel_cy: int,
) -> bytes:
    dx = x - wheel_cx
    dy = y - wheel_cy
    directional = (wheel_cx - x) + (wheel_cy - y)
    facet = (dx * 3 - dy * 2) & 0x0F
    if directional > 24 and facet < 9:
        return _rgba32(249, 248, 247)
    if directional > -4:
        return _rgba32(224, 221, 216)
    return _rgba32(156, 150, 138)


def authored_rubber_rgba(
    x: int,
    y: int,
    wheel_cx: int,
    wheel_cy: int,
) -> bytes:
    dx = x - wheel_cx
    dy = y - wheel_cy
    directional = -(dx + dy)
    if directional > 34:
        return _rgba32(64, 60, 52)
    if directional < -36:
        return _rgba32(29, 26, 21)
    return _rgba32(42, 39, 32)


def authored_saddle_rgba(
    x: int,
    y: int,
    seat_cx: int,
    seat_cy: int,
) -> bytes:
    dx = x - seat_cx
    dy = y - seat_cy
    directional = -(dx + dy)
    underside = dy >= 6
    if directional > 28 and not underside:
        return _rgba32(82, 77, 69)
    if underside:
        return _rgba32(33, 30, 24)
    return _rgba32(49, 45, 38)


def authored_wheel_spokes(
    x: int,
    y: int,
    wheel_cx: int,
    wheel_cy: int,
) -> bool:
    return (
        authored_segment_contains(
            x, y, wheel_cx - 22, wheel_cy, wheel_cx + 22, wheel_cy, 1
        )
        or authored_segment_contains(
            x, y, wheel_cx - 11, wheel_cy - 19,
            wheel_cx + 11, wheel_cy + 19, 1
        )
        or authored_segment_contains(
            x, y, wheel_cx + 11, wheel_cy - 19,
            wheel_cx - 11, wheel_cy + 19, 1
        )
    )


def authored_frame_brace(
    x: int,
    y: int,
    crown_x: int,
    crown_y: int,
    wheel_cx: int,
    wheel_cy: int,
) -> bool:
    return (
        authored_segment_contains(
            x, y, crown_x, crown_y, wheel_cx - 18, wheel_cy - 5, 3
        )
        or authored_segment_contains(
            x, y, crown_x, crown_y, wheel_cx + 18, wheel_cy - 5, 3
        )
    )


def authored_0541_p1_structural_detail(x: int, y: int) -> tuple[bool, bool]:
    """Return (colored frame brace, neutral wheel spokes) for the 1219/1220 pair."""
    frame_brace = (
        authored_segment_contains(x, y, 132, 60, 100, 116, 3)
        or authored_segment_contains(x, y, 132, 60, 150, 116, 3)
    )
    wheel_spokes = authored_wheel_spokes(x, y, 123, 122)
    return frame_brace, wheel_spokes


def authored_p2_structural_detail(
    x: int,
    y: int,
    wheel_cx: int,
    crown_x: int,
) -> tuple[bool, bool]:
    """Return evidence-guided P2 brace/spokes for the 0542/0543 batch."""
    # The retained mismatch maps put the strongest missing frame support on the
    # lower-right run from crown toward the wheel/crank region. Add that brace
    # once, then a restrained three-axis spoke set through the existing hub.
    frame_brace = authored_segment_contains(
        x, y, crown_x, 60, wheel_cx + 20, 116, 3
    )
    wheel_spokes = authored_wheel_spokes(x, y, wheel_cx, 120)
    return frame_brace, wheel_spokes


def sample_authored_0541_p1_rgba(x: int, y: int) -> bytes:
    """Mirror the first native authored Remastered candidate exactly."""
    if x < 0 or y < 0 or x >= W * 4 or y >= H * 4:
        return b"\x00\x00\x00\x00"

    wheel_cx = 123
    wheel_cy = 122
    wx = x - wheel_cx
    wy = y - wheel_cy
    wr2 = wx * wx + wy * wy
    tire = wr2 <= 33 * 33 and wr2 >= 27 * 27
    rim = wr2 < 27 * 27 and wr2 >= 24 * 24
    hub = wr2 <= 6 * 6

    fork_center = 131 - (y - 60) // 14
    fork = y >= 60 and y <= 117 and x >= fork_center - 4 and x <= fork_center + 4

    crank = y >= 116 and y <= 123 and x >= 112 and x <= 138
    pedal = y >= 113 and y <= 118 and x >= 138 and x <= 150

    seat_dx = x - 128
    seat_dy = y - 22
    seat = authored_saddle_contains(x, y, 128, 22, 30, 18, 12, 32)

    neck = y >= 30 and y <= 60 and x >= 128 and x <= 136
    crown_dx = x - 132
    crown_dy = y - 60
    crown = crown_dx * crown_dx + crown_dy * crown_dy <= 10 * 10
    frame_brace, wheel_spokes = authored_0541_p1_structural_detail(x, y)

    if hub or rim or crank or pedal or wheel_spokes:
        return authored_rim_hardware_rgba(x, y, wheel_cx, wheel_cy)
    if seat:
        return authored_saddle_rgba(x, y, 128, 22)
    if fork or frame_brace or neck or crown:
        return authored_red_frame_rgba(x, y)
    if tire:
        return authored_rubber_rgba(x, y, wheel_cx, wheel_cy)
    return b"\x00\x00\x00\x00"


def build_first_authored_candidate_rgba() -> bytes:
    return b"".join(
        sample_authored_0541_p1_rgba(x, y)
        for y in range(H * 4)
        for x in range(W * 4)
    )


def sample_authored_0541_p1_companion_0d2d_rgba(x: int, y: int) -> bytes:
    """Mirror the authored frame-1219 temporal neighbor exactly."""
    if x < 0 or y < 0 or x >= W * 4 or y >= H * 4:
        return b"\x00\x00\x00\x00"

    wheel_cx = 123
    wheel_cy = 122
    wx = x - wheel_cx
    wy = y - wheel_cy
    wr2 = wx * wx + wy * wy
    tire = wr2 <= 33 * 33 and wr2 >= 27 * 27
    rim = wr2 < 27 * 27 and wr2 >= 24 * 24
    hub = wr2 <= 6 * 6

    fork_center = 131 - (y - 60) // 14
    fork = y >= 60 and y <= 117 and x >= fork_center - 4 and x <= fork_center + 4
    crank = y >= 116 and y <= 123 and x >= 112 and x <= 138
    pedal = y >= 113 and y <= 118 and x >= 138 and x <= 150

    seat_dx = x - 130
    seat_dy = y - 23
    seat = authored_saddle_contains(x, y, 130, 23, 32, 13, 8, 34)

    neck = y >= 30 and y <= 60 and x >= 128 and x <= 136
    crown_dx = x - 132
    crown_dy = y - 60
    crown = crown_dx * crown_dx + crown_dy * crown_dy <= 10 * 10
    frame_brace, wheel_spokes = authored_0541_p1_structural_detail(x, y)

    if hub or rim or crank or pedal or wheel_spokes:
        return authored_rim_hardware_rgba(x, y, wheel_cx, wheel_cy)
    if seat:
        return authored_saddle_rgba(x, y, 130, 23)
    if fork or frame_brace or neck or crown:
        return authored_red_frame_rgba(x, y)
    if tire:
        return authored_rubber_rgba(x, y, wheel_cx, wheel_cy)
    return b"\x00\x00\x00\x00"


def build_second_authored_candidate_rgba() -> bytes:
    return b"".join(
        sample_authored_0541_p1_companion_0d2d_rgba(x, y)
        for y in range(H * 4)
        for x in range(W * 4)
    )


def sample_authored_0540_p1_predecessor_rgba(x: int, y: int) -> bytes:
    """Mirror the authored frame-1218 reversed predecessor exactly."""
    if x < 0 or y < 0 or x >= W * 4 or y >= H * 4:
        return b"\x00\x00\x00\x00"

    wheel_cx = 128
    wheel_cy = 120
    wx = x - wheel_cx
    wy = y - wheel_cy
    wr2 = wx * wx + wy * wy
    tire = wr2 <= 35 * 35 and wr2 >= 25 * 25
    rim = wr2 < 25 * 25 and wr2 >= 22 * 22
    hub = wr2 <= 5 * 5

    fork_center = 126 - (y - 60) // 11
    fork = y >= 60 and y <= 117 and x >= fork_center - 5 and x <= fork_center + 5
    crank = y >= 116 and y <= 123 and x >= 111 and x <= 140
    pedal = y >= 113 and y <= 118 and x >= 141 and x <= 145

    seat_dx = x - 130
    seat_dy = y - 22
    seat = authored_saddle_contains(x, y, 130, 22, 35, 12, 8, 36)

    neck = y >= 30 and y <= 60 and x >= 124 and x <= 132
    crown_dx = x - 134
    crown_dy = y - 60
    crown = crown_dx * crown_dx + crown_dy * crown_dy <= 8 * 8
    frame_brace = authored_frame_brace(x, y, 134, 60, wheel_cx, wheel_cy)
    wheel_spokes = authored_wheel_spokes(x, y, wheel_cx, wheel_cy)

    if hub or rim or crank or pedal or wheel_spokes:
        return authored_rim_hardware_rgba(x, y, wheel_cx, wheel_cy)
    if seat:
        return authored_saddle_rgba(x, y, 130, 22)
    if fork or frame_brace or neck or crown:
        return authored_red_frame_rgba(x, y)
    if tire:
        return authored_rubber_rgba(x, y, wheel_cx, wheel_cy)
    return b"\x00\x00\x00\x00"


def build_third_authored_candidate_rgba() -> bytes:
    return b"".join(
        sample_authored_0540_p1_predecessor_rgba(x, y)
        for y in range(H * 4)
        for x in range(W * 4)
    )


def sample_authored_057f_p1_companion_0d4a_rgba(x: int, y: int) -> bytes:
    """Mirror the authored repeated frame-1215/1216 pose exactly."""
    if x < 0 or y < 0 or x >= W * 4 or y >= H * 4:
        return b"\x00\x00\x00\x00"

    wheel_cx = 132
    wheel_cy = 120
    wx = x - wheel_cx
    wy = y - wheel_cy
    wr2 = wx * wx + wy * wy
    tire = wr2 <= 35 * 35 and wr2 >= 25 * 25
    rim = wr2 < 25 * 25 and wr2 >= 22 * 22
    hub = wr2 <= 5 * 5

    fork_center = 130 - (y - 60) // 11
    fork = y >= 60 and y <= 117 and x >= fork_center - 5 and x <= fork_center + 5
    crank = y >= 116 and y <= 123 and x >= 115 and x <= 144
    pedal = y >= 113 and y <= 118 and x >= 145 and x <= 149

    # The bridge pose still carried a small right-heavy saddle block in the
    # true-density mismatch map. Shift/narrow without touching its recovered
    # outer envelope or wheel contact.
    seat_dx = x - 120
    seat_dy = y - 22
    seat = authored_saddle_contains(x, y, 120, 22, 32, 14, 8, 36)

    neck = y >= 30 and y <= 60 and x >= 128 and x <= 136
    crown_dx = x - 136
    crown_dy = y - 60
    crown = crown_dx * crown_dx + crown_dy * crown_dy <= 8 * 8
    frame_brace = authored_frame_brace(x, y, 136, 60, wheel_cx, wheel_cy)
    wheel_spokes = authored_wheel_spokes(x, y, wheel_cx, wheel_cy)

    if hub or rim or crank or pedal or wheel_spokes:
        return authored_rim_hardware_rgba(x, y, wheel_cx, wheel_cy)
    if seat:
        return authored_saddle_rgba(x, y, 120, 22)
    if fork or frame_brace or neck or crown:
        return authored_red_frame_rgba(x, y)
    if tire:
        return authored_rubber_rgba(x, y, wheel_cx, wheel_cy)
    return b"\x00\x00\x00\x00"


def build_fourth_authored_candidate_rgba() -> bytes:
    return b"".join(
        sample_authored_057f_p1_companion_0d4a_rgba(x, y)
        for y in range(H * 4)
        for x in range(W * 4)
    )


def sample_authored_057e_p1_with_p2_0543_rgba(x: int, y: int) -> bytes:
    """Mirror the authored repeated frame-1213/1214 pose exactly."""
    if x < 0 or y < 0 or x >= W * 4 or y >= H * 4:
        return b"\x00\x00\x00\x00"

    wheel_cx = 136
    wheel_cy = 120
    wx = x - wheel_cx
    wy = y - wheel_cy
    wr2 = wx * wx + wy * wy
    tire = wr2 <= 35 * 35 and wr2 >= 25 * 25
    rim = wr2 < 25 * 25 and wr2 >= 22 * 22
    hub = wr2 <= 5 * 5

    fork_center = 134 - (y - 60) // 11
    fork = y >= 60 and y <= 117 and x >= fork_center - 5 and x <= fork_center + 5
    crank = y >= 116 and y <= 123 and x >= 119 and x <= 148
    pedal = y >= 113 and y <= 118 and x >= 149 and x <= 153

    # True-density review showed the old saddle carried a broad block of
    # authored-only mass to the right. Shift/narrow the same smooth ellipse
    # while preserving the recovered whole-pose envelope and contact.
    seat_dx = x - 116
    seat_dy = y - 22
    seat = authored_saddle_contains(x, y, 116, 22, 32, 14, 8, 36)

    neck = y >= 30 and y <= 60 and x >= 132 and x <= 140
    crown_dx = x - 140
    crown_dy = y - 60
    crown = crown_dx * crown_dx + crown_dy * crown_dy <= 8 * 8
    frame_brace = authored_frame_brace(x, y, 140, 60, wheel_cx, wheel_cy)
    wheel_spokes = authored_wheel_spokes(x, y, wheel_cx, wheel_cy)

    if hub or rim or crank or pedal or wheel_spokes:
        return authored_rim_hardware_rgba(x, y, wheel_cx, wheel_cy)
    if seat:
        return authored_saddle_rgba(x, y, 116, 22)
    if fork or frame_brace or neck or crown:
        return authored_red_frame_rgba(x, y)
    if tire:
        return authored_rubber_rgba(x, y, wheel_cx, wheel_cy)
    return b"\x00\x00\x00\x00"


def build_fifth_authored_candidate_rgba() -> bytes:
    return b"".join(
        sample_authored_057e_p1_with_p2_0543_rgba(x, y)
        for y in range(H * 4)
        for x in range(W * 4)
    )


def sample_authored_057d_p1_with_p2_0543_rgba(x: int, y: int) -> bytes:
    """Mirror the authored repeated frame-1207..1212 pose exactly."""
    if x < 0 or y < 0 or x >= W * 4 or y >= H * 4:
        return b"\x00\x00\x00\x00"

    wheel_cx = 140
    wheel_cy = 120
    wx = x - wheel_cx
    wy = y - wheel_cy
    wr2 = wx * wx + wy * wy
    tire = wr2 <= 35 * 35 and wr2 >= 25 * 25
    rim = wr2 < 25 * 25 and wr2 >= 22 * 22
    hub = wr2 <= 5 * 5

    fork_center = 134 - (y - 60) // 11
    fork = y >= 60 and y <= 117 and x >= fork_center - 5 and x <= fork_center + 5
    crank = y >= 116 and y <= 123 and x >= 123 and x <= 152
    pedal = y >= 113 and y <= 118 and x >= 153 and x <= 157

    # The 057D mismatch map shows the same right-heavy saddle mass as 057E.
    # Shift left and narrow it without changing the stock-derived envelope or
    # the wheel-supplied contact anchor.
    seat_dx = x - 112
    seat_dy = y - 26
    seat = authored_saddle_contains(x, y, 112, 26, 28, 14, 12, 40)

    neck = y >= 30 and y <= 60 and x >= 136 and x <= 144
    crown_dx = x - 144
    crown_dy = y - 60
    crown = crown_dx * crown_dx + crown_dy * crown_dy <= 8 * 8
    frame_brace = authored_frame_brace(x, y, 144, 60, wheel_cx, wheel_cy)
    wheel_spokes = authored_wheel_spokes(x, y, wheel_cx, wheel_cy)

    if hub or rim or crank or pedal or wheel_spokes:
        return authored_rim_hardware_rgba(x, y, wheel_cx, wheel_cy)
    if seat:
        return authored_saddle_rgba(x, y, 112, 26)
    if fork or frame_brace or neck or crown:
        return authored_red_frame_rgba(x, y)
    if tire:
        return authored_rubber_rgba(x, y, wheel_cx, wheel_cy)
    return b"\x00\x00\x00\x00"


def build_sixth_authored_candidate_rgba() -> bytes:
    return b"".join(
        sample_authored_057d_p1_with_p2_0543_rgba(x, y)
        for y in range(H * 4)
        for x in range(W * 4)
    )


def sample_authored_0540_p2_baseline_rgba(x: int, y: int) -> bytes:
    """Mirror the first authored P2 baseline representation exactly."""
    if x < 0 or y < 0 or x >= W * 4 or y >= H * 4:
        return b"\x00\x00\x00\x00"

    wheel_cx = 128
    wheel_cy = 120
    wx = x - wheel_cx
    wy = y - wheel_cy
    wr2 = wx * wx + wy * wy
    tire = wr2 <= 35 * 35 and wr2 >= 25 * 25
    rim = wr2 < 25 * 25 and wr2 >= 22 * 22
    hub = wr2 <= 5 * 5

    fork_center = 126 - (y - 60) // 11
    fork = y >= 60 and y <= 117 and x >= fork_center - 5 and x <= fork_center + 5
    crank = y >= 116 and y <= 123 and x >= 111 and x <= 140
    pedal = y >= 113 and y <= 118 and x >= 141 and x <= 145

    seat_dx = x - 130
    seat_dy = y - 22
    seat = authored_saddle_contains(x, y, 130, 22, 35, 12, 12, 36)

    neck = y >= 30 and y <= 60 and x >= 124 and x <= 132
    crown_dx = x - 134
    crown_dy = y - 60
    crown = crown_dx * crown_dx + crown_dy * crown_dy <= 8 * 8
    frame_brace = authored_frame_brace(x, y, 134, 60, wheel_cx, wheel_cy)
    wheel_spokes = authored_wheel_spokes(x, y, wheel_cx, wheel_cy)

    if hub or rim or crank or pedal or wheel_spokes:
        return authored_rim_hardware_rgba(x, y, wheel_cx, wheel_cy)
    if seat:
        return authored_saddle_rgba(x, y, 130, 22)
    if fork or frame_brace or neck or crown:
        return authored_blue_frame_rgba(x, y)
    if tire:
        return authored_rubber_rgba(x, y, wheel_cx, wheel_cy)
    return b"\x00\x00\x00\x00"


def build_seventh_authored_candidate_rgba() -> bytes:
    return b"".join(
        sample_authored_0540_p2_baseline_rgba(x, y)
        for y in range(H * 4)
        for x in range(W * 4)
    )


def sample_authored_0541_p2_predecessor_rgba(x: int, y: int) -> bytes:
    if x < 0 or y < 0 or x >= W * 4 or y >= H * 4:
        return b"\x00\x00\x00\x00"
    wheel_cx, wheel_cy = 124, 120
    wx, wy = x - wheel_cx, y - wheel_cy
    wr2 = wx * wx + wy * wy
    tire = wr2 <= 35 * 35 and wr2 >= 25 * 25
    rim = wr2 < 25 * 25 and wr2 >= 22 * 22
    hub = wr2 <= 5 * 5
    fork_center = 122 - (y - 60) // 11
    fork = y >= 60 and y <= 117 and x >= fork_center - 5 and x <= fork_center + 5
    crank = y >= 116 and y <= 123 and x >= 107 and x <= 136
    pedal = y >= 113 and y <= 118 and x >= 137 and x <= 141
    # The 0541 P2 transition pose is over-broad on the left/top at true
    # density. Shift the same smooth saddle right/down and narrow it while the
    # wheel/fork continue to lock envelope and contact.
    seat_dx, seat_dy = x - 130, y - 26
    seat = authored_saddle_contains(x, y, 130, 26, 30, 12, 12, 40)
    neck = y >= 30 and y <= 60 and x >= 120 and x <= 128
    crown_dx, crown_dy = x - 130, y - 60
    crown = crown_dx * crown_dx + crown_dy * crown_dy <= 8 * 8
    frame_brace = authored_frame_brace(x, y, 130, 60, wheel_cx, wheel_cy)
    wheel_spokes = authored_wheel_spokes(x, y, wheel_cx, wheel_cy)
    if hub or rim or crank or pedal or wheel_spokes:
        return authored_rim_hardware_rgba(x, y, wheel_cx, wheel_cy)
    if seat:
        return authored_saddle_rgba(x, y, 130, 26)
    if fork or frame_brace or neck or crown:
        return authored_blue_frame_rgba(x, y)
    if tire:
        return authored_rubber_rgba(x, y, wheel_cx, wheel_cy)
    return b"\x00\x00\x00\x00"


def build_eighth_authored_candidate_rgba() -> bytes:
    return b"".join(
        sample_authored_0541_p2_predecessor_rgba(x, y)
        for y in range(H * 4)
        for x in range(W * 4)
    )


def sample_authored_0542_p2_rgba(x: int, y: int) -> bytes:
    """Mirror the shared authored P2 0542 pose exactly."""
    if x < 0 or y < 0 or x >= W * 4 or y >= H * 4:
        return b"\x00\x00\x00\x00"

    wheel_cx, wheel_cy = 120, 120
    wx, wy = x - wheel_cx, y - wheel_cy
    wr2 = wx * wx + wy * wy
    tire = wr2 <= 35 * 35 and wr2 >= 25 * 25
    rim = wr2 < 25 * 25 and wr2 >= 22 * 22
    hub = wr2 <= 5 * 5

    fork_center = 118 - (y - 60) // 11
    fork = y >= 60 and y <= 117 and x >= fork_center - 5 and x <= fork_center + 5
    crank = y >= 116 and y <= 123 and x >= 103 and x <= 132
    pedal = y >= 113 and y <= 118 and x >= 133 and x <= 137

    seat_dx, seat_dy = x - 130, y - 26
    seat = authored_saddle_contains(x, y, 130, 26, 35, 14, 16, 40)

    neck = y >= 30 and y <= 60 and x >= 116 and x <= 124
    crown_dx, crown_dy = x - 126, y - 60
    crown = crown_dx * crown_dx + crown_dy * crown_dy <= 8 * 8
    frame_brace, wheel_spokes = authored_p2_structural_detail(
        x, y, 120, 126
    )

    if hub or rim or crank or pedal or wheel_spokes:
        return authored_rim_hardware_rgba(x, y, wheel_cx, wheel_cy)
    if seat:
        return authored_saddle_rgba(x, y, 130, 26)
    if fork or frame_brace or neck or crown:
        return authored_blue_frame_rgba(x, y)
    if tire:
        return authored_rubber_rgba(x, y, wheel_cx, wheel_cy)
    return b"\x00\x00\x00\x00"


def build_ninth_authored_candidate_rgba() -> bytes:
    return b"".join(
        sample_authored_0542_p2_rgba(x, y)
        for y in range(H * 4)
        for x in range(W * 4)
    )


def sample_authored_0543_p2_rgba(x: int, y: int) -> bytes:
    """Mirror the shared authored P2 0543 pose exactly."""
    if x < 0 or y < 0 or x >= W * 4 or y >= H * 4:
        return b"\x00\x00\x00\x00"

    wheel_cx, wheel_cy = 116, 120
    wx, wy = x - wheel_cx, y - wheel_cy
    wr2 = wx * wx + wy * wy
    tire = wr2 <= 36 * 36 and wr2 >= 25 * 25
    rim = wr2 < 25 * 25 and wr2 >= 22 * 22
    hub = wr2 <= 5 * 5

    fork_center = 116 - (y - 60) // 11
    fork = y >= 60 and y <= 117 and x >= fork_center - 5 and x <= fork_center + 5
    crank = y >= 116 and y <= 123 and x >= 101 and x <= 130
    pedal = y >= 113 and y <= 118 and x >= 131 and x <= 135

    seat_dx, seat_dy = x - 130, y - 30
    seat = authored_saddle_contains(x, y, 130, 30, 35, 12, 16, 40)

    neck = y >= 30 and y <= 60 and x >= 114 and x <= 122
    crown_dx, crown_dy = x - 124, y - 60
    crown = crown_dx * crown_dx + crown_dy * crown_dy <= 8 * 8
    frame_brace, wheel_spokes = authored_p2_structural_detail(
        x, y, 116, 124
    )

    if hub or rim or crank or pedal or wheel_spokes:
        return authored_rim_hardware_rgba(x, y, wheel_cx, wheel_cy)
    if seat:
        return authored_saddle_rgba(x, y, 130, 30)
    if fork or frame_brace or neck or crown:
        return authored_blue_frame_rgba(x, y)
    if tire:
        return authored_rubber_rgba(x, y, wheel_cx, wheel_cy)
    return b"\x00\x00\x00\x00"


def build_tenth_authored_candidate_rgba() -> bytes:
    return b"".join(
        sample_authored_0543_p2_rgba(x, y)
        for y in range(H * 4)
        for x in range(W * 4)
    )


def authored_candidate_rgba_for_entry(entry: dict) -> tuple[bytes, str, str]:
    """Return authored RGBA plus the expected generator and native sampler."""
    rid = entry["representation_id"]
    if rid == FIRST_AUTHORED_REPRESENTATION_ID:
        return (
            build_first_authored_candidate_rgba(),
            "tools/build_racer_hd_asset_dossier.py::build_first_authored_candidate_rgba",
            "sample_racer_hd_authored_0541_p1",
        )
    if rid == SECOND_AUTHORED_REPRESENTATION_ID:
        return (
            build_second_authored_candidate_rgba(),
            "tools/build_racer_hd_asset_dossier.py::build_second_authored_candidate_rgba",
            "sample_racer_hd_authored_0541_p1_companion_0d2d",
        )
    if rid in (THIRD_AUTHORED_REPRESENTATION_ID, FOURTH_AUTHORED_REPRESENTATION_ID):
        return (
            build_third_authored_candidate_rgba(),
            "tools/build_racer_hd_asset_dossier.py::build_third_authored_candidate_rgba",
            "sample_racer_hd_authored_0540_p1_predecessor",
        )
    if rid == FIFTH_AUTHORED_REPRESENTATION_ID:
        return (
            build_fourth_authored_candidate_rgba(),
            "tools/build_racer_hd_asset_dossier.py::build_fourth_authored_candidate_rgba",
            "sample_racer_hd_authored_057f_p1_companion_0d4a",
        )
    if rid == SIXTH_AUTHORED_REPRESENTATION_ID:
        return (
            build_fifth_authored_candidate_rgba(),
            "tools/build_racer_hd_asset_dossier.py::build_fifth_authored_candidate_rgba",
            "sample_racer_hd_authored_057e_p1_with_p2_0543",
        )
    if rid == SEVENTH_AUTHORED_REPRESENTATION_ID:
        return (
            build_sixth_authored_candidate_rgba(),
            "tools/build_racer_hd_asset_dossier.py::build_sixth_authored_candidate_rgba",
            "sample_racer_hd_authored_057d_p1_with_p2_0543",
        )
    if rid in (EIGHTH_AUTHORED_REPRESENTATION_ID, NINTH_AUTHORED_REPRESENTATION_ID):
        return (
            build_seventh_authored_candidate_rgba(),
            "tools/build_racer_hd_asset_dossier.py::build_seventh_authored_candidate_rgba",
            "sample_racer_hd_authored_0540_p2_baseline",
        )
    if rid == TENTH_AUTHORED_REPRESENTATION_ID:
        return (
            build_eighth_authored_candidate_rgba(),
            "tools/build_racer_hd_asset_dossier.py::build_eighth_authored_candidate_rgba",
            "sample_racer_hd_authored_0541_p2_predecessor",
        )
    if rid in (ELEVENTH_AUTHORED_REPRESENTATION_ID, TWELFTH_AUTHORED_REPRESENTATION_ID):
        return (
            build_ninth_authored_candidate_rgba(),
            "tools/build_racer_hd_asset_dossier.py::build_ninth_authored_candidate_rgba",
            "sample_racer_hd_authored_0542_p2",
        )
    if rid in (THIRTEENTH_AUTHORED_REPRESENTATION_ID, FOURTEENTH_AUTHORED_REPRESENTATION_ID):
        return (
            build_tenth_authored_candidate_rgba(),
            "tools/build_racer_hd_asset_dossier.py::build_tenth_authored_candidate_rgba",
            "sample_racer_hd_authored_0543_p2",
        )
    raise ValueError(f"unsupported authored candidate registration: {rid}")


def gameplay_sampled_alpha_review(authored_rgba: bytes, stock_rgba: bytes) -> dict:
    candidate = set()
    stock = set()
    for y in range(H):
        for x in range(W):
            authored_index = (((y * 4 + 2) * (W * 4)) + (x * 4 + 2)) * 4 + 3
            stock_index = ((y * W) + x) * 4 + 3
            if authored_rgba[authored_index] != 0:
                candidate.add((x, y))
            if stock_rgba[stock_index] != 0:
                stock.add((x, y))

    def bounds(points: set[tuple[int, int]]) -> list[int]:
        return [
            min(x for x, _ in points),
            min(y for _, y in points),
            max(x for x, _ in points),
            max(y for _, y in points),
        ]

    bottom_y = max(y for _, y in candidate)
    bottom_x = [x for x, y in candidate if y == bottom_y]
    overlap = candidate & stock
    stock_only = sorted(stock - candidate, key=lambda p: (p[1], p[0]))
    candidate_only = sorted(candidate - stock, key=lambda p: (p[1], p[0]))
    intersection = len(overlap)
    union = len(candidate | stock)
    return {
        "sampling": "4x logical pixel centres (x*4+2, y*4+2)",
        "stock_alpha_bounds": bounds(stock),
        "candidate_alpha_bounds": bounds(candidate),
        "candidate_contact_x2_y2": [min(bottom_x) + max(bottom_x), bottom_y * 2],
        "candidate_opaque_pixels": len(candidate),
        "stock_opaque_pixels": len(stock),
        "alpha_intersection_pixels": intersection,
        "alpha_union_pixels": union,
        "alpha_iou": intersection / union,
        "stock_only_pixel_count": len(stock_only),
        "candidate_only_pixel_count": len(candidate_only),
        "stock_only_pixels": [list(point) for point in stock_only],
        "candidate_only_pixels": [list(point) for point in candidate_only],
    }


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-")


def registry_by_representation(registry: dict) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for entry in registry["entries"]:
        rid = entry["representation_id"]
        if rid in out:
            raise ValueError(f"duplicate representation_id: {rid}")
        out[rid] = entry
    return out


def exact_window_rows(trace_report: dict, start: int, end: int) -> list[dict]:
    if start > end:
        raise ValueError("window start must not exceed window end")
    coverage = trace_report.get("registered_composition_coverage")
    if not isinstance(coverage, dict):
        raise ValueError("trace report lacks registered_composition_coverage")
    rows = [
        row for row in coverage.get("frames", [])
        if start <= int(row["frame"]) <= end
    ]
    expected = list(range(start, end + 1))
    frames = [int(row["frame"]) for row in rows]
    if frames != expected:
        raise ValueError(f"trace window is not exact/contiguous: {frames} != {expected}")
    for row in rows:
        if not row.get("fully_registered"):
            raise ValueError(f"frame {row['frame']} is not fully registered")
        for key in ("p1_representation_id", "p2_representation_id"):
            if not row.get(key):
                raise ValueError(f"frame {row['frame']} lacks {key}")
    return rows


def observation_map(rows: list[dict]) -> dict[str, dict]:
    observed: dict[str, dict] = {}
    for row in rows:
        frame = int(row["frame"])
        for player in ("p1", "p2"):
            rid = row[f"{player}_representation_id"]
            item = observed.setdefault(rid, {"player": player, "frames": []})
            if item["player"] != player:
                raise ValueError(f"representation {rid} appears for both players")
            item["frames"].append(frame)
    return observed


def transition_context(rows: list[dict], representation_id: str, player: str) -> dict:
    key = f"{player}_representation_id"
    previous: dict[str, list[int]] = {}
    following: dict[str, list[int]] = {}
    for index, row in enumerate(rows):
        if row[key] != representation_id:
            continue
        frame = int(row["frame"])
        if index > 0:
            rid = rows[index - 1][key]
            if rid != representation_id:
                previous.setdefault(rid, []).append(frame)
        if index + 1 < len(rows):
            rid = rows[index + 1][key]
            if rid != representation_id:
                following.setdefault(rid, []).append(frame)
    return {
        "previous_representations": [
            {"representation_id": rid, "entry_frames": frames}
            for rid, frames in sorted(previous.items())
        ],
        "next_representations": [
            {"representation_id": rid, "exit_frames": frames}
            for rid, frames in sorted(following.items())
        ],
    }


def validate_entry_geometry(stock: bytes, entry: dict) -> dict:
    anchors = entry["registration"]["semantic_anchors"]
    pivot = object_flip_pivot_x2_y2(W, H)
    contact = alpha_contact_anchor_x2_y2(stock, W, H)
    if anchors["flip_pivot_x2_y2"] != pivot:
        raise ValueError(
            f"{entry['representation_id']} pivot mismatch: "
            f"{anchors['flip_pivot_x2_y2']} != {pivot}"
        )
    if anchors["wheel_contact_x2_y2"] != contact:
        raise ValueError(
            f"{entry['representation_id']} contact mismatch: "
            f"{anchors['wheel_contact_x2_y2']} != {contact}"
        )
    return {
        "coordinate_space": anchors["coordinate_space"],
        "fixed_point_scale": int(anchors["fixed_point_scale"]),
        "flip_pivot_x2_y2": pivot,
        "wheel_contact_x2_y2": contact,
        "derivation": {
            "flip_pivot": anchors["flip_pivot_derivation"],
            "wheel_contact": anchors["wheel_contact_derivation"],
        },
    }


def build_dossier(
    rom: bytes,
    registry: dict,
    trace_report: dict,
    start: int,
    end: int,
) -> tuple[dict, dict[str, dict[str, bytes]]]:
    rows = exact_window_rows(trace_report, start, end)
    entries = registry_by_representation(registry)
    observed = observation_map(rows)
    assets: dict[str, dict[str, bytes]] = {}
    representations = []

    for rid in sorted(observed):
        if rid not in entries:
            raise ValueError(f"trace references unregistered representation: {rid}")
        entry = entries[rid]
        player = observed[rid]["player"]
        if entry["player"] != player:
            raise ValueError(f"{rid} player mismatch between trace and registry")

        stock = build_stock_rgba(rom, entry)
        candidate, cw, ch = build_remastered_candidate(stock, entry)
        nearest4 = nearest_rgba(stock, W, H, 4)
        geometry = validate_entry_geometry(stock, entry)

        stock_png = encode_png_rgba(W, H, stock)
        nearest_png = encode_png_rgba(W * 4, H * 4, nearest4)
        candidate_png = encode_png_rgba(cw, ch, candidate)
        assets[rid] = {
            "stock": stock_png,
            "nearest4": nearest_png,
            "contract_candidate": candidate_png,
        }
        authored_candidate = None
        authored_meta = entry.get("authored_candidate")
        if authored_meta is not None:
            authored_rgba, expected_generator, native_sampler = (
                authored_candidate_rgba_for_entry(entry)
            )
            if authored_meta.get("artifact_generator") != expected_generator:
                raise ValueError(f"unsupported authored candidate generator for {rid}")
            authored_png = encode_png_rgba(W * 4, H * 4, authored_rgba)
            assets[rid]["authored_candidate"] = authored_png
            authored_candidate = {
                **authored_meta,
                "dimensions": [W * 4, H * 4],
                "rgba_sha256": sha256(authored_rgba),
                "png": f"authored-candidate/{safe_name(rid)}.png",
                "png_sha256": sha256(authored_png),
                "visual_language": dict(RESOLVED_VISUAL_LANGUAGE),
                "gameplay_scale_review": gameplay_sampled_alpha_review(
                    authored_rgba, stock
                ),
                "native_parity": (
                    "mirrors native/presentation/racer_hd_presenter.hpp "
                    + native_sampler
                ),
            }

        representations.append({
            "representation_id": rid,
            "semantic_frame_id": entry["semantic_frame_id"],
            "player": player,
            "palette_asset_id": entry["palette_asset_id"],
            "composition_guards": entry["composition_guards"],
            "observed_frames_in_window": observed[rid]["frames"],
            "temporal_context": transition_context(rows, rid, player),
            "registration": {
                "logical_canvas_pixels": entry["registration"]["logical_canvas_pixels"],
                "object_origin": entry["registration"]["object_origin"],
                "occupancy_tile_offset": entry["registration"]["occupancy_tile_offset"],
                "orientation_policy": entry["registration"]["orientation_policy"],
                "geometry": geometry,
            },
            "stock_evidence": {
                "kind": entry["original"]["kind"],
                "source": entry["original"]["source"],
                "alpha_bounds": alpha_bounds(stock, W, H),
                "opaque_rgba_histogram": [
                    {"rgba": list(rgba), "count": count}
                    for rgba, count in sorted(
                        __import__("collections").Counter(
                            tuple(stock[i:i + 4])
                            for i in range(0, len(stock), 4)
                            if stock[i + 3] != 0
                        ).items(),
                        key=lambda item: (-item[1], item[0]),
                    )
                ],
                "rgba_sha256": sha256(stock),
                "png": f"stock/{safe_name(rid)}.png",
                "png_sha256": sha256(stock_png),
                "nearest_4x_png": f"nearest-4x/{safe_name(rid)}.png",
                "nearest_4x_png_sha256": sha256(nearest_png),
            },
            "current_contract_candidate": {
                **entry["remastered_candidate"],
                "dimensions": [cw, ch],
                "alpha_bounds": alpha_bounds(candidate, cw, ch),
                "rgba_sha256": sha256(candidate),
                "png": f"contract-candidate/{safe_name(rid)}.png",
                "png_sha256": sha256(candidate_png),
            },
            "fallback": entry["fallback"],
            "art_review": {
                "shipping_art_approved": False,
                "evidence_packet_ready": True,
                "authored_candidate": authored_candidate,
                "resolved_decisions": dict(RESOLVED_VISUAL_LANGUAGE),
                "pending_decisions": list(PENDING_ART_DECISIONS),
                "visual_language_authority": "docs/HD-ART-DIRECTION.md",
                "display_geometry_authority": "docs/DISPLAY-PRESENTATION-POLICY.md",
            },
        })

    timeline = [
        {
            "frame": int(row["frame"]),
            "p1_representation_id": row["p1_representation_id"],
            "p2_representation_id": row["p2_representation_id"],
        }
        for row in rows
    ]

    dossier = {
        "schema_version": 1,
        "family": registry["family"],
        "purpose": (
            "Approval-oriented evidence packet for the first continuously "
            "registered ordinary-race Racer HD temporal window."
        ),
        "temporal_window": {
            "start": start,
            "end": end,
            "frame_count": end - start + 1,
            "source": "registered_composition_coverage from deterministic native semantic trace",
            "all_frames_exactly_registered": True,
        },
        "authoritative_inputs": {
            "semantic_identity": registry["lookup"]["primary_key"],
            "animation_timing": "guest-authored; dossier records observed order only",
            "stock_pixels": "canonical ROM deterministic composition",
            "placement": "live OAM at runtime; not baked into asset identity",
            "display_geometry": (
                "replacement art targets modern square-pixel host geometry; "
                "CRT pixel-aspect policy remains independent"
            ),
        },
        "timeline": timeline,
        "representations": representations,
        "validation": {
            "fully_registered_window": True,
            "registry_representation_ids_unique": True,
            "stock_geometry_rederived_from_rom": True,
            "registered_anchors_match_rederived_stock": True,
            "candidate_status_is_contract_only": all(
                not rep["art_review"]["shipping_art_approved"]
                for rep in representations
            ),
            "ready_for_art_review": True,
        },
        "remaining_scope": {
            "phase_e_globally_complete": False,
            "ordinary_race_racer_family_semantic_gate_reached": True,
            "shipping_art_approved": False,
            "broader_animation_families": "open; admit deliberately by product/art need",
        },
    }
    return dossier, assets


def write_dossier(output_dir: Path, dossier: dict, assets: dict[str, dict[str, bytes]]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for kind in ("stock", "nearest-4x", "contract-candidate", "authored-candidate"):
        (output_dir / kind).mkdir(parents=True, exist_ok=True)
    for rid, payloads in assets.items():
        name = safe_name(rid) + ".png"
        (output_dir / "stock" / name).write_bytes(payloads["stock"])
        (output_dir / "nearest-4x" / name).write_bytes(payloads["nearest4"])
        (output_dir / "contract-candidate" / name).write_bytes(payloads["contract_candidate"])
        if "authored_candidate" in payloads:
            (output_dir / "authored-candidate" / name).write_bytes(payloads["authored_candidate"])
    (output_dir / "manifest.json").write_text(
        json.dumps(dossier, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--trace", type=Path, required=True)
    ap.add_argument(
        "--registry",
        type=Path,
        default=ROOT / "analysis/data/racer-hd-replacement-prototype.json",
    )
    ap.add_argument("--window-start", type=int, required=True)
    ap.add_argument("--window-end", type=int, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()

    dossier, assets = build_dossier(
        args.rom.read_bytes(),
        json.loads(args.registry.read_text(encoding="utf-8")),
        json.loads(args.trace.read_text(encoding="utf-8")),
        args.window_start,
        args.window_end,
    )
    write_dossier(args.output_dir, dossier, assets)
    print(json.dumps(dossier, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
