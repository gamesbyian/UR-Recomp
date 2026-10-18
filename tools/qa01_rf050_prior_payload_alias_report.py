#!/usr/bin/env python3
"""RF050 retrospective D0/63 sound-payload alias witness (not time alignment).

Use an exact archived RF049 original/native Zoo case. Show why a port3 D0
followed by port2 63 *occurring earlier* cannot be equated to the later
original LDA 11:C774 merely because its output bytes are identical. Preserve
source log ordinals/ages, native host-master axis and their separate epochs.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
import qa01_rf049_sound_operand_report as rf049

O="QA01RF037ORIGCPU2 "
N="QA01RF037NATIVEUP "
L="QA01RF049LDA "
S="QA01RF049STA "
def fields(l:str)->dict:
    out={}
    for part in l.split()[1:]:
        if "=" in part:
            k,v=part.split("=",1)
            if not k or k in out:raise ValueError("ambiguous source/native writer field")
            out[k]=v
    return out

def analyze(original:str,native:str)->dict:
    original_lines=original.splitlines()
    native_lines=native.splitlines()
    if "QA01RF037ORIGCPU2_TRUNCATED" in original or        "QA01RF037NATIVEUP_TRUNCATED" in native:
        raise ValueError("RF037 writer prefix truncated, not a valid alias census")
    source=[(i,fields(row)) for i,row in enumerate(original_lines) if row.startswith(O)]
    guest=[(i,fields(row)) for i,row in enumerate(native_lines)
           if row.startswith(N) and "kind=rtl-apu-enter " in row]
    loads=[(i,fields(row)) for i,row in enumerate(original_lines) if row.startswith(L)]
    stores=[(i,fields(row)) for i,row in enumerate(original_lines) if row.startswith(S)]
    if not source or not guest or not loads or len(stores)!=2:
        raise ValueError("missing qualified original/native bus or source LDA/STA evidence")
    aliases_o=[i for i in range(len(source)-1)
               if (source[i][1].get("port"),source[i][1].get("val"),
                   source[i+1][1].get("port"),source[i+1][1].get("val"))
                  ==("3","D0","2","63")]
    aliases_n=[i for i in range(len(guest)-1)
               if (guest[i][1].get("reg"),guest[i][1].get("val"),
                   guest[i+1][1].get("reg"),guest[i+1][1].get("val"))
                  ==("2143","D0","2142","63")]
    if len(aliases_o)!=1 or len(aliases_n)!=1:
        raise ValueError("identical D0/63 alias is absent or not unique in observed prefix")
    a,b=aliases_o[0],aliases_n[0]
    if a!=b:
        raise ValueError("source/native writer prefix ordinals disagree")
    if (source[a][0]>=loads[0][0] or source[-1][0]>=loads[0][0] or
        source[a+1][0]>=loads[0][0]):
        raise ValueError("earlier captured alias does not precede original later LDA")
    first=loads[0][1]
    if (first.get("ea"),first.get("frame"),first.get("a1"))!=("11C774","6124","63D0"):
        raise ValueError("original source later LDA identity has changed")
    if [item[1].get("pc") for item in stores]!=["82:82F2","82:82F6"]:
        raise ValueError("original later STA instructions missing or out of order")
    if [item[1].get("a0") for item in stores]!=["63D0","D063"]:
        raise ValueError("original later STA outputs do not encode D0/63")
    if any(item[0]<=loads[0][0] for item in stores):
        raise ValueError("original source later STA is not after LDA")
    def at(row,keys):return {k:row[k] for k in keys}
    return {
        "schema":"rf050-source-native-earlier-payload-alias-v1",
        "older_original_source_port_capture_size":len(source),
        "older_native_guest_port_capture_size":len(guest),
        "older_D0_63_pair_unique_in_both_captured_streams":True,
        "older_D0_63_zero_based_writer_pair_ordinals":[a,a+1],
        "older_source_original_log_line_indices":[source[a][0],source[a+1][0]],
        "older_original_source_writer_pair":[
            at(source[i][1],("age","v","h","port","val")) for i in (a,a+1)],
        "older_native_host_writer_pair":[
            at(guest[i][1],("frame","master","reg","val","scope")) for i in (b,b+1)],
        "original_later_LDA_log_line":loads[0][0],
        "original_later_source_LDA":at(first,("ordinal","frame","v","h","ea","a0","a1")),
        "original_later_original_STA":[
            at(x[1],("frame","v","h","pc","a0","a1")) for x in stores],
        "original_writer_capture_ends_before_later_LDA":True,
        "same_output_bytes_are_not_sufficient_transaction_identity":True,
        "source_original_CPU_frame_to_native_host_registered":False,
        "late_original_real_S9xAPUWritePort_publication_proven_by_this_archive":False,
        "complete_USA_events_accepted":0,
    }

def report(case:Path)->dict:
    with zipfile.ZipFile(case) as z:
        original=z.read("work/zoom-zoo/replay/reference.log").decode("utf8","replace")
        native=z.read("work/zoom-zoo/replay/native.log").decode("utf8","replace")
    out=analyze(original,native)
    qualified=rf049.analyze_source(original)
    out["qualified_source_LDA_census_count"]=qualified["genuine_original_82F0_LDA_count"]
    out["case_zip_sha256"]=hashlib.sha256(case.read_bytes()).hexdigest()
    return out

def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("case",type=Path)
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    body=json.dumps(report(args.case),indent=2,sort_keys=True)+"\n"
    if args.out:args.out.write_text(body,encoding="utf8")
    else:print(body,end="")
if __name__=="__main__":main()
