#!/usr/bin/env python3
"""RF083 independent original Zoo DP source trace audit, ROM-free.

Requires actual prior and instrumented case ZIPs and external SHA-256s.
No guest execution, source-mutating patch, or release acceptance.
"""
from __future__ import annotations
import argparse, collections, hashlib, json, re, zipfile
from pathlib import Path

SCHEMA="ur-qa01-rf083-source-archive-audit/1"
PREFIX="work/zoom-zoo/replay/"
SLOTS=(0x63,0x64,0x65,0x69)
EVENT_FIELDS={"seq","type","frame","pc","op","pre_v","pre_h",
              "post_v","post_h","slot","old","new","setterCount",
              "setterAddr","setterVal","clock"}

def ensure(value, reason):
    if not value: raise ValueError(reason)

def sha(path):
    digest=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            digest.update(block)
    return digest.hexdigest()

def inspect_zip(z):
    names=z.namelist()
    ensure(len(names)==len(set(names)), "duplicate archive members")
    ensure(z.testzip() is None,"corrupt archive CRC")
    ensure(all(not n.startswith("/") and ".." not in Path(n).parts
               for n in names),"unsafe archive member")
    return set(names)

def fields(row,marker):
    ensure(row.startswith(marker),"unexpected source event")
    parts=row[len(marker):].split()
    ensure(all(part.count("=")==1 for part in parts),"invalid source event token")
    pairs=[part.split("=",1) for part in parts]
    ensure(len(pairs)==len(dict(pairs)),"duplicate source event key")
    return dict(pairs)

def parse_trace(log):
    ensure("QA01RF083ORIG_TRUNCATED" not in log,
           "truncated real original CPU sound observer")
    heartbeats=[];events=[]
    for line in log.splitlines():
        if line.startswith("QA01RF083ORIG_HEART "):
            row=fields(line,"QA01RF083ORIG_HEART ")
            ensure(set(row)=={"frame","v","h"},"original heartbeat schema")
            heartbeats.append(int(row["frame"]))
        if line.startswith("QA01RF083ORIG seq="):
            row=fields(line,"QA01RF083ORIG ")
            ensure(set(row)==EVENT_FIELDS,"original event schema")
            ensure(int(row["seq"])==len(events)+1,"source event ordinal gap/duplicate")
            ensure(int(row["frame"]) in range(6069,6080),"wrong source CPU frame")
            ensure(row["clock"]=="original_cpu","host/native clock substituted")
            ensure(row["type"] in ("opcode_delta","setter_entry"),"invalid source event kind")
            ensure(int(row["slot"],16) in SLOTS,"unexpected source memory address")
            for key,width in (("pc",6),("op",2),("slot",4),("old",2),
                              ("new",2),("setterAddr",8),("setterVal",2)):
                ensure(bool(re.fullmatch("[0-9A-F]{"+str(width)+"}",row[key])),
                       "invalid original hex "+key)
            if row["type"]=="opcode_delta":
                ensure(row["old"]!=row["new"],"unchanged raw opcode byte")
            events.append(row)
    ensure(heartbeats==list(range(6069,6080)),
           "source frame heartbeat missing, repeated or out of order")
    ensure(events,"actual original source executed no selected opcode")
    return events,heartbeats

def audit(before:Path,after:Path,before_sha:str,after_sha:str,expected=320):
    for label,path,target in (("baseline",before,before_sha),
                              ("instrumented",after,after_sha)):
        ensure(bool(re.fullmatch("[0-9a-f]{64}",target)),"missing expected "+label+" SHA")
        ensure(path.is_file() and not path.is_symlink(),"missing original "+label+" archive")
        ensure(sha(path)==target,label+" archive SHA drift")
    with zipfile.ZipFile(before) as b,zipfile.ZipFile(after) as a:
        old=inspect_zip(b);new=inspect_zip(a)
        raw=sorted(name for name in old if name.startswith(PREFIX) and
                   name.endswith((".wram.bin",".sram.bin")))
        ensure(len(raw)==expected and expected>0,
               "unexpected number of original unmasked raw images")
        for name in raw:
            ensure(name in new,"missing historical source raw image "+name)
            size=131072 if name.endswith(".wram.bin") else 8192
            r0,r1=b.read(name),a.read(name)
            ensure(len(r0)==size and len(r1)==size,
                   "wrong original unmasked image byte size")
            ensure(r0==r1,"actual source/native raw image changed "+name)
        ensure("producer-report.json" in old and "producer-report.json" in new,
               "missing source case report")
        p0=json.loads(b.read("producer-report.json"))
        p1=json.loads(a.read("producer-report.json"))
        for key in ("rom_sha256","original_movie_sha256","source_sram_sha256",
                    "native_executable_sha256","zoo_race_mesh"):
            ensure(p0.get(key)==p1.get(key),
                   "source identity or unmasked original/native mesh changed: "+key)
        ensure(p0["reference_core_sha256"]!=p1["reference_core_sha256"],
               "original source core was not instrumented")
        frames=[]
        for offset in range(5034,5047):
            fname=f"scene-{offset:05d}.wram.bin"
            rn,nn=PREFIX+"ref/"+fname,PREFIX+"native/"+fname
            ensure(rn in new and nn in new,"missing genuine original/native WRAM pair")
            r,n=a.read(rn),a.read(nn)
            ensure(len(r)==len(n)==131072,"short full raw WRAM pair")
            diff=[i for i,(x,y) in enumerate(zip(r,n)) if x!=y]
            if offset==5039:ensure(not diff,"+5039 no longer full WRAM equal")
            if offset==5040:ensure(diff==[0x63,0x69],
                                   "+5040 lost exact source two-byte discrepancy")
            frames.append({"offset":offset,"difference_count":len(diff),
                           "difference_offsets":diff,
                           "source_sha256":hashlib.sha256(r).hexdigest(),
                           "native_sha256":hashlib.sha256(n).hexdigest()})
        ensure(PREFIX+"reference.log" in new,"missing genuine Snes9x source log")
        events,heartbeats=parse_trace(a.read(PREFIX+"reference.log").decode("utf8"))
        mutations=collections.Counter(e["slot"] for e in events if e["type"]=="opcode_delta")
        sites=collections.defaultdict(collections.Counter)
        for e in events:
            if e["type"]=="opcode_delta":
                sites[e["slot"]][e["pc"]+"|"+e["op"]]+=1
        return {"schema":SCHEMA,"baseline_zip_sha256":before_sha,
                "instrumented_zip_sha256":after_sha,
                "native_binary_sha256":p1["native_executable_sha256"],
                "original_core_instrumented_sha256":p1["reference_core_sha256"],
                "original_source_input_sha256":p1["original_movie_sha256"],
                "control_raw_images_unmasked_byte_exact":len(raw),
                "control_raw_images_checked":len(raw),
                "source_local_heartbeat_frames":heartbeats,
                "total_rf083_events":len(events),
                "original_opcode_delta_count":sum(mutations.values()),
                "original_real_setbyte_entry_count":sum(
                    e["type"]=="setter_entry" for e in events),
                "source_mutations_by_slot":dict(sorted(mutations.items())),
                "source_executed_pc_opcode_counts":{
                    k:dict(sorted(c.items())) for k,c in sorted(sites.items())},
                "raw_wram_phase_census":frames,
                "native_executed_same_phase_cause_proven":False,
                "complete_usa_event_credit":0,"windows_release_gate_credit":0}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for flag in ("baseline","instrumented","baseline-sha256",
                 "instrumented-sha256","out"):
        p.add_argument("--"+flag,required=True,type=Path if flag in (
            "baseline","instrumented","out") else str)
    p.add_argument("--expected-common-raw",type=int,default=320)
    args=p.parse_args()
    receipt=audit(args.baseline,args.instrumented,args.baseline_sha256,
                  args.instrumented_sha256,args.expected_common_raw)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
    print("RF083 original executed-source events",receipt["total_rf083_events"],
          "raw identical",receipt["control_raw_images_checked"],"release credit 0")
if __name__=="__main__":main()
