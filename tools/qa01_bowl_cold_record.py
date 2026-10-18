#!/usr/bin/env python3
"""Actual fresh Snes9x/native cold record reload after 2014 USA Bowl Stunt.

Source-qualified research evidence only, never Windows autosave or 45-event
acceptance. Reuses the existing QA01 guest runners and ranked SRAM format.
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
import qa01_bowl_switcher_handoff as handoff

EXPECTED_ROM = shared.ROM_SHA
EXPECTED_MOVIE = shared.MOVIE_SHA
BOOT_FRAMES = shared.BOOT_FRAMES
RESULT = 11985
ENTRY = 8620
SCORE = 764
BOWL_INDEX = 2
SEED_OFFSET = 354
SCHEMA = "UR-QA01-BOWL-COLD-GUEST-RECORD-RELOAD/1"
HEXSHA = re.compile(r"^[0-9a-f]{64}$")


class BowlColdEvidenceError(ValueError):
    pass


def rank_record(data: bytes) -> dict:
    if len(data) != shared.SIZE:
        raise BowlColdEvidenceError("Bowl ranked record must be full 8192-byte SRAM")
    word = lambda at: int.from_bytes(data[at:at + 2], "little")
    common = shared.ranked(data)
    return {
        "crawler_bowl_rank0_score": word(0x0422 + BOWL_INDEX * 2),
        "crawler_bowl_rank0_holder": data[0x0550 + BOWL_INDEX],
        "record_checksum_stored": common["record_checksum_stored"],
        "record_checksum_calculated": common["record_checksum_calculated"],
        "all_150_record_words_sha256": common["all_150_record_words_sha256"],
        "all_150_record_holders_sha256": common["all_150_record_holders_sha256"],
    }


def expected_script_sha256() -> str:
    script = event.replay_script(
        3, 0x18, event.sample_frames("bowl", 3365), True,
        tally_phase=True, source_followthrough=True, bowl_next_switcher=True)
    return hashlib.sha256(script.encode("utf-8")).hexdigest()


def validate_source(report: dict, replay: Path) -> dict:
    source = report.get("original_source_event", {})
    comparison = report.get("comparison", {})
    hand = report.get("bowl_next_switcher_handoff")
    if (report.get("schema_version") != 1
            or report.get("name") != "bowl"
            or report.get("course_id") != "course:03"
            or report.get("family") != "stunt"
            or report.get("native_backend") != "pinned-baldosa"
            or report.get("admission") != "investigative candidate; not a release-ledger pass"
            or report.get("rom_sha256") != EXPECTED_ROM
            or report.get("original_movie_sha256") != EXPECTED_MOVIE
            or report.get("input_sha256") != expected_script_sha256()
            or report.get("reference_script_sha256") != report["input_sha256"]
            or not isinstance(source, dict)
            or source.get("original_entry_frame") != ENTRY
            or source.get("original_result_frame") != RESULT
            or source.get("source_active_frames_to_result") != 3365
            or source.get("source_stunt_tally_frame") != 11915
            or not isinstance(comparison, dict)
            or comparison.get("first_sample_disagreement") is not None
            or comparison.get("rendered_result_and_score_text_matched") is not True
            or comparison.get("intermediate_result_text_matched") is not True
            or comparison.get("stunt_positive_score_visible") is not True
            or comparison.get("both_reached_terminal_menu") is not True
            or comparison.get("terminal_result_guest_frame",
                              {}).get("reference_relative") != 3365
            or not isinstance(hand, dict)
            or hand.get("schema") != handoff.SCHEMA
            or hand.get("source_original_result_frame") != RESULT
            or hand.get("source_original_next_switcher_frame") != 12327
            or hand.get("source_next_switcher_entry_offset") != 342
            or hand.get("source_controller_masks_modified") is not False
            or hand.get("source_earned_bowl_rank0_764_and_checksum_every_sample") is not True
            or hand.get("release_complete_event_credit") != 0
            or hand.get("original_native_clocks_unrebased") is not True
            or hand.get("cold_process_disk_persistence_proven") is not False
            or hand.get("shipping_windows_candidate_proven") is not False
            or hand.get("sample_offsets") != list(handoff.OFFSETS)):
        raise BowlColdEvidenceError("not authenticated Bowl 2014 full Stunt/handoff source")
    if any(not isinstance(report.get(k), str)
           or not HEXSHA.fullmatch(report[k])
           for k in ("native_executable_sha256", "reference_core_sha256",
                     "source_sram_sha256", "original_movie_window_sha256")):
        raise BowlColdEvidenceError("Bowl identity hashes incomplete")
    if (comparison["terminal_result_guest_frame"].get("native_relative")
            not in (3364, 3365)):
        raise BowlColdEvidenceError("unknown native Bowl terminal-frame phase")
    samples = hand.get("samples")
    if (not isinstance(samples, list) or len(samples) != len(handoff.OFFSETS)
            or [x.get("offset_from_observed_bowl_result")
                for x in samples if isinstance(x, dict)] != list(handoff.OFFSETS)):
        raise BowlColdEvidenceError("missing ordered complete Bowl handoff")
    last = samples[-1]
    seeds = {}
    for side, subdir in (("original", "ref"), ("native", "native")):
        rec = last.get("fresh_guests", {}).get(side)
        if (not isinstance(rec, dict)
                or rec.get("in_race") != 1
                or rec.get("track") != 3
                or rec.get("full_sram_bytes") != 8192
                or rec.get("source_earned_bowl_rank0") != {
                    "rank": 0, "value_word": SCORE, "holder_index": 0}
                or rec.get("record_table_checksum_matches") is not True):
            raise BowlColdEvidenceError("actual terminal seed lacks source-earned Bowl MIKE record")
        path = replay / subdir / f"bowl-next-switcher-{SEED_OFFSET}.sram.bin"
        expected = rec.get("sram_sha256")
        if not isinstance(expected, str) or not HEXSHA.fullmatch(expected):
            raise BowlColdEvidenceError("missing source-authenticated Bowl seed digest")
        seed = shared.byte_image(path, expected)
        ranked = rank_record(seed)
        if (ranked["crawler_bowl_rank0_score"] != SCORE
                or ranked["crawler_bowl_rank0_holder"] != 0
                or ranked["record_checksum_stored"] != ranked["record_checksum_calculated"]):
            raise BowlColdEvidenceError("Bowl record/checksum absent from raw captured SRAM")
        seeds[side] = {"path": path, "sha256": shared.digest(seed),
                       "ranked": ranked}
    return seeds


def evaluate_cold(seeds: dict, root: Path) -> dict:
    rows = []
    for frame in BOOT_FRAMES:
        checks = {}
        for side, subdir in (("original", "ref"), ("native", "native")):
            path = root / side / subdir / f"cold-{frame:03d}.sram.bin"
            if not path.is_file():
                raise BowlColdEvidenceError(f"missing actual new-guest Bowl SRAM {path}")
            raw = path.read_bytes()
            ranked = rank_record(raw)
            if ranked != seeds[side]["ranked"]:
                raise BowlColdEvidenceError(
                    f"{side} lost or rewrote source-earned Bowl ranked records at boot+{frame}")
            checks[side] = {"full_sram_bytes": len(raw),
                            "sram_sha256": shared.digest(raw),
                            "ranked": ranked}
        if checks["original"]["ranked"] != checks["native"]["ranked"]:
            raise BowlColdEvidenceError("original/native fresh Bowl ranked records differ")
        rows.append({"boot_host_frame": frame, "fresh_guests": checks})
    return {
        "schema": SCHEMA,
        "source_seed_sha256": {k: v["sha256"] for k, v in seeds.items()},
        "source_qualified_bowl_score": SCORE,
        "two_independent_new_guest_processes_observed": True,
        "fresh_guest_loaded_entire_ranked_table_holders_and_checksum": True,
        "boot_observations": rows,
        "native_guest_seed_is_original_captured_sram_not_synthetic": True,
        "full_source_native_guest_sram_equality_not_assumed": True,
        "actual_host_disk_publication_or_power_failure_proven": False,
        "complete_original_native_course_fidelity_proven": False,
        "all_guest_frames_cpu_spc_ppu_equal_proven": False,
        "release_complete_usa_event_credit": 0,
    }


def execute(args) -> dict:
    report = json.loads(args.producer_report.read_text("utf-8"))
    for field, path in (("rom_sha256", args.rom),
                        ("original_movie_sha256", args.movie),
                        ("reference_core_sha256", args.core),
                        ("native_executable_sha256", args.native)):
        if shared.digest(path.read_bytes()) != report.get(field):
            raise BowlColdEvidenceError(f"source-bound original Bowl {field} mismatch")
    seeds = validate_source(report, args.replay)
    if args.work.exists():
        raise BowlColdEvidenceError("cold replay output root must be unused")
    args.work.mkdir(parents=True)
    script = args.work / "cold.script"
    script.write_text("wait 300\ndump cold-300\nwait 120\ndump cold-420\nquit\n",
                      encoding="ascii")
    for side in ("original", "native"):
        work = args.work / side
        work.mkdir()
        cfg = SimpleNamespace(**vars(args))
        cfg.sram = seeds[side]["path"]
        if side == "original":
            log = runner.run_reference(work, cfg, script, [])
        else:
            log = event.run_pinned_baldosa(work, cfg, script, [], 0)
        (args.work / f"{side}.log").write_text(log, encoding="utf-8")
        for frame in BOOT_FRAMES:
            if event.observed_dump_frame(log, f"cold-{frame:03d}") != frame:
                raise BowlColdEvidenceError(f"unanchored new {side} guest boot")
    result = evaluate_cold(seeds, args.work)
    result["original_source_identities"] = {
        k: report[k] for k in (
            "rom_sha256", "original_movie_sha256", "original_movie_window_sha256",
            "input_sha256", "reference_core_sha256", "native_executable_sha256")}
    result["original_producer_report_sha256"] = shared.digest(
        args.producer_report.read_bytes())
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ("producer-report", "replay", "snesref", "core", "native",
                  "rom", "movie", "work", "out"):
        parser.add_argument("--" + field, required=True, type=Path)
    args = parser.parse_args()
    for k in ("producer_report", "replay", "snesref", "core", "native",
              "rom", "movie", "work", "out"):
        setattr(args, k, getattr(args, k).resolve())
    result = execute(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                        encoding="utf-8")
    print("Original/native cold USA Bowl score/checksum qualified at two guest boots; 0/45 event passes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
