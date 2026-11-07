#!/usr/bin/env python3
"""Source-pinned optional 2026 rotating axle with bored stationary bearing.

Owner-selected wider pedals and orange tread mirror are unchanged.
The preceding optional model #3236 drew its long through-shaft in the
stationary fork/frame parent, where it overlapped the lower fork and solid
central sleeve. This source experiment reassigns the shaft to the rotating
pedal/crank parent and cuts a clearance bore through BOTH fixed materials.
It is NOT approved 1994 mechanics, artist likeness or shipping art.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from tools.art.mirrored_outboard_tread_review import (
        MIRRORED_OUTBOARD_SOURCE_SHA256, mirrored_tread_source,
    )
except ModuleNotFoundError:
    from mirrored_outboard_tread_review import (
        MIRRORED_OUTBOARD_SOURCE_SHA256, mirrored_tread_source,
    )

ROTATING_AXLE_SOURCE_SHA256 = "829eaa90ec41a993c998c47ce06f65dc525e81b015bf53b1f82a8485147e0928"
SHAFT_RADIUS = 0.065
BORE_RADIUS = 0.071
BORE_FN = 80
BORE_INNER_APOTHEM = BORE_RADIUS * __import__("math").cos(__import__("math").pi / BORE_FN)
MIN_CLEARANCE = BORE_INNER_APOTHEM - SHAFT_RADIUS

PATCHES = (
    ("""  color([0.68,0.74,0.80])member([0,-0.475,0],p2,0.055,0.036);
  pedal_body(p1);pedal_body(p2);""",
     """  color([0.68,0.74,0.80])member([0,-0.475,0],p2,0.055,0.036);
  // Moving drive shaft is a child of the same rotating parent as both cranks.
  color([0.68,0.74,0.80])rotate([90,0,0])cylinder(h=1.08,r=0.065,center=true);
  pedal_body(p1);pedal_body(p2);"""),
    ("""    color(rig_color)frame_member([-0.02,y,0.07],[-0.10,y,0.83],0.09,0.105);""",
     """    color(rig_color)difference(){
      frame_member([-0.02,y,0.07],[-0.10,y,0.83],0.09,0.105);
      // Stationary leg must not penetrate the axle rotational envelope.
      rotate([90,0,0])cylinder(h=1.08+0.02,r=0.071,center=true,$fn=80);
    }"""),
    ("""  color([0.52,0.60,0.67])union(){
    rotate([90,0,0])cylinder(h=0.56,r=0.13,center=true);
    // Narrow, symmetric through-axle joins the outboard cranks.
    rotate([90,0,0])cylinder(h=1.08,r=0.065,center=true);
  }""",
     """  // Stationary hollow bearing sleeve around the independently rotating axle.
  color([0.52,0.60,0.67])difference(){
    rotate([90,0,0])cylinder(h=0.56,r=0.13,center=true);
    rotate([90,0,0])cylinder(h=0.56+0.02,r=0.071,center=true,$fn=80);
  }"""),
)


def rotating_axle_source(canonical_bytes: bytes) -> bytes:
    """Derive an immutable owner-preferred *optional* candidate; no in-place edit."""
    old = mirrored_tread_source(canonical_bytes)
    if hashlib.sha256(old).hexdigest() != MIRRORED_OUTBOARD_SOURCE_SHA256:
        raise ValueError("owner-preferred mirrored source drift")
    source = old.decode("utf-8")
    for prior, proposed in PATCHES:
        if source.count(prior) != 1 or proposed in source:
            raise ValueError("rotating axle review does not match old source grammar")
        source = source.replace(prior, proposed)
    result = source.encode("utf-8")
    if hashlib.sha256(result).hexdigest() != ROTATING_AXLE_SOURCE_SHA256:
        raise ValueError("rotating axle bearing review source differs from original experiment")
    return result


def generate(canonical_source: Path, destination: Path) -> dict:
    if canonical_source.resolve() == destination.resolve():
        raise ValueError("refusing to overwrite original authoring rig")
    original = canonical_source.read_bytes()
    candidate = rotating_axle_source(original)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb") as out:
        out.write(candidate)
    if canonical_source.read_bytes() != original:
        raise ValueError("source changed during qualification")
    return {
        "schema": "UR-ART4K-OWNER-ROTATING-AXLE-BEARING-SOURCE-REVIEW/1",
        "owner_preferred_mirrored_outboard_source_sha256": MIRRORED_OUTBOARD_SOURCE_SHA256,
        "rotating_axle_bearing_candidate_scad_sha256": ROTATING_AXLE_SOURCE_SHA256,
        "shaft_parent": "pedals",
        "bearing_and_bored_lower_fork_parent": "fork_and_frame",
        "shaft_radius": SHAFT_RADIUS,
        "bores_radius": BORE_RADIUS,
        "bores_polygon_apothem": BORE_INNER_APOTHEM,
        "minimum_ideal_source_bore_shaft_gap": MIN_CLEARANCE,
        "owner_preferred_wider_spacing_and_mirrored_tread_preserved": True,
        "original_1994_bearing_or_axle_mechanics_recovered": False,
        "actual_GLb_surface_clearance_proved_by_source_generator": False,
        "shipping_art_approved": False,
        "output": str(destination),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("canonical_scad", type=Path)
    parser.add_argument("candidate_scad", type=Path)
    args = parser.parse_args()
    print(json.dumps(generate(args.canonical_scad, args.candidate_scad),
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
