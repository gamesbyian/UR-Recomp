#!/usr/bin/env python3
"""Fail-closed *original* RF063 bus-entry/checkpoint ordinal qualification.

Never normalize an RF044 getset-entry sample as a returned guest bus read.
An RF045 post-call pull or another consumer witness is still required.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

BUS="QA01RF063ORIGBUS "
CHECK="QA01RF063ORIGCHECKPOINT "
NMI="QA01RF044ORIGNMI "
HEX5=re.compile(r"[0-9A-Fa-f]{10}\\Z")
HEX4=re.compile(r"[0-9A-Fa-f]{4}\\Z")


def fields(line: str) -> dict[str, str]:
    return dict(re.findall(r"(?<!\\S)([A-Za-z][A-Za-z0-9]*)=([^\\s]+)",line))


def inspect(raw: str) -> dict:
    seen=[]
    checkpoints=[]
    nmis=[]
    for line in raw.splitlines():
        for tag in (BUS,CHECK):
            if tag in line and not line.startswith(tag):
                raise ValueError("RF063 event embedded in another log record")
        if "QA01RF063ORIGBUS_TRUNCATED" in line:
            raise ValueError("RF063 original bus recorder truncated")
        if line.startswith(NMI):
            nmis.append(fields(line))
        if not line.startswith(BUS) and not line.startswith(CHECK):
            continue
        checkpoint=line.startswith(CHECK)
        f=fields(line)
        try:
            seq=int(f["seq"])
            frame=int(f["f"])
        except (KeyError,ValueError) as e:
            raise ValueError("RF063 missing original event ordinal/frame") from e
        if seq!=len(seen)+1 or frame<1017 or frame>1025:
            raise ValueError("RF063 duplicate, missing or reordered original event")
        if checkpoint:
            if frame!=1017 or f.get("phase")!="post_real_nmi_push" or not HEX5.fullmatch(f.get("stack","")):
                raise ValueError("RF063 original checkpoint missing real raw five bytes")
            checkpoints.append((seq,f))
        else:
            if f.get("phase")!="getset_entry" or f.get("kind") not in ("rb","rw","wb","ww"):
                raise ValueError("RF063 original bus entry incomplete")
            if f.get("width") not in ("1","2") or not HEX4.fullmatch(f.get("sampled","")):
                raise ValueError("RF063 original bus sample missing")
            if not re.fullmatch(r"[0-9A-Fa-f]{2}:[0-9A-Fa-f]{4}",f.get("pc","")):
                raise ValueError("RF063 original observed PC missing")
            try:
                off=int(f["addr"],16)
                bank=int(f["bank"],16)
            except (KeyError,ValueError) as e:
                raise ValueError("RF063 original physical location missing") from e
            width=int(f["width"])
            if off>0x01f1 or off+width-1<0x01ed or not (bank==0x7e or ((bank&0x7f)<0x40 and off<0x2000)):
                raise ValueError("RF063 bus outside pinned stack filter")
        seen.append((seq,frame,checkpoint))
    if not seen or not any(not c for _,_,c in seen):
        raise ValueError("no actual original getset-entry samples")
    if len(checkpoints)!=1:
        raise ValueError("need exactly one original 2014 physical NMI checkpoint")
    matching=[f for f in nmis if f.get("f")=="1017"]
    if len(matching)!=1 or not HEX5.fullmatch(matching[0].get("new","")):
        raise ValueError("missing independently observed RF044 original NMI post-stack")
    checkpoint=checkpoints[0][1]
    if checkpoint["stack"].upper()!=matching[0]["new"].upper():
        raise ValueError("RF063 raw NMI checkpoint disagrees with independent RF044 observation")
    return {
        "schema":"ur-qa01-rf063-original-source-order/1",
        "sha256_source_log":hashlib.sha256(raw.encode()).hexdigest(),
        "sequenced_original_bus_entries":sum(not c for _,_,c in seen),
        "sequenced_original_checkpoint_count":1,
        "checkpoint_seq":checkpoints[0][0],
        "checkpoint_frame":1017,
        "checkpoint_actual_unmasked_stack_01ed_to_01f1":checkpoint["stack"].upper(),
        "ordinal_contiguous_across_original_bus_and_checkpoint":True,
        "RF044_post_NMI_5_byte_snapshot_matches":True,
        "bus_sampled_before_helper_return":True,
        "actual_bus_read_return_value_for_all_events_proven":False,
        "RF045_post_call_macro_ordinals_joined":False,
        "native_matching_semantic_checkpoint_verified":False,
        "eligible_for_qa01_causal_window":False,
        "accepted_USA_events":0,
    }


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source_log",type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    report=inspect(a.source_log.read_text())
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\\n")
    print("RF063 original source ordering qualified; read-return/native parity remain HOLD")


if __name__=="__main__":
    main()
