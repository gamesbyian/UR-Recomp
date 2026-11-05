#!/usr/bin/env python3
"""Audit a claimed 16-pedal-pose period against the actual 24x64 ROM sprite grid.

Original DMA Design interview recalls sixteen rendered pedal versions, while
the original USA ROM exposes an *independently verified* 24x64 graphics index
lattice. Neither observation identifies a physical 3D wheel angle. Check one
predeclared matched-base, nonwrapped 16-lag counterfactual and all 1..15
competing lags on exact original 4bpp-index pixels, not guessed GLB motion.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

from tools.art.no_replace_report import publish_text_once
from tools.art.recover_original_mesen24_rom_pose_ids import (
    ROM_SHA,source_frame_tiles,render_original_primary_sprite64
)

SCHEMA="UR-ART4K-ORIGINAL-ROM-16-PEDAL-INTERVIEW-VS-24-PHASE-PIXELS/1"
INTERVIEW="https://www.nintendolife.com/news/2010/03/feature_the_making_of_unirally"
PHASES=24
ANGLES=64
PIXELS=4096
BASE_PHASES=tuple(range(8))
LAGS=tuple(range(1,17))


def phase_support_positions(images:tuple[bytes,...])->tuple[int,...]:
    if (not isinstance(images,tuple) or len(images)!=PHASES or
            any(type(x) is not bytes or len(x)!=PIXELS or
                max(x)>15 for x in images)):
        raise ValueError("24 exact source 64x64 original 4bpp index planes required")
    first=images[0]
    indices=tuple(i for i in range(PIXELS)
                  if any(img[i]!=first[i] for img in images[1:]))
    if not indices:
        raise ValueError("original source has no phase-dependent 4bpp pixels")
    return indices


def score_one_original_orientation(images:tuple[bytes,...])->dict:
    """All lags compare precisely eight fixed base phases, zero fitted shifts."""
    positions=phase_support_positions(images)
    trials={}
    for lag in LAGS:
        indexed=0;alpha_tp=0;alpha_fp=0;alpha_fn=0;opaque_exact=0;src_opaque=0
        for base in BASE_PHASES:
            left,right=images[base],images[base+lag]
            for i in positions:
                a,b=left[i],right[i]
                indexed+=int(a==b)
                opaque_exact+=int(a!=0 and a==b)
                src_opaque+=int(a!=0)
                alpha_tp+=int(a!=0 and b!=0)
                alpha_fp+=int(a==0 and b!=0)
                alpha_fn+=int(a!=0 and b==0)
        total=len(positions)*len(BASE_PHASES)
        d=alpha_tp+alpha_fp+alpha_fn
        trials[str(lag)]={
            "original_first_eight_base_phase_pair_count":len(BASE_PHASES),
            "source_phase_support_pixel_instances":total,
            "source_exact_4bpp_index_matches":indexed,
            "source_exact_4bpp_index_match_fraction":round(indexed/total,8),
            "source_opaque_exact_4bpp_matches":opaque_exact,
            "source_original_opaque_pixel_instances":src_opaque,
            "source_original_opaque_index_recall":
                round(opaque_exact/src_opaque,8) if src_opaque else 1.,
            "phase_support_alpha_tp_fp_fn":{"tp":alpha_tp,"fp":alpha_fp,"fn":alpha_fn},
            "phase_support_alpha_iou":round(alpha_tp/d,8) if d else 1.,
        }
    return {"source_phase_sensitive_support_pixels":len(positions),"lag_results":trials}


def audit(rom:bytes)->dict:
    if type(rom) is not bytes or len(rom)!=2097152 or hashlib.sha256(rom).hexdigest()!=ROM_SHA:
        raise ValueError("wrong original USA ROM or source 24-phase image evidence")
    frames=source_frame_tiles(rom)
    if len(frames)!=1536:
        raise ValueError("original ROM 24x64 table incomplete")
    rows={}
    accum={str(lag):{"exact":0,"pixels":0,"opaque_exact":0,"src_opaque":0,
                     "tp":0,"fp":0,"fn":0} for lag in LAGS}
    for angle in range(ANGLES):
        originals=tuple(render_original_primary_sprite64(frames[phase*ANGLES+angle])
                        for phase in range(PHASES))
        one=score_one_original_orientation(originals)
        rows[str(angle)]=one
        for lag in LAGS:
            r=one["lag_results"][str(lag)]
            a=accum[str(lag)]
            a["exact"]+=r["source_exact_4bpp_index_matches"]
            a["pixels"]+=r["source_phase_support_pixel_instances"]
            a["opaque_exact"]+=r["source_opaque_exact_4bpp_matches"]
            a["src_opaque"]+=r["source_original_opaque_pixel_instances"]
            for key in ("tp","fp","fn"):
                a[key]+=r["phase_support_alpha_tp_fp_fn"][key]
    table={}
    for lag in LAGS:
        a=accum[str(lag)]
        den=a["tp"]+a["fp"]+a["fn"]
        table[str(lag)]={
            "equal_base_pair_count":ANGLES*len(BASE_PHASES),
            "phase_support_pixel_instances":a["pixels"],
            "exact_original_4bpp_index_matches":a["exact"],
            "source_exact_index_fraction":round(a["exact"]/a["pixels"],8),
            "opaque_index_recall":round(a["opaque_exact"]/a["src_opaque"],8)
                if a["src_opaque"] else 1.,
            "source_phase_sensitive_alpha_iou":round(a["tp"]/den,8) if den else 1.,
            "alpha_tp_fp_fn":{k:a[k] for k in ("tp","fp","fn")}
        }
    # Source indexing is 24 by source code; sixteen pedal variants are an
    # independently cited, uncalibrated artist recollection, not a 24->16 map.
    non16={k:v for k,v in table.items() if k!="16"}
    best=max(non16,key=lambda k:(non16[k]["source_exact_index_fraction"],-int(k)))
    return {
        "schema":SCHEMA,
        "original_USA_ROM_sha256":ROM_SHA,
        "source_1536_distinct_original_ROM_frame_records_verified":True,
        "original_ROM_presentation_grid":[24,64],
        "historical_artist_interview_source_url":INTERVIEW,
        "historical_interview_pedal_variant_count_recollected":16,
        "historical_16_pedal_variants_NOT_identified_as_ROM_phase_period":True,
        "predeclared_lag_values":list(LAGS),
        "same_first_eight_source_base_phases_for_each_lag":list(BASE_PHASES),
        "nonwrapped_lag_pairs_per_orientation":len(BASE_PHASES),
        "source_all_64_orientation_indices_scored":True,
        "source_phase_only_pixel_ROI_is_all_original_24_phase_variation_at_each_angle":True,
        "source_original_4bpp_palette_indices_are_not_2026_GLb_materials":True,
        "original_1994_3D_pedal_angle_or_mesh_recovered":False,
        "source_pixels_previously_inspected_not_prospective_holdout":True,
        "lag16_exceeds_every_other_tested_lag_in_exact_source_index_fraction":
            table["16"]["source_exact_index_fraction"]>
            non16[best]["source_exact_index_fraction"],
        "best_other_lag_by_exact_source_index_fraction":int(best),
        "all_lag_summary":table,
        "all_original_64_orientation_diagnostics":rows,
    }


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rom",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    data=audit(a.rom.read_bytes())
    publish_text_once(a.out,json.dumps(data,sort_keys=True,indent=2)+"\n")
    print("ART4K_ORIGINAL_16_PEDAL_INTERVIEW_LAG_TEST",
          json.dumps({"lag16":data["all_lag_summary"]["16"],
                      "best_other_lag":data["best_other_lag_by_exact_source_index_fraction"],
                      "best_other_summary":data["all_lag_summary"][
                          str(data["best_other_lag_by_exact_source_index_fraction"])],
                      "exact_index_lag16_dominates":
                          data["lag16_exceeds_every_other_tested_lag_in_exact_source_index_fraction"]
          },sort_keys=True))


if __name__=="__main__":
    main()
