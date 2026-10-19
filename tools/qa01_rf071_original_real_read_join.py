#!/usr/bin/env python3
"""RF071: authenticate REAL source getset read-entry -> actual stack return.

This is a bounded original-only verifier, not a CPU interpreter, source/native
clock equivalence argument or an independent complete-USA-event adjudication.
Never attach a post-Pull PC to a preceding getter as a fetched opcode PC.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

import qa01_rf063_original_sequence_report as rf63
import qa01_rf064_original_pull_return_report as rf64
import qa01_rf066_original_consumed_report as rf66

SCHEMA="ur-qa01-rf071-original-executed-getset-stack-pull-transaction/1"
CASE_SHA256="90b03d7e035c7a1939b488211b98165615e3fc63226fe57ac718fc7e3e772763"
ORIGINAL_LOG_SHA256="04989c5b60a92b9d393a66ad8e5a84e522f72d8f92bde2af83de5df2cd94bcb9"
SOURCE_SHA="2cfb99308303ba77a05188ee03cf91b894a46954"
LOG="work/zoom-zoo/replay/reference.log"

def require(ok:bool,why:str)->None:
    if not ok:
        raise ValueError(why)

def validate_log(raw:str)->dict:
    # All three earlier readers have separate fail-closed contracts.
    orig=rf63.inspect(raw)
    old=rf64.check(raw)
    current=rf66.examine(raw)
    events=rf64.extract(raw,rf63.BUS)
    mirrors=rf64.extract(raw,"QA01RF044ORIGBUS ")
    pulls=rf64.extract(raw,rf64.PULL)
    actual=rf64.extract(raw,rf66.TAG)
    rf45=rf64.extract(raw,rf64.MACRO)
    require(len(events)==len(mirrors) and
            len(actual)==len(pulls)==len([x for x in rf45
                                          if x.get("kind") in ("pullB","pullW")]),
            "RF071 actual source original read/write/return populations incomplete")
    by_seq={}
    mirror_reads=0
    for x,y in zip(events,mirrors):
        require(all(x.get(key)==y.get(legacy) for key,legacy in
                    (("f","f"),("v","v"),("h","h"),("kind","kind"),
                     ("bank","bank"),("addr","addr"),("width","w"),
                     ("sampled","value"),("S","S"))),
                "RF071 physically executed original RF044/RF063 getset observations disagree")
        require(x["pc"]==y.get("pb")+":"+y.get("pc"),
                "RF071 original getter PC snapshots from two witnesses disagree")
        index=int(x["seq"])
        require(index not in by_seq,"RF071 duplicate original real getset sequence")
        by_seq[index]=x
        if x["kind"] in ("rb","rw"):
            mirror_reads+=1
    joined=[]
    for ordinal,(row,post) in enumerate(zip(pulls,actual),1):
        try:
            before=int(row["before"]);after=int(row["after"])
            value=int(row["returned"],16);frame=int(row["f"])
            width=int(row["width"]);physical=int(row["base"],16)
            seq=int(post["seq"])
        except (ValueError,KeyError) as e:
            raise ValueError("RF071 genuine returned stack value/interval missing") from e
        require(after==before+1 and seq==after+1 and row.get("unique")=="1"
                and post.get("bounded")=="0",
                "RF071 actual original getter interval has zero/multiple bus entries")
        entry=by_seq.get(after)
        require(entry is not None and
                entry.get("phase")=="getset_entry" and
                entry["kind"]==("rb" if row["kind"]=="pullB" else "rw") and
                entry["bank"]=="00" and int(entry["addr"],16)==physical and
                int(entry["width"])==width and int(entry["sampled"],16)==value,
                "RF071 actual original bus read identity/value disagrees with returned stack value")
        require(entry["f"]==row["f"]==post["f"] and
                entry["width"]==post["width"] and
                entry["addr"]==post["base"] and
                entry["kind"] in ("rb","rw"),
                "RF071 original real read operation/frame not bound to actual post-getter return")
        # Snes9x's V counter and H cycles MAY cross a scanline inside
        # the same genuine S9xGetWord call. Never require equal V/H.
        try:
            sample_clock=(int(entry["v"]),int(entry["h"]))
            return_clock=(int(row["v"]),int(row["h"]))
        except (ValueError,KeyError) as e:
            raise ValueError("RF071 original local execution clock missing") from e
        require(sample_clock<=return_clock and
                row["v"]==post["v"] and row["h"]==post["h"],
                "RF071 original local getter return clock regressed")
        joined.append({
            "ordinal":ordinal,
            "source_getset_seq":after,
            "source_post_call_seq":seq,
            "host_frame":frame,
            "bus_kind":entry["kind"],
            "physical_bus_address":"00:"+entry["addr"],
            "returned":f"{value:0{width*2}X}",
            "real_getset_entry_PC_context":entry["pc"],
            "post_call_PC_context":row["pc"],
            "source_getset_scanline":sample_clock[0],
            "source_getset_cycles":sample_clock[1],
            "post_call_scanline":return_clock[0],
            "post_call_cycles":return_clock[1]
        })
    require(len(joined)==mirror_reads and old["actual_returns_with_unique_source_bus_entry"]==len(joined)
            and current["sequenced_source_getset_read_entries"]==len(joined)
            and orig["sequenced_original_bus_entries"]==2*len(joined),
            "RF071 source bus-read event population does not exhaust genuine returned stack pulls")
    # 1+ clock phase difference is allowed; no cross-guest rebase.
    scanlines_crossed=sum((r["source_getset_scanline"]!=r["post_call_scanline"]) for r in joined)
    return {
        "schema":SCHEMA,
        "original_source_log_sha256":hashlib.sha256(raw.encode()).hexdigest(),
        "authenticated_original_source":False,
        "independent_RF044_RF063_real_getset_bus_entries":len(mirrors),
        "executed_source_original_getset_reads":mirror_reads,
        "actual_original_stack_getter_returns":len(joined),
        "read_entries_uniquely_bound_to_real_return":len(joined),
        "sampled_source_bus_value_equals_real_original_post_call_return":True,
        "genuine_getter_calls_crossing_original_V_scanline":scanlines_crossed,
        "actual_source_NMI_postpush_raw_5_bytes":current["real_source_original_post_NMI_raw_5_stack_bytes"],
        "real_original_getter_PC_equals_post_call_PC_in_all_cases":all(
            r["real_getset_entry_PC_context"]==r["post_call_PC_context"] for r in joined),
        "actual_opcode_fetch_PC_at_return_proven":False,
        "original_native_clock_alignment_proven":False,
        "native_stack_first_differing_byte_consumer_proven":False,
        "independent_complete_USA_event_accepted":False,
        "accepted_USA_events":0,
        # The exact individual transaction receipts make misalignments auditable.
        "transactions":joined,
    }

def authenticated_case(path:Path)->dict:
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    require(digest==CASE_SHA256,"RF071 source-authentic case artifact SHA256 mismatch")
    with zipfile.ZipFile(path) as z:
        names=z.namelist()
        require(z.testzip() is None and len(names)==len(set(names)) and len(names)==412,
                "RF071 frozen real source archive missing/corrupt/duplicated members")
        for name in (LOG,"case-result.json","producer-report.json",
                     "qa01-zoo-independent-raw-audit.json",
                     "rf064-original-pulls.json","rf066-original-consumed.json"):
            require(name in names,"RF071 original source control missing: "+name)
        source=z.read(LOG)
        require(hashlib.sha256(source).hexdigest()==ORIGINAL_LOG_SHA256,
                "RF071 actual source original replay log differs from bound producer")
        case=json.loads(z.read("case-result.json"))
        producer=json.loads(z.read("producer-report.json"))
        qa=json.loads(z.read("qa01-zoo-independent-raw-audit.json"))
        prior64=json.loads(z.read("rf064-original-pulls.json"))
        prior66=json.loads(z.read("rf066-original-consumed.json"))
    require(case.get("source_sha")==SOURCE_SHA and case.get("disposition")=="strict_candidate"
            and case.get("release_credit")==0,
            "RF071 source identity / unaccepted USA case changed")
    evidence=case["evidence"]
    require(evidence["core_sha256"]==producer["reference_core_sha256"] and
            evidence["native_sha256"]==producer["native_executable_sha256"] and
            evidence["input_sha256"]==producer["input_sha256"] and
            evidence["movie_sha256"]==producer["original_movie_sha256"] and
            evidence["rom_sha256"]==producer["rom_sha256"],
            "RF071 original/native exact binaries, ROM/movie/input identity mismatch")
    require(evidence["original_event_frames"]==5163 and
            evidence["next_bowl_bounded"]["fresh_original_entry_offset"]==267 and
            evidence["next_bowl_bounded"]["fresh_native_entry_offset"]==267 and
            evidence["next_bowl_bounded"]["release_credit"]==0 and
            producer["zoo_race_mesh"]["mesh_checkpoint_count"]==78 and
            producer["zoo_race_mesh"]["masked_or_excluded_wram_bytes"]==0 and
            qa["full_zoo_mesh_rehashed_original_native_128k_pairs"]==78 and
            qa["full_zoo_mesh_exact_pairs"]==51 and
            qa["full_zoo_mesh_unmasked_differing_byte_occurrences"]==92 and
            qa["independent_usa_event_adjudication"]=="HOLD" and
            qa["accepted_usa_events"]==0,
            "RF071 genuine 78-pair / unmasked WRAM / Zoo/Bowl strict game controls moved")
    result=validate_log(source.decode("utf8"))
    require(prior64["actual_returns_with_unique_source_bus_entry"]==
            result["read_entries_uniquely_bound_to_real_return"] and
            prior66["sequenced_source_getset_read_entries"]==
            result["executed_source_original_getset_reads"] and
            prior66["real_source_original_post_NMI_raw_5_stack_bytes"]==
            result["actual_source_NMI_postpush_raw_5_bytes"],
            "RF071 independent genuine case RF064/RF066 producer qualification differs")
    result["authenticated_original_source"]=True
    result["case_archive_sha256"]=digest
    result["source_sha"]=SOURCE_SHA
    result["original_core_sha256"]=evidence["core_sha256"]
    result["native_executable_sha256"]=evidence["native_sha256"]
    result["rom_sha256"]=producer["rom_sha256"]
    result["movie_sha256"]=producer["original_movie_sha256"]
    result["input_sha256"]=producer["input_sha256"]
    result["full_unmasked_128KiB_original_native_Wram_pairs"]=78
    result["exact_original_native_Wram_pairs"]=51
    result["unmasked_differing_byte_occurrences"]=92
    return result

def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("case_zip",type=Path)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    report=authenticated_case(args.case_zip)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("RF071 genuine original getset-to-postcall source reads bound; original/native first-difference QA still HOLD")

if __name__=="__main__":
    main()
