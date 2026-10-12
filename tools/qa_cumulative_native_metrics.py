#!/usr/bin/env python3
"""Bounded cumulative native frame consistency and long-process resource evidence.

Production executable, real two-pad controller stream, real guest WRAM/frame dumps.
Graphics: bit-identical product pixels/WRAM for SAME seeded input across fresh runs.
Performance: prolonged one-PID gameplay progression, sampled Linux resident memory,
file descriptors and CPU time. Neither proves original SNES parity/physical output.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import qa02_native_2p_seeded_endurance as native
from controller_input import load_controller_runs
from check_framedump_identity import compare_dirs

SCHEMA={"graphics":"ur-cumulative-graphics/1",
        "performance":"ur-cumulative-performance/1"}
MODES=tuple(SCHEMA)
HEX40=re.compile(r"[0-9a-f]{40}\Z")
FRAME_START,FRAME_END=1620,2400
PERF_SAMPLES=8
RSS_MAX_KIB=2*1024*1024


def sha(path:Path)->str:
    d=hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda:stream.read(1<<20),b""):
            d.update(block)
    return d.hexdigest()


def save(path:Path,value:dict)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,sort_keys=True,indent=2)+"\n",encoding="utf8")


def extended_case(seed:int,mode:str,root:Path)->tuple[Path,Path,dict]:
    source_input,source_script=native.base_source()
    actions,diversity=native.input_plan(seed)
    if mode=="performance":
        rng=random.Random(seed+113)
        # Exercise different left/right/airborne movements across a long
        # continuously alive real guest process, not N repeated restarts.
        for start in range(3520,43400,139):
            p1=rng.choice((0,0x080,0x040,0x100,0x180,0x140))
            p2=rng.choice((0,0x080,0x040,0x100,0x180,0x140))
            if p1 or p2:
                actions.append((start,rng.randint(12,95),p1,p2))
    input_file=root/"controls.input"
    input_file.write_text(native.render_input(source_input,actions,None),encoding="utf8")
    load_controller_runs(input_file)  # exact source-owned dual-pad grammar
    script=native.render_script(source_script)
    if mode=="performance":
        if not script.endswith("quit\n"):
            raise ValueError("source-authenticated script terminal not found")
        script=script[:-len("quit\n")]
        for i in range(PERF_SAMPLES):
            script+=f"wait 5000\ndump perf-long-{i:02d}\n"
        script+="quit\n"
    script_file=root/"route.script"
    script_file.write_text(script,encoding="utf8")
    return input_file,script_file,diversity


def sample_linux(pid:int)->dict:
    status=Path(f"/proc/{pid}/status").read_text(encoding="ascii")
    fields={}
    for name in ("VmRSS","VmHWM","VmSize"):
        match=re.search(r"^"+name+r":\s+(\d+)\s+kB$",status,re.M)
        if match:
            fields[name+"_kib"]=int(match.group(1))
    fields["file_descriptors"]=len(list(Path(f"/proc/{pid}/fd").iterdir()))
    return fields


def run_native(exe:Path,rom:Path,input_file:Path,script:Path,
               root:Path,mode:str,timeout:int)->dict:
    root.mkdir()
    (root/"data").mkdir()
    (root/"dumps").mkdir()
    (root/"frames").mkdir()
    config=root/"fast-authentic.ini"
    config.write_text("[General]\nDisableFrameDelay = 1\nSkipLauncher = 1\nAutosave = 0\n"
                      "[Sound]\nEnableAudio = 0\n",encoding="ascii")
    state=root/"host-state.txt"
    state.write_text("UR-HOST-STATE/6\nprofile=\n"
                     "pause_on_focus_loss=1\nvibration_enabled=1\n"
                     "widescreen=original\n",encoding="ascii")
    env=dict(os.environ)
    env.update({
        "SDL_AUDIODRIVER":"dummy","SDL_VIDEODRIVER":"x11",
        "DISPLAY":":97","UR_EXECUTION_MODE":"authentic",
        "UR_RECOMP_USER_DATA_ROOT":str(root/"data"),
        "SNESRECOMP_USER_DATA_DIR":str(root/"data"),
        "SNESRECOMP_DUMP_DIR":str(root/"dumps"),
        "SNESRECOMP_INPUT_FILE":str(input_file),
        "UR_HOST_STATE_PATH":str(state),
    })
    if mode=="graphics":
        env.update({
            "SNESRECOMP_FRAMEDUMP_PIXELS":"1",
            "SNESRECOMP_FRAMEDUMP_START":str(FRAME_START),
            "SNESRECOMP_FRAMEDUMP_END":str(FRAME_END),
        })
    server=subprocess.Popen(["Xvfb",":97","-screen","0","1280x800x24","-nolisten","tcp"],
                            cwd=root,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    process=None
    try:
        # Waiting for Xvfb socket is prerequisite initialization, not test padding.
        display=Path("/tmp/.X11-unix/X97")
        for _ in range(50):
            if display.is_socket():
                break
            if server.poll() is not None:
                raise RuntimeError("headless display exited before game launch")
            time.sleep(0.1)
        if not display.is_socket():
            raise RuntimeError("headless native display startup timed out")
        cmd=[str(exe),str(rom),"--config",str(config),"--script",str(script)]
        if mode=="graphics":
            cmd+=["--framedump",str(root/"frames")]
        with (root/"native.log").open("wb") as output:
            process=subprocess.Popen(cmd,cwd=root,env=env,stdout=output,
                                     stderr=subprocess.STDOUT)
            start=time.monotonic()
            observations=[]
            while process.poll() is None:
                if time.monotonic()-start>timeout:
                    process.kill()
                    raise RuntimeError(f"uninterrupted native game exceeded {timeout}s watchdog")
                try:
                    observations.append(sample_linux(process.pid))
                except (OSError,ProcessLookupError):
                    if process.poll() is None:
                        raise
                time.sleep(0.25)
            elapsed=round(time.monotonic()-start,3)
            if process.returncode != 0:
                tail=(root/"native.log").read_text(errors="replace")[-900:]
                raise RuntimeError(f"real guest process exit={process.returncode}; {tail}")
        checkpoints=("two-player-both-post-1620","endurance-1740","endurance-3420")
        if mode=="performance":
            checkpoints=(*checkpoints,*[f"perf-long-{i:02d}" for i in range(PERF_SAMPLES)])
        for label in checkpoints:
            p=root/"dumps"/(label+".wram.bin")
            if not p.is_file() or p.stat().st_size!=131072:
                raise ValueError(f"native missing exact 128KiB game-state checkpoint {label}")
        original=(root/"dumps"/(checkpoints[0]+".wram.bin")).read_bytes()
        if original[0x0313]!=1:
            raise ValueError("no authentic source-entered active two-player race")
        if len(observations)<2:
            raise ValueError("insufficient distinct real process resource observations")
        rss=[v["VmRSS_kib"] for v in observations if "VmRSS_kib" in v]
        if len(rss)<2 or max(rss)>RSS_MAX_KIB:
            raise ValueError("missing resource samples or excessive native RSS memory")
        fds=[v["file_descriptors"] for v in observations]
        return {
            "duration_seconds":elapsed,
            "peak_rss_kib":max(rss),
            "rss_first_kib":rss[0],"rss_last_kib":rss[-1],
            "peak_open_fds":max(fds),"observed_resource_samples":len(observations),
            "checkpoint_sha256":{label:sha(root/"dumps"/(label+".wram.bin"))
                                 for label in checkpoints},
            "frames":str(root/"frames"),"dumps":str(root/"dumps"),
            "identity":sha(exe),
        }
    finally:
        if process is not None and process.poll() is None:
            process.kill()
            process.wait(timeout=10)
        server.terminate()
        try:
            server.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
            server.communicate(timeout=10)


def trial(exe:Path,rom:Path,root:Path,mode:str,seed:int,timeout:int)->dict:
    root.mkdir()
    input_file,script,diversity=extended_case(seed,mode,root)
    first=run_native(exe,rom,input_file,script,root/"first",mode,timeout)
    result={
        "seed":seed,"controller_sha256":sha(input_file),"script_sha256":sha(script),
        "first_process_seconds":first["duration_seconds"],
        "first_peak_rss_kib":first["peak_rss_kib"],
        "first_rss_delta_kib":first["rss_last_kib"]-first["rss_first_kib"],
        "first_peak_open_fds":first["peak_open_fds"],
        "observed_resource_samples":first["observed_resource_samples"],
        "real_native_processes":1,
        "verified_guest_checkpoints":len(first["checkpoint_sha256"]),
        **diversity,
    }
    if mode=="graphics":
        second=run_native(exe,rom,input_file,script,root/"replay",mode,timeout)
        frame=compare_dirs(Path(first["frames"]),Path(second["frames"]))
        dump=compare_dirs(Path(first["dumps"]),Path(second["dumps"]))
        if (frame["frames_compared"]<300 or frame["differing_files"]!=0
                or frame["only_in_baseline"] or frame["only_in_candidate"]
                or dump["differing_files"]!=0 or dump["only_in_baseline"]
                or dump["only_in_candidate"]):
            raise ValueError(f"real frame/WRAM replay differs: frames={frame}, dumps={dump}")
        result.update(real_native_processes=2,
                      measured_frame_checks=frame["frames_compared"],
                      compared_frame_files=frame["files_compared"],
                      replay_bit_identical=True,
                      total_process_seconds=first["duration_seconds"]+second["duration_seconds"])
    else:
        result["total_process_seconds"]=first["duration_seconds"]
        result["reached_long_horizon"]=("perf-long-07" in first["checkpoint_sha256"])
    return result


def campaign(*,exe:Path,rom:Path,source_sha:str,mode:str,
             minutes:int,seed:int,root:Path,max_cases:int=500)->dict:
    if (mode not in MODES or minutes not in (15,60,120) or
        not HEX40.fullmatch(source_sha) or type(seed) is not int or
        not 0<=seed<=99999999 or not 1<=max_cases<=500):
        raise ValueError("unbounded or source-unqualified native study request")
    if root.exists() or not exe.is_file() or not rom.is_file():
        raise ValueError("missing exact native executable/ROM or reused process root")
    if sha(rom)!=native.ROM_SHA:
        raise ValueError("noncanonical USA retail ROM")
    root.mkdir(parents=True)
    started=time.monotonic()
    deadline=started+60*minutes
    rows=[]
    failures=[]
    attempted=0
    while attempted<max_cases and (not attempted or time.monotonic()<deadline):
        i=attempted
        attempted+=1
        trial_root=root/f"case-{i:05d}"
        try:
            row=trial(exe,rom,trial_root,mode,seed+i,850)
            rows.append(row)
            shutil.rmtree(trial_root)
        except Exception as exc:
            failures.append({"index":i,"seed":seed+i,"class":type(exc).__name__,
                             "reason":str(exc)[-700:]})
            break
    status="completed_positive" if not failures and rows else "invariant_violation"
    result={
        "schema":SCHEMA[mode],"source_sha":source_sha,"mode":mode,
        "native_executable_sha256":sha(exe),"rom_sha256":native.ROM_SHA,
        "base_seed":seed,"minutes_budget":minutes,"max_cases":max_cases,
        "attempted_cases":attempted,"failed_cases":failures,
        "completed_processes":sum(row["real_native_processes"] for row in rows),
        "sampled_process_seconds":int(sum(row["total_process_seconds"] for row in rows)),
        "unique_seeded_frame_sweeps":len(rows) if mode=="graphics" else 0,
        "measured_frame_checks":sum(row.get("measured_frame_checks",0) for row in rows),
        "observed_cases":rows,"elapsed_seconds":round(time.monotonic()-started,3),
        "stop_reason":"invariant_failure" if failures else
                     ("case_cap" if attempted>=max_cases else "wall_budget"),
        "disposition":status,"issues":[f["reason"] for f in failures],
        "release_gate_credit":0,
        "original_native_event_parity":False,
        "physical_4k_tested":False,
        "windows_build_tested":False,
        "scope":"Source-qualified authentic native real-process /proc and frame replay research; not original guest equality or physical release certification",
    }
    result["receipt_sha256"]=hashlib.sha256(json.dumps(
        result,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return result


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--exe",type=Path,required=True)
    p.add_argument("--rom",type=Path,required=True)
    p.add_argument("--source-sha",required=True)
    p.add_argument("--mode",choices=MODES,required=True)
    p.add_argument("--minutes",type=int,required=True)
    p.add_argument("--seed",type=int,required=True)
    p.add_argument("--work",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    result=campaign(exe=args.exe.resolve(),rom=args.rom.resolve(),
                    source_sha=args.source_sha,mode=args.mode,
                    minutes=args.minutes,seed=args.seed,root=args.work)
    save(args.out,result)
    print(f"NATIVE_{args.mode.upper()} {result['disposition']} "
          f"seeds={len(result['observed_cases'])} "
          f"real_processes={result['completed_processes']} "
          f"seconds={result['sampled_process_seconds']} "
          f"actual_wall={result['elapsed_seconds']}")
    return 0 if result["disposition"]=="completed_positive" else 1


if __name__=="__main__":
    raise SystemExit(main())
