#!/usr/bin/env python3
"""RF051 actual source SPC late input, bounded and fail-closed.

Does not equate sender bytes with SPC reads, or original local ages with
native master clocks. Require independent true CPU port publications from
RF050 before ordering any receiver observations.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

def parse_row(line: str)->dict:
    row={}
    for token in line.split()[1:]:
        if "=" in token:
            k,v=token.split("=",1)
            if not k or k in row:raise ValueError("duplicate original source SPC field")
            row[k]=v
    return row

def examine(source: str)->dict:
    if "QA01RF051ORIGSPC_TRUNCATED" in source:
        raise ValueError("RF051 original SPC actual read trace truncated")
    lines=source.splitlines()
    writes=[parse_row(l) for l in lines if l.startswith("QA01RF050ORIGAPU ")]
    if not writes:raise ValueError("RF050 genuine late original CPU→APU writes not present")
    pairs=[(a,b) for a,b in zip(writes,writes[1:])
           if (a.get("port"),a.get("val"),b.get("port"),b.get("val"))
              ==("3","D0","2","63")]
    if len(pairs)!=1:raise ValueError("RF050 source transaction unique D0/63 pair not found")
    source_age0=int(pairs[0][0]["age"])
    source_age1=int(pairs[0][1]["age"])
    if (source_age0,source_age1)!=(104485254,104485258):
        raise ValueError("RF050 exact original source publication clock changed")
    read_rows=[parse_row(l) for l in lines if l.startswith("QA01RF051ORIGSPC ")]
    samples=[]
    for i,row in enumerate(read_rows,1):
        if any(k not in row for k in ("seq","age","v","h","spcpc","port","val","debt")):
            raise ValueError("RF051 genuine source read missing identity")
        if int(row["seq"])!=i or row["port"] not in ("2","3"):
            raise ValueError("RF051 source SPC read sequence/port invalid")
        age=int(row["age"])
        if not 104485200<=age<=104488000:
            raise ValueError("RF051 source SPC clock outside pinned window")
        if len(row["val"])!=2 or any(ch not in "0123456789ABCDEF" for ch in row["val"]):
            raise ValueError("RF051 source SPC read payload malformed")
        samples.append({
            "ordinal":i, "source_SPC_age":age,
            "relative_to_original_port3_publication":age-source_age0,
            "relative_to_original_port2_publication":age-source_age1,
            "port":int(row["port"]),"value":row["val"],
            "SPC_pc":row["spcpc"],"SPC_debt":int(row["debt"]),
            "source_cpu_v":int(row["v"]),"source_cpu_h":int(row["h"])
        })
    if any(b["source_SPC_age"]<a["source_SPC_age"] for a,b in zip(samples,samples[1:])):
        raise ValueError("RF051 source SPC read age reversed")
    return {"schema":"rf051-real-original-late-spc-f6f7-v1",
        "frozen_original_port3_publication_age":source_age0,
        "frozen_original_port2_publication_age":source_age1,
        "real_original_SPC_F6_F7_read_count":len(samples),
        "source_receiver_capture_missing":not bool(samples),
        "true_source_SPC_observations":samples[:256],
        "original_SPC_trace_is_not_native_clock_registration":True,
        "native_corresponding_late_transaction_proven":False,
        "USA_complete_event_credit":0}

def report(case:Path)->dict:
    with zipfile.ZipFile(case) as z:
        text=z.read("work/zoom-zoo/replay/reference.log").decode("utf8","replace")
        result=json.loads(z.read("case-result.json"))
    out=examine(text)
    if result.get("release_credit")!=0 or result.get("disposition")!="strict_candidate":
        raise ValueError("RF051 case release admission changed")
    out["case_sha256"]=hashlib.sha256(case.read_bytes()).hexdigest()
    out["frozen_run_source_sha"]=result.get("source_sha")
    return out
def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("case",type=Path)
    a=p.parse_args()
    print(json.dumps(report(a.case),indent=2,sort_keys=True))
if __name__=="__main__":main()
