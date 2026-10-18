#!/usr/bin/env python3
"""Independent source-byte acceptance reader for named-profile Windows NTFS full test.

Never runs the game. The original GitHub Actions artifact and independent
product/source identities must be supplied explicitly. No release-gate credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import stat
import zipfile

STAGES = ("before", "actual-full", "cold1", "cold2")
CANONICAL = ("raw", "typed", "selector", "catalog")
BINARIES = {
    f"source-bytes/{stage}.{field}.bin"
    for stage in STAGES for field in CANONICAL
}
LOGS = (
    "fixture.log", "warm.log", "full-ntfs-original-CMD.log",
    "cold-1.log", "cold-2.log",
)
JSONS = (
    "candidate.json", "real-ntfs-substrate.json",
    "full-process.json", "result.json",
)
MEMBERS = BINARIES | set(LOGS) | set(JSONS)
HASH64 = re.compile(r"[0-9a-f]{64}\Z")
COMMIT = re.compile(r"[0-9a-f]{40}\Z")
TYPED = re.compile(rb"(?m)^stock_sram=([0-9a-f]{16384})\r?$")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def must(condition: bool, explanation: str) -> None:
    if not condition:
        raise ValueError("QA02_NAMED_REAL_NTFS_SOURCE_REJECTED: " + explanation)


def read_json(z: zipfile.ZipFile, name: str) -> dict:
    obj = json.loads(z.read(name).decode("utf-8-sig"))
    must(type(obj) is dict, "invalid original JSON " + name)
    return obj


def audit(
    path: Path,
    original_artifact_sha: str,
    expected_source: str,
    expected_cmd: str,
    expected_fixture: str,
    expected_rom: str,
) -> dict:
    must(type(expected_source) is str and
         COMMIT.fullmatch(expected_source) is not None,
         "expected exact 40-character tested Git commit")
    for name, value in (
        ("artifact", original_artifact_sha), ("CMD", expected_cmd),
        ("native fixture", expected_fixture), ("USA ROM", expected_rom),
    ):
        must(type(value) is str and HASH64.fullmatch(value) is not None,
             "missing explicit independent " + name + " identity")
    must(path.is_file() and not path.is_symlink() and
         0 < path.stat().st_size <= 1_000_000 and
         sha(path.read_bytes()) == original_artifact_sha,
         "actual GitHub Actions original artifact absent or changed")
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        must(len(entries) == 25 and
             {i.filename for i in entries} == MEMBERS and
             sum(i.file_size for i in entries) <= 3_000_000 and
             archive.testzip() is None,
             "original exact 25 source members / CRC / length not valid")
        for item in entries:
            mode = stat.S_IFMT(item.external_attr >> 16)
            must(
                not item.is_dir() and not (item.flag_bits & 1) and
                mode in (0, stat.S_IFREG) and item.file_size > 0 and
                not item.filename.startswith("/") and
                "\\" not in item.filename and
                ".." not in item.filename.split("/"),
                "untrusted/unsafe original Actions ZIP entry " + item.filename,
            )
        original = {name: archive.read(name) for name in BINARIES}
        candidate = read_json(archive, "candidate.json")
        os_info = read_json(archive, "real-ntfs-substrate.json")
        full = read_json(archive, "full-process.json")
        result = read_json(archive, "result.json")
        expected_values = {
            "cmd_sha256": expected_cmd,
            "fixture_sha256": expected_fixture,
            "original_rom_sha256": expected_rom,
        }
        for key, value in expected_values.items():
            must(candidate.get(key) == value,
                 "original candidate identity mismatch " + key)
        must(
            type(candidate.get("seed_sha256")) is str and
            HASH64.fullmatch(candidate["seed_sha256"]) is not None and
            type(candidate.get("base")) is dict and
            set(candidate["base"]) == set(CANONICAL),
            "missing source original fixture or base receipt",
        )
        receipts = result.get("exact_before_full_two_cold_binary_members")
        must(
            result.get("schema") == "ur-real-original-cmd-ntfs-disk-full/1" and
            type(receipts) is dict and
            set(receipts) == {
                f"{stage}.{field}.bin"
                for stage in STAGES for field in CANONICAL
            } and
            result.get("actual_isolated_vhd_ntfs_full") is True and
            result.get("actual_native_cmd_exit8_during_original_guest_save") is True and
            result.get("original_cmd_sha256") == expected_cmd and
            result.get("original_fixture_sha256") == expected_fixture and
            result.get("human_operator") is False and
            result.get("real_power_loss_or_partial_write") is False and
            type(result.get("release_gate_credit")) is int and
            result["release_gate_credit"] == 0,
            "source schema, scoped claim or 16 binary receipt set invalid",
        )
        for name, binary in original.items():
            leaf = name.split("/", 1)[1]
            receipt = receipts[leaf]
            must(
                type(receipt) is dict and
                set(receipt) == {"bytes", "sha256"} and
                type(receipt["bytes"]) is int and
                receipt["bytes"] == len(binary) and
                receipt["sha256"] == sha(binary),
                "source original binary hash/length mismatch " + name,
            )
        for field in CANONICAL:
            original_bytes = original[f"source-bytes/before.{field}.bin"]
            base = candidate["base"][field]
            must(
                type(base) is dict and
                type(base.get("bytes")) is int and
                base["bytes"] == len(original_bytes) and
                base.get("sha256") == sha(original_bytes),
                "initial exact source baseline disagrees " + field,
            )
            for stage in STAGES[1:]:
                must(
                    original[f"source-bytes/{stage}.{field}.bin"] == original_bytes,
                    "actual Windows fault or cold boot altered " + field,
                )
        raw = original["source-bytes/before.raw.bin"]
        typed = original["source-bytes/before.typed.bin"]
        matches = TYPED.findall(typed)
        must(
            len(raw) == 8192 and
            typed.startswith(b"UR-HOST-PROFILE/5\n") and
            typed.count(b"profile=native-ci-rider\n") == 1 and
            len(matches) == 1 and
            bytes.fromhex(matches[0].decode("ascii")) == raw,
            "original named native typed state does not match 8KiB SRAM",
        )
        must(
            original["source-bytes/before.catalog.bin"].startswith(
                b"UR-PROFILE-CATALOG/1\n"
            ) and
            original["source-bytes/before.selector.bin"].startswith(
                b"UR-HOST-STATE/6\n"
            ),
            "source catalog/selector schema was replaced",
        )
        must(
            os_info.get("schema") ==
                "ur-product-source-real-win32-ntfs-diskfull-substrate/1" and
            os_info.get("actual_ephemeral_ntfs_vhdx") is True and
            os_info.get("original_source_warm_boot_completed_before_fill") is True and
            os_info.get("tested_commit") == expected_source and
            type(os_info.get("fresh_process_os_error")) is int and
            os_info["fresh_process_os_error"] == 112 and
            type(os_info.get("capacity_megabytes")) is int and
            os_info["capacity_megabytes"] == 128 and
            type(os_info.get("original_free_bytes")) is int and
            os_info["original_free_bytes"] > 8192 and
            type(os_info.get("accepted_filler_bytes")) is int and
            0 < os_info["accepted_filler_bytes"] <= os_info["original_free_bytes"] and
            os_info.get("product_not_release_qa") is True and
            os_info.get("power_loss_or_short_write") is False and
            type(os_info.get("release_gate_credit")) is int and
            os_info["release_gate_credit"] == 0,
            "genuine isolated Win32 process 112 not independently sourced",
        )
        must(
            type(full.get("native_cmd_exit")) is int and
            full["native_cmd_exit"] == 8 and
            full.get("full_original_raw_sha256") == sha(raw) and
            full.get("before_raw_sha256") == sha(raw) and
            full.get("original_full_ntfs_cmd_sha256") == expected_cmd and
            full.get("original_guest_save_message") is True and
            full.get("original_game_race_armed") is True and
            full.get("canonical_equal_before_after") is True and
            type(full.get("qa_gate_credit")) is int and
            full["qa_gate_credit"] == 0,
            "guest race/exit8/full-volume original process proof absent",
        )
        warm = archive.read("warm.log")
        live = archive.read("full-ntfs-original-CMD.log")
        must(
            b"UR_BALDOSA_NATIVE_PROFILE APPLIED profile=native-ci-rider" in warm and
            b"UR_BALDOSA_NATIVE_PAUSE ARMED guest=2200" in live and
            b"UR_BALDOSA_NATIVE_PAUSE_MENU QUIT_QUEUED=1" in live and
            b"UR-BALDOSA-SAVE-FAILED:" in live and
            b"UR-BALDOSA-RECOVERY-COMMITTED:" not in live,
            "original CMD guest save and player warning were not observed",
        )
        for idx in (1, 2):
            log = archive.read(f"cold-{idx}.log")
            must(
                b"UR_BALDOSA_NATIVE_PROFILE APPLIED profile=native-ci-rider" in log and
                b"UR-BALDOSA-STARTUP-PROFILE-REJECTED" not in log and
                b"UR-BALDOSA-RECOVERY-COMMITTED:" not in log,
                "real original Windows cold game failed " + str(idx),
            )
    return {
        "schema": "UR-QA02-INDEPENDENT-NAMED-WIN32-NTFS-FULL/1",
        "original_actions_zip_sha256": original_artifact_sha,
        "exact_tested_product_merge": expected_source,
        "original_CMD_sha256": expected_cmd,
        "verified_canonical_source_objects": len(BINARIES),
        "genuine_second_process_OS_error": 112,
        "original_native_game_exit": 8,
        "exact_canonical_bytes_preserved_over_two_cold_boots": True,
        "complete_named_typed_CAS_storage_faults_accepted": False,
        "physical_owner_or_power_loss_accepted": False,
        "release_gate_credit": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--source-sha256", required=True)
    parser.add_argument("--cmd-sha256", required=True)
    parser.add_argument("--fixture-sha256", required=True)
    parser.add_argument("--rom-sha256", required=True)
    args = parser.parse_args()
    try:
        result = audit(
            args.zip, args.sha256, args.source_sha256,
            args.cmd_sha256, args.fixture_sha256, args.rom_sha256,
        )
    except (ValueError, TypeError, KeyError, OSError, UnicodeError,
            zipfile.BadZipFile, json.JSONDecodeError) as err:
        parser.exit(2, str(err) + "\n")
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
