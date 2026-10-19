#!/usr/bin/env python3
"""Independent read-only audit of the actual 2014 original source 36000 ZIP.

Every source trace write targets low 8KiB WRAM. It cannot reconstruct the
other 120KiB, other guest clocks, or 45-course acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from zipfile import ZipFile

SCHEMA = "UR-QA01-POST-SWITCHER-ORIGINAL-LOW8K-RAW-AUDIT/1"
PRODUCER_SCHEMA = "UR-QA01-2014-POST-SWITCHER-SOURCE-CONTINUATION/1"
ROM_SHA = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
MOVIE_SHA = "06dce29e9d36997fc2a1fac4bab72180ab6c8096366cfcf05780c1b2dea4b442"
TARGETS = tuple(sorted(set((
    794,2874,3190,8353,8620,11985,12327,17030,22000,
    22940,22941,22942,22943,22944,22945,22946,22947,22948,
    25335,25336,25337,25338,25339,25340,25341,25342,25343,
    25344,25345,25346,25347,25348,25349,25350,25351,
    25730,25731,36000)) | set(range(12326,12335))
    | set(range(16990,17038)) | {17087,17088}))
DUMPS = ((17030,"original-switcher-result"),(22000,"prior-horizon"),
         (36000,"new-horizon"))
BASELINE = ((794,0,1),(3190,1,1),(8620,2,1),(12327,3,1))
RESULTS = ((2874,0,153),(8353,1,188),(11985,2,24),(17030,3,153))
NAMES = ("menu","track","in_race","tour_row")
ADDRESSES = (0x9F,0xCE,0x313,0xD0)


class ArchiveError(ValueError):
    pass


def must(ok: bool, reason: str) -> None:
    if not ok:
        raise ArchiveError(reason)


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def read_exact(z: ZipFile, name: str, n: int | None = None) -> bytes:
    must(name in z.namelist(), "missing source archive member: "+name)
    info=z.getinfo(name)
    if n is not None:
        must(info.file_size==n, "short/long original source image: "+name)
    raw=z.read(name)
    if n is not None:
        must(len(raw)==n, "truncated original source image: "+name)
    return raw


def actual_host(log: str, name: str, frame: int) -> None:
    hits=re.findall(r"script f=(\d+) dump "+re.escape(name)+r"(?=\s|$)", log)
    must(len(hits)==1 and int(hits[0])==frame,
         "original Snes9x host acknowledgment absent, ambiguous or altered")


def reconstruct(trace):
    low=bytearray(8192)
    snapshots={}
    last=0
    target_index=0
    total=0
    addresses=set()
    for raw in trace:
        row=json.loads(raw)
        frame=row.get("f")
        must(type(frame) is int and last<=frame<=36000,
             "source frame not monotonically within exact horizon")
        while target_index<len(TARGETS) and TARGETS[target_index]<frame:
            snapshots[TARGETS[target_index]]=bytes(low)
            target_index+=1
        last=frame
        address=int(row["adr"],16)
        old=int(row["old"],16)
        value=int(row["val"],16)
        must(0<=address<8192 and 0<=old<=255 and 0<=value<=255,
             "source trace contains out-of-coverage memory address/value")
        must(low[address]==old,
             "source original old-byte does not match replayed WRAM history")
        low[address]=value
        addresses.add(address)
        total+=1
    while target_index<len(TARGETS):
        snapshots[TARGETS[target_index]]=bytes(low)
        target_index+=1
    must(total>0 and len(snapshots)==len(TARGETS),
         "incomplete historical low-WRAM replay")
    return snapshots,total,len(addresses)


def named(low: bytes) -> dict:
    return dict(zip(NAMES,(low[i] for i in ADDRESSES)))


def attest_switcher_original_source_terminal(snapshots: dict[int, bytes]) -> dict:
    """Exact 2014 source WRAM result prelude, never a native timing exception.

    Low 8KiB values are reconstructed with old-byte validation from the
    authenticated Snes9x source trace and registered to its three full
    original-source guest memory dumps. Require every original frame of
    the 34-frame transient track-0 stage, four restored active course-3
    frames, the one inactive predecessor, and the stable Race B result.
    """
    def state(frame: int) -> dict:
        raw=snapshots.get(frame)
        must(isinstance(raw,bytes) and len(raw)==8192,
             "missing original Switcher source frame from real low-WRAM trace")
        return named(raw)

    must(state(12326)["track"]==3 and state(12326)["in_race"]!=1,
         "original Switcher source entry was not preceded by inactive course 3")
    must(all(state(f)["track"]==3 and state(f)["in_race"]==1
             and state(f)["tour_row"]==0 for f in range(12327,12335)),
         "original Switcher course 3 race entry not sustained eight frames")
    must(state(16990)["track"]==3 and state(16990)["in_race"]==1,
         "original Switcher prelude is not downstream of active course 3")
    must(all(state(f)["menu"]==0x84 and state(f)["track"]==0
             and state(f)["in_race"]==1 and state(f)["tour_row"]==0
             for f in range(16991,17025)),
         "original Switcher transient course-zero prelude not exactly 34 frames")
    must(all(state(f)["menu"]==0x16 and state(f)["track"]==3
             and state(f)["in_race"]==1 and state(f)["tour_row"]==0
             for f in range(17025,17029)),
         "original Switcher four restored active course-3 frames absent")
    must(state(17029)=={"menu":0x16,"track":3,"in_race":0,"tour_row":0},
         "original Switcher race-active exit predecessor differs")
    must(all(state(f)=={"menu":0x99,"track":3,"in_race":0,"tour_row":0}
             for f in list(range(17030,17038))+[17087]),
         "original Switcher Race B result was not stable and course-qualified")
    must(state(17088)=={"menu":0xF6,"track":3,"in_race":0,"tour_row":0},
         "original Switcher source result exit to selection not authenticated")
    return {
        "schema":"UR-QA01-SWITCHER-2014-ORIGINAL-RAW-TERMINAL/1",
        "event_course_id":"course:04",
        "source_movie_entry_frame":12327,
        "source_movie_result_frame":17030,
        "source_movie_result_relative_frames":4703,
        "source_prelude_track0_frames":[16991,17024],
        "source_prelude_menu_0x84_title_not_second_dragster_race":True,
        "source_restored_course3_active_frames":[17025,17028],
        "source_race_inactive_predecessor":17029,
        "source_stable_result_menu_0x99_frames":[17030,17087],
        "source_result_exit_select_tour_frame":17088,
        "all_transition_frames_independently_replayed_from_source_low8k":True,
        "genuine_stable_result_is_switcher_not_earlier_dragster":True,
        "native_guest_clocks_compared":False,
        "second_course0_event_during_prelude_proven":False,
        "source_original_upper_120k_intermediate_reconstructed":False,
        "accepted_usa_course_credit":0,
    }


def audit(archive: Path, expected_zip_sha256: str) -> dict:
    must(re.fullmatch("[0-9a-f]{64}",expected_zip_sha256) is not None,
         "expected original Actions artifact SHA256 mandatory")
    whole=archive.read_bytes()
    must(sha(whole)==expected_zip_sha256,"downloaded original source ZIP SHA256 mismatch")
    with ZipFile(archive) as z:
        names=z.namelist()
        must(len(names)==len(set(names)) and not any(
             x.startswith("/") or ".." in Path(x).parts for x in names),
             "duplicate or unsafe source ZIP member")
        rbytes=read_exact(z,"source-report.json")
        r=json.loads(rbytes)
        must(r.get("schema")==PRODUCER_SCHEMA and
             r.get("usa_rom_sha256")==ROM_SHA and
             r.get("original_movie_sha256")==MOVIE_SHA and
             r.get("source_controller_masks_modified") is False and
             r.get("USA_accepted_event_credit")==0 and
             r.get("fresh_original_or_native_event_proven") is False and
             r.get("new_horizon")==36000 and
             r.get("completed_new_unique_source_course_candidates")==0 and
             r.get("completed_repeat_of_previously_sourced_course")==1,
             "original source producer report not authenticated or falsely promoted")
        log=read_exact(z,"source/source.log")
        must(sha(log)==r.get("source_executed_log_sha256"),
             "real original runner execution log digest mismatches")
        for frame,tag in DUMPS:
            actual_host(log.decode("utf8",errors="replace"),tag,frame)
        trace_member="source/source-trace.jsonl"
        must(trace_member in names, "original source write trace missing")
        trace_info=z.getinfo(trace_member)
        must(trace_info.file_size==r.get("source_trace_bytes"),
             "original source trace byte length differs")
        source_digest=hashlib.sha256()
        with z.open(trace_member) as stream:
            for block in iter(lambda:stream.read(1024*1024),b""):
                source_digest.update(block)
        trace_sha=source_digest.hexdigest()
        must(trace_sha==r.get("source_raw_trace_sha256"),
             "actual original source trace bytes/hash differ from producer")
        with z.open(trace_member) as stream:
            snapshots,total,distinct=reconstruct(stream)
        all_sources=[]
        for frame,tag in DUMPS:
            full=read_exact(z,f"source/{tag}.wram.bin",131072)
            must(full[:8192]==snapshots[frame],
                 f"original source raw lower-8KiB disagrees at guest dump {frame}")
            all_sources.append({"source_movie_frame":frame,
                                "full_128k_wram_sha256":sha(full),
                                "reconstructed_exact_low_8k_sha256":sha(snapshots[frame])})
        for frame,track,race in BASELINE:
            measured=named(snapshots[frame])
            must(measured["track"]==track and measured["in_race"]==race,
                 "old original movie course entry not reproduced from actual trace")
        for frame,track,menu in RESULTS:
            measured=named(snapshots[frame])
            must(measured["track"]==track and measured["menu"]==menu
                 and measured["in_race"]!=1,
                 "old original movie terminal result not reproduced from trace")
        switcher_original=attest_switcher_original_source_terminal(snapshots)
        first,done,next_entry=(named(snapshots[f]) for f in (22941,25344,25731))
        must(named(snapshots[22940])["in_race"]!=1 and
             all(named(snapshots[f])["in_race"]==1 and
                 named(snapshots[f])["track"]==0 for f in range(22941,22949)),
             "not a genuinely entering and sustained repeat of original Dragster")
        must(all(named(snapshots[f])["in_race"]==1 and
                 named(snapshots[f])["track"]==0 for f in range(25335,25343))
             and named(snapshots[25343])["in_race"]!=1,
             "original Dragster repeat terminal predecessor not observed")
        must(all(named(snapshots[f])["menu"]==153 and
                 named(snapshots[f])["track"]==0 and
                 named(snapshots[f])["in_race"]!=1 for f in range(25344,25352)),
             "original repeated Dragster stable eight-frame result absent")
        must(named(snapshots[25730])["in_race"]!=1 and
             named(snapshots[36000])["in_race"]==1,
             "subsequent same-course attempt boundary absent")
        must(first["track"]==0 and first["tour_row"]==0 and first["in_race"]==1,
             "later source Dragster entry unsupported by WRAM")
        must(done["menu"]==153 and done["track"]==0
             and done["in_race"]!=1 and done["tour_row"]==0,
             "later source Dragster result unsupported by WRAM")
        must(next_entry["track"]==0 and next_entry["in_race"]==1,
             "subsequent original repeated course onset unsupported")
        runs=r["genuine_original_source_sustained_active_runs_after_switcher"]
        must(isinstance(runs,list) and len(runs)==2
             and runs[0].get("start")==22941
             and runs[0].get("last_active")==25342
             and runs[0].get("separately_observed_terminal_result",{}).get("host_frame")==25344
             and runs[0].get("track")==0
             and runs[1].get("start")==25731
             and runs[1].get("track")==0 and
             runs[1].get("separately_observed_terminal_result") is None,
             "claimed repeated known-course source interval changed")
        return {
            "schema":SCHEMA,
            "original_actions_zip_sha256":expected_zip_sha256,
            "original_source_producer_report_sha256":sha(rbytes),
            "original_source_trace_sha256":trace_sha,
            "original_2014_movie_sha256":MOVIE_SHA,
            "usa_rom_sha256":ROM_SHA,
            "real_2014_snes9x_trace_writes_replayed":total,
            "all_recorded_old_bytes_match_reconstructed_wram":True,
            "trace_distinct_low_wram_addresses":distinct,
            "trace_observable_wram_range":[0,8191],
            "outside_trace_120k_reconstruction_possible":False,
            "exact_full_128k_guest_dumps_checked_for_low8k":all_sources,
            "four_prior_original_course_entries_and_results_reproduced":True,
            "switcher_original_source_terminal":switcher_original,
            "post_switcher_known_course_repeat":{
                "track":0,"tour_row":0,"real_source_entry":22941,
                "real_source_result":25344,
                "named_entry_state":first,"named_result_state":done,
            },
            "second_original_source_repeat":{
                "track":0,"start":25731,"terminal_observed_by36000":False,
            },
            "distinct_new_usa_courses_proven":0,
            "original_native_event_equivalence_proven":False,
            "historical_second_dragster_full_128k_entry_image_available":False,
            "source_movie_controller_masks_retimed":False,
            "usa_event_accepted_credit":0,
        }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("zip_path",type=Path)
    p.add_argument("--zip-sha256",required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    r=audit(args.zip_path,args.zip_sha256)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(r,sort_keys=True,indent=2)+"\n")
    print("2014 real-source low-8KiB replay qualified; no new unique USA course, 0/45 accepted.")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
