#!/usr/bin/env python3
"""Optional source-locked 2026 outboard crank/axle clearance study.

The owner-approved straight collar, thin spokes, near-correct saddle,
symmetric rounded fork and the unapproved canonical source stay untouched.
This study preserves opposite crank phases while moving them outside the
fork legs and joining them to a slim, symmetric through-axle. It is NOT an
approved original 1994 joint design, likeness or shipping art.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

try:
    from tools.art.rounded_fork_clearance_review import (
        REPAIRED_SOURCE_SHA256, clearance_repaired_fork_source,
    )
    from tools.art.collar_transition_review import assert_seatpost_aligned
except ModuleNotFoundError:
    from rounded_fork_clearance_review import (
        REPAIRED_SOURCE_SHA256, clearance_repaired_fork_source,
    )
    from collar_transition_review import assert_seatpost_aligned

OUTBOARD_SOURCE_SHA256 = "f53c84fc040c8c0551b7313a26e34704e3b850e374e6c7b8e138ae1553da6e3a"

PATCHES = (
    ("p1=[0.31*cos(phase),0.39,0.31*sin(phase)];",
     "p1=[0.31*cos(phase),0.56,0.31*sin(phase)];"),
    ("p2=[-0.31*cos(phase),-0.39,-0.31*sin(phase)];",
     "p2=[-0.31*cos(phase),-0.56,-0.31*sin(phase)];"),
    ("member([0,0.19,0],p1,0.055,0.036);",
     "member([0,0.475,0],p1,0.055,0.036);"),
    ("member([0,-0.19,0],p2,0.055,0.036);",
     "member([0,-0.475,0],p2,0.055,0.036);"),
    ("color([0.52,0.60,0.67])rotate([90,0,0])cylinder(h=0.56,r=0.13,center=true);",
     """color([0.52,0.60,0.67])union(){
    rotate([90,0,0])cylinder(h=0.56,r=0.13,center=true);
    // Narrow, symmetric through-axle joins the outboard cranks.
    rotate([90,0,0])cylinder(h=1.08,r=0.065,center=true);
  }"""),
)

# All dimensions are explicitly source-owned. No fitted original 1994 law.
CRANK_RADIUS_XZ = 0.31
CRANK_BASE_Y = 0.475
CRANK_BASE_RADIUS = 0.055
CRANK_TIP_RADIUS = 0.036
PEDAL_CENTER_Y = 0.56
PEDAL_BLOCK_HALF_Y = 0.17 / 2
PEDAL_ROUND_RADIUS = 0.036
TREAD_OFFSET_Y = -0.124
TREAD_HALF_Y = 0.012 / 2
AXLE_EXTENSION_HALF_Y = 1.08 / 2


def outboard_pedal_source(canonical_bytes: bytes) -> bytes:
    """Make one exact, auditable source candidate; preserve the old review."""
    rounded = clearance_repaired_fork_source(canonical_bytes)
    if hashlib.sha256(rounded).hexdigest() != REPAIRED_SOURCE_SHA256:
        raise ValueError("rounded-fork input differs from qualified review source")
    source = rounded.decode("utf-8")
    for old, new in PATCHES:
        if source.count(old) != 1 or new in source:
            raise ValueError("unexpected authored pedal/axle geometry")
        source = source.replace(old, new)
    assert_seatpost_aligned(source)
    result = source.encode("utf-8")
    if hashlib.sha256(result).hexdigest() != OUTBOARD_SOURCE_SHA256:
        raise ValueError("outboard candidate SCAD differs from source-locked geometry")
    return result


def continuous_clearance_bounds(blue_fork_max_abs_y: float) -> dict:
    """Conservative 360-degree axis-separation and radial tube envelopes.

    The 2026 coloured fork is a triangle mesh; linear interpolation cannot
    exceed its vertices' maximum absolute Y coordinate. The crank hull of
    two source spheres lies within its swept Y range, and both pedal bodies
    are box plus sphere Minkowski sums. These are *whole-volume* bounds, not
    a discrete phase-sampling extrapolation. Only the blue fork material is
    covered: the joined axle is intentionally excluded.
    """
    if not math.isfinite(blue_fork_max_abs_y) or blue_fork_max_abs_y < 0:
        raise ValueError("finite nonnegative actual blue-fork Y extent required")
    body_y = PEDAL_CENTER_Y - PEDAL_BLOCK_HALF_Y - PEDAL_ROUND_RADIUS
    crank_y = CRANK_BASE_Y - max(CRANK_BASE_RADIUS, CRANK_TIP_RADIUS)
    # Both original orange-tread boxes remain offset toward negative Y;
    # report the nearer (+Y) one conservatively, without implying symmetry.
    tread_y = PEDAL_CENTER_Y + TREAD_OFFSET_Y - TREAD_HALF_Y
    minimum = min(body_y, crank_y, tread_y)
    max_body_radial = CRANK_RADIUS_XZ + math.hypot(
        .39 / 2 + PEDAL_ROUND_RADIUS,
        .115 / 2 + PEDAL_ROUND_RADIUS)
    max_crank_radial = CRANK_RADIUS_XZ + max(CRANK_BASE_RADIUS, CRANK_TIP_RADIUS)
    max_tread_radial = CRANK_RADIUS_XZ + math.hypot(.25 / 2, .064 / 2)
    max_radial = max(max_body_radial, max_crank_radial, max_tread_radial)
    # Torus inner radial bounds, irrespective of material Y or crank phase.
    return {
        "coloured_fork_max_abs_y_from_actual_glb": float(blue_fork_max_abs_y),
        "crank_min_abs_y": crank_y,
        "footpad_min_abs_y": body_y,
        "positive_tread_min_abs_y": tread_y,
        "continuous_fork_vs_all_pedal_material_y_gap_lower_bound":
            minimum - blue_fork_max_abs_y,
        "continuous_tire_radial_gap_lower_bound": (.85 - .15) - max_radial,
        "continuous_nearside_stripe_radial_gap_lower_bound":
            (.80 - .028) - max_radial,
        "continuous_outer_rim_radial_gap_lower_bound":
            (.715 - .055) - max_radial,
        "continuous_inner_rim_radial_gap_lower_bound":
            (.63 - .022) - max_radial,
        "symmetric_crank_base_overlaps_axle_extension":
            CRANK_BASE_Y < AXLE_EXTENSION_HALF_Y,
        "proof_restricted_to_2026_authored_geometry": True,
        "intended_axle_crank_mating_independently_boolean_verified": False,
        "original_1994_mechanical_design_recovered": False,
    }


def make_candidate(canonical_scad: Path, destination_scad: Path) -> dict:
    if canonical_scad.resolve() == destination_scad.resolve():
        raise ValueError("cannot overwrite original 2026 authoring source")
    generated = outboard_pedal_source(canonical_scad.read_bytes())
    destination_scad.parent.mkdir(parents=True, exist_ok=True)
    with destination_scad.open("xb") as target:
        target.write(generated)
    return {
        "schema": "UR-ART4K-OUTBOARD-PEDAL-AXLE-REVIEW/1",
        "historical_straight_rounded_scad_sha256": REPAIRED_SOURCE_SHA256,
        "candidate_scad_sha256": OUTBOARD_SOURCE_SHA256,
        "changed_material_roles_expected": [
            "fork_and_frame__material_3",
            "pedals__material_0", "pedals__material_1",
            "pedals__material_2",
        ],
        "unchanged_canonical_authoring_source": True,
        "original_1994_mesh_recovered": False,
        "owner_likeness_approved": False,
        "shipping_art_approved": False,
        "output": str(destination_scad),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("canonical_scad", type=Path)
    ap.add_argument("new_candidate_scad", type=Path)
    args = ap.parse_args()
    print(json.dumps(make_candidate(args.canonical_scad, args.new_candidate_scad),
                     sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
