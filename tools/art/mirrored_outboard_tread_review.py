#!/usr/bin/env python3
"""Owner-directed, review-only bilateral orange tread correction.

The November 6 source-qualified wider axle/pedals remain the foundation.
November 6 local owner judgment: "after is better" and orange markings
must be "mirrored across the axle". Change ONLY the authored tread Y
offset on negative-side pedal. Preserve the old candidate exactly, the
canonical SCAD and all shipping model assets.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

try:
    from tools.art.pedal_axle_clearance_review import (
        OUTBOARD_SOURCE_SHA256, outboard_pedal_source,
        continuous_clearance_bounds,
    )
except ModuleNotFoundError:
    from pedal_axle_clearance_review import (
        OUTBOARD_SOURCE_SHA256, outboard_pedal_source,
        continuous_clearance_bounds,
    )

MIRRORED_OUTBOARD_SOURCE_SHA256 = "0b7a801228c526d6cdf4466019e111d446b0ab264bdcbf66d9241e37ce7c9c65"
OLD_TREAD = "translate(vadd(p,[0,-0.124,0]))"
NEW_TREAD = "translate(vadd(p,[0,p[1]>=0?-0.124:0.124,0]))"


def mirrored_tread_source(canonical_bytes: bytes) -> bytes:
    """Pin the exact old candidate first; refuse accidental branch drift."""
    old = outboard_pedal_source(canonical_bytes)
    if hashlib.sha256(old).hexdigest() != OUTBOARD_SOURCE_SHA256:
        raise ValueError("old qualified outboard review source drifted")
    text = old.decode("utf-8")
    if text.count(OLD_TREAD) != 1 or NEW_TREAD in text:
        raise ValueError("orange tread replacement has unexpected source grammar")
    after = text.replace(OLD_TREAD, NEW_TREAD).encode("utf-8")
    if hashlib.sha256(after).hexdigest() != MIRRORED_OUTBOARD_SOURCE_SHA256:
        raise ValueError("mirrored candidate is not source-identical to owner review")
    return after


def make_candidate(canonical: Path, destination: Path) -> dict:
    if canonical.resolve() == destination.resolve():
        raise ValueError("must not overwrite canonical source")
    before = canonical.read_bytes()
    out = mirrored_tread_source(before)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb") as handle:
        handle.write(out)
    if canonical.read_bytes() != before:
        raise ValueError("canonical source changed during review generation")
    return {
        "schema": "UR-ART4K-OWNER-MIRRORED-OUTBOARD-TREAD/1",
        "preexisting_outboard_review_sha256": OUTBOARD_SOURCE_SHA256,
        "candidate_scad_sha256": MIRRORED_OUTBOARD_SOURCE_SHA256,
        "owner_preferred_wider_assembly": True,
        "owner_requested_tread_mirroring": True,
        "only_changed_source_statement": "pedal_body(p) orange-tread lateral offset",
        "source_candidate_2026_geometry_only": True,
        "original_1994_mechanics_or_likeness_recovered": False,
        "shipping_art_approved": False,
        "output": str(destination),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("canonical_scad", type=Path)
    ap.add_argument("new_candidate_scad", type=Path)
    args = ap.parse_args()
    print(json.dumps(make_candidate(args.canonical_scad,args.new_candidate_scad),
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
