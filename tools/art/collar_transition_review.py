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
  // Owner November 6 correction: silver post leaves collar straight up,
  // coaxial at X=-0.22/Y=0 from base to upper saddle bracket.
  // Fork may lean *below* the collar; the silver post must not lean inside it.
  // Preserve source material group order: silver seatpost, then dark trim.
  color([0.75,0.81,0.84])frame_member([-0.22,0,1.67],[-0.22,0,2.235],0.065,0.058);
  color([0.30,0.40,0.45])translate([-0.22,0,1.775])
    cylinder(h=0.035,r=0.105,center=true,$fn=64);
  color([0.30,0.40,0.45])frame_member([-0.22,0,2.225],[-0.03,0,2.2],0.083,0.088);"""


def assert_seatpost_aligned(candidate_source: str) -> None:
    """A source-level invariant for the owner's straight-from-collar geometry.

    The coloured collar's two sphere centres, silver rod endpoints and the
    upper saddle bracket all share one X/Y axis. This says nothing about the
    uncalibrated 1994 pose's world vertical under a stunt rotation.
    """
    import re

    def pairs(pattern: str):
        match = re.search(pattern, candidate_source)
        if match is None:
            raise ValueError("missing unique owner-authored collar/post axis")
        return [tuple(float(v) for v in re.findall(r"-?\\d+(?:\\.\\d+)?", item))
                for item in match.groups()]

    collar = pairs(r"color\\(rig_color\\)hull\\(\\)\\{\\s*"
                   r"translate\\(\\[([^]]+)\\]\\)sphere\\(r=0\\.14"
                   r"[^;]*;\\s*translate\\(\\[([^]]+)\\]\\)sphere\\(r=0\\.14")
    post = pairs(r"color\\(\\[0\\.75,0\\.81,0\\.84\\]\\)frame_member\\("
                 r"\\[([^]]+)\\],\\[([^]]+)\\],0\\.065,0\\.058\\)")
    upper = pairs(r"color\\(\\[0\\.30,0\\.40,0\\.45\\]\\)frame_member\\("
                  r"\\[([^]]+)\\],\\[([^]]+)\\],0\\.083,0\\.088\\)")
    if any(len(x) != 3 for x in collar + post + upper):
        raise ValueError("expected three-dimensional seatpost endpoints")
    anchor = collar[0][:2]
    if not all(point[:2] == anchor for point in collar+post+upper[:1]):
        raise ValueError("seatpost meets coloured collar off-axis or at an angle")
    if not post[0][2] < collar[-1][2] < post[1][2]:
        raise ValueError("straight post does not pass through the collar into saddle")
    if not upper[0][2] <= post[1][2]:
        raise ValueError("post and saddle support no longer join")


def canonical_source_bytes(source_bytes: bytes) -> bytes:
    """Recover Git's LF blob from a Windows all-CRLF checkout, not arbitrary drift."""
    if b"\r\n" in source_bytes:
        if source_bytes.count(b"\r\n") != source_bytes.count(b"\n"):
            raise ValueError("mixed source newlines; re-review owner collar patch")
        source_bytes = source_bytes.replace(b"\r\n", b"\n")
    return source_bytes


def sculpt(source_bytes: bytes) -> bytes:
    """One exact-authoring-source replacement, no second source model fork."""
    source_bytes = canonical_source_bytes(source_bytes)
    digest = hashlib.sha256(source_bytes).hexdigest()
    if digest != BASELINE_SOURCE_SHA256:
        raise ValueError("canonical 2026 source SHA changed; re-review owner collar patch")
    source = source_bytes.decode("utf-8")
    if source.count(OLD) != 1:
        raise ValueError("expected exactly one original coloured/metal saddle neck")
    replacement = source.replace(OLD, NEW)
    assert_seatpost_aligned(replacement)
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
