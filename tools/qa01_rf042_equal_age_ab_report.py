#!/usr/bin/env python3
"""RF042: bounded genuine original/native Zoo equal-age queue-order A/B.

Never admits a course from a local sound handshake. Fails closed on missing
source/original observations, aborted trials, or incomplete WRAM coverage.
"""
import argparse,hashlib,json,zipfile
from pathlib import Path

REF="work/zoom-zoo/replay/reference.log"
NATIVE="work/zoom-zoo/replay/native.log"
def parse(s,prefix):
    return [(i,dict(z.split("=",1) for z in line.split()[1:] if "=" in z))
            for i,line in enumerate(s.splitlines()) if line.startswith(prefix+" ")]

def load(path):
    with zipfile.ZipFile(path) as z:
        return (json.loads(z.read("producer-report.json")),
                json.loads(z.read("case-result.json")),
                z.read(REF).decode("utf8","replace"),
                z.read(NATIVE).decode("utf8","replace"))

def report(baseline:Path,trial:Path):
    a,ac,ao,an=load(baseline)
    b,bc,bo,bn=load(trial)
    am=a["zoo_race_mesh"]; bm=b["zoo_race_mesh"]
    if am["mesh_checkpoint_count"]!=78 or bm["mesh_checkpoint_count"]!=78:
        raise ValueError("RF042 full 78-checkpoint unmasked mesh missing")
    if am["masked_or_excluded_wram_bytes"] or bm["masked_or_excluded_wram_bytes"]:
        raise ValueError("RF042 forbidden WRAM masking")
    if ac["release_credit"] or bc["release_credit"]:
        raise ValueError("RF042 unexpected release credit")
    if len(am["samples"])!=78 or len(bm["samples"])!=78:
        raise ValueError("RF042 incomplete mesh records")
    original_same=all(
        x["race_relative_frame"]==y["race_relative_frame"] and
        x["original_native_full_wram_byte_difference"]["original_wram_sha256"]==
        y["original_native_full_wram_byte_difference"]["original_wram_sha256"]
        for x,y in zip(am["samples"],bm["samples"]))
    if not original_same:
        raise ValueError("RF042 independent original baseline drifted")
    if b["source_sram_sha256"]!=a["source_sram_sha256"]:
        raise ValueError("RF042 source seed SRAM drifted")
    ties=parse(bn,"QA01RF042TIE")
    if "QA01RF042TIE_TRUNCATED" in bn or not ties:
        raise ValueError("RF042 missing/truncated actual native tie trial")
    orig_cpu=parse(bo,"QA01RF040ORIGCPU")
    if [x.get("value") for _,x in orig_cpu]!=["23"]*5+["24"]:
        raise ValueError("RF042 real source CPU poll-return control drifted")
    orig_pub=parse(bo,"QA01RF037ORIGCPU2")
    nat_pub=[(i,x) for i,x in parse(bn,"QA01RF037NATIVEUP")
             if x.get("kind")=="rtl-apu-enter" and x.get("frame")=="6091"]
    src24=[(i,x) for i,x in orig_pub if x.get("age")=="103919450"
           and x.get("port")=="2" and x.get("val")=="24"]
    nat24=[(i,x) for i,x in nat_pub if x.get("reg")=="2142"
           and x.get("val")=="24" and x.get("master")=="2176886834"]
    if len(src24)!=1 or len(nat24)!=1:
        raise ValueError("RF042 missing exact source-native target writer")
    after=[(i,x) for i,x in nat_pub if i>nat24[0][0] and x.get("reg")=="2143" and x.get("val")=="02"]
    if len(after)!=1:
        raise ValueError("RF042 missing/duplicated actual native port3 publication")
    paced=[(i,x) for i,x in parse(bn,"QA01RF038NATIVEPACE")
           if nat24[0][0]<i<after[0][0] and x.get("frame")=="6091"
           and x.get("op")=="read8" and x.get("addr")=="2142"]
    allreturns=parse(bn,"QA01RF040NATIVECPU")
    values=[]
    for j,(idx,x) in enumerate(paced):
        stop=paced[j+1][0] if j+1<len(paced) else after[0][0]
        match=[v for i,v in allreturns if idx<i<stop and v.get("frame")=="6091"
               and v.get("port")=="2"]
        if len(match)!=1 or match[0].get("returned")!=match[0].get("raw"):
            raise ValueError("RF042 missing/different post-SPC native returned byte")
        values.append(match[0]["returned"])
    if not values or len(values)>12 or "24" not in values:
        raise ValueError("RF042 no bounded native echo return progression")
    reads=[x for _,x in parse(bn,"QA01RF037NATIVEBUS")
           if x.get("kind")=="spc-read" and x.get("frame")=="6091"
           and x.get("port")=="2" and x.get("pc")=="154F"
           and 103919420<=int(x["age"])<=103919470]
    if not reads:raise ValueError("RF042 native F6 instruction witness missing")
    info=lambda m:[(s["race_relative_frame"],
                   s["original_native_full_wram_byte_difference"]["differing_byte_count"])
                  for s in m["samples"]]
    changes=[
        {"relative_frame":x["race_relative_frame"],
         "baseline_native":x["original_native_full_wram_byte_difference"]["native_wram_sha256"],
         "trial_native":y["original_native_full_wram_byte_difference"]["native_wram_sha256"],
         "baseline_diff_bytes":x["original_native_full_wram_byte_difference"]["differing_byte_count"],
         "trial_diff_bytes":y["original_native_full_wram_byte_difference"]["differing_byte_count"]}
        for x,y in zip(am["samples"],bm["samples"])
        if x["original_native_full_wram_byte_difference"]["native_wram_sha256"]!=
           y["original_native_full_wram_byte_difference"]["native_wram_sha256"]]
    return {
      "schema":"rf042-qualifying-zoo-equal-age-native-ab-v1",
      "control_case_sha256":hashlib.sha256(baseline.read_bytes()).hexdigest(),
      "trial_case_sha256":hashlib.sha256(trial.read_bytes()).hexdigest(),
      "control_source_sha":ac["source_sha"],"trial_source_sha":bc["source_sha"],
      "trial_case_disposition":bc["disposition"],
      "original_all_78_sha256_snapshots_equal":original_same,
      "native_tie_markers":ties[:16],
      "native_actual_target_writer_master":2176886834,
      "native_actual_port3_writer_master":int(after[0][1]["master"]),
      "native_paced_return_values":values,
      "native_target_f6_reads":reads,
      "original_cpu_return_values":[x["value"] for _,x in orig_cpu],
      "control_full_wram_exact_pairs":am["raw_byte_exact_sample_count"],
      "trial_full_wram_exact_pairs":bm["raw_byte_exact_sample_count"],
      "control_unmasked_different_byte_occurrences":sum(v for _,v in info(am)),
      "trial_unmasked_different_byte_occurrences":sum(v for _,v in info(bm)),
      "native_changed_frame_details":changes,
      "next_bowl_handoff_unchanged":a["zoo_next_bowl_handoff"]==b["zoo_next_bowl_handoff"],
      "terminal_followthrough_unchanged":a["source_terminal_followthrough"]==
                                         b["source_terminal_followthrough"],
      "full_13_sample_sound_dp_equal":am["late_direct_page_window"]==
                                      bm["late_direct_page_window"],
      "local_echo_fix_alone_never_admits_usa_event":True,
      "source_qualified_windows_timing_fix_authorized":False,
      "complete_usa_events_accepted":0,
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("baseline",type=Path)
    p.add_argument("trial",type=Path)
    p.add_argument("--json-out",type=Path)
    a=p.parse_args()
    payload=json.dumps(report(a.baseline,a.trial),indent=2,sort_keys=True)+"\n"
    if a.json_out:
        a.json_out.parent.mkdir(parents=True,exist_ok=True)
        a.json_out.write_text(payload,encoding="utf8")
    else:print(payload,end="")
if __name__=="__main__":main()
