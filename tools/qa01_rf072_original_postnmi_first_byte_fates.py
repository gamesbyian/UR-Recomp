#!/usr/bin/env python3
"""RF072: actual first original stack-byte reads after a REAL NMI checkpoint.

Only source-local event ordinals and already-qualified RF071 true getter-to-
return transactions; no native relative-clock or semantic-checkpoint mapping.
An actual source read with NO transaction proof cannot silently count.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import zipfile

import qa01_rf063_original_sequence_report as rf63
import qa01_rf071_original_real_read_join as rf71

ADDRESSES=tuple(range(0x01ed,0x01f2))
SCHEMA="ur-qa01-rf072-original-after-NMI-source-byte-fates/1"

def require(ok:bool, why:str)->None:
    if not ok:
        raise ValueError(why)

def fates(raw:str, transactions:list[dict])->dict:
    lines=raw.splitlines()
    checkpoints=[rf63.fields(s) for s in lines if s.startswith(rf63.CHECK)]
    require(len(checkpoints)==1,"RF072 real source NMI stack checkpoint absent or ambiguous")
    cp=checkpoints[0]
    try:
        cp_seq=int(cp["seq"]);cp_frame=int(cp["f"])
        cp_bytes=bytes.fromhex(cp["stack"])
    except (KeyError,ValueError) as e:
        raise ValueError("RF072 raw original post-real-NMI stack checkpoint malformed") from e
    require(cp_frame==1017 and len(cp_bytes)==5 and cp["phase"]=="post_real_nmi_push",
            "RF072 original source NMI observation phase changed")
    by_read_seq={}
    for tx in transactions:
        index=tx["source_getset_seq"]
        require(index not in by_read_seq,"RF072 duplicate independently qualified source getter")
        by_read_seq[index]=tx
    entries=[]
    for s in lines:
        if not s.startswith(rf63.BUS):
            continue
        row=rf63.fields(s)
        try:
            seq=int(row["seq"]);frame=int(row["f"])
            base=int(row["addr"],16);width=int(row["width"])
            value=int(row["sampled"],16)
        except (KeyError,ValueError) as e:
            raise ValueError("RF072 executed original getset entry incomplete") from e
        if seq<=cp_seq:
            continue
        require(frame>=cp_frame and width in (1,2) and row["kind"] in ("rb","rw","wb","ww"),
                "RF072 source original guest event regressed or corrupt")
        if base+width<=ADDRESSES[0] or base>ADDRESSES[-1]:
            continue
        entries.append((seq,row,base,width,value))
    # This method intentionally does not invent unrecorded writes, aliases,
    # DMA or instruction fetches. Only the visible getset substream is known.
    first_fates={}
    for i,address in enumerate(ADDRESSES):
        reads=[];writes=[]
        for seq,row,base,width,value in entries:
            if not base<=address<base+width:
                continue
            byte=(value>>(8*(address-base)))&255
            kind=row["kind"]
            if kind.startswith("r"):
                transaction=by_read_seq.get(seq)
                require(transaction is not None and
                        transaction["physical_bus_address"]==f"00:{base:04X}" and
                        transaction["bus_kind"]==kind and
                        transaction["host_frame"]==int(row["f"]) and
                        ((int(transaction["returned"],16)>>(8*(address-base)))&255)==byte,
                        "RF072 observed source read not qualified as actual getter-to-return byte")
                reads.append((seq,row,byte))
            else:
                writes.append((seq,row,byte))
        first_read=reads[0] if reads else None
        first_write=writes[0] if writes else None
        fate=("read_before_first_observed_write"
              if first_read and (not first_write or first_read[0]<first_write[0])
              else "first_observed_write_precedes_read"
              if first_write else "neither_observed_in_bounded_source_window")
        if first_read and fate=="read_before_first_observed_write":
            require(first_read[2]==cp_bytes[i],
                    "RF072 source real first read changed checkpoint byte before any recorded writer")
        def receipt(v):
            if v is None:
                return None
            seq,row,byte=v
            return {"source_global_seq":seq,"host_frame":int(row["f"]),
                    "source_PC_context":row["pc"],
                    "physical_original_bus_address":f"00:{int(row['addr'],16):04X}",
                    "width":int(row["width"]),"raw_byte":f"{byte:02X}",
                    "original_V":int(row["v"]),"original_H":int(row["h"])}
        first_fates[f"00:{address:04X}"]={
            "checkpoint_byte":f"{cp_bytes[i]:02X}",
            "first_actual_original_byte_read":receipt(first_read),
            "first_observed_original_byte_write":receipt(first_write),
            "fate_in_recorded_original_getset_window":fate,
            "no_unobserved_other_path_writers_proven":False
        }
    return {
        "schema":SCHEMA,
        "source_original_checkpoint_seq":cp_seq,
        "source_original_checkpoint_frame":cp_frame,
        "source_real_post_NMI_stack_01ed_to_01f1":cp["stack"].upper(),
        "source_original_byte_fates":first_fates,
        "all_five_original_bytes_have_a_real_qualified_read_before_next_observed_write":
            all(v["fate_in_recorded_original_getset_window"]==
                "read_before_first_observed_write" for v in first_fates.values()),
        "original_native_semantically_equivalent_checkpoint_proven":False,
        "native_first_differing_byte_actual_reader_proven":False,
        "every_original_non_getset_write_proven_absent":False,
        "all_race_frames_proven_equal":False,
        "eligible_for_QA01_causal_window":False,
        "accepted_USA_events":0,
    }

def authenticated_case(path:Path)->dict:
    previous=rf71.authenticated_case(path)
    with zipfile.ZipFile(path) as z:
        raw=z.read(rf71.LOG).decode("utf8")
    result=fates(raw,previous["transactions"])
    require(result["source_original_checkpoint_seq"]==193 and
            result["source_real_post_NMI_stack_01ed_to_01f1"]=="26F0D48226" and
            result["all_five_original_bytes_have_a_real_qualified_read_before_next_observed_write"],
            "RF072 genuine original five-byte after-NMI first-consumer chain changed")
    expected_read_seq=[194,196,196,198,200]
    expected_write_seq=[210,210,203,203,202]
    require([
        result["source_original_byte_fates"][f"00:{x:04X}"]["first_actual_original_byte_read"]["source_global_seq"]
        for x in ADDRESSES]==expected_read_seq and [
        result["source_original_byte_fates"][f"00:{x:04X}"]["first_observed_original_byte_write"]["source_global_seq"]
        for x in ADDRESSES]==expected_write_seq,
        "RF072 exact real original source first-read/overwrite event identities changed")
    result["source_authenticated_archive_SHA256"]=previous["case_archive_sha256"]
    result["source_exact_original_replay_log_SHA256"]=previous["original_source_log_sha256"]
    result["reused_RF071_903_original_real_bus_getter_return_join_count"]=len(previous["transactions"])
    result["unmasked_original_native_full_Wram_byte_difference_occurrences"] = 92
    return result

def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("case_zip",type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    result=authenticated_case(a.case_zip)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("RF072 all 5 actually read in original after NMI; native causal equivalence still HOLD")

if __name__=="__main__":
    main()
