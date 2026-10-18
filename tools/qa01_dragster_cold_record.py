#!/usr/bin/env python3
"""Two real cold guest-process loads of a source-earned 2014 USA Dragster record.

Read-only source-bound event research. Not actual host disk publication,
full CPU/SPC equivalence, shipping Windows behavior or an accepted USA event.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from types import SimpleNamespace

import probe_original_event_complete as event
import probe_jumpover_fallthrough_native as runner
import qa01_cold_result_record as shared
import qa01_dragster_zoo_handoff as handoff

SCHEMA = "UR-QA01-DRAGSTER-2508-COLD-GUEST-RECORD/1"
RESULT = 2874
ENTRY = 794
NEXT_ZOO_ENTRY = 3190
SCORE = 2508
SEED_OFFSET = 336
MOVIE_WINDOW_SHA = "aec7f8850085d662656117303f9daa802e737aca2d12b8af89962acbb206d1c1"
HEX256 = re.compile(r"^[0-9a-f]{64}$")
BOOT_FRAMES = shared.BOOT_FRAMES


class DragsterColdError(ValueError):
    pass


def score_record(data: bytes) -> dict:
    if len(data) != shared.SIZE:
        raise DragsterColdError("Dragster ranked SRAM must be exactly 8192 bytes")
    common = shared.ranked(data)
    return {
        "dragster_rank_zero_value": int.from_bytes(data[0x0422:0x0424],"little"),
        "dragster_rank_zero_holder": data[0x0550],
        "record_checksum_stored": common["record_checksum_stored"],
        "record_checksum_calculated": common["record_checksum_calculated"],
        "all_150_record_words_sha256": common["all_150_record_words_sha256"],
        "all_150_record_holders_sha256": common["all_150_record_holders_sha256"],
    }


def source_script_sha() -> str:
    script=event.replay_script(
        1, 0x99, event.sample_frames("dragster",2080), False,
        source_followthrough=True, dragster_next_zoo=True)
    return hashlib.sha256(script.encode("utf-8")).hexdigest()


def source_seeds(report: dict, replay: Path) -> dict:
    source=report.get("original_source_event") or {}
    comparison=report.get("comparison") or {}
    hand=report.get("dragster_next_zoo_handoff") or {}
    frames=comparison.get("terminal_result_guest_frame") or {}
    if (report.get("schema_version") != 1 or report.get("name") != "dragster"
            or report.get("course_id") != "course:01"
            or report.get("family") != "race-a"
            or report.get("native_backend") != "pinned-baldosa"
            or report.get("admission") != "investigative candidate; not a release-ledger pass"
            or report.get("rom_sha256") != shared.ROM_SHA
            or report.get("original_movie_sha256") != shared.MOVIE_SHA
            or report.get("original_movie_window_sha256") != MOVIE_WINDOW_SHA
            or report.get("input_sha256") != source_script_sha()
            or report.get("reference_script_sha256") != report.get("input_sha256")
            or any(not isinstance(report.get(k),str)
                   or not HEX256.fullmatch(report[k])
                   for k in ("reference_core_sha256","native_executable_sha256",
                             "source_sram_sha256"))
            or source.get("original_entry_frame") != ENTRY
            or source.get("original_result_frame") != RESULT
            or source.get("source_active_frames_to_result") != 2080
            or frames != {"reference_relative":2081,"native_relative":2079}
            or comparison.get("first_sample_disagreement") is not None
            or comparison.get("both_reached_terminal_menu") is not True
            or comparison.get("rendered_result_and_score_text_matched") is not True
            or comparison.get("timed_race_or_circuit_result_visible") is not True
            or comparison.get("original_source_entry_equivalent") is not True
            or comparison.get("fresh_guest_entry_equivalent") is not True
            or comparison.get("paired_event_candidate") is not False
            or hand.get("schema") != handoff.SCHEMA
            or hand.get("original_movie_dragster_result_frame") != RESULT
            or hand.get("original_movie_zoo_entry_frame") != NEXT_ZOO_ENTRY
            or hand.get("original_movie_zoo_entry_relative_to_dragster_result") != 316
            or hand.get("sample_offsets") != list(handoff.OFFSETS)
            or hand.get("source_controller_masks_rephased") is not False
            or hand.get("release_complete_usa_event_credit") != 0
            or hand.get("original_native_ranked_checksum_valid_all_samples") is not True
            or hand.get("fresh_original_loaded_true_zoo_course_while_active") is not True
            or hand.get("fresh_native_loaded_true_zoo_course_while_active") is not True):
        raise DragsterColdError("wrong original-USA Dragster source, controller or result")
    samples=hand.get("samples")
    if (not isinstance(samples,list) or len(samples)!=len(handoff.OFFSETS)
            or [row.get("offset_from_respective_dragster_result")
                for row in samples if isinstance(row,dict)] != list(handoff.OFFSETS)):
        raise DragsterColdError("missing complete genuine Dragster next-Zoo sample population")
    last=samples[-1]
    seeds={}
    for side,subdir in (("original","ref"),("native","native")):
        guest=last.get("fresh_guests",{}).get(side)
        if (not isinstance(guest,dict)
                or guest.get("track") != 1 or guest.get("tour_row") != 0
                or guest.get("in_race") != 1
                or guest.get("full_sram_bytes") != 8192
                or guest.get("ranked_records_checksum_valid") is not True
                or guest.get("dragster_record_three_ranks",[None])[0] != {
                    "rank":0,"value_word":SCORE,"holder_index":0}):
            raise DragsterColdError("guest not in live Zoo with source-earned Dragster MIKE record")
        digest=guest.get("full_sram_sha256")
        if not isinstance(digest,str) or not HEX256.fullmatch(digest):
            raise DragsterColdError("missing guest SRAM seed digest")
        path=replay/subdir/f"dragster-next-zoo-{SEED_OFFSET:03d}.sram.bin"
        seed=shared.byte_image(path,digest)
        ranked=score_record(seed)
        if (ranked["dragster_rank_zero_value"]!=SCORE
                or ranked["dragster_rank_zero_holder"]!=0
                or ranked["record_checksum_calculated"]!=ranked["record_checksum_stored"]):
            raise DragsterColdError("real source-earned Dragster record missing in raw seed")
        seeds[side]={"path":path,"sha256":shared.digest(seed),"ranked":ranked}
    if seeds["original"]["ranked"] != seeds["native"]["ranked"]:
        raise DragsterColdError("paired guests disagree on original ranked table before cold boot")
    return seeds


def evaluate_cold(seeds:dict, work:Path) -> dict:
    rows=[]
    for frame in BOOT_FRAMES:
        samples={}
        for side,sub in (("original","ref"),("native","native")):
            path=work/side/sub/f"cold-{frame:03d}.sram.bin"
            if not path.is_file():
                raise DragsterColdError("missing real newly booted guest SRAM")
            raw=path.read_bytes()
            rank=score_record(raw)
            if rank!=seeds[side]["ranked"]:
                raise DragsterColdError(f"{side} lost or changed Dragster ranked table at cold +{frame}")
            samples[side]={
                "entire_battery_bytes":len(raw),
                "sram_sha256":shared.digest(raw),
                "ranked":rank,
            }
        if samples["original"]["ranked"]!=samples["native"]["ranked"]:
            raise DragsterColdError("fresh original/native ranked records unequal")
        rows.append({"host_frame_since_fresh_boot":frame,"fresh_guests":samples})
    return {
        "schema":SCHEMA,
        "source_earned_dragster_rank0_centiseconds":SCORE,
        "source_sram_digest_per_guest":{k:v["sha256"] for k,v in seeds.items()},
        "two_independent_original_native_new_guest_processes":True,
        "full_150_ranked_words_holders_checksum_preserved":True,
        "boot_observations":rows,
        "source_seeds_from_actual_completed_race_plus_336":True,
        "entire_original_native_sram_equality_claimed":False,
        "actual_windows_host_disk_autosave_power_cut_proven":False,
        "complete_original_native_dragster_event_parity_proven":False,
        "cpu_spc_instruction_tick_parity_proven":False,
        "release_complete_usa_event_credit":0,
    }


def execute(args) -> dict:
    report=json.loads(args.producer_report.read_text(encoding="utf-8"))
    for field,path in (("rom_sha256",args.rom),
                       ("original_movie_sha256",args.movie),
                       ("reference_core_sha256",args.core),
                       ("native_executable_sha256",args.native)):
        if shared.digest(path.read_bytes())!=report.get(field):
            raise DragsterColdError(f"wrong actual producer {field} executable/input identity")
    seeds=source_seeds(report,args.replay)
    if args.work.exists():
        raise DragsterColdError("new cold guest process root must not preexist")
    args.work.mkdir(parents=True)
    script=args.work/"cold.script"
    script.write_text("wait 300\ndump cold-300\nwait 120\ndump cold-420\nquit\n",encoding="ascii")
    for side in ("original","native"):
        work=args.work/side
        work.mkdir()
        cfg=SimpleNamespace(**vars(args))
        cfg.sram=seeds[side]["path"]
        if side=="original":
            log=runner.run_reference(work,cfg,script,[])
        else:
            log=event.run_pinned_baldosa(work,cfg,script,[],0)
        (args.work/f"{side}.log").write_text(log,encoding="utf-8")
        for frame in BOOT_FRAMES:
            if event.observed_dump_frame(log,f"cold-{frame:03d}")!=frame:
                raise DragsterColdError("unanchored actual new guest boot")
    result=evaluate_cold(seeds,args.work)
    result["source_bound_identities"]={
        k:report[k] for k in ("rom_sha256","original_movie_sha256",
                              "original_movie_window_sha256","input_sha256",
                              "reference_core_sha256","native_executable_sha256")}
    result["producer_report_sha256"]=shared.digest(args.producer_report.read_bytes())
    return result


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    for f in ("producer-report","replay","snesref","core","native",
              "rom","movie","work","out"):
        p.add_argument("--"+f,required=True,type=Path)
    args=p.parse_args()
    for f in ("producer_report","replay","snesref","core","native",
              "rom","movie","work","out"):
        setattr(args,f,getattr(args,f).resolve())
    data=execute(args)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(data,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("Genuine Dragster 25.08 ranked record in two cold guest processes; 0/45 USA event credit")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
