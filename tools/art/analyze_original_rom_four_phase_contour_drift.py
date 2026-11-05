#!/usr/bin/env python3
"""Quantify phase-dependent original 2D contour, excluding unobserved views.

Operates exclusively on the SHA-pinned ROM source's already-normalized
four-phase/64-orientation 4bpp consensus receipt. No 1994 joint or 3D
surface inference; no GLB renderer or additional original emulator.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from tools.art.no_replace_report import publish_text_once
from tools.art.recover_original_rom_derotated_consensus import (
    SCHEMA as SOURCE_SCHEMA, ROM_SHA, SOURCE_SHA, N, BANDS, PHASES,
    MIN_VALID_ORIENTATIONS, FROZEN_EVEN_ORIENTATION_PIVOT,
)

SCHEMA="UR-ART4K-ORIGINAL-ROM-FOUR-PHASE-2D-CONTOUR-DRIFT/1"
EXPECTED_PHASES=tuple(str(p) for p in PHASES)
PAIRS=tuple((a,b) for i,a in enumerate(EXPECTED_PHASES)
            for b in EXPECTED_PHASES[i+1:])


def _phase(record:dict)->dict:
    if (not isinstance(record,dict) or record.get("orientation_samples")!=64 or
            record.get("source_min_valid_view_count")!=MIN_VALID_ORIENTATIONS):
        raise ValueError("original four-phase contour requires 64 original source orientations")
    valid=record.get("source_valid_orientation_observation_count_64")
    opaque=record.get("source_opaque_observation_count_64")
    rows=record.get("source_consensus_index4_64rows")
    if (not isinstance(valid,list) or not isinstance(opaque,list) or
            len(valid)!=N or len(opaque)!=N or
            any(type(n) is not int or not 0<=n<=64 for n in valid) or
            any(type(n) is not int or n<0 or n>v for n,v in zip(opaque,valid)) or
            not isinstance(rows,list) or len(rows)!=64 or
            any(type(row) is not str or len(row)!=64
                or any(c not in "0123456789abcdef" for c in row) for row in rows)):
        raise ValueError("original 64px 4bpp source observation coverage malformed")
    source_index=bytes(int(c,16) for row in rows for c in row)
    accepted=bytes(int(n>=MIN_VALID_ORIENTATIONS) for n in valid)
    consensus=bytes(int(accepted[i] and opaque[i]*2>valid[i]) for i in range(N))
    core=bytes(int(accepted[i] and opaque[i]>0 and opaque[i]*10>=valid[i]*9)
               for i in range(N))
    if (any(bool(source_index[i])!=bool(consensus[i]) for i in range(N)) or
            hashlib.sha256(consensus).hexdigest()!=record.get("source_consensus_binary_sha256") or
            hashlib.sha256(core).hexdigest()!=record.get("source_core_binary_sha256") or
            hashlib.sha256(source_index).hexdigest()!=record.get("source_plurality_original_4bpp_sha256") or
            sum(consensus)!=record.get("source_consensus_opaque_pixels") or
            sum(core)!=record.get("source_near_invariant_opaque_core_pixels")):
        raise ValueError("original source 4bpp consensus digest/count inconsistent")
    return {"accepted":accepted,"consensus":consensus,"core":core,"index":source_index}


def analyze(source:dict)->dict:
    if (not isinstance(source,dict) or source.get("schema")!=SOURCE_SCHEMA or
            source.get("original_ROM_USA_sha256")!=ROM_SHA or
            source.get("original_24x64_source_report_sha256")!=SOURCE_SHA or
            source.get("original_grid_dimensions")!=[24,64] or
            source.get("original_phase_indices_examined")!=list(PHASES) or
            source.get("source_even_index_only_frozen_2D_rotation_pivot_xy")!=
                list(FROZEN_EVEN_ORIENTATION_PIVOT) or
            source.get("source_64x64_rotation_canvas_cropping_not_counted_as_background") is not True or
            source.get("original_1994_3D_geometry_camera_joint_or_materials_recovered") is not False or
            source.get("owner_art_likeness_approved") is not False or
            set(source.get("per_original_ROM_phase",{}))!=set(EXPECTED_PHASES)):
        raise ValueError("authenticated original ROM four-phase source receipt required")
    phases={p:_phase(source["per_original_ROM_phase"][p]) for p in EXPECTED_PHASES}
    common=bytes(int(all(phases[p]["accepted"][i] for p in EXPECTED_PHASES))
                 for i in range(N))
    invariant=bytes(int(common[i] and all(phases[p]["core"][i]
                     for p in EXPECTED_PHASES)) for i in range(N))
    all_consensus=bytes(int(common[i] and all(phases[p]["consensus"][i]
                         for p in EXPECTED_PHASES)) for i in range(N))
    any_consensus=bytes(int(common[i] and any(phases[p]["consensus"][i]
                         for p in EXPECTED_PHASES)) for i in range(N))
    phase_varying=bytes(int(any_consensus[i] and not all_consensus[i])
                        for i in range(N))
    per_band={}
    for name,lo,hi in BANDS:
        idx=range(lo*64,(hi+1)*64)
        per_band[name]={
            "original_four_phase_common_valid_2D_pixels":sum(common[i] for i in idx),
            "original_four_phase_always_consensus_alpha_pixels":
                sum(all_consensus[i] for i in idx),
            "original_four_phase_at_least_once_consensus_alpha_pixels":
                sum(any_consensus[i] for i in idx),
            "original_four_phase_phase_varying_2D_alpha_pixels":
                sum(phase_varying[i] for i in idx),
            "original_four_phase_always_near_invariant_opaque_core_pixels":
                sum(invariant[i] for i in idx),
        }
    assert sum(v["original_four_phase_common_valid_2D_pixels"]
               for v in per_band.values())==sum(common)
    assert sum(v["original_four_phase_phase_varying_2D_alpha_pixels"]
               for v in per_band.values())==sum(phase_varying)
    pairs={}
    for a,b in PAIRS:
        one,two=phases[a],phases[b]
        valid=[i for i in range(N) if one["accepted"][i] and two["accepted"][i]]
        tp=sum(one["consensus"][i] and two["consensus"][i] for i in valid)
        fp=sum(not one["consensus"][i] and two["consensus"][i] for i in valid)
        fn=sum(one["consensus"][i] and not two["consensus"][i] for i in valid)
        exact_index=sum(one["consensus"][i] and two["consensus"][i] and
                        one["index"][i]==two["index"][i] for i in valid)
        per_pair_band={}
        for name,lo,hi in BANDS:
            local=[i for i in valid if lo<=i//64<=hi]
            per_pair_band[name]={
                "common_valid_original_source_pixels":len(local),
                "phase_a_only_consensus_alpha_pixels":
                    sum(one["consensus"][i] and not two["consensus"][i] for i in local),
                "phase_b_only_consensus_alpha_pixels":
                    sum(two["consensus"][i] and not one["consensus"][i] for i in local),
                "shared_opaque_original_alpha_pixels":
                    sum(one["consensus"][i] and two["consensus"][i] for i in local),
            }
        if (sum(v["common_valid_original_source_pixels"] for v in per_pair_band.values())!=len(valid)
                or sum(v["shared_opaque_original_alpha_pixels"] for v in per_pair_band.values())!=tp
                or sum(v["phase_b_only_consensus_alpha_pixels"] for v in per_pair_band.values())!=fp
                or sum(v["phase_a_only_consensus_alpha_pixels"] for v in per_pair_band.values())!=fn):
            raise ValueError("original source view validity / 2D phase bands not conserved")
        den=tp+fp+fn
        pairs[f"{a}->{b}"]={
            "source_original_common_valid_pixel_count":len(valid),
            "source_2D_consensus_tp_fp_fn":{"tp":tp,"fp":fp,"fn":fn},
            "source_2D_consensus_alpha_iou":round(tp/den,8) if den else 1.,
            "source_exact_4bpp_index_paint_matches_on_shared_consensus_alpha":
                exact_index,
            "source_shared_consensus_opaque_pixels":tp,
            "source_exact_index_paint_recall_on_shared_opaque":
                round(exact_index/tp,8) if tp else 1.,
            "fixed_source_y_bands":per_pair_band,
        }
    return {
        "schema":SCHEMA,
        "original_ROM_USA_sha256":ROM_SHA,
        "original_24x64_source_report_sha256":SOURCE_SHA,
        "original_four_ROM_phases_compared":list(EXPECTED_PHASES),
        "original_source_inverse_2D_rotation_pivot_xy":
            list(FROZEN_EVEN_ORIENTATION_PIVOT),
        "source_view_cropping_never_counted_as_observed_transparency":True,
        "original_2D_phase_drift_not_recovered_1994_physical_3D_geometry":True,
        "source_views_previously_inspected_not_prospective_holdout":True,
        "original_four_phase_common_valid_pixels":sum(common),
        "original_four_phase_always_near_invariant_core_pixels":sum(invariant),
        "original_four_phase_always_consensus_alpha_pixels":sum(all_consensus),
        "original_four_phase_at_least_once_consensus_alpha_pixels":sum(any_consensus),
        "original_four_phase_phase_varying_2D_alpha_pixels":sum(phase_varying),
        "per_fixed_source_y_band":per_band,
        "all_six_original_phase_pair_comparisons":pairs,
    }


def main()->None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--original-consensus-report",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    result=analyze(json.loads(a.original_consensus_report.read_bytes()))
    publish_text_once(a.out,json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("ART4K_ORIGINAL_FOUR_PHASE_CONSENSUS_2D_DRIFT",
          json.dumps({"source_phase_varying_pixels":
                      result["original_four_phase_phase_varying_2D_alpha_pixels"],
                      "common_valid":result["original_four_phase_common_valid_pixels"],
                      "pairs":{k:v["source_2D_consensus_alpha_iou"]
                               for k,v in result["all_six_original_phase_pair_comparisons"].items()}},
                     sort_keys=True))


if __name__=="__main__":
    main()
