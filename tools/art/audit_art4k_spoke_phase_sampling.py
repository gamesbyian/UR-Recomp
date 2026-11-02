#!/usr/bin/env python3
"""Exact sampling alias controls for the *unapproved* 2026 unicycle rig.

The canonical OpenSCAD rim has fixed spokes (a=i*45+11); only pedals
receive the authored 18+720*t crank phase. The direct-drive spoke motion
analyzed here is a counterfactual proposal, NOT a canonical 3D export.
This says nothing about the 1994 game's live PPU timing or appearance.
"""
from __future__ import annotations
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path

SOURCE_SCAD_SHA256="e99ef45bfe72f09ee97f51b7d7449c501aee2ca2d93596106ede4b56caddc984"
SCHEMA="UR-ART4K-2026-SPOKE-PHASE-SAMPLING-ALIAS/2"
SPOKE_COUNT=8
SOURCE_RIDE_REVOLUTIONS=2
SPOKE_PERIOD=Fraction(360,SPOKE_COUNT)
CANONICAL_RIM_OFFSET=Fraction(11)


def parse_time(value:str)->Fraction:
    if type(value) is not str or not value or len(value)>32:
        raise ValueError("normalized model time must be a bounded rational string")
    try:
        time=Fraction(value)
    except (ValueError,ZeroDivisionError,OverflowError) as error:
        raise ValueError("invalid source normalized time") from error
    if not 0<=time<=1 or time.denominator>65536:
        raise ValueError("source time outside 0..1 or unbounded precision")
    return time


def phase_modulo_spokes(t:Fraction)->Fraction:
    """Counterfactual direct-drive rotation; canonical rim does NOT do this."""
    if not isinstance(t,Fraction) or not 0<=t<=1:
        raise ValueError("invalid normalized model time")
    return (360*SOURCE_RIDE_REVOLUTIONS*t)%SPOKE_PERIOD


def verify_canonical_source(source:bytes)->None:
    """Fail closed on exact source drift and rim/pedal separation."""
    if hashlib.sha256(source).hexdigest()!=SOURCE_SCAD_SHA256:
        raise ValueError("canonical 2026 OpenSCAD source digest mismatch")
    text=source.decode("utf-8")
    anchors=(
        "module rim_and_hub() {",
        "for(i=[0:7]){\n    a=i*45+11;",
        "tire();rim_and_hub();fork_and_frame();pedals(pedal);saddle(seat_lean);",
        "shared_rig(pedal=18+720*u,seat_lean=3*sin(360*u));",
    )
    if any(text.count(anchor)!=1 for anchor in anchors):
        raise ValueError("canonical rim and crank source contract drift")


def analyze(times:list[str],*,canonical_source:bytes|None=None)->dict:
    if not isinstance(times,list) or not 1<=len(times)<=512 or any(type(t) is not str for t in times):
        raise ValueError("finite nonempty list of source times required")
    parsed=[parse_time(t) for t in times]
    if parsed!=sorted(set(parsed)):
        raise ValueError("source sample times must be strictly ascending and unique")
    if canonical_source is not None:
        verify_canonical_source(canonical_source)
    hypothetical=[phase_modulo_spokes(t) for t in parsed]
    canonical=[CANONICAL_RIM_OFFSET%SPOKE_PERIOD for _ in parsed]
    return {
        "schema":SCHEMA,
        "source_model_scad_sha256":SOURCE_SCAD_SHA256,
        "canonical_source_digest_and_contract_checked":canonical_source is not None,
        "source_authored_pedal_degrees":"18+720*t",
        "source_spoke_count":SPOKE_COUNT,
        "spoke_set_period_degrees":str(SPOKE_PERIOD),
        "source_sample_times":[str(t) for t in parsed],
        "canonical_rim_spoke_phase_modulo_45_degrees":[str(p) for p in canonical],
        "canonical_rim_unique_spoke_set_orientations":len(set(canonical)),
        "canonical_rim_rotates_with_pedals":False,
        "counterfactual_direct_drive_spoke_phase_modulo_45_degrees":[str(p) for p in hypothetical],
        "counterfactual_direct_drive_unique_spoke_set_orientations":len(set(hypothetical)),
        "counterfactual_direct_drive_samples_aliased":len(set(hypothetical))==1,
        "counterfactual_direct_drive_implemented_in_canonical_rig":False,
        "source_ride_animation_1994_ppu_cadence_verified":False,
        "source_3d_model_recovered":False,
        "owner_likeness_approved":False,
        "shipping_art_approved":False,
    }

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("times",nargs="*",help="e.g. 0 1/64 1/32 3/64 1/16")
    parser.add_argument("--canonical-scad",type=Path,
                        help="exact pinned #2832 OpenSCAD source for stationary-rim control")
    args=parser.parse_args()
    grid=args.times or ["0","1/64","1/32","3/64","1/16"]
    source=args.canonical_scad.read_bytes() if args.canonical_scad else None
    print(json.dumps(analyze(grid,canonical_source=source),sort_keys=True,indent=2))


if __name__=="__main__":
    main()
