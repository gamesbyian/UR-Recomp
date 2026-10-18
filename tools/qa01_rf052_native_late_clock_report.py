#!/usr/bin/env python3
"""RF052: exact native later clock-window APU event census, original-source blind.

Source SPC age and native portClock remain separate clocks. Same bytes or
similar clock numbers do not establish corresponding execution transactions.
The original source SPC F6/F7 receipt and full Zoo/Bowl/SRAM controls are
inherited from independently executed RF051/RF050/RF047 source observers.
"""
from __future__ import annotations
import argparse,hashlib,json,zipfile
from pathlib import Path
import qa01_rf051_late_source_spc_report as rf051
import qa01_rf050_late_port_publication_report as rf050

TAG="QA01RF052NATIVE "
FINAL="QA01RF052NATIVE_FINAL "
SOURCE="work/zoom-zoo/replay/reference.log"
NATIVE="work/zoom-zoo/replay/native.log"
def fields(line:str)->dict:
    result={}
    for token in line.split()[1:]:
        if "=" in token:
            k,v=token.split("=",1)
            if not k or k in result:
                raise ValueError("ambiguous native RF052 field")
            result[k]=v
    return result

def analyze_native(native:str)->dict:
    if "QA01RF052NATIVE_TRUNCATED" in native:
        raise ValueError("RF052 native late window truncated")
    lines=native.splitlines()
    fs=[fields(x) for x in lines if x.startswith(FINAL)]
    if len(fs)!=1:raise ValueError("RF052 requires one genuine after-window native terminal summary")
    final=fs[0]
    if any(k not in final for k in ("clock","printed","overflow","schedules","applies","reads")):
        raise ValueError("RF052 incomplete after-window native summary")
    if int(final["clock"])<=104495000:
        raise ValueError("RF052 native did not reach beyond target local clock")
    if int(final["overflow"])!=0:
        raise ValueError("RF052 native incomplete/truncated late events")
    rows=[fields(x) for x in lines if x.startswith(TAG)]
    if len(rows)!=int(final["printed"]):
        raise ValueError("RF052 missing native clock-window event rows")
    per_kind_last={}
    out=[]
    for i,row in enumerate(rows,1):
        keys=("seq","kind","global_kind_ord","frame","clock","target","pc","port","val","q")
        if any(k not in row for k in keys):
            raise ValueError("RF052 incomplete native event source identity")
        if int(row["seq"])!=i:
            raise ValueError("RF052 missing or duplicate native event order")
        if row["kind"] not in ("schedule","apply","spc-read"):
            raise ValueError("RF052 unknown real native queue/receiver kind")
        if not 6110<=int(row["frame"])<=6140 or not 104478000<=int(row["clock"])<=104495000:
            raise ValueError("RF052 native event outside originally declared host/clock window")
        if row["port"] not in ("2","3") or len(row["val"])!=2 or any(c not in "0123456789ABCDEF" for c in row["val"]):
            raise ValueError("RF052 invalid native port/value")
        k=row["kind"]
        ordinal=int(row["global_kind_ord"])
        if ordinal<=per_kind_last.get(k,0):
            raise ValueError("RF052 native cumulative per-kind event ordinal regressed")
        per_kind_last[k]=ordinal
        out.append(row)
    if any(int(b["clock"])<int(a["clock"]) for a,b in zip(out,out[1:])):
        raise ValueError("RF052 native local clock sequence regressed")
    summary={"schedule":"schedules","apply":"applies","spc-read":"reads"}
    for k,field in summary.items():
        if int(final[field])<per_kind_last.get(k,0):
            raise ValueError("RF052 final global kind counts shorter than witnessed native rows")
    schedules=[x for x in out if x["kind"]=="schedule"]
    candidates=[]
    for first,second in zip(schedules,schedules[1:]):
        if (first["port"],first["val"],second["port"],second["val"])!=("3","D0","2","63"):
            continue
        candidates.append({
            "native_schedule_global_kind_ordinals":[int(first["global_kind_ord"]),int(second["global_kind_ord"])],
            "native_port_clocks":[int(first["clock"]),int(second["clock"])],
            "native_host_frames":[int(first["frame"]),int(second["frame"])],
            "native_local_clock_separation":int(second["clock"])-int(first["clock"]),
            "native_apu_schedule_is_actual_writer_path":True,
            "source_original_late_transaction_identity_proven":False,
            "source_original_to_native_time_alignment_proven":False,
            "native_following_events":[
                x for x in out
                if int(x["clock"])>=int(second["clock"]) and x["kind"] in ("apply","spc-read")
            ][:12]
        })
    return {
        "schema":"rf052-native-late-sound-queue-and-receiver-v1",
        "native_portClock_window":[104478000,104495000],
        "native_host_frame_guard":[6110,6140],
        "native_window_events":len(out),
        "native_window_first_last_clocks":[int(out[0]["clock"]),int(out[-1]["clock"])] if out else None,
        "native_events_by_kind":{k:sum(x["kind"]==k for x in out) for k in summary},
        "native_cumulative_real_events_by_kind":{k:int(final[field]) for k,field in summary.items()},
        "native_D0_63_scheduled_candidate_pairs":candidates[:256],
        "native_D0_63_candidate_count":len(candidates),
        "native_observation_complete_through_window":True,
        "native_schedule_pairs_not_proven_to_match_source_original":True,
        "clock_epoch_correspondence_proven":False,
        "unmasked_source_vs_native_event_parity_proven":False,
        "complete_USA_events_accepted":0,
    }

def report(case:Path,baseline:Path)->dict:
    with zipfile.ZipFile(case) as z:
        orig=z.read(SOURCE).decode("utf8","replace")
        native=z.read(NATIVE).decode("utf8","replace")
    result=analyze_native(native)
    source=rf051.examine(orig)
    if source["real_original_SPC_F6_F7_read_count"]<3:
        raise ValueError("RF052 source RF051 genuine receiver insufficient")
    samples=source["true_source_SPC_observations"]
    late=[x for x in samples if x["source_SPC_age"]>104485258]
    if [(x["source_SPC_age"],x["port"],x["value"]) for x in late[:3]]!=[
        (104485261,2,"63"),(104485266,3,"D0"),(104485269,2,"63")]:
        raise ValueError("RF052 genuine original post-publication receiver sequence changed")
    old=rf050.report(case,baseline)
    if not old["all_RF047_original_native_unmasked_Zoo_Bowl_SRAM_controls_unchanged"]:
        raise ValueError("RF052 old original/native full Zoo/Bowl/SRAM control drift")
    result["genuine_original_SPC_F6_F7_count"]=source["real_original_SPC_F6_F7_read_count"]
    result["original_true_after_APU_publication_first_three"]=late[:3]
    result["full_RF047_Zoo_Bowl_SRAM_controls_unchanged"]=True
    result["frozen_case_source_sha"]=old["frozen_research_source_sha"]
    result["case_zip_sha256"]=hashlib.sha256(case.read_bytes()).hexdigest()
    result["baseline_zip_sha256"]=hashlib.sha256(baseline.read_bytes()).hexdigest()
    return result
def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("case",type=Path)
    p.add_argument("--baseline",type=Path,required=True)
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    value=json.dumps(report(a.case,a.baseline),indent=2,sort_keys=True)+"\n"
    if a.output:a.output.write_text(value,encoding="utf8")
    else:print(value,end="")
if __name__=="__main__":main()
