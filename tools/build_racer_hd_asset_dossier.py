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
from probe_racer_hd_fallback_family import (
    palette_normalized_rgba,
    palette_role_indices,
)
from extract_racer_presentation_family import rgba_palette



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
FIFTEENTH_AUTHORED_REPRESENTATION_ID = (
    "ordinary-racer-0x057E-p1-sync-reference"
)
SIXTEENTH_AUTHORED_REPRESENTATION_ID = (
    "ordinary-racer-0x057E-p1-companion-0D69-reference"
)
SEVENTEENTH_AUTHORED_REPRESENTATION_ID = (
    "ordinary-racer-0x0544-p2-sync-reference"
)
EIGHTEENTH_AUTHORED_REPRESENTATION_ID = (
    "ordinary-racer-0x0544-p2-with-p1-companion-0D69-reference"
)
NINETEENTH_AUTHORED_REPRESENTATION_ID = (
    "ordinary-racer-0x0543-p1-third-family-hold-reference"
)
TWENTIETH_AUTHORED_REPRESENTATION_ID = (
    "ordinary-racer-0x0540-p2-third-family-hold-0D2C-reference"
)
TWENTY_FIRST_AUTHORED_REPRESENTATION_ID = (
    "ordinary-racer-0x0542-p1-third-family-recovery-reference"
)
TWENTY_SECOND_AUTHORED_REPRESENTATION_ID = (
    "ordinary-racer-0x0541-p2-third-family-recovery-0D2D-reference"
)
TWENTY_THIRD_AUTHORED_REPRESENTATION_ID = (
    "ordinary-racer-0x0540-p1-fourth-family-entry-reference"
)
TWENTY_FOURTH_AUTHORED_REPRESENTATION_ID = (
    "ordinary-racer-0x057F-p2-fourth-family-entry-0D2A-reference"
)
TWENTY_FIFTH_AUTHORED_REPRESENTATION_ID = (
    "ordinary-racer-0x0540-p1-fourth-family-hold-reference"
)
TWENTY_SIXTH_AUTHORED_REPRESENTATION_ID = (
    "ordinary-racer-0x0540-p2-fourth-family-hold-reference"
)
TWENTY_SEVENTH_AUTHORED_REPRESENTATION_ID = (
    "ordinary-racer-0x0541-p1-fourth-family-exit-reference"
)
TWENTY_EIGHTH_AUTHORED_REPRESENTATION_ID = (
    "ordinary-racer-0x057F-p2-fourth-family-exit-0D2A-reference"
)
TWENTY_NINTH_AUTHORED_REPRESENTATION_ID = (
    "ordinary-racer-0x057E-p1-fifth-family-0542-reference"
)
THIRTIETH_AUTHORED_REPRESENTATION_ID = (
    "ordinary-racer-0x0542-p2-fifth-family-057E-reference"
)
THIRTY_FIRST_AUTHORED_REPRESENTATION_ID = (
    "ordinary-racer-0x057D-p1-fifth-family-0541-reference"
)
THIRTY_SECOND_AUTHORED_REPRESENTATION_ID = (
    "ordinary-racer-0x0541-p2-fifth-family-057D-reference"
)
THIRTY_THIRD_AUTHORED_REPRESENTATION_ID = (
    "ordinary-racer-0x057D-p1-fifth-family-0540-reference"
)
THIRTY_FOURTH_AUTHORED_REPRESENTATION_ID = (
    "ordinary-racer-0x0540-p2-fifth-family-057D-reference"
)
THIRTY_FIFTH_AUTHORED_REPRESENTATION_ID = (
    "ordinary-racer-0x057C-p1-fifth-family-0540-reference"
)
THIRTY_SIXTH_AUTHORED_REPRESENTATION_ID = (
    "ordinary-racer-0x0540-p2-fifth-family-057C-reference"
)

THIRTY_SEVENTH_AUTHORED_REPRESENTATION_ID = (
    "ordinary-racer-0x0544-p1-frequency-0578-reference"
)
THIRTY_EIGHTH_AUTHORED_REPRESENTATION_ID = (
    "ordinary-racer-0x0578-p2-frequency-0544-reference"
)
THIRTY_NINTH_AUTHORED_REPRESENTATION_ID = (
    "ordinary-racer-0x04B9-p1-broader-frequency-reference"
)
FORTIETH_AUTHORED_REPRESENTATION_ID = (
    "ordinary-racer-0x0239-p1-broader-frequency-reference"
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


def authored_crank_contains(
    x: int,
    y: int,
    wheel_cx: int,
    wheel_cy: int,
    pedal_root_x: int,
) -> bool:
    return authored_segment_contains(
        x, y, wheel_cx, wheel_cy, pedal_root_x, 116, 2
    )


def authored_pedal_contains(
    x: int,
    y: int,
    pedal_min_x: int,
    pedal_max_x: int,
) -> bool:
    return authored_segment_contains(
        x, y, pedal_min_x, 116, pedal_max_x, 116, 2
    )


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


def authored_hub_hardware_rgba(
    x: int,
    y: int,
    wheel_cx: int,
    wheel_cy: int,
) -> bytes:
    """Mirror the native compact radial hub depth cue exactly."""
    directional = (wheel_cx - x) + (wheel_cy - y)
    if directional > 2:
        return _rgba32(249, 248, 247)
    if directional < -2:
        return _rgba32(156, 150, 138)
    return _rgba32(224, 221, 216)


def authored_drivetrain_hardware_rgba(
    y: int,
    wheel_cy: int,
) -> bytes:
    """Mirror the native stable crank/pedal depth bands exactly."""
    if y <= wheel_cy - 3:
        return _rgba32(249, 248, 247)
    if y >= wheel_cy + 1:
        return _rgba32(156, 150, 138)
    return _rgba32(224, 221, 216)


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
    radius_y: int,
) -> bytes:
    dx = x - seat_cx
    dy = y - seat_cy
    directional = -(dx + dy)
    upper_shell = -(radius_y // 4)
    underside_start = radius_y // 4
    lower_lip = radius_y // 2
    if dy <= upper_shell and directional > 18:
        return _rgba32(82, 77, 69)
    if dy >= lower_lip:
        return _rgba32(25, 23, 17)
    if dy >= underside_start:
        return _rgba32(41, 37, 29)
    if directional > 28:
        return _rgba32(69, 64, 56)
    return _rgba32(49, 45, 38)


def authored_frame_junction_rgba(
    x: int,
    y: int,
    crown_x: int,
    crown_y: int,
    blue_frame: bool,
    member_overlap: bool,
) -> bytes:
    """Mirror the native integrated forged crown/junction material exactly."""
    dx = x - crown_x
    dy = y - crown_y
    radial2 = dx * dx + dy * dy
    shoulder_highlight = dy <= -1 and dx <= 2 and radial2 >= 12
    integrated_throat = dy >= 1 and (dx >= -2 or radial2 <= 20)
    outer_shadow = dx >= 4 or dy >= 5
    if member_overlap:
        return (
            authored_blue_frame_rgba(x, y)
            if blue_frame
            else authored_red_frame_rgba(x, y)
        )
    if blue_frame:
        if shoulder_highlight:
            return _rgba32(83, 115, 232)
        if outer_shadow:
            return _rgba32(24, 40, 120)
        if integrated_throat:
            return _rgba32(35, 51, 150)
        return _rgba32(52, 77, 201)
    if shoulder_highlight:
        return _rgba32(232, 83, 83)
    if outer_shadow:
        return _rgba32(120, 24, 24)
    if integrated_throat:
        return _rgba32(150, 35, 35)
    return _rgba32(201, 52, 52)


def authored_saddle_mount_contains(
    x: int,
    y: int,
    neck_min_x: int,
    neck_max_x: int,
    mount_y: int,
) -> bool:
    """Mirror the native saddle/post clamp without adding occupied pixels."""
    mount_cx = (neck_min_x + neck_max_x) // 2
    radius_x = ((neck_max_x - neck_min_x) // 2) + 1
    dx = x - mount_cx
    dy = y - mount_y
    return (
        dx * dx * 4 + dy * dy * radius_x * radius_x
        <= radius_x * radius_x * 4
    )


def authored_saddle_mount_rgba(y: int, mount_y: int) -> bytes:
    """Restrained two-tone metal shared with the native clamp treatment."""
    if y < mount_y:
        return _rgba32(217, 213, 208)
    return _rgba32(159, 153, 142)


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

    crank = authored_crank_contains(x, y, wheel_cx, wheel_cy, 138)
    pedal = authored_pedal_contains(x, y, 138, 150)
    seat = authored_saddle_contains(x, y, 128, 22, 30, 18, 12, 32)

    neck = y >= 30 and y <= 60 and x >= 128 and x <= 136
    saddle_mount = (
        (seat or neck)
        and authored_saddle_mount_contains(x, y, 128, 136, 29)
    )
    crown_dx = x - 132
    crown_dy = y - 60
    crown = crown_dx * crown_dx + crown_dy * crown_dy <= 10 * 10
    frame_brace, wheel_spokes = authored_0541_p1_structural_detail(x, y)

    if hub:
        return authored_hub_hardware_rgba(x, y, wheel_cx, wheel_cy)
    if crank or pedal:
        return authored_drivetrain_hardware_rgba(y, wheel_cy)
    if rim or wheel_spokes:
        return authored_rim_hardware_rgba(x, y, wheel_cx, wheel_cy)
    if saddle_mount:
        return authored_saddle_mount_rgba(y, 29)
    if seat:
        return authored_saddle_rgba(x, y, 128, 22, 18)
    if crown:
        return authored_frame_junction_rgba(x, y, 132, 60, False, fork or frame_brace or neck)
    if fork or frame_brace or neck:
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
    crank = authored_crank_contains(x, y, wheel_cx, wheel_cy, 138)
    pedal = authored_pedal_contains(x, y, 138, 150)
    seat = authored_saddle_contains(x, y, 130, 23, 32, 13, 8, 34)

    neck = y >= 30 and y <= 60 and x >= 128 and x <= 136
    saddle_mount = (
        (seat or neck)
        and authored_saddle_mount_contains(x, y, 128, 136, 30)
    )
    crown_dx = x - 132
    crown_dy = y - 60
    crown = crown_dx * crown_dx + crown_dy * crown_dy <= 10 * 10
    frame_brace, wheel_spokes = authored_0541_p1_structural_detail(x, y)

    if hub:
        return authored_hub_hardware_rgba(x, y, wheel_cx, wheel_cy)
    if crank or pedal:
        return authored_drivetrain_hardware_rgba(y, wheel_cy)
    if rim or wheel_spokes:
        return authored_rim_hardware_rgba(x, y, wheel_cx, wheel_cy)
    if saddle_mount:
        return authored_saddle_mount_rgba(y, 30)
    if seat:
        return authored_saddle_rgba(x, y, 130, 23, 13)
    if crown:
        return authored_frame_junction_rgba(x, y, 132, 60, False, fork or frame_brace or neck)
    if fork or frame_brace or neck:
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
    crank = authored_crank_contains(x, y, wheel_cx, wheel_cy, 141)
    pedal = authored_pedal_contains(x, y, 141, 145)
    seat = authored_saddle_contains(x, y, 130, 22, 35, 12, 8, 36)

    neck = y >= 30 and y <= 60 and x >= 124 and x <= 132
    saddle_mount = (
        (seat or neck)
        and authored_saddle_mount_contains(x, y, 124, 132, 29)
    )
    crown_dx = x - 134
    crown_dy = y - 60
    crown = crown_dx * crown_dx + crown_dy * crown_dy <= 8 * 8
    frame_brace = authored_frame_brace(x, y, 134, 60, wheel_cx, wheel_cy)
    wheel_spokes = authored_wheel_spokes(x, y, wheel_cx, wheel_cy)

    if hub:
        return authored_hub_hardware_rgba(x, y, wheel_cx, wheel_cy)
    if crank or pedal:
        return authored_drivetrain_hardware_rgba(y, wheel_cy)
    if rim or wheel_spokes:
        return authored_rim_hardware_rgba(x, y, wheel_cx, wheel_cy)
    if saddle_mount:
        return authored_saddle_mount_rgba(y, 29)
    if seat:
        return authored_saddle_rgba(x, y, 130, 22, 12)
    if crown:
        return authored_frame_junction_rgba(x, y, 134, 60, False, fork or frame_brace or neck)
    if fork or frame_brace or neck:
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
    crank = authored_crank_contains(x, y, wheel_cx, wheel_cy, 145)
    pedal = authored_pedal_contains(x, y, 145, 149)

    # The bridge pose still carried a small right-heavy saddle block in the
    # true-density mismatch map. Shift/narrow without touching its recovered
    # outer envelope or wheel contact.
    seat = authored_saddle_contains(x, y, 120, 22, 32, 14, 8, 36)

    neck = y >= 30 and y <= 60 and x >= 128 and x <= 136
    saddle_mount = (
        (seat or neck)
        and authored_saddle_mount_contains(x, y, 128, 136, 29)
    )
    crown_dx = x - 136
    crown_dy = y - 60
    crown = crown_dx * crown_dx + crown_dy * crown_dy <= 8 * 8
    frame_brace = authored_frame_brace(x, y, 136, 60, wheel_cx, wheel_cy)
    wheel_spokes = authored_wheel_spokes(x, y, wheel_cx, wheel_cy)

    if hub:
        return authored_hub_hardware_rgba(x, y, wheel_cx, wheel_cy)
    if crank or pedal:
        return authored_drivetrain_hardware_rgba(y, wheel_cy)
    if rim or wheel_spokes:
        return authored_rim_hardware_rgba(x, y, wheel_cx, wheel_cy)
    if saddle_mount:
        return authored_saddle_mount_rgba(y, 29)
    if seat:
        return authored_saddle_rgba(x, y, 120, 22, 14)
    if crown:
        return authored_frame_junction_rgba(x, y, 136, 60, False, fork or frame_brace or neck)
    if fork or frame_brace or neck:
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
    crank = authored_crank_contains(x, y, wheel_cx, wheel_cy, 149)
    pedal = authored_pedal_contains(x, y, 149, 153)

    # True-density review showed the old saddle carried a broad block of
    # authored-only mass to the right. Shift/narrow the same smooth ellipse
    # while preserving the recovered whole-pose envelope and contact.
    seat = authored_saddle_contains(x, y, 116, 22, 32, 14, 8, 36)

    neck = y >= 30 and y <= 60 and x >= 132 and x <= 140
    saddle_mount = (
        (seat or neck)
        and authored_saddle_mount_contains(x, y, 132, 140, 29)
    )
    crown_dx = x - 140
    crown_dy = y - 60
    crown = crown_dx * crown_dx + crown_dy * crown_dy <= 8 * 8
    frame_brace = authored_frame_brace(x, y, 140, 60, wheel_cx, wheel_cy)
    wheel_spokes = authored_wheel_spokes(x, y, wheel_cx, wheel_cy)

    if hub:
        return authored_hub_hardware_rgba(x, y, wheel_cx, wheel_cy)
    if crank or pedal:
        return authored_drivetrain_hardware_rgba(y, wheel_cy)
    if rim or wheel_spokes:
        return authored_rim_hardware_rgba(x, y, wheel_cx, wheel_cy)
    if saddle_mount:
        return authored_saddle_mount_rgba(y, 29)
    if seat:
        return authored_saddle_rgba(x, y, 116, 22, 14)
    if crown:
        return authored_frame_junction_rgba(x, y, 140, 60, False, fork or frame_brace or neck)
    if fork or frame_brace or neck:
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
    crank = authored_crank_contains(x, y, wheel_cx, wheel_cy, 153)
    pedal = authored_pedal_contains(x, y, 153, 157)

    # The 057D mismatch map shows the same right-heavy saddle mass as 057E.
    # Shift left and narrow it without changing the stock-derived envelope or
    # the wheel-supplied contact anchor.
    seat = authored_saddle_contains(x, y, 112, 26, 28, 14, 12, 40)

    neck = y >= 30 and y <= 60 and x >= 136 and x <= 144
    saddle_mount = (
        (seat or neck)
        and authored_saddle_mount_contains(x, y, 136, 144, 33)
    )
    crown_dx = x - 144
    crown_dy = y - 60
    crown = crown_dx * crown_dx + crown_dy * crown_dy <= 8 * 8
    frame_brace = authored_frame_brace(x, y, 144, 60, wheel_cx, wheel_cy)
    wheel_spokes = authored_wheel_spokes(x, y, wheel_cx, wheel_cy)

    if hub:
        return authored_hub_hardware_rgba(x, y, wheel_cx, wheel_cy)
    if crank or pedal:
        return authored_drivetrain_hardware_rgba(y, wheel_cy)
    if rim or wheel_spokes:
        return authored_rim_hardware_rgba(x, y, wheel_cx, wheel_cy)
    if saddle_mount:
        return authored_saddle_mount_rgba(y, 33)
    if seat:
        return authored_saddle_rgba(x, y, 112, 26, 14)
    if crown:
        return authored_frame_junction_rgba(x, y, 144, 60, False, fork or frame_brace or neck)
    if fork or frame_brace or neck:
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


def sample_authored_057c_p1_fifth_family_rgba(x: int, y: int) -> bytes:
    """Continue the reviewed 057E->057D motion strip into the 057C stock pose."""
    if x < 0 or y < 0 or x >= W * 4 or y >= H * 4:
        return b"\x00\x00\x00\x00"

    # Stock advances the wheel-contact centre one logical pixel right again:
    # 057E [67,76] -> 057D [69,76] -> 057C [71,76].
    wheel_cx = 144
    wheel_cy = 120
    wx = x - wheel_cx
    wy = y - wheel_cy
    wr2 = wx * wx + wy * wy
    tire = wr2 <= 35 * 35 and wr2 >= 25 * 25
    rim = wr2 < 25 * 25 and wr2 >= 22 * 22
    hub = wr2 <= 5 * 5

    fork_center = 138 - (y - 60) // 11
    fork = y >= 60 and y <= 117 and x >= fork_center - 5 and x <= fork_center + 5
    crank = authored_crank_contains(x, y, wheel_cx, wheel_cy, 157)
    pedal = authored_pedal_contains(x, y, 157, 161)

    # Continue the leftward saddle progression from 057D so the authored
    # envelope reaches the measured stock x=20 edge while the wheel reaches
    # x=44. The rest of the material hierarchy is unchanged.
    seat = authored_saddle_contains(x, y, 108, 26, 28, 14, 12, 40)
    neck = y >= 30 and y <= 60 and x >= 140 and x <= 148
    saddle_mount = (
        (seat or neck)
        and authored_saddle_mount_contains(x, y, 140, 148, 33)
    )
    crown_dx = x - 148
    crown_dy = y - 60
    crown = crown_dx * crown_dx + crown_dy * crown_dy <= 8 * 8
    frame_brace = authored_frame_brace(x, y, 148, 60, wheel_cx, wheel_cy)
    wheel_spokes = authored_wheel_spokes(x, y, wheel_cx, wheel_cy)

    if hub:
        return authored_hub_hardware_rgba(x, y, wheel_cx, wheel_cy)
    if crank or pedal:
        return authored_drivetrain_hardware_rgba(y, wheel_cy)
    if rim or wheel_spokes:
        return authored_rim_hardware_rgba(x, y, wheel_cx, wheel_cy)
    if saddle_mount:
        return authored_saddle_mount_rgba(y, 33)
    if seat:
        return authored_saddle_rgba(x, y, 108, 26, 14)
    if crown:
        return authored_frame_junction_rgba(x, y, 148, 60, False, fork or frame_brace or neck)
    if fork or frame_brace or neck:
        return authored_red_frame_rgba(x, y)
    if tire:
        return authored_rubber_rgba(x, y, wheel_cx, wheel_cy)
    return b"\x00\x00\x00\x00"


def build_nineteenth_authored_candidate_rgba() -> bytes:
    return b"".join(
        sample_authored_057c_p1_fifth_family_rgba(x, y)
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
    crank = authored_crank_contains(x, y, wheel_cx, wheel_cy, 141)
    pedal = authored_pedal_contains(x, y, 141, 145)
    seat = authored_saddle_contains(x, y, 130, 22, 35, 12, 12, 36)

    neck = y >= 30 and y <= 60 and x >= 124 and x <= 132
    saddle_mount = (
        (seat or neck)
        and authored_saddle_mount_contains(x, y, 124, 132, 29)
    )
    crown_dx = x - 134
    crown_dy = y - 60
    crown = crown_dx * crown_dx + crown_dy * crown_dy <= 8 * 8
    frame_brace = authored_frame_brace(x, y, 134, 60, wheel_cx, wheel_cy)
    wheel_spokes = authored_wheel_spokes(x, y, wheel_cx, wheel_cy)

    if hub:
        return authored_hub_hardware_rgba(x, y, wheel_cx, wheel_cy)
    if crank or pedal:
        return authored_drivetrain_hardware_rgba(y, wheel_cy)
    if rim or wheel_spokes:
        return authored_rim_hardware_rgba(x, y, wheel_cx, wheel_cy)
    if saddle_mount:
        return authored_saddle_mount_rgba(y, 29)
    if seat:
        return authored_saddle_rgba(x, y, 130, 22, 12)
    if crown:
        return authored_frame_junction_rgba(x, y, 134, 60, True, fork or frame_brace or neck)
    if fork or frame_brace or neck:
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
    crank = authored_crank_contains(x, y, wheel_cx, wheel_cy, 137)
    pedal = authored_pedal_contains(x, y, 137, 141)
    # The 0541 P2 transition pose is over-broad on the left/top at true
    # density. Shift the same smooth saddle right/down and narrow it while the
    # wheel/fork continue to lock envelope and contact.
    seat_dx, seat_dy = x - 130, y - 26
    seat = authored_saddle_contains(x, y, 130, 26, 30, 12, 12, 40)
    neck = y >= 30 and y <= 60 and x >= 120 and x <= 128
    saddle_mount = (
        (seat or neck)
        and authored_saddle_mount_contains(x, y, 120, 128, 33)
    )
    crown_dx, crown_dy = x - 130, y - 60
    crown = crown_dx * crown_dx + crown_dy * crown_dy <= 8 * 8
    frame_brace = authored_frame_brace(x, y, 130, 60, wheel_cx, wheel_cy)
    wheel_spokes = authored_wheel_spokes(x, y, wheel_cx, wheel_cy)
    if hub:
        return authored_hub_hardware_rgba(x, y, wheel_cx, wheel_cy)
    if crank or pedal:
        return authored_drivetrain_hardware_rgba(y, wheel_cy)
    if rim or wheel_spokes:
        return authored_rim_hardware_rgba(x, y, wheel_cx, wheel_cy)
    if saddle_mount:
        return authored_saddle_mount_rgba(y, 33)
    if seat:
        return authored_saddle_rgba(x, y, 130, 26, 12)
    if crown:
        return authored_frame_junction_rgba(x, y, 130, 60, True, fork or frame_brace or neck)
    if fork or frame_brace or neck:
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
    crank = authored_crank_contains(x, y, wheel_cx, wheel_cy, 133)
    pedal = authored_pedal_contains(x, y, 133, 137)

    seat_dx, seat_dy = x - 130, y - 26
    seat = authored_saddle_contains(x, y, 130, 26, 35, 14, 16, 40)

    neck = y >= 30 and y <= 60 and x >= 116 and x <= 124
    saddle_mount = (
        (seat or neck)
        and authored_saddle_mount_contains(x, y, 116, 124, 33)
    )
    crown_dx, crown_dy = x - 126, y - 60
    crown = crown_dx * crown_dx + crown_dy * crown_dy <= 8 * 8
    frame_brace, wheel_spokes = authored_p2_structural_detail(
        x, y, 120, 126
    )

    if hub:
        return authored_hub_hardware_rgba(x, y, wheel_cx, wheel_cy)
    if crank or pedal:
        return authored_drivetrain_hardware_rgba(y, wheel_cy)
    if rim or wheel_spokes:
        return authored_rim_hardware_rgba(x, y, wheel_cx, wheel_cy)
    if saddle_mount:
        return authored_saddle_mount_rgba(y, 33)
    if seat:
        return authored_saddle_rgba(x, y, 130, 26, 14)
    if crown:
        return authored_frame_junction_rgba(x, y, 126, 60, True, fork or frame_brace or neck)
    if fork or frame_brace or neck:
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
    crank = authored_crank_contains(x, y, wheel_cx, wheel_cy, 131)
    pedal = authored_pedal_contains(x, y, 131, 135)

    seat_dx, seat_dy = x - 130, y - 30
    seat = authored_saddle_contains(x, y, 130, 30, 35, 12, 16, 40)

    neck = y >= 30 and y <= 60 and x >= 114 and x <= 122
    saddle_mount = (
        (seat or neck)
        and authored_saddle_mount_contains(x, y, 114, 122, 37)
    )
    crown_dx, crown_dy = x - 124, y - 60
    crown = crown_dx * crown_dx + crown_dy * crown_dy <= 8 * 8
    frame_brace, wheel_spokes = authored_p2_structural_detail(
        x, y, 116, 124
    )

    if hub:
        return authored_hub_hardware_rgba(x, y, wheel_cx, wheel_cy)
    if crank or pedal:
        return authored_drivetrain_hardware_rgba(y, wheel_cy)
    if rim or wheel_spokes:
        return authored_rim_hardware_rgba(x, y, wheel_cx, wheel_cy)
    if saddle_mount:
        return authored_saddle_mount_rgba(y, 37)
    if seat:
        return authored_saddle_rgba(x, y, 130, 30, 12)
    if crown:
        return authored_frame_junction_rgba(x, y, 124, 60, True, fork or frame_brace or neck)
    if fork or frame_brace or neck:
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



def sample_authored_057e_p1_companion_0d69_rgba(x: int, y: int) -> bytes:
    """Author the distinct 1306 P1 companion pose in the approved material language."""
    if x < 0 or y < 0 or x >= W * 4 or y >= H * 4:
        return b"\x00\x00\x00\x00"
    wheel_cx, wheel_cy = 136, 120
    wx, wy = x - wheel_cx, y - wheel_cy
    wr2 = wx * wx + wy * wy
    tire = wr2 <= 35 * 35 and wr2 >= 25 * 25
    rim = wr2 < 25 * 25 and wr2 >= 22 * 22
    hub = wr2 <= 5 * 5
    fork_center = 134 - (y - 60) // 11
    fork = y >= 60 and y <= 117 and x >= fork_center - 5 and x <= fork_center + 5
    crank = authored_crank_contains(x, y, wheel_cx, wheel_cy, 149)
    pedal = authored_pedal_contains(x, y, 149, 153)
    seat = authored_saddle_contains(x, y, 120, 22, 32, 14, 8, 36)
    neck = y >= 30 and y <= 60 and x >= 132 and x <= 140
    saddle_mount = (seat or neck) and authored_saddle_mount_contains(x, y, 132, 140, 29)
    crown_dx, crown_dy = x - 140, y - 60
    crown = crown_dx * crown_dx + crown_dy * crown_dy <= 8 * 8
    frame_brace = authored_frame_brace(x, y, 140, 60, wheel_cx, wheel_cy)
    wheel_spokes = authored_wheel_spokes(x, y, wheel_cx, wheel_cy)
    if hub:
        return authored_hub_hardware_rgba(x, y, wheel_cx, wheel_cy)
    if crank or pedal:
        return authored_drivetrain_hardware_rgba(y, wheel_cy)
    if rim or wheel_spokes:
        return authored_rim_hardware_rgba(x, y, wheel_cx, wheel_cy)
    if saddle_mount:
        return authored_saddle_mount_rgba(y, 29)
    if seat:
        return authored_saddle_rgba(x, y, 120, 22, 14)
    if crown:
        return authored_frame_junction_rgba(x, y, 140, 60, False, fork or frame_brace or neck)
    if fork or frame_brace or neck:
        return authored_red_frame_rgba(x, y)
    if tire:
        return authored_rubber_rgba(x, y, wheel_cx, wheel_cy)
    return b"\x00\x00\x00\x00"


def build_eleventh_authored_candidate_rgba() -> bytes:
    return b"".join(
        sample_authored_057e_p1_companion_0d69_rgba(x, y)
        for y in range(H * 4)
        for x in range(W * 4)
    )


def sample_authored_0544_p2_rgba(x: int, y: int) -> bytes:
    """Author the shared 0544 P2 pose used by both 1305-1306 guards."""
    if x < 0 or y < 0 or x >= W * 4 or y >= H * 4:
        return b"\x00\x00\x00\x00"
    wheel_cx, wheel_cy = 112, 120
    wx, wy = x - wheel_cx, y - wheel_cy
    wr2 = wx * wx + wy * wy
    tire = wr2 <= 36 * 36 and wr2 >= 25 * 25
    rim = wr2 < 25 * 25 and wr2 >= 22 * 22
    hub = wr2 <= 5 * 5
    fork_center = 112 - (y - 60) // 11
    fork = y >= 60 and y <= 117 and x >= fork_center - 5 and x <= fork_center + 5
    crank = authored_crank_contains(x, y, wheel_cx, wheel_cy, 127)
    pedal = authored_pedal_contains(x, y, 127, 131)
    seat = authored_saddle_contains(x, y, 134, 32, 35, 12, 16, 44)
    neck = y >= 30 and y <= 60 and x >= 110 and x <= 118
    saddle_mount = (seat or neck) and authored_saddle_mount_contains(x, y, 110, 118, 39)
    crown_dx, crown_dy = x - 120, y - 60
    crown = crown_dx * crown_dx + crown_dy * crown_dy <= 8 * 8
    frame_brace, wheel_spokes = authored_p2_structural_detail(x, y, 112, 120)
    if hub:
        return authored_hub_hardware_rgba(x, y, wheel_cx, wheel_cy)
    if crank or pedal:
        return authored_drivetrain_hardware_rgba(y, wheel_cy)
    if rim or wheel_spokes:
        return authored_rim_hardware_rgba(x, y, wheel_cx, wheel_cy)
    if saddle_mount:
        return authored_saddle_mount_rgba(y, 39)
    if seat:
        return authored_saddle_rgba(x, y, 134, 32, 12)
    if crown:
        return authored_frame_junction_rgba(x, y, 120, 60, True, fork or frame_brace or neck)
    if fork or frame_brace or neck:
        return authored_blue_frame_rgba(x, y)
    if tire:
        return authored_rubber_rgba(x, y, wheel_cx, wheel_cy)
    return b"\x00\x00\x00\x00"


def build_twelfth_authored_candidate_rgba() -> bytes:
    return b"".join(
        sample_authored_0544_p2_rgba(x, y)
        for y in range(H * 4)
        for x in range(W * 4)
    )


def sample_authored_0544_p1_frequency_rgba(x: int, y: int) -> bytes:
    """Reuse the approved 0544 geometry with only the proven player-color swap."""
    return recolor_authored_frame_rgba(
        sample_authored_0544_p2_rgba(x, y),
        blue_frame=False,
    )


def build_twentieth_authored_candidate_rgba() -> bytes:
    return b"".join(
        sample_authored_0544_p1_frequency_rgba(x, y)
        for y in range(H * 4)
        for x in range(W * 4)
    )


def sample_authored_0578_p2_frequency_rgba(x: int, y: int) -> bytes:
    """Author the measured 0578 P2 pose from the exact 1280-1286 stock reference."""
    if x < 0 or y < 0 or x >= W * 4 or y >= H * 4:
        return b"\x00\x00\x00\x00"

    wheel_cx, wheel_cy = 155, 111
    wx, wy = x - wheel_cx, y - wheel_cy
    wr2 = wx * wx + wy * wy
    tire = wr2 <= 36 * 36 and wr2 >= 26 * 26
    rim = wr2 < 26 * 26 and wr2 >= 22 * 22
    hub = wr2 <= 5 * 5

    wheel_spokes = (
        authored_segment_contains(x, y, 133, 111, 177, 111, 1)
        or authored_segment_contains(x, y, 144, 92, 166, 130, 1)
        or authored_segment_contains(x, y, 166, 92, 144, 130, 1)
    )
    seat = authored_segment_contains(x, y, 70, 27, 111, 47, 8)
    neck = authored_segment_contains(x, y, 108, 45, 124, 61, 5)
    fork = authored_segment_contains(x, y, 121, 58, 151, 106, 5)
    frame_brace = authored_segment_contains(x, y, 121, 58, 168, 106, 3)
    crank = authored_segment_contains(x, y, 155, 111, 170, 106, 2)
    pedal = authored_segment_contains(x, y, 170, 106, 180, 106, 2)
    crown_dx, crown_dy = x - 121, y - 58
    crown = crown_dx * crown_dx + crown_dy * crown_dy <= 8 * 8

    if hub:
        return authored_hub_hardware_rgba(x, y, wheel_cx, wheel_cy)
    if crank or pedal:
        return authored_drivetrain_hardware_rgba(y, wheel_cy)
    if rim or wheel_spokes:
        return authored_rim_hardware_rgba(x, y, wheel_cx, wheel_cy)
    if seat:
        return authored_saddle_rgba(x, y, 91, 32, 12)
    if neck and y < 53:
        return authored_saddle_mount_rgba(y, 49)
    if crown:
        return authored_frame_junction_rgba(
            x, y, 121, 58, True, fork or frame_brace or neck
        )
    if neck or fork or frame_brace:
        return authored_blue_frame_rgba(x, y)
    if tire:
        return authored_rubber_rgba(x, y, wheel_cx, wheel_cy)
    return b"\x00\x00\x00\x00"


def build_twenty_first_authored_candidate_rgba() -> bytes:
    return b"".join(
        sample_authored_0578_p2_frequency_rgba(x, y)
        for y in range(H * 4)
        for x in range(W * 4)
    )


def sample_authored_04b9_p1_broader_rgba(x: int, y: int) -> bytes:
    """Author the high-frequency dynamic P1 04B9 pose from canonical stock evidence."""
    if x < 0 or y < 0 or x >= W * 4 or y >= H * 4:
        return b"\x00\x00\x00\x00"

    wheel_cx, wheel_cy = 155, 111
    wx, wy = x - wheel_cx, y - wheel_cy
    wr2 = wx * wx + wy * wy
    tire = wr2 <= 36 * 36 and wr2 >= 26 * 26
    rim = wr2 < 26 * 26 and wr2 >= 22 * 22
    hub = wr2 <= 5 * 5
    wheel_spokes = (
        authored_segment_contains(x, y, 133, 111, 177, 111, 1)
        or authored_segment_contains(x, y, 144, 92, 166, 130, 1)
        or authored_segment_contains(x, y, 166, 92, 144, 130, 1)
    )
    # The 04B9 stock envelope is one logical pixel narrower on the left than
    # the nearby 0578 pose. Preserve the distinct silhouette instead of
    # aliasing the two stock states.
    seat = authored_segment_contains(x, y, 74, 27, 111, 47, 8)
    neck = authored_segment_contains(x, y, 108, 45, 124, 61, 5)
    fork = authored_segment_contains(x, y, 121, 58, 151, 106, 5)
    frame_brace = authored_segment_contains(x, y, 121, 58, 168, 106, 3)
    crank = authored_segment_contains(x, y, 155, 111, 170, 106, 2)
    pedal = authored_segment_contains(x, y, 170, 106, 180, 106, 2)
    crown_dx, crown_dy = x - 121, y - 58
    crown = crown_dx * crown_dx + crown_dy * crown_dy <= 8 * 8

    if hub:
        return authored_hub_hardware_rgba(x, y, wheel_cx, wheel_cy)
    if crank or pedal:
        return authored_drivetrain_hardware_rgba(y, wheel_cy)
    if rim or wheel_spokes:
        return authored_rim_hardware_rgba(x, y, wheel_cx, wheel_cy)
    if seat:
        return authored_saddle_rgba(x, y, 93, 32, 12)
    if neck and y < 53:
        return authored_saddle_mount_rgba(y, 49)
    if crown:
        return authored_frame_junction_rgba(
            x, y, 121, 58, False, fork or frame_brace or neck
        )
    if neck or fork or frame_brace:
        return authored_red_frame_rgba(x, y)
    if tire:
        return authored_rubber_rgba(x, y, wheel_cx, wheel_cy)
    return b"\x00\x00\x00\x00"


def build_twenty_second_authored_candidate_rgba() -> bytes:
    return b"".join(
        sample_authored_04b9_p1_broader_rgba(x, y)
        for y in range(H * 4)
        for x in range(W * 4)
    )


def sample_authored_0239_p1_broader_rgba(x: int, y: int) -> bytes:
    """Author the next measured P1 0239 dynamic-play pose."""
    if x < 0 or y < 0 or x >= W * 4 or y >= H * 4:
        return b"\x00\x00\x00\x00"
    wheel_cx, wheel_cy = 155, 111
    wx, wy = x - wheel_cx, y - wheel_cy
    wr2 = wx * wx + wy * wy
    tire = wr2 <= 36 * 36 and wr2 >= 26 * 26
    rim = wr2 < 26 * 26 and wr2 >= 22 * 22
    hub = wr2 <= 5 * 5
    wheel_spokes = (
        authored_segment_contains(x, y, 133, 111, 177, 111, 1)
        or authored_segment_contains(x, y, 144, 92, 166, 130, 1)
        or authored_segment_contains(x, y, 166, 92, 144, 130, 1)
    )
    seat = authored_segment_contains(x, y, 74, 25, 111, 46, 8)
    neck = authored_segment_contains(x, y, 106, 41, 124, 61, 5)
    fork = authored_segment_contains(x, y, 121, 58, 151, 106, 5)
    frame_brace = authored_segment_contains(x, y, 121, 58, 168, 106, 3)
    crank = authored_segment_contains(x, y, 155, 111, 170, 106, 2)
    pedal = authored_segment_contains(x, y, 170, 106, 180, 106, 2)
    crown_dx, crown_dy = x - 121, y - 58
    crown = crown_dx * crown_dx + crown_dy * crown_dy <= 8 * 8
    if hub:
        return authored_hub_hardware_rgba(x, y, wheel_cx, wheel_cy)
    if crank or pedal:
        return authored_drivetrain_hardware_rgba(y, wheel_cy)
    if rim or wheel_spokes:
        return authored_rim_hardware_rgba(x, y, wheel_cx, wheel_cy)
    if seat:
        return authored_saddle_rgba(x, y, 93, 31, 12)
    if neck and y < 52:
        return authored_saddle_mount_rgba(y, 47)
    if crown:
        return authored_frame_junction_rgba(
            x, y, 121, 58, False, fork or frame_brace or neck
        )
    if neck or fork or frame_brace:
        return authored_red_frame_rgba(x, y)
    if tire:
        return authored_rubber_rgba(x, y, wheel_cx, wheel_cy)
    return b"\x00\x00\x00\x00"


def build_twenty_third_authored_candidate_rgba() -> bytes:
    return b"".join(
        sample_authored_0239_p1_broader_rgba(x, y)
        for y in range(H * 4)
        for x in range(W * 4)
    )



_RED_TO_BLUE_FRAME_RGBA = {
    _rgba32(232, 83, 83): _rgba32(83, 115, 232),
    _rgba32(201, 52, 52): _rgba32(52, 77, 201),
    _rgba32(163, 37, 37): _rgba32(37, 58, 163),
    _rgba32(120, 24, 24): _rgba32(24, 40, 120),
    _rgba32(150, 35, 35): _rgba32(35, 51, 150),
}
_BLUE_TO_RED_FRAME_RGBA = {blue: red for red, blue in _RED_TO_BLUE_FRAME_RGBA.items()}


def recolor_authored_frame_rgba(pixel: bytes, *, blue_frame: bool) -> bytes:
    """Swap only approved colored-frame material; preserve alpha/neutral materials."""
    table = _RED_TO_BLUE_FRAME_RGBA if blue_frame else _BLUE_TO_RED_FRAME_RGBA
    return table.get(pixel, pixel)


def normalize_authored_frame_rgba(rgba: bytes) -> bytes:
    """Normalize only the authored red/blue frame material to stable role tokens."""
    red_values = list(_RED_TO_BLUE_FRAME_RGBA.keys())
    blue_values = list(_RED_TO_BLUE_FRAME_RGBA.values())
    mapping: dict[bytes, bytes] = {}
    for index, (red, blue) in enumerate(zip(red_values, blue_values), start=1):
        token = bytes((index, 0, 0, 255))
        mapping[red] = token
        mapping[blue] = token
    out = bytearray(rgba)
    for i in range(0, len(out), 4):
        token = mapping.get(bytes(out[i:i + 4]))
        if token is not None:
            out[i:i + 4] = token
    return bytes(out)


def sample_authored_0543_p1_third_family_rgba(x: int, y: int) -> bytes:
    return recolor_authored_frame_rgba(
        sample_authored_0543_p2_rgba(x, y),
        blue_frame=False,
    )


def sample_authored_0540d2c_p2_third_family_rgba(x: int, y: int) -> bytes:
    return recolor_authored_frame_rgba(
        sample_authored_0540_p1_predecessor_rgba(x, y),
        blue_frame=True,
    )


def sample_authored_0542_p1_third_family_rgba(x: int, y: int) -> bytes:
    return recolor_authored_frame_rgba(
        sample_authored_0542_p2_rgba(x, y),
        blue_frame=False,
    )


def sample_authored_0541d2d_p2_third_family_rgba(x: int, y: int) -> bytes:
    return recolor_authored_frame_rgba(
        sample_authored_0541_p1_companion_0d2d_rgba(x, y),
        blue_frame=True,
    )


def build_thirteenth_authored_candidate_rgba() -> bytes:
    return b"".join(
        sample_authored_0543_p1_third_family_rgba(x, y)
        for y in range(H * 4)
        for x in range(W * 4)
    )


def build_fourteenth_authored_candidate_rgba() -> bytes:
    return b"".join(
        sample_authored_0540d2c_p2_third_family_rgba(x, y)
        for y in range(H * 4)
        for x in range(W * 4)
    )


def build_fifteenth_authored_candidate_rgba() -> bytes:
    return b"".join(
        sample_authored_0542_p1_third_family_rgba(x, y)
        for y in range(H * 4)
        for x in range(W * 4)
    )


def build_sixteenth_authored_candidate_rgba() -> bytes:
    return b"".join(
        sample_authored_0541d2d_p2_third_family_rgba(x, y)
        for y in range(H * 4)
        for x in range(W * 4)
    )



def sample_authored_0540d0c_p2_fourth_family_rgba(x: int, y: int) -> bytes:
    # The fourth-family 0540+0D0C stock pose is a close companion-context
    # variant of the approved 0540+0D2C pose with the same envelope/contact.
    # Preserve the reviewed geometry/material treatment and transpose only the
    # player frame palette; family-local stock review decides shipping fitness.
    return recolor_authored_frame_rgba(
        sample_authored_0540_p1_predecessor_rgba(x, y),
        blue_frame=True,
    )


def sample_authored_057fd2a_p2_fourth_family_rgba(x: int, y: int) -> bytes:
    # Likewise start from the approved 057F bridge pose. The 0D2A companion
    # context differs slightly from 0D4A stock geometry, but shares the same
    # recovered envelope/contact and is reviewed against its own stock raster.
    return recolor_authored_frame_rgba(
        sample_authored_057f_p1_companion_0d4a_rgba(x, y),
        blue_frame=True,
    )


def build_seventeenth_authored_candidate_rgba() -> bytes:
    return b"".join(
        sample_authored_0540d0c_p2_fourth_family_rgba(x, y)
        for y in range(H * 4)
        for x in range(W * 4)
    )


def build_eighteenth_authored_candidate_rgba() -> bytes:
    return b"".join(
        sample_authored_057fd2a_p2_fourth_family_rgba(x, y)
        for y in range(H * 4)
        for x in range(W * 4)
    )

def authored_candidate_rgba_for_entry(entry: dict) -> tuple[bytes, str, str]:
    """Return authored RGBA plus the expected generator and native sampler."""
    rid = entry["representation_id"]
    authored_meta = entry.get("authored_candidate") or {}
    reused_from = authored_meta.get("reused_from_representation_id")
    if reused_from and reused_from != rid:
        proxy = dict(entry)
        proxy["representation_id"] = reused_from
        return authored_candidate_rgba_for_entry(proxy)
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
    if rid == FIFTEENTH_AUTHORED_REPRESENTATION_ID:
        return (
            build_fifth_authored_candidate_rgba(),
            "tools/build_racer_hd_asset_dossier.py::build_fifth_authored_candidate_rgba",
            "sample_racer_hd_authored_057e_p1_with_p2_0543",
        )
    if rid == SIXTEENTH_AUTHORED_REPRESENTATION_ID:
        return (
            build_eleventh_authored_candidate_rgba(),
            "tools/build_racer_hd_asset_dossier.py::build_eleventh_authored_candidate_rgba",
            "sample_racer_hd_authored_057e_p1_companion_0d69",
        )
    if rid in (SEVENTEENTH_AUTHORED_REPRESENTATION_ID, EIGHTEENTH_AUTHORED_REPRESENTATION_ID):
        return (
            build_twelfth_authored_candidate_rgba(),
            "tools/build_racer_hd_asset_dossier.py::build_twelfth_authored_candidate_rgba",
            "sample_racer_hd_authored_0544_p2",
        )
    if rid == NINETEENTH_AUTHORED_REPRESENTATION_ID:
        return (
            build_thirteenth_authored_candidate_rgba(),
            "tools/build_racer_hd_asset_dossier.py::build_thirteenth_authored_candidate_rgba",
            "sample_racer_hd_authored_0543_p1_third_family",
        )
    if rid == TWENTIETH_AUTHORED_REPRESENTATION_ID:
        return (
            build_fourteenth_authored_candidate_rgba(),
            "tools/build_racer_hd_asset_dossier.py::build_fourteenth_authored_candidate_rgba",
            "sample_racer_hd_authored_0540d2c_p2_third_family",
        )
    if rid == TWENTY_FIRST_AUTHORED_REPRESENTATION_ID:
        return (
            build_fifteenth_authored_candidate_rgba(),
            "tools/build_racer_hd_asset_dossier.py::build_fifteenth_authored_candidate_rgba",
            "sample_racer_hd_authored_0542_p1_third_family",
        )
    if rid == TWENTY_SECOND_AUTHORED_REPRESENTATION_ID:
        return (
            build_sixteenth_authored_candidate_rgba(),
            "tools/build_racer_hd_asset_dossier.py::build_sixteenth_authored_candidate_rgba",
            "sample_racer_hd_authored_0541d2d_p2_third_family",
        )
    if rid in (TWENTY_THIRD_AUTHORED_REPRESENTATION_ID, TWENTY_FIFTH_AUTHORED_REPRESENTATION_ID):
        return (
            build_third_authored_candidate_rgba(),
            "tools/build_racer_hd_asset_dossier.py::build_third_authored_candidate_rgba",
            "sample_racer_hd_authored_0540_p1_predecessor",
        )
    if rid in (TWENTY_FOURTH_AUTHORED_REPRESENTATION_ID, TWENTY_EIGHTH_AUTHORED_REPRESENTATION_ID):
        return (
            build_eighteenth_authored_candidate_rgba(),
            "tools/build_racer_hd_asset_dossier.py::build_eighteenth_authored_candidate_rgba",
            "sample_racer_hd_authored_057fd2a_p2_fourth_family",
        )
    if rid == TWENTY_SIXTH_AUTHORED_REPRESENTATION_ID:
        return (
            build_seventeenth_authored_candidate_rgba(),
            "tools/build_racer_hd_asset_dossier.py::build_seventeenth_authored_candidate_rgba",
            "sample_racer_hd_authored_0540d0c_p2_fourth_family",
        )
    if rid == TWENTY_SEVENTH_AUTHORED_REPRESENTATION_ID:
        return (
            build_first_authored_candidate_rgba(),
            "tools/build_racer_hd_asset_dossier.py::build_first_authored_candidate_rgba",
            "sample_racer_hd_authored_0541_p1",
        )
    if rid == TWENTY_NINTH_AUTHORED_REPRESENTATION_ID:
        return (
            build_fifth_authored_candidate_rgba(),
            "tools/build_racer_hd_asset_dossier.py::build_fifth_authored_candidate_rgba",
            "sample_racer_hd_authored_057e_p1_with_p2_0543",
        )
    if rid == THIRTIETH_AUTHORED_REPRESENTATION_ID:
        return (
            build_ninth_authored_candidate_rgba(),
            "tools/build_racer_hd_asset_dossier.py::build_ninth_authored_candidate_rgba",
            "sample_racer_hd_authored_0542_p2",
        )
    if rid in (THIRTY_FIRST_AUTHORED_REPRESENTATION_ID, THIRTY_THIRD_AUTHORED_REPRESENTATION_ID):
        return (
            build_sixth_authored_candidate_rgba(),
            "tools/build_racer_hd_asset_dossier.py::build_sixth_authored_candidate_rgba",
            "sample_racer_hd_authored_057d_p1_with_p2_0543",
        )
    if rid == THIRTY_SECOND_AUTHORED_REPRESENTATION_ID:
        return (
            build_eighth_authored_candidate_rgba(),
            "tools/build_racer_hd_asset_dossier.py::build_eighth_authored_candidate_rgba",
            "sample_racer_hd_authored_0541_p2_predecessor",
        )
    if rid in (THIRTY_FOURTH_AUTHORED_REPRESENTATION_ID, THIRTY_SIXTH_AUTHORED_REPRESENTATION_ID):
        return (
            build_seventh_authored_candidate_rgba(),
            "tools/build_racer_hd_asset_dossier.py::build_seventh_authored_candidate_rgba",
            "sample_racer_hd_authored_0540_p2_baseline",
        )
    if rid == THIRTY_FIFTH_AUTHORED_REPRESENTATION_ID:
        return (
            build_nineteenth_authored_candidate_rgba(),
            "tools/build_racer_hd_asset_dossier.py::build_nineteenth_authored_candidate_rgba",
            "sample_racer_hd_authored_057c_p1_fifth_family",
        )
    if rid == THIRTY_SEVENTH_AUTHORED_REPRESENTATION_ID:
        return (
            build_twentieth_authored_candidate_rgba(),
            "tools/build_racer_hd_asset_dossier.py::build_twentieth_authored_candidate_rgba",
            "sample_racer_hd_authored_0544_p1_frequency",
        )
    if rid == THIRTY_EIGHTH_AUTHORED_REPRESENTATION_ID:
        return (
            build_twenty_first_authored_candidate_rgba(),
            "tools/build_racer_hd_asset_dossier.py::build_twenty_first_authored_candidate_rgba",
            "sample_racer_hd_authored_0578_p2_frequency",
        )
    if rid == THIRTY_NINTH_AUTHORED_REPRESENTATION_ID:
        return (
            build_twenty_second_authored_candidate_rgba(),
            "tools/build_racer_hd_asset_dossier.py::build_twenty_second_authored_candidate_rgba",
            "sample_racer_hd_authored_04b9_p1_broader",
        )
    if rid == FORTIETH_AUTHORED_REPRESENTATION_ID:
        return (
            build_twenty_third_authored_candidate_rgba(),
            "tools/build_racer_hd_asset_dossier.py::build_twenty_third_authored_candidate_rgba",
            "sample_racer_hd_authored_0239_p1_broader",
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


def exact_window_rows(
    trace_report: dict,
    start: int,
    end: int,
    players: tuple[str, ...] = ("p1", "p2"),
) -> list[dict]:
    if start > end:
        raise ValueError("window start must not exceed window end")
    if not players or any(player not in ("p1", "p2") for player in players):
        raise ValueError(f"invalid review players: {players}")
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
        if players == ("p1", "p2") and not row.get("fully_registered"):
            raise ValueError(f"frame {row['frame']} is not fully registered")
        for player in players:
            key = f"{player}_representation_id"
            if not row.get(key):
                raise ValueError(f"frame {row['frame']} lacks {key}")
    return rows


def observation_map(
    rows: list[dict],
    players: tuple[str, ...] = ("p1", "p2"),
) -> dict[str, dict]:
    observed: dict[str, dict] = {}
    for row in rows:
        frame = int(row["frame"])
        for player in players:
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
    players: tuple[str, ...] = ("p1", "p2"),
) -> tuple[dict, dict[str, dict[str, bytes]]]:
    rows = exact_window_rows(trace_report, start, end, players)
    entries = registry_by_representation(registry)
    observed = observation_map(rows, players)
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
        reuse_proof = None
        palette_reuse_proof = None
        if authored_meta is not None and authored_meta.get("reused_from_representation_id"):
            source_id = authored_meta["reused_from_representation_id"]
            source_entry = entries.get(source_id)
            if source_entry is None:
                raise ValueError(f"{rid} reuse source is not registered: {source_id}")
            if source_entry["player"] != entry["player"]:
                raise ValueError(f"{rid} reuse source crosses players: {source_id}")
            source_stock = build_stock_rgba(rom, source_entry)
            if source_stock != stock:
                raise ValueError(
                    f"{rid} reuse source stock RGBA differs from target: {source_id}"
                )
            source_authored, _source_generator, _source_sampler = (
                authored_candidate_rgba_for_entry(source_entry)
            )
            reuse_proof = {
                "source_representation_id": source_id,
                "same_player": True,
                "stock_rgba_byte_identical": True,
                "stock_rgba_sha256": sha256(stock),
                "source_stock_rgba_sha256": sha256(source_stock),
                "source_authored_rgba_sha256": sha256(source_authored),
            }
        if authored_meta is not None and authored_meta.get("palette_reused_from_representation_id"):
            source_id = authored_meta["palette_reused_from_representation_id"]
            source_entry = entries.get(source_id)
            if source_entry is None:
                raise ValueError(f"{rid} palette reuse source is not registered: {source_id}")
            source_stock = build_stock_rgba(rom, source_entry)
            roles = palette_role_indices(rom)
            declared_roles = authored_meta.get("palette_normalization_role_indices")
            if declared_roles != roles:
                raise ValueError(
                    f"{rid} palette role declaration drift: {declared_roles} != {roles}"
                )
            target_palette = rgba_palette(
                rom, int(entry["palette_asset_id"], 16)
            )
            source_palette = rgba_palette(
                rom, int(source_entry["palette_asset_id"], 16)
            )
            target_normalized = palette_normalized_rgba(stock, target_palette, roles)
            source_normalized = palette_normalized_rgba(source_stock, source_palette, roles)
            if target_normalized != source_normalized:
                raise ValueError(
                    f"{rid} palette-normalized stock differs from source: {source_id}"
                )
            normalized_hash = sha256(target_normalized)
            if normalized_hash != authored_meta.get("palette_normalized_stock_sha256"):
                raise ValueError(
                    f"{rid} palette-normalized stock hash drift: {normalized_hash}"
                )
            source_authored, _source_generator, _source_sampler = (
                authored_candidate_rgba_for_entry(source_entry)
            )
            palette_reuse_proof = {
                "source_representation_id": source_id,
                "cross_player": source_entry["player"] != entry["player"],
                "normalized_role_indices": roles,
                "stock_normalized_byte_identical": True,
                "normalized_stock_sha256": normalized_hash,
                "source_stock_rgba_sha256": sha256(source_stock),
                "target_stock_rgba_sha256": sha256(stock),
                "source_authored_rgba_sha256": sha256(source_authored),
                "authored_transform": "tools/build_racer_hd_asset_dossier.py::recolor_authored_frame_rgba",
            }
        if authored_meta is not None:
            authored_rgba, expected_generator, native_sampler = (
                authored_candidate_rgba_for_entry(entry)
            )
            if authored_meta.get("artifact_generator") != expected_generator:
                raise ValueError(f"unsupported authored candidate generator for {rid}")
            authored_png = encode_png_rgba(W * 4, H * 4, authored_rgba)
            if palette_reuse_proof is not None:
                source_id = palette_reuse_proof["source_representation_id"]
                source_entry = entries[source_id]
                source_authored, _source_generator, _source_sampler = (
                    authored_candidate_rgba_for_entry(source_entry)
                )
                target_authored_normalized = normalize_authored_frame_rgba(authored_rgba)
                source_authored_normalized = normalize_authored_frame_rgba(source_authored)
                if target_authored_normalized != source_authored_normalized:
                    raise ValueError(
                        f"{rid} normalized authored output differs from palette source: {source_id}"
                    )
                palette_reuse_proof["authored_normalized_byte_identical"] = True
                palette_reuse_proof["normalized_authored_sha256"] = sha256(
                    target_authored_normalized
                )
                palette_reuse_proof["target_authored_rgba_sha256"] = sha256(
                    authored_rgba
                )
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
                "shipping_approval_source": (
                    authored_candidate.get("shipping_approval_source")
                    if authored_candidate is not None
                    else None
                ),
                "evidence_packet_ready": True,
                "authored_candidate": authored_candidate,
                "reuse_proof": reuse_proof,
                "palette_reuse_proof": palette_reuse_proof,
                "resolved_decisions": dict(RESOLVED_VISUAL_LANGUAGE),
                "pending_decisions": list(PENDING_ART_DECISIONS),
                "visual_language_authority": "docs/HD-ART-DIRECTION.md",
                "display_geometry_authority": "docs/DISPLAY-PRESENTATION-POLICY.md",
            },
        })

    timeline = [
        {
            "frame": int(row["frame"]),
            **{
                f"{player}_representation_id": row[f"{player}_representation_id"]
                for player in players
            },
        }
        for row in rows
    ]

    dossier = {
        "schema_version": 1,
        "family": registry["family"],
        "purpose": (
            "Approval-oriented evidence packet for a continuously registered "
            "ordinary-race Racer HD review window."
        ),
        "review_players": list(players),
        "temporal_window": {
            "start": start,
            "end": end,
            "frame_count": end - start + 1,
            "source": "registered_composition_coverage from deterministic native semantic trace",
            "all_frames_exactly_registered": players == ("p1", "p2"),
            "all_review_players_exactly_registered": True,
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
            "fully_registered_window": players == ("p1", "p2"),
            "review_players_registered_window": True,
            "registry_representation_ids_unique": True,
            "stock_geometry_rederived_from_rom": True,
            "registered_anchors_match_rederived_stock": True,
            "candidate_status_is_contract_only": all(
                rep["current_contract_candidate"]["approval_status"]
                == "contract-only candidate; not approved shipping art"
                for rep in representations
            ),
            "authored_shipping_approval_externalized": all(
                rep["art_review"]["authored_candidate"] is not None
                and isinstance(rep["art_review"]["shipping_approval_source"], str)
                and rep["art_review"]["shipping_approval_source"].startswith(
                    "analysis/data/racer-hd-art-approval"
                )
                and rep["art_review"]["shipping_approval_source"].endswith(".json")
                for rep in representations
            ),
            "ready_for_art_review": True,
        },
        "remaining_scope": {
            "phase_e_globally_complete": False,
            "ordinary_race_racer_family_semantic_gate_reached": True,
            "shipping_art_approval_source": (
                "analysis/data/racer-hd-art-approval.json joined by "
                "tools/build_racer_hd_shipping_readiness.py"
            ),
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
    ap.add_argument(
        "--player",
        action="append",
        choices=("p1", "p2"),
        help="review only this player; repeat for both. Omit to require both players.",
    )
    args = ap.parse_args()
    players = tuple(args.player) if args.player else ("p1", "p2")

    dossier, assets = build_dossier(
        args.rom.read_bytes(),
        json.loads(args.registry.read_text(encoding="utf-8")),
        json.loads(args.trace.read_text(encoding="utf-8")),
        args.window_start,
        args.window_end,
        players,
    )
    write_dossier(args.output_dir, dossier, assets)
    print(json.dumps(dossier, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
