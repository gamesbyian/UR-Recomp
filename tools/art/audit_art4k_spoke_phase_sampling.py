#!/usr/bin/env python3
"""Exact rational eight-spoke alias test for the single unapproved 2026 rig.

The authored ride crank phase is 18+720*t degrees. Eight equal spokes at 45°
intervals repeat their geometric set under any 45° rotation. This tests only
2026 model sampling, not original 1994 PPU timing or recovered 3D animation.
"""
from __future__ import annotations
import argparse
from fractions import Fraction
import json

SOURCE_SCAD_SHA256="e99ef45bfe72f09ee97f51b7d7449c501aee2ca2d93596106ede4b56caddc984"
SCHEMA="UR-ART4K-2026-SPOKE-PHASE-SAMPLING-ALIAS/1"
SPOKE_COUNT=8
SOURCE_RIDE_REVOLUTIONS=2
SPOKE_PERIOD=Fraction(360,SPOKE_COUNT)


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
    if not isinstance(t,Fraction) or not 0<=t<=1:
        raise ValueError("invalid normalized model time")
    return (360*SOURCE_RIDE_REVOLUTIONS*t)%SPOKE_PERIOD


def analyze(times:list[str])->dict:
    if not isinstance(times,list) or not 1<=len(times)<=512 or any(type(t) is not str for t in times):
        raise ValueError("finite nonempty list of source times required")
    parsed=[parse_time(t) for t in times]
    if parsed!=sorted(set(parsed)):
        raise ValueError("source sample times must be strictly ascending and unique")
    phases=[phase_modulo_spokes(t) for t in parsed]
    unique=sorted(set(phases))
    return {
        "schema":SCHEMA,
        "source_model_scad_sha256":SOURCE_SCAD_SHA256,
        "source_authored_crank_degrees":"18+720*t",
        "source_spoke_count":SPOKE_COUNT,
        "spoke_set_period_degrees":str(SPOKE_PERIOD),
        "source_sample_times":[str(t) for t in parsed],
        "relative_spoke_phase_modulo_45_degrees":[str(p) for p in phases],
        "unique_spoke_set_orientations":len(unique),
        "all_samples_spoke_aliased":len(unique)==1,
        "source_ride_animation_1994_ppu_cadence_verified":False,
        "source_3d_model_recovered":False,
        "owner_likeness_approved":False,
        "shipping_art_approved":False,
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("times",nargs="*",help="e.g. 0 1/64 1/32 3/64 1/16")
    args=parser.parse_args()
    grid=args.times or ["0","1/64","1/32","3/64","1/16"]
    print(json.dumps(analyze(grid),sort_keys=True,indent=2))


if __name__=="__main__":
    main()
