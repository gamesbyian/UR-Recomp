#!/usr/bin/env python3
"""Owner-directed saddle/seatpost collar study on ONE existing unapproved rig.

Exact-source, deterministic SCAD patch for the canonical 2026 authoring model.
Never alters the source on main, original references, released art or gameplay.
Use the *existing* GLB exporter and viewer to evaluate this one design change.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

BASELINE_SOURCE_SHA256 = "e99ef45bfe72f09ee97f51b7d7449c501aee2ca2d93596106ede4b56caddc984"
OLD = """  color(rig_color)frame_member([-0.17,0,1.39],[-0.25,0,2.09],0.16,0.126);
  color([0.75,0.81,0.84])frame_member([-0.21,0,1.91],[-0.19,0,2.13],0.116,0.105);
  color([0.30,0.40,0.45])frame_member([-0.20,0,2.1],[-0.03,0,2.2],0.10,0.09);"""
NEW = """  // Owner reference: official 1994 manual fork-facing illustration.
  // Short rounded coloured collar at fork crown; long, slim exposed seatpost.
  // Every new element lies on Y=0; original saddle, wheel and spokes untouched.
  color(rig_color)frame_member([-0.17,0,1.39],[-0.22,0,1.60],0.16,0.135);
  color(rig_color)hull(){
    translate([-0.22,0,1.59])sphere(r=0.14,$fn=48);
    translate([-0.22,0,1.65])sphere(r=0.14,$fn=48);
  }
  // Preserve source material group order: silver seatpost, then dark trim.
  color([0.75,0.81,0.84])frame_member([-0.22,0,1.67],[-0.20,0,2.235],0.065,0.058);
  color([0.30,0.40,0.45])translate([-0.22,0,1.775])
    cylinder(h=0.035,r=0.105,center=true,$fn=64);
  color([0.30,0.40,0.45])frame_member([-0.20,0,2.225],[-0.03,0,2.2],0.083,0.088);"""


def sculpt(source_bytes: bytes) -> bytes:
    """One exact-authoring-source replacement, no second source model fork."""
    digest = hashlib.sha256(source_bytes).hexdigest()
    if digest != BASELINE_SOURCE_SHA256:
        raise ValueError("canonical 2026 source SHA changed; re-review owner collar patch")
    source = source_bytes.decode("utf-8")
    if source.count(OLD) != 1:
        raise ValueError("expected exactly one original coloured/metal saddle neck")
    replacement = source.replace(OLD, NEW)
    if replacement.count(NEW) != 1 or OLD in replacement:
        raise ValueError("collar replacement failed")
    return replacement.encode("utf-8")


def make_candidate(source: Path, target: Path) -> dict:
    if source.resolve() == target.resolve():
        raise ValueError("must not overwrite canonical OpenSCAD source")
    generated = sculpt(source.read_bytes())
    target.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive create protects other owners' files and avoids silent replacement.
    with target.open("xb") as output:
        output.write(generated)
    return {
        "schema": "UR-ART4K-OWNER-COLLAR-SCULPT-20261106/1",
        "baseline_scad_sha256": BASELINE_SOURCE_SHA256,
        "candidate_scad_sha256": hashlib.sha256(generated).hexdigest(),
        "source_file_untouched": True,
        "original_saddle_tire_rim_spokes_pedals_unchanged": True,
        "source_1994_3d_recovered": False,
        "owner_likeness_approved": False,
        "output": str(target),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("canonical_scad", type=Path)
    parser.add_argument("new_candidate_scad", type=Path)
    args = parser.parse_args()
    print(json.dumps(make_candidate(args.canonical_scad, args.new_candidate_scad),
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
