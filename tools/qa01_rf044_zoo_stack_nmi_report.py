#!/usr/bin/env python3
"""RF044: fail-closed replay attestation for the Zoo first NMI stack window.

The original NMI before/after RAM observations and native authentic WRAM
writer journal must not be conflated with complete two-sided bus provenance.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import zipfile

REF="work/zoom-zoo/replay/reference.log"
NATIVE="work/zoom-zoo/replay/native.log"
EXPECTED_SHA="84d6906af7ebfe0dee3f77fb90b4c4f50400fc7c45add3e586f14035daf15357"
SRC_RE=re.compile(r"^QA01RF044ORIGNMI f=(\d+) f1=(\d+) pc=([A-Fa-f0-9]{6}) S0=([A-Fa-f0-9]{4}) S1=([A-Fa-f0-9]{4}) old=([A-Fa-f0-9]{10}) new=([A-Fa-f0-9]{10})$")
WR_RE=re.compile(r"^f(\d+)\s+([A-Fa-f0-9]{2}):([A-Fa-f0-9]{4})=([A-Fa-f0-9]{2,4}) w([12]) (.*?) rf044_S=([A-Fa-f0-9]{4}) IPC=([A-Fa-f0-9]{6})$")
FIRST_WRITES=("01F0","01EF","01EE","01ED")
EXPECTED_NATIVE=("82","D4","EE","26")
FRAMES=tuple(range(1017,1026))

def inspect(ref:str,native:str)->dict:
    if any(x in ref+"\n"+native for x in ("QA01RF044ORIGBUS_TRUNCATED","QA01RF044NATIVEREAD_TRUNCATED","QA01RF044NATIVEWRITE_TRUNCATED")):
        raise ValueError("RF044 incomplete observer, truncation flag present")
    ref_lines=ref.splitlines()
    nmi=[]
    for line in ref_lines:
        if line.startswith("QA01RF044ORIGNMI"):
            m=SRC_RE.fullmatch(line)
            if not m: raise ValueError("RF044 malformed original NMI")
            f,f1,pc,s0,s1,old,new=m.groups()
            if int(f)!=int(f1) or (s0,s1)!=("01F0","01EC"):
                raise ValueError("RF044 original interrupt frame/SP mismatch")
            nmi.append({"frame":int(f),"interrupted_pc":pc,"sp_before":s0,
                        "sp_after":s1,"bytes_before":old,"bytes_after":new})
    if [x["frame"] for x in nmi]!=list(FRAMES):
        raise ValueError("RF044 exactly nine source NMI entries required")
    expected_source=("82D4F0","82D4EE","82D4F0","82D4EE","82D4F0",
                     "82D4EE","82D4F0","82D4EE","82D4EE")
    if tuple(x["interrupted_pc"] for x in nmi)!=expected_source:
        raise ValueError("RF044 source interrupted PCs differ")
    if any(x["bytes_after"]!="26"+x["interrupted_pc"][4:6]+x["interrupted_pc"][2:4]+x["interrupted_pc"][:2]+"26"
           for x in nmi):
        raise ValueError("RF044 true Snes9x NMI stack postimage differs from interrupted PC/status")
    # Source original byte/word bus hooks were staged, but there are zero rows.
    # This never means "zero guest reads/writes"; it means the bus probe was
    # unproductive and any source last-writer/reader claim must remain open.
    orig_bus=sum(x.startswith("QA01RF044ORIGBUS ") for x in ref_lines)
    native_lines=native.splitlines()
    native_read=sum(x.startswith("QA01RF044NATIVEREAD ") and " scope=" in x for x in native_lines)
    writers={}
    for line in native_lines:
        m=WR_RE.fullmatch(line)
        if not m:continue
        frame,bank,addr,val,width,scope,sp,ipc=m.groups()
        if int(frame) not in FRAMES:continue
        writers.setdefault(int(frame),[]).append(
          {"bank":bank,"addr":addr,"value":val,"width":int(width),
           "scope":scope,"sp":sp,"ipc":ipc})
    first_writers=[]
    for f in FRAMES:
        all_w=writers.get(f,[])
        first=all_w[:4]
        if len(first)!=4 or tuple(x["addr"] for x in first)!=FIRST_WRITES or tuple(x["value"] for x in first)!=EXPECTED_NATIVE or any(x["scope"]!="(none)" for x in first):
            raise ValueError(f"RF044 native first NMI-style writer four bytes absent or changed at {f}")
        first_writers.append({"frame":f,"first_four":first,"valid_writer_rows":len(all_w)})
    return {
      "original_nmi":nmi,"native_first_four_writer_per_frame":first_writers,
      "original_getset_bus_row_count":orig_bus,
      "native_valid_read_row_count":native_read,
      "native_read_log_interleaved_with_writer_stderr_possible":True,
      "actual_source_nmi_entry_and_four_byte_postimage_proven":True,
      "native_four_WM_WRAM_stores_per_host_frame_observed":True,
      "native_writer_scope_none_is_not_proof_of_interrupt_handler_pc":True,
      "original_single_bus_writer_and_reader_proven":False,
      "original_bus_probe_complete":False,
      "two_guest_instruction_phase_alignment_proven":False,
      "same_frame_NMI_return_pc_parity_proven":False,
      "no_stack_byte_mask_authorized":True,
      "full_USA_event_accepted":False,
      "accepted_USA_event_count":0
    }

def report(case:Path,baseline:Path|None=None,strict_sha:bool=True)->dict:
    digest=hashlib.sha256(case.read_bytes()).hexdigest()
    if strict_sha and digest!=EXPECTED_SHA:raise ValueError("RF044 immutable V5 case SHA changed")
    with zipfile.ZipFile(case) as z:
        control=json.loads(z.read("producer-report.json"))
        result=json.loads(z.read("case-result.json"))
        ref=z.read(REF).decode("utf8","replace")
        native=z.read(NATIVE).decode("utf8","replace")
        files=z.namelist()
    m=control["zoo_race_mesh"]
    if len(files)!=18 or m["mesh_checkpoint_count"]!=78 or m["raw_byte_exact_sample_count"]!=51 or m["masked_or_excluded_wram_bytes"] or sum(x["original_native_full_wram_byte_difference"]["differing_byte_count"] for x in m["samples"])!=92 or result["disposition"]!="strict_candidate":
        raise ValueError("RF044 strict underlying full-source Zoo controls failed")
    detail=inspect(ref,native)
    detail.update({"schema":"rf044-executed-zoo-first-stack-NMI-readwrite-v1",
                   "source_research_head":"216a8818f5a6719f7963205208e362c9e812cf30",
                   "action_run_id":39078406796,"case_artifact_id":12118217074,
                   "case_zip_sha256":digest,"case_file_count":len(files),
                   "source_core_sha256":control.get("reference_core_sha256"),
                   "native_executable_sha256":control.get("native_executable_sha256"),
                   "unmasked_128KiB_pair_count":78,
                   "whole_wram_exact_pair_count":51,
                   "unmasked_byte_difference_occurrences":92})
    if baseline is not None:
        with zipfile.ZipFile(baseline) as z:
            p=json.loads(z.read("producer-report.json"))
        fields=("zoo_race_mesh","zoo_next_bowl_handoff","source_terminal_followthrough")
        for key in fields:
            if p[key]!=control[key]:raise ValueError("RF044 versus RF041 control differs: "+key)
        detail["RF041_all_78_WM_and_13_DP_and_handoff_controls_bit_identical"]=True
        detail["RF041_case_zip_sha256"]=hashlib.sha256(baseline.read_bytes()).hexdigest()
    return detail

def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("case_zip",type=Path)
    p.add_argument("--compare-case",type=Path)
    p.add_argument("--output",type=Path)
    p.add_argument("--allow-other-zip",action="store_true")
    a=p.parse_args()
    out=json.dumps(report(a.case_zip,a.compare_case,not a.allow_other_zip),indent=2,sort_keys=True)+"\n"
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(out,encoding="utf8")
    else: print(out,end="")

if __name__=="__main__":main()
