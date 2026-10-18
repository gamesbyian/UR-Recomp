#!/usr/bin/env python3
"""RF045 authentic Snes9x Push/Pull macro bus-access and Zoo NMI provenance.

A stack macro is an actual guest bus operation. A missing first pull is only
absence of a captured macro pull, not proof the stored byte is dead.
"""
from __future__ import annotations
import argparse,hashlib,json,re,zipfile
from pathlib import Path
import qa01_rf044_zoo_stack_nmi_report as rf044

MACRO_RE=re.compile(
 r"^QA01RF045ORIGSTACK f=(\d+) v=(\d+) h=(-?\d+) "
 r"kind=(pushB|pushW|pullB|pullW) addr=([A-F0-9]{4}) "
 r"width=(\d+) value=([A-F0-9]{4}) sp0=([A-F0-9]{4}) "
 r"sp1=([A-F0-9]{4}) pc=([A-F0-9]{2}):([A-F0-9]{4})$")
B=rf044.REF
N=rf044.NATIVE
FRAMES=rf044.FRAMES

def observe(source:str, native:str)->dict:
    base=rf044.inspect(source,native)
    if "QA01RF045ORIGSTACK_TRUNCATED" in source:
        raise ValueError("RF045 genuine source stack log truncated")
    ordered=[]
    nmi_indices=[]
    for i,line in enumerate(source.splitlines()):
        if line.startswith("QA01RF045ORIGSTACK"):
            match=MACRO_RE.fullmatch(line)
            if not match:raise ValueError("RF045 malformed authentic source macro")
            f,v,h,kind,addr,width,val,sp0,sp1,pb,pc=match.groups()
            if int(f) not in FRAMES:raise ValueError("RF045 out-of-bounds frame")
            width=int(width)
            if ((kind.endswith("B") and width!=1) or
                (kind.endswith("W") and width!=2) or
                (kind.startswith("push") and int(sp1,16)!=int(sp0,16)-width) or
                (kind.startswith("pull") and int(sp1,16)!=int(sp0,16)+width)):
                raise ValueError("RF045 stack macro width/SP does not match true operation")
            ordered.append({"log_index":i,"frame":int(f),"beam_v":int(v),"beam_h":int(h),
                            "kind":kind,"address":addr,"width":width,"value":val,
                            "SP0":sp0,"SP1":sp1,"PB_PC":pb+":"+pc})
        elif line.startswith("QA01RF044ORIGNMI "):
            nmi_indices.append((i,int(line.split()[1].split("=")[1])))
    if len(nmi_indices)!=9 or [f for _,f in nmi_indices]!=list(FRAMES):
        raise ValueError("RF045 original true NMI calendar changed")
    nmi_calls=[]
    for index,frame in nmi_indices:
        pc=base["original_nmi"][frame-1017]["interrupted_pc"]
        last=[e for e in ordered if e["log_index"]<index and e["frame"]==frame][-3:]
        if len(last)!=3 or [e["kind"] for e in last]!=["pushB","pushW","pushB"] or \
           [e["address"] for e in last]!=["01F0","01EE","01ED"] or \
           [e["value"] for e in last]!=["0082",pc[2:], "0026"]:
            raise ValueError(f"RF045 missing/misaligned actual original NMI macro pushes at {frame}")
        nmi_calls.append({"frame":frame,"NMI_interrupted_pc":pc,"actual_NMI_push_calls":last})
    if len(ordered)<27:
        raise ValueError("RF045 source NMI macro bus witness absent")
    pulls=[e for e in ordered if e["kind"].startswith("pull")]
    return {
        "schema":"rf045-genuine-zoo-stack-Push-Pull-origin-nmi-v1",
        "source_real_NMI_push_macro_groups":nmi_calls,
        "source_actual_stack_macro_rows":len(ordered),
        "source_actual_stack_pull_macro_rows":len(pulls),
        "source_actual_bounded_pulls":pulls,
        "source_actual_NMI_push_instruction_calls_proven":True,
        "native_first_four_genuine_WM_WRAM_writer_rows":base["native_first_four_writer_per_frame"],
        "native_intact_read_helper_rows":base["native_valid_read_row_count"],
        "original_NMI_SP01F0_to_SP01EC_proven":True,
        "absolute_original_native_CPU_opcode_phase_registered":False,
        "every_possible_original_memory_writer_observed":False,
        "original_unobserved_non_macro_stack_read_excluded":False,
        "NMI_stale_frame_bytes_proven_never_consumed":False,
        "USA_full_course_accepted":False,"USA_accepted_count":0
    }

def report(case:Path,prior:Path|None=None)->dict:
    digest=hashlib.sha256(case.read_bytes()).hexdigest()
    with zipfile.ZipFile(case) as z:
        p=json.loads(z.read("producer-report.json"))
        c=json.loads(z.read("case-result.json"))
        source=z.read(B).decode("utf8","replace")
        native=z.read(N).decode("utf8","replace")
        n=len(z.namelist())
    mesh=p["zoo_race_mesh"]
    if n!=18 or mesh["mesh_checkpoint_count"]!=78 or mesh["raw_byte_exact_sample_count"]!=51 or mesh["masked_or_excluded_wram_bytes"]!=0 or c["disposition"]!="strict_candidate" or c["release_credit"]!=0 or sum(x["original_native_full_wram_byte_difference"]["differing_byte_count"] for x in mesh["samples"])!=92:
        raise ValueError("RF045 strict original/native full unmasked Zoo control changed")
    record=observe(source,native)
    record.update({"source_research_case_sha256":digest,
                   "case_file_count":n,
                   "full_wram_pair_count":78,
                   "exact_full_wram_pair_count":51,
                   "all_92_WM_occurrences_unmasked":True})
    if prior is not None:
        with zipfile.ZipFile(prior) as z:old=json.loads(z.read("producer-report.json"))
        for key in ("zoo_race_mesh","zoo_next_bowl_handoff","source_terminal_followthrough"):
            if old[key]!=p[key]:raise ValueError("RF045 changed RF044 control: "+key)
        record["RF044_all_78_WM_13_DP_and_source_result_controls_identical"]=True
        record["RF044_case_sha256"]=hashlib.sha256(prior.read_bytes()).hexdigest()
    return record

def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("case_zip",type=Path)
    p.add_argument("--baseline",type=Path)
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    v=json.dumps(report(a.case_zip,a.baseline),indent=2,sort_keys=True)+"\n"
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(v,encoding="utf8")
    else: print(v,end="")
if __name__=="__main__":main()
