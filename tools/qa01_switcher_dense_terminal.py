#!/usr/bin/env python3
"""Exact executed-frame Switcher original/native terminal mesh, not event admission.

Use the established pinned 2014 source and stock calibrated guest inputs.
Do not rebase entry clocks, change controls or mask any memory bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

SCHEMA = "UR-QA01-SWITCHER-FULL-TERMINAL-RAW-MESH/1"
OFFSETS = tuple(range(4658,4702))
SOURCE_MOVIE_SHA = "06dce29e9d36997fc2a1fac4bab72180ab6c8096366cfcf05780c1b2dea4b442"
SOURCE_ROM_SHA = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"


class EvidenceError(ValueError):
    pass


def require(ok: bool, reason: str):
    if not ok:
        raise EvidenceError(reason)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def real_dump(log: str, tag: str) -> int:
    rows=re.findall(r"(?m)^script f=(\d+) dump "+re.escape(tag)+r"(?=\s|$)",log)
    require(len(rows)==1,"real guest host frame missing or ambiguous: "+tag)
    return int(rows[0])


def named(w: bytes) -> dict:
    require(len(w)==131072,"missing whole executed 128KiB guest WRAM")
    return {
        "menu":w[0x9f],"track":w[0xce],
        "in_race":w[0x313],"tour_row":w[0xd0],
    }


def memory_difference(a: bytes,b: bytes) -> dict:
    require(len(a)==len(b),"unmatched full original/native memory sizes")
    offsets=[i for i in range(len(a)) if a[i]!=b[i]]
    return {"total_bytes":len(a),"unmasked_difference_count":len(offsets),
            "unmasked_byte_equal":not offsets,
            "first_differing_offsets":offsets[:24],
            "offsets_truncated":len(offsets)>24}


def intervals(rows: list[dict],side: str) -> list[dict]:
    runs=[];start=None;end=None
    for row in rows:
        v=row["guest"][side]["named"]
        active=(v["menu"]==0x84 and v["track"]==0
                and v["in_race"]==1 and v["tour_row"]==0)
        off=row["offset"]
        if active:
            if start is None:start=off
            end=off
        elif start is not None:
            runs.append({"first_result_relative":start,
                         "last_result_relative":end,"observed_length":end-start+1})
            start=None
    if start is not None:
        runs.append({"first_result_relative":start,
                     "last_result_relative":end,"observed_length":end-start+1})
    return runs


def audit(root: Path) -> dict:
    report_path=root/"switcher-report.json"
    require(report_path.is_file() and not report_path.is_symlink(),
            "missing real original/native Switcher producer report")
    report=json.loads(report_path.read_bytes())
    source=report.get("original_source_event") or {}
    cmp=report.get("comparison") or {}
    require(report.get("course_id")=="course:04" and report.get("name")=="switcher"
            and report.get("rom_sha256")==SOURCE_ROM_SHA
            and report.get("original_movie_sha256")==SOURCE_MOVIE_SHA
            and report.get("native_backend")=="pinned-baldosa"
            and source.get("original_entry_frame")==12327
            and source.get("original_result_frame")==17030
            and source.get("source_active_frames_to_result")==4703
            and report.get("relative_sample_frames") is not None
            and all(o in report["relative_sample_frames"] for o in OFFSETS)
            and cmp.get("both_reached_terminal_menu") is True
            and cmp.get("rendered_result_and_score_text_matched") is True
            and cmp.get("original_source_entry_equivalent") is True
            and cmp.get("fresh_guest_entry_equivalent") is True,
            "real source/original/native Switcher result route not qualified")
    entries={"original":report.get("reference_entry"),"native":report.get("native_entry")}
    clocks=cmp.get("terminal_result_guest_frame") or {}
    require(all(type(v) is int and 0<v<20000 for v in entries.values()),
            "separately calibrated guest entries missing")
    require(all(type(clocks.get(k)) is int and clocks[k]>max(OFFSETS)
                for k in ("reference_relative","native_relative")),
            "independently measured terminal result clock missing")
    replay=root/"switcher"/"replay"
    logs={name:(replay/file).read_text(encoding="utf-8",errors="replace")
          for name,file in (("original","reference.log"),("native","native.log"))}
    require(all(real_dump(logs[side],"result-onset") ==
                entries[side]+clocks["reference_relative" if side=="original"
                                     else "native_relative"]
                for side in ("original","native")),
            "actual original/native terminal result host clocks inconsistent")
    rows=[];hosts={"original":{},"native":{}}
    for offset in OFFSETS:
        guest={}
        for side,folder in (("original","ref"),("native","native")):
            tag=f"scene-{offset:05d}"
            host=real_dump(logs[side],tag)
            require(host==entries[side]+offset,
                    "actual original/native guest dump relative host clock mismatch")
            images={}
            for kind,size in (("wram",131072),("sram",8192)):
                p=replay/folder/f"{tag}.{kind}.bin"
                require(p.is_file() and not p.is_symlink() and p.stat().st_size==size,
                        "missing actual whole executed guest "+kind+" frame "+tag)
                images[kind]=p.read_bytes()
            info={"offset":offset,"host":host,"named":named(images["wram"]),
                  "full_wram_sha256":sha(images["wram"]),
                  "full_sram_sha256":sha(images["sram"])}
            guest[side]=info
            hosts[side][host]=(offset,images,info)
        o=hosts["original"][guest["original"]["host"]][1]
        n=hosts["native"][guest["native"]["host"]][1]
        rows.append({"offset":offset,"guest":guest,
                     "relative_frame_wram":memory_difference(o["wram"],n["wram"]),
                     "relative_frame_sram":memory_difference(o["sram"],n["sram"])})
    same=[]
    for host in sorted(set(hosts["original"]) & set(hosts["native"])):
        ro,wo,no=hosts["original"][host]
        rn,wn,nn=hosts["native"][host]
        same.append({
            "absolute_guest_host_frame":host,
            "original_result_relative_frame":ro,
            "native_result_relative_frame":rn,
            "original_named":no["named"],"native_named":nn["named"],
            "full_wram":memory_difference(wo["wram"],wn["wram"]),
            "full_sram":memory_difference(wo["sram"],wn["sram"]),
        })
    require(len(same)>=30,
            "insufficient actual equal-host original/native Switcher transitions")
    stages={k:intervals(rows,k) for k in ("original","native")}
    require(all(stages.values()),
            "one real guest never observed the authentic course-zero result stage")
    return {
        "schema":SCHEMA,
        "actual_source_original_movie_entry":12327,
        "actual_source_original_movie_result":17030,
        "authentic_source_result_relative":4703,
        "source_ROM_SHA256":SOURCE_ROM_SHA,
        "source_movie_SHA256":SOURCE_MOVIE_SHA,
        "producer_report_sha256":sha(report_path.read_bytes()),
        "original_native_independently_calibrated_entries":entries,
        "original_native_real_result_relative_frames":clocks,
        "original_native_actual_result_host_frames":{
            "original":entries["original"]+clocks["reference_relative"],
            "native":entries["native"]+clocks["native_relative"],
        },
        "captured_result_relative_frames":list(OFFSETS),
        "original_native_stages_observed":stages,
        "same_absolute_guest_host_pairs":same,
        "same_absolute_guest_host_pair_count":len(same),
        "result_relative_original_native_pairs":rows,
        "source_movie_controls_rephased":False,
        "memory_bytes_excluded":0,
        "cpu_spc_first_consumed_writer_proven":False,
        "full_original_native_course_parity_proven":False,
        "windows_shipping_disk_record_proven":False,
        "independent_USA_event_acceptance":0,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--work-root",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    r=audit(a.work_root)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print("Real original/native Switcher stage observed from whole guest bytes; USA 0/45")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
