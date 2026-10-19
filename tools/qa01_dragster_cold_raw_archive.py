#!/usr/bin/env python3
"""Read-only byte-level witness of real Dragster 2508 cold-guest SRAM reloads.

Original and native processes are separate. Verify retained execution logs,
original post-race seeds and all subsequent full 8192-byte guest snapshots.
No host-disk durability, Windows shipping or complete USA event acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from qa01_bowl_handoff_raw_archive_audit import read_exact, read_logged_frame

SCHEMA = "UR-QA01-DRAGSTER-COLD-RAW-GUEST-SNAPSHOT-AUDIT/1"
COLD_SCHEMA = "UR-QA01-DRAGSTER-2508-COLD-GUEST-RECORD/1"
FRAMES = (300, 420)
SEED_OFFSET = 336


def must(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def ranked(data: bytes) -> dict:
    must(len(data) == 8192, "cold guest did not retain full 8KiB SRAM")
    word = lambda at: int.from_bytes(data[at:at + 2], "little")
    return {
        "dragster_rank_zero_value": word(0x422),
        "dragster_rank_zero_holder": data[0x550],
        "record_checksum_stored": word(0x54E),
        "record_checksum_calculated": sum(word(0x422 + i * 2) for i in range(150)) & 0xFFFF,
        "all_150_record_words_sha256": sha(data[0x422:0x54E]),
        "all_150_record_holders_sha256": sha(data[0x550:0x5E6]),
    }


def audit(root: Path) -> dict:
    producer_path = root / "dragster-report.json"
    cold_path = root / "dragster-cold.json"
    must(producer_path.is_file() and not producer_path.is_symlink() and
         cold_path.is_file() and not cold_path.is_symlink(),
         "missing real source-bound Dragster producer/cold report")
    producer = json.loads(producer_path.read_bytes())
    report = json.loads(cold_path.read_bytes())
    must(producer.get("course_id") == "course:01" and
         producer.get("name") == "dragster" and
         producer.get("original_source_event", {}).get("original_result_frame") == 2874 and
         producer.get("comparison", {}).get("paired_event_candidate") is False and
         producer.get("dragster_next_zoo_handoff", {}).get("release_complete_usa_event_credit") == 0,
         "source original Dragster not qualified as strict-negative research")
    must(report.get("schema") == COLD_SCHEMA and
         report.get("producer_report_sha256") == sha(producer_path.read_bytes()) and
         report.get("source_earned_dragster_rank0_centiseconds") == 2508 and
         report.get("two_independent_original_native_new_guest_processes") is True and
         report.get("source_seeds_from_actual_completed_race_plus_336") is True and
         report.get("release_complete_usa_event_credit") == 0 and
         report.get("actual_windows_host_disk_autosave_power_cut_proven") is False and
         report.get("complete_original_native_dragster_event_parity_proven") is False,
         "cold result not original-source anchored or falsely promoted")
    bound = report.get("source_bound_identities")
    must(isinstance(bound, dict) and all(
         bound.get(key) == producer.get(key) for key in (
             "rom_sha256", "original_movie_sha256", "original_movie_window_sha256",
             "input_sha256", "reference_core_sha256", "native_executable_sha256")),
         "reported cold source/input/executable IDs differ from original producer")
    observations = report.get("boot_observations")
    must(isinstance(observations, list) and len(observations) == 2 and
         [r.get("host_frame_since_fresh_boot") for r in observations] == list(FRAMES),
         "cold actual boot frame series incomplete")
    seeds = {}
    sampled = []
    for side, folder in (("original", "ref"), ("native", "native")):
        guest_rows = producer["dragster_next_zoo_handoff"]["samples"]
        must(len(guest_rows) == 14 and
             guest_rows[-1].get("offset_from_respective_dragster_result") == SEED_OFFSET,
             "missing original earned score guest seed receipt")
        producer_seed = guest_rows[-1]["fresh_guests"][side]
        seed_path = root / "dragster/replay" / folder / (
            f"dragster-next-zoo-{SEED_OFFSET}.sram.bin")
        seed = read_exact(seed_path, 8192)
        must(sha(seed) == producer_seed.get("full_sram_sha256") and
             sha(seed) == report.get("source_sram_digest_per_guest", {}).get(side),
             "source 2508 guest seed raw-image SHA256 differs")
        expected = ranked(seed)
        must(expected["dragster_rank_zero_value"] == 2508 and
             expected["dragster_rank_zero_holder"] == 0 and
             expected["record_checksum_calculated"] == expected["record_checksum_stored"],
             "original earned Dragster record is missing/corrupted in seed")
        seeds[side] = expected
        log_path = root / "cold-boot" / f"{side}.log"
        must(log_path.is_file() and not log_path.is_symlink(),
             "missing original/new guest process output log")
        log = log_path.read_text(encoding="utf8", errors="replace")
        for i, frame in enumerate(FRAMES):
            must(read_logged_frame(log, f"cold-{frame}") == frame,
                 "new cold guest observed at incorrect host clock")
            path = root / "cold-boot" / side / folder / f"cold-{frame}.sram.bin"
            raw = read_exact(path, 8192)
            measured = ranked(raw)
            stated = observations[i].get("fresh_guests", {}).get(side)
            must(isinstance(stated, dict) and
                 stated.get("entire_battery_bytes") == len(raw) and
                 stated.get("sram_sha256") == sha(raw) and
                 stated.get("ranked") == measured and
                 measured == expected,
                 "actual new guest cold record differs from seed/report")
            sampled.append({
                "side": side, "guest_boot_host_frame": frame,
                "whole_sram_sha256": sha(raw),
                "whole_sram_equals_original_seed": raw == seed,
                "ranked_150_words_holders_checksum_exact": True,
            })
    must(seeds["original"] == seeds["native"],
         "original/native complete ranked table differs after actual earned result")
    return {
        "schema": SCHEMA, "producer_report_sha256": sha(producer_path.read_bytes()),
        "cold_report_sha256": sha(cold_path.read_bytes()),
        "original_and_native_genuine_guest_processes": 2,
        "independently_rehashed_full_8k_sram_snapshots": len(sampled),
        "actual_cold_guest_host_frames": list(FRAMES),
        "complete_150_ranked_words_holders_and_checksum_reconfirmed": True,
        "source_earned_dragster_2508_preserved": True,
        "sampled": sampled,
        "full_8192_byte_original_native_sram_equality_assumed": False,
        "actual_windows_host_disk_durability_proven": False,
        "complete_original_native_usa_event_fidelity_proven": False,
        "accepted_usa_event_credit": 0,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive-root", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    result = audit(args.archive_root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf8")
    print("Four actual newly booted original/native SRAM snapshots rehashed; USA 0/45")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
