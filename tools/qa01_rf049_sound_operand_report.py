#!/usr/bin/env python3
"""RF049 immutable case validator: actual original USA 82F0 operand census.

No heuristic time alignment or source/native phase guess. Input is the exact
replay case ZIP. Require a single terminal sentinel after the source observation
window and no loss of bank/target records before interpreting absence.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import zipfile
import qa01_rf048_original_sound_pointer_report as rf048

TAG_FINAL="QA01RF049FINAL "
TAG_LDA="QA01RF049LDA "
TAG_STA="QA01RF049STA "

def fields(line: str)->dict:
    out={}
    for token in line.split()[1:]:
        if "=" in token:
            k,v=token.split("=",1)
            if k in out or not k:raise ValueError("duplicate/empty RF049 field")
            out[k]=v
    return out

def analyze_source(original: str)->dict:
    lines=original.splitlines()
    finals=[fields(row) for row in lines if row.startswith(TAG_FINAL)]
    if len(finals)!=1:
        raise ValueError("RF049 requires exactly one post-window original final census")
    f=finals[0]
    required=["first","last","total","other","unmapped","lowC774","lowD0B4",
              "exact13C774","exact13D0B4","target_logged","target_overflow","unclosed"]
    for k in range(10,14):
        required+=["bank"+str(k),"min"+str(k),"max"+str(k)]
    if any(k not in f for k in required):
        raise ValueError("incomplete RF049 terminal census")
    d={}
    for key in required:
        try:d[key]=int(f[key],16 if key.startswith(("min","max")) else 10)
        except ValueError as exc:raise ValueError("non-numeric RF049 terminal value") from exc
        if d[key]<0:raise ValueError("negative original source count")
    if d["first"]!=6072 or d["last"]>6150 or d["last"]<d["first"]:
        raise ValueError("original RF049 source-frame window incomplete/wrong origin")
    if d["total"]<40000:
        raise ValueError("original RF049 opcode census unexpectedly short")
    if sum(d["bank"+str(k)] for k in range(10,14))+d["other"]+d["unmapped"]!=d["total"]:
        raise ValueError("original RF049 incomplete per-bank opcode coverage")
    if d["target_overflow"] or d["unclosed"]:
        raise ValueError("original RF049 target observation truncated/unpaired")
    # RF048 was independently installed before RF049 on this immutable
    # source guest; cross-check every completed source frame's LDA count.
    independent=[]
    for line in lines:
        if line.startswith("QA01RF048ORIGCOUNT "):
            x=fields(line)
            if "frame" not in x or "actual_lda" not in x:
                raise ValueError("original RF048 independent frame count incomplete")
            independent.append((int(x["frame"]),int(x["actual_lda"])))
    expected_frames=list(range(d["first"],d["last"]))
    if [frame for frame,_ in independent]!=expected_frames:
        raise ValueError("original RF048 independently counted frame window incomplete")
    if any(count<=0 or count>2000 for _,count in independent):
        raise ValueError("original RF048 impossible independent source frame count")
    independent_prior_sum=sum(count for _,count in independent)
    final_frame_count=d["total"]-independent_prior_sum
    if final_frame_count<=0 or final_frame_count>2000:
        raise ValueError("original RF049 census conflicts with independent RF048 frame counts")
    for k in range(10,14):
        n=d["bank"+str(k)]
        if n and d["min"+str(k)]>d["max"+str(k)]:
            raise ValueError("inverted original source bank range")
        if not n and d["max"+str(k)]:
            raise ValueError("original source bank max without opcode")
    lda=[fields(l) for l in lines if l.startswith(TAG_LDA)]
    sta=[fields(l) for l in lines if l.startswith(TAG_STA)]
    if len(lda)!=d["target_logged"]:
        raise ValueError("original target rows inconsistent with complete census")
    if len(sta)!=2*len(lda):
        raise ValueError("real source target STA opcode linkage incomplete")
    ordinals=[]
    for i,row in enumerate(lda,1):
        for name in ("ordinal","frame","d","ptr","y","ea","a0","a1"):
            if name not in row:raise ValueError("incomplete original target LDA")
        ordinal=int(row["ordinal"])
        if ordinals and ordinal<=ordinals[-1]:raise ValueError("original LDA order regression")
        ordinals.append(ordinal)
        try:expected=(int(row["ptr"],16)+int(row["y"],16))&0xffffff
        except ValueError as exc:raise ValueError("invalid original target operand") from exc
        if int(row["ea"],16)!=expected:
            raise ValueError("original 24-bit target effective operand inconsistent")
        for step,pc in ((0,"82:82F2"),(1,"82:82F6")):
            output=sta[(i-1)*2+step]
            if output.get("target")!=str(i) or output.get("pc")!=pc:
                raise ValueError("original target LDA->STA 2143/2142 not source-linked")
    matched=[row for row in lda if row["ea"] in ("13C774","13D0B4")]
    cnt=Counter(row["ea"] for row in matched)
    if cnt["13C774"]!=d["exact13C774"] or cnt["13D0B4"]!=d["exact13D0B4"]:
        raise ValueError("actual source full-bank operand target count disagrees with final")
    for low in ("C774","D0B4"):
        if sum(row["ea"].endswith(low) for row in lda)!=d["low"+low]:
            raise ValueError("original all-bank exact low-word count lacks a row")
    return {
      "schema":"rf049-source-opcode-full-operand-census-v1",
      "original_first_last_internal_frames":[d["first"],d["last"]],
      "genuine_original_82F0_LDA_count":d["total"],
      "independent_RF048_prior_frame_count_receipts":len(independent),
      "independent_RF048_prior_frames_LDA_total":independent_prior_sum,
      "qualified_final_original_frame_LDA_count":final_frame_count,
      "source_bank_counts":{str(k):d["bank"+str(k)] for k in range(10,14)},
      "source_bank_lowword_extrema":{
         str(k):[f'{d["min"+str(k)]:04X}',f'{d["max"+str(k)]:04X}']
         for k in range(10,14)},
      "other_bank_count":d["other"],"unmapped_DP_count":d["unmapped"],
      "exact_original_full_operand_13C774":d["exact13C774"],
      "exact_original_full_operand_13D0B4":d["exact13D0B4"],
      "all_bank_original_lowword_C774":d["lowC774"],
      "all_bank_original_lowword_D0B4":d["lowD0B4"],
      "source_true_LDA_followed_by_STA_2143_and_STA_2142":len(lda),
      "target_LDA_and_STA_source_examples":{"lda":lda[:12],"sta":sta[:24]},
      "source_target_truncated":False,"source_observation_complete_inside_6072_to_6150_only":True,
      "source_lack_of_full_operand_does_not_prove_absence_outside_window":True,
      "source_vs_native_host_epoch_registered":False,
      "complete_USA_events_accepted":0,
    }

def report(case_zip:Path,baseline:Path|None=None)->dict:
    with zipfile.ZipFile(case_zip) as z:
        original=z.read("work/zoom-zoo/replay/reference.log").decode("utf8","replace")
        native=z.read("work/zoom-zoo/replay/native.log").decode("utf8","replace")
    census=analyze_source(original)
    old=rf048.report(case_zip,baseline)
    census["RF048_bank_qualified_native_boundary_reads"]=old["native_verified_boundary_read_pairs"]
    census["case_zip_sha256"]=hashlib.sha256(case_zip.read_bytes()).hexdigest()
    census["source_guest_controls"]= {
      k:old[k] for k in ("case_source_sha","actual_WM_pairs","exact_WM_pairs",
                         "admitted_events","unchanged_RF047_Zoo_Bowl_and_full_WM_controls")
      if k in old
    }
    return census

def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("case_zip",type=Path)
    p.add_argument("--baseline",type=Path,required=True)
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    output=json.dumps(report(args.case_zip,args.baseline),indent=2,sort_keys=True)+"\n"
    if args.out:args.out.write_text(output,encoding="utf8")
    else:print(output,end="")
if __name__=="__main__":main()
