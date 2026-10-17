#!/usr/bin/env python3
"""Independently verify original hosted Win32 game on genuine full NTFS evidence.

Read-only original GitHub Actions ZIP consumer. Requires the externally pinned
original artifact SHA and the exact tested QA PR-merge commit. Verifies only
default raw 8 KiB SRAM fresh-allocation denial, not typed or power-cut QA.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import stat
import zipfile

PREFIX = "qa02-game-on-real-full-volume/"
OS = "qa02-real-ntfs-result/result.json"
STAGES = ("baseline", "full", "restored")
MEMBERS = {OS} | {PREFIX + stage + "-result.json" for stage in STAGES}
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
GAME_SOURCE = "2073471dd6bcf2d5dbc22042e587ddee1852af8c"
PE = "b0638f31aa8fa782b5c261b9898dd82c2bf5b751768995d0460a37949f1ac59a"
CMD = "b61d6b3836e21da6dd91dc4bcbf5cff19a85df6f73f07ee2bcd29a377fc678c3"
ROUTE = "4e714899f53c3bbe501bbfcacf91dd549989c9beb7c2cf6265b13eb687142ec6"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def demand(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError("QA02_REAL_GAME_NTFS_FULL_REJECTED: " + reason)


def accepted_receipt(z: zipfile.ZipFile, name: str) -> dict:
    d = json.loads(z.read(name).decode("utf-8-sig"))
    demand(type(d) is dict, "nonobject original JSON " + name)
    return d


def validate(path: Path, expected_sha: str, tested_qa_merge: str) -> dict:
    demand(type(expected_sha) is str and type(tested_qa_merge) is str and
           HEX64.fullmatch(expected_sha) is not None and
           HEX64.fullmatch(tested_qa_merge) is not None,
           "require externally pinned original Actions ZIP SHA and exact tested QA merge")
    demand(path.is_file() and not path.is_symlink() and
           0 < path.stat().st_size <= 100_000 and
           sha(path.read_bytes()) == expected_sha,
           "missing/mutated original Windows Actions ZIP")
    with zipfile.ZipFile(path) as z:
        info = z.infolist()
        demand(len(info) == 4 and {a.filename for a in info} == MEMBERS and
               sum(a.file_size for a in info) <= 60_000 and z.testzip() is None,
               "four original OS/game stage sources missing, repeated or damaged")
        for a in info:
            typ = stat.S_IFMT(a.external_attr >> 16)
            demand(not a.is_dir() and not (a.flag_bits & 1) and
                   typ in (0, stat.S_IFREG) and
                   0 < a.file_size <= 30_000,
                   "original archive includes unsafe/empty/nonregular source")
        os_event = accepted_receipt(z, OS)
        demand(os_event.get("schema") ==
                   "UR-QA02-REAL-WIN32-ISOLATED-NTFS-DISKFULL-PREFLIGHT/1" and
               os_event.get("source_revision") == tested_qa_merge and
               all(os_event.get(k) is True for k in (
                   "VHDX_isolated_NTFS", "actual_Win32_disk_full_observed",
                   "real_original_8192_bytes_preserved",
                   "native_game_tested", "native_game_receipt_is_independent_stage_file",
                   "game_ROM_used_in_ephemeral_runner",
                   "user_ROM_or_player_data_used")) and
               os_event.get("private_player_save_uploaded") is False and
               type(os_event.get("genuine_second_process_ERROR_DISK_FULL")) is int and
               os_event["genuine_second_process_ERROR_DISK_FULL"] == 112 and
               type(os_event.get("recovered_new_write_bytes")) is int and
               os_event["recovered_new_write_bytes"] == 8192 and
               type(os_event.get("capacity_megabytes")) is int and
               os_event["capacity_megabytes"] == 128 and
               type(os_event.get("original_free_bytes")) is int and
               os_event["original_free_bytes"] > 8192 and
               type(os_event.get("accepted_filler_bytes")) is int and
               os_event["accepted_filler_bytes"] > 0 and
               os_event["accepted_filler_bytes"] <= os_event["original_free_bytes"] and
               HEX64.fullmatch(os_event.get("checker_sha256", "")) is not None and
               os_event.get("power_loss_or_partial_IO_tested") is False and
               os_event.get("physical_operator") is False and
               type(os_event.get("release_gate_credit")) is int and
               os_event["release_gate_credit"] == 0,
               "actual isolated native OS-full and game-on-volume contract differs")
        records = {stage: accepted_receipt(z, PREFIX + stage + "-result.json")
                   for stage in STAGES}
        for stage, d in records.items():
            demand(d.get("schema") ==
                       "UR-QA02-ORIGINAL-PACKAGED-GAME-REAL-NTFS-FULL/1" and
                   d.get("stage") == stage and
                   d.get("tested_product_pr_merge") == GAME_SOURCE and
                   d.get("tested_PE_SHA256") == PE and
                   d.get("tested_CMD_SHA256") == CMD and
                   d.get("route_SHA256") == ROUTE and
                   d.get("native_launcher_WindowsPowerShell_modules_normalized") is True and
                   d.get("tested_demand_for_fresh_sram_allocation") is True and
                   d.get("timeout") is False and
                   d.get("human_hardware_or_power_cut") is False and
                   type(d.get("release_gate_credit")) is int and
                   d["release_gate_credit"] == 0 and
                   d.get("result") == "bounded_pass" and
                   d.get("failure") == "" and
                   HEX64.fullmatch(d.get("stdout_SHA256", "")) is not None and
                   HEX64.fullmatch(d.get("stderr_SHA256", "")) is not None and
                   type(d.get("canonical_receipts")) is list and
                   type(d.get("original_launcher_bounded_markers")) is list,
                   "source-bound original packaged game receipt differs " + stage)
        baseline, full, restored = (records[s] for s in STAGES)
        old = baseline.get("original_preserved_sram_sha256")
        demand(type(old) is str and HEX64.fullmatch(old) is not None and
               full.get("original_preserved_sram_sha256") == old and
               restored.get("original_preserved_sram_sha256") == "" and
               old != sha(b"") and
               baseline.get("Windows_process_exit") == 0 and
               restored.get("Windows_process_exit") == 0 and
               full.get("Windows_process_exit") == 8 and
               type(full.get("Windows_process_exit")) is int and
               all("first frame simulated" in d["original_launcher_bounded_markers"]
                   for d in (baseline, full, restored)) and
               "UR-BALDOSA-SAVE-FAILED" in full["original_launcher_bounded_markers"] and
               "UR-BALDOSA-SAVE-FAILED" not in baseline["original_launcher_bounded_markers"] and
               "UR-BALDOSA-SAVE-FAILED" not in restored["original_launcher_bounded_markers"] and
               baseline["canonical_receipts"] == [] and
               full["canonical_receipts"] == [] and
               type(restored.get("canonical_receipts")) is list and
               len(restored["canonical_receipts"]) == 1,
               "true fresh-save-failure/old SRAM archival/cold recovery not proven")
        item = restored["canonical_receipts"][0]
        demand(type(item) is dict and set(item) == {"path", "bytes", "sha256"} and
               item["path"] == "saves/save.srm" and
               type(item["bytes"]) is int and item["bytes"] == 8192 and
               type(item["sha256"]) is str and
               HEX64.fullmatch(item["sha256"]) is not None and
               item["sha256"] != old,
               "restored genuine guest SRAM not complete or source original stale")
    return {
        "schema": "UR-INDEPENDENT-QA02-GENUINE-WINDOWS-GAME-NTFS-FULL/1",
        "original_github_actions_artifact_sha256": expected_sha,
        "exact_tested_qa_pr_merge": tested_qa_merge,
        "original_product_source": GAME_SOURCE,
        "original_product_PE_sha256": PE,
        "original_product_CMD_sha256": CMD,
        "old_saved_8192_bytes_preserved_sha256": old,
        "native_new_save_allocation_refused_with_exit8": True,
        "actual_Win32_second_process_disk_full_112": True,
        "restored_new_8192_byte_SRAM_sha256": item["sha256"],
        "named_typed_transaction_tested": False,
        "human_input_or_power_cut_tested": False,
        "release_gate_credit": 0,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--zip", type=Path, required=True)
    ap.add_argument("--sha256", required=True)
    ap.add_argument("--qa-pr-merge-sha", required=True)
    args = ap.parse_args()
    try:
        result = validate(args.zip, args.sha256, args.qa_pr_merge_sha)
    except (ValueError, KeyError, TypeError, OSError,
            zipfile.BadZipFile, UnicodeError, json.JSONDecodeError) as err:
        ap.exit(2, str(err) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
