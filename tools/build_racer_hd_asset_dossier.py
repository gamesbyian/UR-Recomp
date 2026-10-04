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


def authored_metal_rgba(x: int, y: int) -> bytes:
    light = (255 - x) + (255 - y)
    if light > 305:
        return _rgba32(246, 244, 242)
    if light > 275:
        return _rgba32(217, 213, 208)
    return _rgba32(159, 153, 142)


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
    seat = (
        (seat_dx * seat_dx) * 11 + (seat_dy * seat_dy) * 30 <= 30 * 30 * 11
        and y >= 12 and y <= 32
    )

    neck = y >= 30 and y <= 60 and x >= 128 and x <= 136
    crown_dx = x - 132
    crown_dy = y - 60
    crown = crown_dx * crown_dx + crown_dy * crown_dy <= 10 * 10

    if hub or rim or crank or pedal:
        return authored_metal_rgba(x, y)
    if seat:
        seat_light = (255 - x) + (255 - y)
        return _rgba32(75, 71, 65) if seat_light > 350 else _rgba32(43, 39, 32)
    if fork or neck or crown:
        return authored_red_frame_rgba(x, y)
    if tire:
        tire_light = (255 - x) + (255 - y)
        return _rgba32(64, 60, 53) if tire_light > 310 else _rgba32(32, 29, 23)
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
    seat = (
        (seat_dx * seat_dx) * 13 * 13
        + (seat_dy * seat_dy) * 32 * 32
        <= 32 * 32 * 13 * 13
        and y >= 8 and y <= 34
    )

    neck = y >= 30 and y <= 60 and x >= 128 and x <= 136
    crown_dx = x - 132
    crown_dy = y - 60
    crown = crown_dx * crown_dx + crown_dy * crown_dy <= 10 * 10

    if hub or rim or crank or pedal:
        return authored_metal_rgba(x, y)
    if seat:
        seat_light = (255 - x) + (255 - y)
        return _rgba32(75, 71, 65) if seat_light > 350 else _rgba32(43, 39, 32)
    if fork or neck or crown:
        return authored_red_frame_rgba(x, y)
    if tire:
        tire_light = (255 - x) + (255 - y)
        return _rgba32(64, 60, 53) if tire_light > 310 else _rgba32(32, 29, 23)
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
    seat = (
        (seat_dx * seat_dx) * 12 * 12
        + (seat_dy * seat_dy) * 35 * 35
        <= 35 * 35 * 12 * 12
        and y >= 8 and y <= 36
    )

    neck = y >= 30 and y <= 60 and x >= 124 and x <= 132
    crown_dx = x - 134
    crown_dy = y - 60
    crown = crown_dx * crown_dx + crown_dy * crown_dy <= 8 * 8

    if hub or rim or crank or pedal:
        return authored_metal_rgba(x, y)
    if seat:
        seat_light = (255 - x) + (255 - y)
        return _rgba32(75, 71, 65) if seat_light > 350 else _rgba32(43, 39, 32)
    if fork or neck or crown:
        return authored_red_frame_rgba(x, y)
    if tire:
        tire_light = (255 - x) + (255 - y)
        return _rgba32(64, 60, 53) if tire_light > 310 else _rgba32(32, 29, 23)
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

    seat_dx = x - 124
    seat_dy = y - 22
    seat = (
        (seat_dx * seat_dx) * 14 * 14
        + (seat_dy * seat_dy) * 35 * 35
        <= 35 * 35 * 14 * 14
        and y >= 8 and y <= 36
    )

    neck = y >= 30 and y <= 60 and x >= 128 and x <= 136
    crown_dx = x - 136
    crown_dy = y - 60
    crown = crown_dx * crown_dx + crown_dy * crown_dy <= 8 * 8

    if hub or rim or crank or pedal:
        return authored_metal_rgba(x, y)
    if seat:
        seat_light = (255 - x) + (255 - y)
        return _rgba32(75, 71, 65) if seat_light > 350 else _rgba32(43, 39, 32)
    if fork or neck or crown:
        return authored_red_frame_rgba(x, y)
    if tire:
        tire_light = (255 - x) + (255 - y)
        return _rgba32(64, 60, 53) if tire_light > 310 else _rgba32(32, 29, 23)
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

    seat_dx = x - 124
    seat_dy = y - 22
    seat = (
        (seat_dx * seat_dx) * 14 * 14
        + (seat_dy * seat_dy) * 39 * 39
        <= 39 * 39 * 14 * 14
        and y >= 8 and y <= 36
    )

    neck = y >= 30 and y <= 60 and x >= 132 and x <= 140
    crown_dx = x - 140
    crown_dy = y - 60
    crown = crown_dx * crown_dx + crown_dy * crown_dy <= 8 * 8

    if hub or rim or crank or pedal:
        return authored_metal_rgba(x, y)
    if seat:
        seat_light = (255 - x) + (255 - y)
        return _rgba32(75, 71, 65) if seat_light > 350 else _rgba32(43, 39, 32)
    if fork or neck or crown:
        return authored_red_frame_rgba(x, y)
    if tire:
        tire_light = (255 - x) + (255 - y)
        return _rgba32(64, 60, 53) if tire_light > 310 else _rgba32(32, 29, 23)
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

    fork_center = 138 - (y - 60) // 11
    fork = y >= 60 and y <= 117 and x >= fork_center - 5 and x <= fork_center + 5
    crank = y >= 116 and y <= 123 and x >= 123 and x <= 152
    pedal = y >= 113 and y <= 118 and x >= 153 and x <= 157

    seat_dx = x - 124
    seat_dy = y - 26
    seat = (
        (seat_dx * seat_dx) * 14 * 14
        + (seat_dy * seat_dy) * 39 * 39
        <= 39 * 39 * 14 * 14
        and y >= 12 and y <= 40
    )

    neck = y >= 30 and y <= 60 and x >= 136 and x <= 144
    crown_dx = x - 144
    crown_dy = y - 60
    crown = crown_dx * crown_dx + crown_dy * crown_dy <= 8 * 8

    if hub or rim or crank or pedal:
        return authored_metal_rgba(x, y)
    if seat:
        seat_light = (255 - x) + (255 - y)
        return _rgba32(75, 71, 65) if seat_light > 350 else _rgba32(43, 39, 32)
    if fork or neck or crown:
        return authored_red_frame_rgba(x, y)
    if tire:
        tire_light = (255 - x) + (255 - y)
        return _rgba32(64, 60, 53) if tire_light > 310 else _rgba32(32, 29, 23)
    return b"\x00\x00\x00\x00"


def build_sixth_authored_candidate_rgba() -> bytes:
    return b"".join(
        sample_authored_057d_p1_with_p2_0543_rgba(x, y)
        for y in range(H * 4)
        for x in range(W * 4)
    )


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
    intersection = len(candidate & stock)
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
            if rid == FIRST_AUTHORED_REPRESENTATION_ID:
                expected_generator = (
                    "tools/build_racer_hd_asset_dossier.py::"
                    "build_first_authored_candidate_rgba"
                )
                authored_rgba = build_first_authored_candidate_rgba()
                native_sampler = "sample_racer_hd_authored_0541_p1"
            elif rid == SECOND_AUTHORED_REPRESENTATION_ID:
                expected_generator = (
                    "tools/build_racer_hd_asset_dossier.py::"
                    "build_second_authored_candidate_rgba"
                )
                authored_rgba = build_second_authored_candidate_rgba()
                native_sampler = "sample_racer_hd_authored_0541_p1_companion_0d2d"
            elif rid in (
                THIRD_AUTHORED_REPRESENTATION_ID,
                FOURTH_AUTHORED_REPRESENTATION_ID,
            ):
                expected_generator = (
                    "tools/build_racer_hd_asset_dossier.py::"
                    "build_third_authored_candidate_rgba"
                )
                authored_rgba = build_third_authored_candidate_rgba()
                native_sampler = "sample_racer_hd_authored_0540_p1_predecessor"
            elif rid == FIFTH_AUTHORED_REPRESENTATION_ID:
                expected_generator = (
                    "tools/build_racer_hd_asset_dossier.py::"
                    "build_fourth_authored_candidate_rgba"
                )
                authored_rgba = build_fourth_authored_candidate_rgba()
                native_sampler = "sample_racer_hd_authored_057f_p1_companion_0d4a"
            elif rid == SIXTH_AUTHORED_REPRESENTATION_ID:
                expected_generator = (
                    "tools/build_racer_hd_asset_dossier.py::"
                    "build_fifth_authored_candidate_rgba"
                )
                authored_rgba = build_fifth_authored_candidate_rgba()
                native_sampler = "sample_racer_hd_authored_057e_p1_with_p2_0543"
            elif rid == SEVENTH_AUTHORED_REPRESENTATION_ID:
                expected_generator = (
                    "tools/build_racer_hd_asset_dossier.py::"
                    "build_sixth_authored_candidate_rgba"
                )
                authored_rgba = build_sixth_authored_candidate_rgba()
                native_sampler = "sample_racer_hd_authored_057d_p1_with_p2_0543"
            else:
                raise ValueError(f"unsupported authored candidate registration: {rid}")
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
