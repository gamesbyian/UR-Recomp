#!/usr/bin/env python3
"""One-shot source-only 2014 USA movie discovery after the verified Switcher result.

Never extrapolate an active race from a course selection. Never submit a
native guest, alter controller timing, or award course acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SMV_SHA = "06dce29e9d36997fc2a1fac4bab72180ab6c8096366cfcf05780c1b2dea4b442"
ROM_SHA = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
BASELINE = ((794,0,1),(3190,1,1),(8620,2,1),(12327,3,1))
RESULTS = ((2874,0,0x99),(8353,1,0xBC),(11985,2,0x18),(17030,3,0x99))
SOURCE_RESULT = 17030
ORIGINAL_HORIZON = 22000
HORIZON = 36000
FIELDS = {"menu":0x009f,"track":0x00ce,"in_race":0x0313,"tour_row":0x00d0}
TAG = {f'"adr":"0x{addr:05x}"'.encode(): k for k,addr in FIELDS.items()}
SCHEMA = "UR-QA01-2014-POST-SWITCHER-SOURCE-CONTINUATION/1"


class SourceDiscoveryError(ValueError):
    pass


def sha(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()


def frame_states(lines, horizon: int) -> list[dict]:
    """Stream only four source-written bytes, reconstruct exact held frame states.

    Records are genuine Snes9x after-frame writes. State for a frame is the
    last actual write in that frame; an empty frame holds its earlier value.
    """
    if type(horizon) is not int or not ORIGINAL_HORIZON < horizon <= 42000:
        raise SourceDiscoveryError("out-of-contract bounded source horizon")
    current={k:0 for k in FIELDS}
    out=[]
    last=0
    observed=0
    for line in lines:
        name=next((key for marker,key in TAG.items() if marker in line),None)
        if name is None:
            continue
        row=json.loads(line)
        frame=row.get("f")
        if type(frame) is not int or not last <= frame <= horizon:
            raise SourceDiscoveryError("nonmonotonic/out-of-window observed source frame")
        if int(row["adr"],16)!=FIELDS[name]:
            raise SourceDiscoveryError("source trace address mismatch")
        if frame>last:
            out.extend(current.copy() for _ in range(frame-last))
            last=frame
        value=int(row["val"],16)
        if not 0<=value<=255:
            raise SourceDiscoveryError("invalid source WRAM write")
        current[name]=value
        observed+=1
    if not observed:
        raise SourceDiscoveryError("no source WRAM trace writes")
    out.extend(current.copy() for _ in range(horizon+1-last))
    if len(out)!=horizon+1:
        raise SourceDiscoveryError("missing timeline frames")
    return out


def sustained_runs(states: list[dict]) -> list[dict]:
    """>=8 frame real active course with a fixed track and tour."""
    out=[]
    start=None
    active=None
    for frame,row in enumerate(states):
        key=(row["tour_row"],row["track"]) if row["in_race"]==1 and row["track"]<45 else None
        if key!=active:
            if active is not None and frame-start>=8:
                out.append({"start":start,"last_active":frame-1,
                            "duration":frame-start,"tour_row":active[0],
                            "track":active[1]})
            start=frame
            active=key
    if active is not None and len(states)-start>=8:
        out.append({"start":start,"last_active":len(states)-1,
                    "duration":len(states)-start,"tour_row":active[0],
                    "track":active[1]})
    return out


def assess(states: list[dict]) -> dict:
    if len(states)<HORIZON+1:
        raise SourceDiscoveryError("source timeline did not reach 36000")
    for frame,track,race in BASELINE:
        if states[frame]["track"]!=track or states[frame]["in_race"]!=race:
            raise SourceDiscoveryError(f"lost authenticated 2014 source entry {frame}")
    for frame,track,menu in RESULTS:
        row=states[frame]
        if (row["menu"],row["track"])!=(menu,track) or row["in_race"]==1:
            raise SourceDiscoveryError(f"lost independently authenticated result {frame}")
    runs=sustained_runs(states)
    candidates=[run.copy() for run in runs
                if run["start"]>SOURCE_RESULT and run["start"]<=HORIZON-8]
    # The game can use the track byte as scratch. A result must be tied to
    # the same active course and >=8 stable inactive frames afterward.
    for run in candidates:
        result=None
        for f in range(run["last_active"]+1,min(HORIZON-7,run["last_active"]+12000)+1):
            row=states[f]
            if (row["track"]==run["track"] and row["tour_row"]==run["tour_row"]
                    and row["menu"] in (0x99,0xBC,0x18,0x2f)
                    and row["in_race"]!=1
                    and all(states[f+j]["menu"]==row["menu"]
                            and states[f+j]["in_race"]!=1
                            and states[f+j]["track"]==row["track"]
                            for j in range(8))):
                result={"host_frame":f,"result_menu":row["menu"]}
                break
        run["separately_observed_terminal_result"]=result
        run["complete_source_entry_and_terminal_candidate"]=result is not None
    window=states[ORIGINAL_HORIZON:HORIZON+1]
    change_points=[]
    previous=None
    for n,s in enumerate(window):
        tup=(s["menu"],s["track"],s["in_race"],s["tour_row"])
        if tup!=previous:
            if len(change_points)<150:
                change_points.append({"source_frame":ORIGINAL_HORIZON+n,
                                      "menu":tup[0],"track":tup[1],
                                      "in_race":tup[2],"tour_row":tup[3]})
            previous=tup
    return {
        "schema":SCHEMA,
        "source_baseline_four_entries_and_results_unchanged":True,
        "source_original_switcher_result":SOURCE_RESULT,
        "old_2014_original_source_horizon":ORIGINAL_HORIZON,
        "new_horizon":HORIZON,
        "genuine_original_source_sustained_active_runs_after_switcher":candidates,
        "completed_post_switcher_source_attempts":sum(
            x["complete_source_entry_and_terminal_candidate"] for x in candidates),
        "completed_repeat_of_previously_sourced_course":sum(
            x["complete_source_entry_and_terminal_candidate"] and
            x["track"] in (0,1,2,3) for x in candidates),
        "completed_new_unique_source_course_candidates":sum(
            x["complete_source_entry_and_terminal_candidate"] and
            x["track"] not in (0,1,2,3) for x in candidates),
        "new_event_status":(
            "new_unique_course_source_candidate_requires_event_specific_proof"
            if any(x["complete_source_entry_and_terminal_candidate"] and
                   x["track"] not in (0,1,2,3) for x in candidates)
            else "post_switcher_repeats_previously_sourced_course"
            if any(x["complete_source_entry_and_terminal_candidate"] for x in candidates)
            else "no_complete_post_switcher_source_attempt_through_horizon"),
        "post22000_state_change_prefix":change_points,
        "post22000_state_change_prefix_is_truncated":sum(
            1 for i in range(1,len(window))
            if window[i]!=window[i-1])>150,
        "source_controller_masks_modified":False,
        "fresh_original_or_native_event_proven":False,
        "USA_accepted_event_credit":0,
    }


def actual_host_frame(log: str,label: str) -> int:
    m=re.findall(r"script f=(\d+) dump "+re.escape(label)+r"(?=\s|$)",log)
    if len(m)!=1:
        raise SourceDiscoveryError("no unique executed original host frame "+label)
    return int(m[0])


def execute(args) -> dict:
    args.work.mkdir(parents=True,exist_ok=False)
    if sha(args.movie)!=SMV_SHA or sha(args.rom)!=ROM_SHA:
        raise SourceDiscoveryError("USA original movie or ROM SHA identity mismatch")
    inputfile,sram=args.work/"2014.input",args.work/"2014.sram"
    meta=args.work/"movie-meta.json"
    subprocess.run([sys.executable,str(ROOT/"tools/extract_smv_input.py"),
                    str(args.movie),"--input-out",str(inputfile),"--sram-out",str(sram),
                    "--sram-size","8192","--json-out",str(meta)],check=True)
    m=json.loads(meta.read_text())
    if (m.get("sample_count")!=8767529 or m.get("pal") is not False
        or m.get("reset_anchored") is not True or m.get("emitted_sram_size")!=8192):
        raise SourceDiscoveryError("source original 2014 movie metadata changed")
    script=args.work/"source.script"
    script.write_text("wait 17030\ndump original-switcher-result\n"
                      "wait 4970\ndump prior-horizon\n"
                      "wait 14000\ndump new-horizon\nquit\n")
    logpath=args.work/"source.log"
    trace=args.work/"source-trace.jsonl"
    env=dict(os.environ,SNESREF_HEADLESS="1",SNESREF_FAST="1",SNESREF_WRAM_FILL="0",
             SNESREF_SRAM_IN=str(sram),SNESREF_SCRIPT=str(script),
             SNESREF_INPUT_FILE=str(inputfile),SNESREF_TRACE_FILE=str(trace),
             SNESREF_DUMP_DIR=str(args.work))
    p=subprocess.run([str(args.snesref),str(args.core),str(args.rom)],
                     env=env,cwd=args.work,capture_output=True,text=True,timeout=900)
    logpath.write_text(p.stdout+p.stderr)
    if p.returncode:
        raise SourceDiscoveryError("authentic source Snes9x failed: "+(p.stdout+p.stderr)[-1100:])
    log=logpath.read_text()
    for label,frame in (("original-switcher-result",17030),
                        ("prior-horizon",22000),("new-horizon",HORIZON)):
        if actual_host_frame(log,label)!=frame:
            raise SourceDiscoveryError("source movie clock not attested at "+label)
        raw=args.work/(label+".wram.bin")
        if not raw.is_file() or raw.stat().st_size!=131072:
            raise SourceDiscoveryError("source WRAM unavailable at "+label)
    with trace.open("rb") as f:
        states=frame_states(f,HORIZON)
    result=assess(states)
    result.update({
        "original_movie_sha256":SMV_SHA,"usa_rom_sha256":ROM_SHA,
        "original_input_file_sha256":sha(inputfile),
        "original_2014_sram_sha256":sha(sram),
        "snesref_executable_sha256":sha(args.snesref),
        "reference_core_sha256":sha(args.core),
        "source_raw_trace_sha256":sha(trace),
        "source_executed_log_sha256":sha(logpath),
        "independently_observed_host_clocks":[17030,22000,HORIZON],
        "source_trace_bytes":trace.stat().st_size,
    })
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--snesref",type=Path,required=True)
    p.add_argument("--core",type=Path,required=True)
    p.add_argument("--rom",type=Path,required=True)
    p.add_argument("--movie",type=Path,required=True)
    p.add_argument("--work",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    args.work=args.work.resolve()
    try:
        result=execute(args)
    except (OSError,ValueError,subprocess.SubprocessError,SourceDiscoveryError) as exc:
        p.exit(2,"QA01_SOURCE_CONTINUATION_INVALID: "+str(exc)+"\n")
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in result.items()
                      if k not in ("post22000_state_change_prefix",)},sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
