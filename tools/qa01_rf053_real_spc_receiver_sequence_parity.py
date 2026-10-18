#!/usr/bin/env python3
"""RF053: uniquely align real original/native late SPC700 F6/F7 read sequences.

No new replay: audit the *actual* RF051 original and RF052 native event rows
inside one genuine source-qualified 2014 USA Zoo case ZIP. Never equate source
65816 frame, CPU publication time, or native host frame with source SPC age.
Same-port/byte alone cannot identify a transfer; the true executed SPC PC is
also matched for every ordered read and the entire sequence must be unique.
"""
from __future__ import annotations
import argparse, collections, hashlib, json, zipfile
from pathlib import Path
import qa01_rf050_late_port_publication_report as rf050
import qa01_rf051_late_source_spc_report as rf051

ORIG="work/zoom-zoo/replay/reference.log"
NATIVE="work/zoom-zoo/replay/native.log"
SOURCE_TAG="QA01RF051ORIGSPC "
NATIVE_TAG="QA01RF052NATIVE seq="
FINAL_TAG="QA01RF052NATIVE_FINAL "
CONTROL=("zoo_race_mesh","zoo_next_bowl_handoff","source_terminal_followthrough")
IDENTITY=("rom_sha256","original_movie_sha256","source_sram_sha256","input_sha256")

def fields(line: str) -> dict:
    out={}
    for token in line.split()[1:]:
        if "=" not in token: continue
        k,v=token.split("=",1)
        if not k or k in out:raise ValueError("ambiguous duplicate event field")
        out[k]=v
    return out

def exact_alignment(original: str, native: str, *, expected_count: int|None=None) -> dict:
    if "QA01RF051ORIGSPC_TRUNCATED" in original:
        raise ValueError("original genuine SPC read trace truncated")
    if "QA01RF052NATIVE_TRUNCATED" in native:
        raise ValueError("native genuine SPC queue/receiver trace truncated")
    source=[fields(x) for x in original.splitlines() if x.startswith(SOURCE_TAG)]
    events=[fields(x) for x in native.splitlines() if x.startswith(NATIVE_TAG)]
    finals=[fields(x) for x in native.splitlines() if x.startswith(FINAL_TAG)]
    if len(finals)!=1:raise ValueError("native SPC window missing/ambiguous terminal census")
    f=finals[0]
    if not source or (expected_count is not None and len(source)!=expected_count):
        raise ValueError("original source SPC observation count missing/changed")
    if not events:raise ValueError("native real queue/receiver rows missing")
    if any(k not in f for k in ("printed","clock","overflow","schedules","applies","reads")):
        raise ValueError("native terminal event fields missing")
    if int(f["overflow"]) or int(f["printed"])!=len(events):
        raise ValueError("native complete trace counts overflowed or disagree")
    if int(f["clock"])<=104495000:
        raise ValueError("native late clock window not completed")
    source_records=[]
    for i,row in enumerate(source,1):
        if any(k not in row for k in ("seq","age","spcpc","port","val")):
            raise ValueError("original executed SPC read lacks source identity")
        if int(row["seq"])!=i or row["port"] not in ("2","3"):
            raise ValueError("original executed SPC ordinal/port wrong")
        if len(row["val"])!=2 or any(c not in "0123456789ABCDEF" for c in row["val"]):
            raise ValueError("original executed SPC value malformed")
        source_records.append((row["port"],row["val"],row["spcpc"]))
    native_reads=[]
    kinds=collections.Counter()
    last_native_age=None
    for i,row in enumerate(events,1):
        keys=("seq","kind","global_kind_ord","frame","clock","target","pc","port","val","q")
        if any(k not in row for k in keys):raise ValueError("native executed port event incomplete")
        if int(row["seq"])!=i:raise ValueError("native recorded queue/receiver row order broken")
        kind=row["kind"]
        if kind not in ("schedule","apply","spc-read"):raise ValueError("native event kind unexpected")
        clock=int(row["clock"])
        if last_native_age is not None and clock<last_native_age:
            raise ValueError("native local portClock order reversed")
        last_native_age=clock
        if row["port"] not in ("2","3"):raise ValueError("native event port invalid")
        kinds[kind]+=1
        if kind=="spc-read":native_reads.append(row)
    for k,v in (("schedules","schedule"),("applies","apply"),("reads","spc-read")):
        if int(f[k])<kinds[v]:raise ValueError("native terminal kind counts incomplete")
    needle=tuple(source_records)
    haystack=tuple((r["port"],r["val"],r["pc"]) for r in native_reads)
    starts=[i for i in range(len(haystack)-len(needle)+1)
            if haystack[i:i+len(needle)]==needle]
    if len(starts)!=1:
        raise ValueError("original/native genuine SPC ordered read sequence not uniquely matched")
    pos=starts[0]
    aligned=native_reads[pos:pos+len(source)]
    if any(int(a["age"])<int(b["age"]) for a,b in zip(source[1:],source[:-1])):
        raise ValueError("original source SPC local clock regressed")
    if any(int(a["global_kind_ord"])!=int(b["global_kind_ord"])+1
           for a,b in zip(aligned[1:],aligned[:-1])):
        raise ValueError("matched native real SPC reads not consecutive in executed ordinal")
    diffs=[int(o["age"])-int(n["clock"]) for o,n in zip(source,aligned)]
    hist=collections.Counter(diffs)
    first=aligned[0];last=aligned[-1]
    anchor=[{"original_seq":i+1,"original_age":int(source[i]["age"]),
             "original_pc":source[i]["spcpc"],"native_read_ord":int(aligned[i]["global_kind_ord"]),
             "native_age":int(aligned[i]["clock"]),"value":source[i]["val"],
             "port":int(source[i]["port"]),"source_minus_native_local_ticks":diffs[i]}
            for i in (0,min(6,len(source)-1),min(7,len(source)-1),
                      min(8,len(source)-1),len(source)-1)]
    return {
        "schema":"rf053-unique-true-spc-receiver-sequence-parity-v1",
        "original_real_spc_read_count":len(source),
        "native_window_real_spc_read_count":len(native_reads),
        "native_complete_window_event_count":len(events),
        "native_event_counts_in_window":dict(kinds),
        "unique_full_source_read_sequence_matches_in_native_window":len(starts),
        "native_read_window_zero_based_match_start":pos,
        "native_matched_global_read_ordinals_first_last":[
            int(first["global_kind_ord"]),int(last["global_kind_ord"])],
        "native_matched_host_frame_first_last":[int(first["frame"]),int(last["frame"])],
        "original_SPC_ages_first_last":[int(source[0]["age"]),int(source[-1]["age"])],
        "native_SPC_portClocks_first_last":[int(first["clock"]),int(last["clock"])],
        "all_original_native_SPc_PC_port_value_triples_equal":True,
        "source_minus_native_same_recipient_local_clock_difference_counts":{
             str(k):v for k,v in sorted(hist.items())},
        "same_receiver_read_sequence_but_unregistered_CPU_publication_clocks":True,
        "native_receiver_execution_matches_original_read_sequence":True,
        "no_CPU_APU_timing_change_justified":True,
        "complete_USA_events_accepted":0,
        "selected_source_native_read_anchor_receipts":anchor,
    }

def one_case(case:Path,baseline:Path)->dict:
    with zipfile.ZipFile(case) as z, zipfile.ZipFile(baseline) as old:
        source=z.read(ORIG).decode("utf8","replace")
        native=z.read(NATIVE).decode("utf8","replace")
        producer=json.loads(z.read("producer-report.json"))
        prior=json.loads(old.read("producer-report.json"))
        case_result=json.loads(z.read("case-result.json"))
    for k in CONTROL+IDENTITY:
        if producer[k]!=prior[k]:
            raise ValueError("RF053 original/native full controls or USA provenance changed: "+k)
    if case_result.get("disposition")!="strict_candidate" or case_result.get("release_credit")!=0:
        raise ValueError("RF053 original/native case admission was changed")
    if producer["zoo_race_mesh"]["masked_or_excluded_wram_bytes"]!=0 or (
         producer["zoo_race_mesh"]["mesh_checkpoint_count"]!=78):
        raise ValueError("RF053 full original/native WRAM comparator altered")
    originals=rf051.examine(source)
    if originals["real_original_SPC_F6_F7_read_count"]!=322:
        raise ValueError("RF051 real original SPC receiver count changed")
    if (originals["frozen_original_port3_publication_age"],
        originals["frozen_original_port2_publication_age"])!=(104485254,104485258):
        raise ValueError("RF050 real original publication order changed")
    link=rf050.source_instruction_publication_link(source)
    if not link["both_real_port_publications_inside_original_instruction_segments"]:
        raise ValueError("RF050 original CPU→APU instructions no longer directly linked")
    out=exact_alignment(source,native,expected_count=322)
    out["source_exact_guest_sha"]=case_result["source_sha"]
    out["case_zip_sha256"]=hashlib.sha256(case.read_bytes()).hexdigest()
    out["baseline_zip_sha256"]=hashlib.sha256(baseline.read_bytes()).hexdigest()
    out["all_RF047_Zoo_Bowl_terminal_producer_controls_equal"]=True
    out["USA_source_ROM_movie_input_SRAM_identical_to_RF047"]=True
    out["original_CPU_APU_port_publications_directly_observed"]=True
    return out

def compare_cases(a:Path,b:Path,baseline:Path)->dict:
    first=one_case(a,baseline)
    second=one_case(b,baseline)
    keys=("original_real_spc_read_count","native_window_real_spc_read_count",
          "native_complete_window_event_count","native_event_counts_in_window",
          "unique_full_source_read_sequence_matches_in_native_window",
          "native_read_window_zero_based_match_start",
          "original_SPC_ages_first_last","native_SPC_portClocks_first_last",
          "source_minus_native_same_recipient_local_clock_difference_counts")
    for k in keys:
        if first[k]!=second[k]:
            raise ValueError("RF053 independent frozen native variant changes observed receiver:"+k)
    return {"schema":"rf053-two-authentic-native-source-replay-comparison-v1",
            "case_A":first,"case_B":second,
            "genuine_receiver_signature_and_clock_offset_repeat_in_both":True,
            "different_native_debug_global_counters_not_CPU_clock_parity":True,
            "accepted_USA_events":0}

def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("case",type=Path)
    p.add_argument("--baseline",type=Path,required=True)
    p.add_argument("--compare",type=Path)
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    result=(compare_cases(args.case,args.compare,args.baseline)
            if args.compare else one_case(args.case,args.baseline))
    body=json.dumps(result,indent=2,sort_keys=True)+"\n"
    if args.out:args.out.write_text(body,encoding="utf8")
    else:print(body,end="")
if __name__=="__main__":main()
