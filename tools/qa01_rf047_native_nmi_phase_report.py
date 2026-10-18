#!/usr/bin/env python3
"""RF047 native interrupt/stack access phase, strictly ordered by native seq.

No stdout/stderr rendered line order can determine execution order. No assumed
original/native clock epoch, no automatic stack exclusion or event admission.
"""
from __future__ import annotations
import argparse,hashlib,json,re,zipfile
from collections import defaultdict
from pathlib import Path

REF="work/zoom-zoo/replay/reference.log"
NATIVE="work/zoom-zoo/replay/native.log"
FRAMES=tuple(range(1017,1026))
TAG="QA01RF047NATIVE "
STACK="26EED482"
def fields(line: str)->dict:
    return dict(x.split("=",1) for x in line.split()[1:] if "=" in x)
def classify(native: str)->dict:
    if "QA01RF047NATIVE_TRUNCATED" in native:
        raise ValueError("RF047 native source read/interrupt log truncated")
    observed=[]
    for line in native.splitlines():
        # Native WRAM writer fragments can precede a whole atomic RF047
        # record on the same physical line. Extract only the single-event
        # suffix; never interpret line order as event order.
        pos=line.find(TAG)
        if pos<0:continue
        row=fields(line[pos:])
        if not all(k in row for k in ("seq","stage","f")):
            raise ValueError("RF047 truncated native event header")
        if int(row["f"]) not in FRAMES or row["stage"] not in ("entry","after_push","handler_return","read","interp_rti","compiled_rti"):
            raise ValueError("RF047 out-of-domain native event")
        observed.append({**row,"seq":int(row["seq"]),"f":int(row["f"])})
    if not observed:
        raise ValueError("RF047 no true native interrupt/stack row executed")
    numbers=[x["seq"] for x in observed]
    if sorted(numbers)!=list(range(1,len(observed)+1)):
        raise ValueError("RF047 native source sequence gap/duplication")
    # Rendered stdout/stderr lines may be intermixed; only the native
    # recorder's unique monotone sequence defines native instruction order.
    ordered=sorted(observed,key=lambda r:r["seq"])
    by_frame=defaultdict(list)
    for row in ordered:by_frame[row["f"]].append(row)
    result=[]
    for f in FRAMES:
        rows=by_frame[f]
        boundary=[row for row in rows if row["stage"] in ("entry","after_push","handler_return")]
        if [r["stage"] for r in boundary] != ["entry","after_push","handler_return"]:
            raise ValueError(f"RF047 missing or repeated native interrupt boundary {f}")
        before,pushed,returned=boundary
        for r in boundary:
            if not all(k in r for k in ("resume","vector","PB","P","S","emu","master",
                                        "beamMaster","beamV","beamH","stack")):
                raise ValueError(f"RF047 missing native interrupted-state source field {f}")
        if before["S"]!="01F0" or pushed["S"]!="01EC" or pushed["stack"]!=STACK:
            raise ValueError(f"RF047 actual native NMI pushed state unexpected {f}")
        if before["resume"]!=pushed["resume"] or before["vector"]!=pushed["vector"]:
            raise ValueError(f"RF047 captured inconsistent same-call NMI resume/vector {f}")
        # An actual helper read might happen outside the NMI handler, but only
        # same-sequence reads *between* its push and handler-return qualify as
        # possible return-consumer witnesses.
        inside=[x for x in rows if x["stage"]=="read"
                 and pushed["seq"]<x["seq"]<returned["seq"] and x.get("nmi")=="1"]
        first_reader=inside[0] if inside else None
        return_ops=[x for x in rows if x["stage"] in ("interp_rti","compiled_rti")]
        if len(return_ops)>1:
            raise ValueError(f"RF047 duplicate native RTI source events at {f}")
        return_op=return_ops[0] if return_ops else None
        if return_op is not None:
            if not (pushed["seq"]<return_op["seq"]<returned["seq"]):
                raise ValueError(f"RF047 RTI outside native NMI boundaries at {f}")
            if any(k not in return_op for k in ("opcodePC","returnPC","P","S","master")):
                raise ValueError(f"RF047 incomplete native RTI source event at {f}")
            if return_op["S"]!=returned["S"]:
                raise ValueError(f"RF047 RTI versus native handler-return SP mismatch at {f}")
        result.append({"native_host_frame":f,
                       "native_interrupt_entry_resume_PC":before["resume"],
                       "native_interrupt_vector":before["vector"],
                       "native_interrupt_entry_master":int(before["master"]),
                       "native_interrupt_entry_beam":(int(before["beamV"]),int(before["beamH"])),
                       "native_real_push_stack_01ED_01F0":pushed["stack"],
                       "native_handler_return_resume_PC":returned["resume"],
                       "native_handler_return_SP":returned["S"],
                       "native_handler_return_master":int(returned["master"]),
                       "native_inhandler_actual_read_helper_count":len(inside),
                       "native_first_inhandler_actual_stack_read":first_reader,
                       "native_explicit_RTI_event":return_op,
                       "native_actual_RTI_return_PC":return_op["returnPC"] if return_op and return_op["stage"]=="interp_rti" else None,
                       "native_RTI_return_PC_matches_saved_resume":
                           return_op["returnPC"]==before["resume"] if return_op and return_op["stage"]=="interp_rti" else None,
                       "native_true_RTI_opcode_and_return_PC_proven":
                           return_op is not None and return_op["stage"]=="interp_rti"})
    explicit=sum(x["native_explicit_RTI_event"] is not None for x in result)
    if 0<explicit<len(result):
        raise ValueError("RF047 native partial actual RTI instrumentation")
    return {"schema":"rf047-native-NMI-phase-true-guest-ops-v2",
            "native_source_order_is_event_sequence_not_merged_log_lines":True,
            "native_explicit_RTI_evidence_frames":explicit,
            "native_nmi_frames":len(result),
            "native_all_nine_first_window_NMI_entry_afterpush_return":True,
            "native_interrupt_paired_operations":result,
            "native_exact_RTI_opcode_proven":
                explicit==len(result) and all(x["native_true_RTI_opcode_and_return_PC_proven"] for x in result),
            "native_checkpoints_share_original_interrupt_phase_proven":False,
            "complete_USA_event_credit":0}
def report(path:Path,prior:Path|None=None)->dict:
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    with zipfile.ZipFile(path) as z:
        p=json.loads(z.read("producer-report.json"))
        c=json.loads(z.read("case-result.json"))
        native=z.read(NATIVE).decode("utf8","replace")
        source=z.read(REF).decode("utf8","replace")
    mesh=p["zoo_race_mesh"]
    if mesh["mesh_checkpoint_count"]!=78 or mesh["masked_or_excluded_wram_bytes"]!=0 or \
       mesh["raw_byte_exact_sample_count"]!=51 or c["release_credit"]!=0 or \
       c["disposition"]!="strict_candidate":
        raise ValueError("RF047 genuine unmasked Zoo input/control changed")
    out=classify(native)
    source_pc={}
    for line in source.splitlines():
        if line.startswith("QA01RF044ORIGNMI "):
            row=fields(line)
            source_pc[int(row["f"])]=row["pc"]
    if set(source_pc)!=set(FRAMES):
        raise ValueError("RF047 missing nine actual original NMI PCs")
    for pair in out["native_interrupt_paired_operations"]:
        frame=pair["native_host_frame"]
        pair["original_same_host_actual_interrupted_PC"]=source_pc[frame]
        pair["native_resume_equals_original_same_host_PC"]=(
            pair["native_interrupt_entry_resume_PC"]==source_pc[frame])
    out["native_resume_and_original_NMI_PC_9_frame_equal_count"]=sum(
        p["native_resume_equals_original_same_host_PC"]
        for p in out["native_interrupt_paired_operations"])
    out.update({"case_zip_sha256":digest,"source_sha":c["source_sha"],
                "full_WM_pairs":78,"unmasked_exact_pairs":51,"USA_events_accepted":0})
    if prior:
        with zipfile.ZipFile(prior) as z:old=json.loads(z.read("producer-report.json"))
        for key in ("zoo_race_mesh","zoo_next_bowl_handoff","source_terminal_followthrough"):
            if old[key]!=p[key]:raise ValueError("RF047 changed immutable RF045 control "+key)
        out["RF045_full_WM_13_DP_result_Bowl_controls_identical"]=True
        out["RF045_case_zip_sha256"]=hashlib.sha256(prior.read_bytes()).hexdigest()
    if "QA01RF045ORIGSTACK" not in source:
        raise ValueError("RF047 expected original RF045 actual stack counterpart missing")
    return out
def main()->None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("case_zip",type=Path)
    ap.add_argument("--baseline",type=Path)
    ap.add_argument("--output",type=Path)
    a=ap.parse_args()
    s=json.dumps(report(a.case_zip,a.baseline),indent=2,sort_keys=True)+"\n"
    if a.output:a.output.write_text(s,encoding="utf8")
    else:print(s,end="")
if __name__=="__main__":main()
