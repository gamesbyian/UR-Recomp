#!/usr/bin/env python3
"""Independent read-only Win32 QA-02 raw/typed fault archive consumer.

Checks archived bytes/producer logs, NEVER proves execution, Win32 source/PE,
physical hardware, power-loss atomicity or a release-quality gate. Intended
for externally SHA-pinned original and next-candidate evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import zipfile
from pathlib import Path

LABELS = ("raw-sram", "typed-profile", "selector", "roster")
SOURCE = re.compile(r"[0-9a-f]{40}\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")
MAX_ARCHIVE_BYTES = 1_000_000


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError("QA02_SNAPSHOT_REJECTED: " + reason)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def difference_count(a: bytes, b: bytes) -> int:
    return sum(x != y for x, y in zip(a, b)) + abs(len(a) - len(b))


def typed_stock_sram(data: bytes) -> tuple[bytes, int]:
    lines = data.decode("ascii").splitlines()
    require(bool(lines) and lines[0] == "UR-HOST-PROFILE/5",
            "typed format not source-qualified")
    sram = [line[11:] for line in lines if line.startswith("stock_sram=")]
    gen = [line[11:] for line in lines if line.startswith("generation=")]
    require(len(sram) == 1 and len(gen) == 1 and
            re.fullmatch(r"[0-9a-f]{16384}", sram[0]) is not None and
            re.fullmatch(r"[0-9]+", gen[0]) is not None,
            "missing or invalid 8192-byte typed SRAM and generation")
    return bytes.fromhex(sram[0]), int(gen[0])


def inspect(archive: Path, expected_sha: str, mode: str, *,
            source: str = "", exe: str = "") -> dict:
    require(mode in ("historic", "unjournaled", "journaled"), "unsupported case")
    require(SHA.fullmatch(expected_sha) is not None,
            "whole original Actions ZIP SHA256 is required")
    require(archive.is_file() and not archive.is_symlink() and
            0 < archive.stat().st_size <= MAX_ARCHIVE_BYTES,
            "ZIP missing, redirected or oversized")
    require(digest(archive.read_bytes()) == expected_sha,
            "actual archive ZIP differs from external digest")
    stages = ("before", "after") if mode == "historic" else ("before", "crash", "after")
    expected = {f"{label}.{stage}.bin" for label in LABELS for stage in stages}
    expected.update(("file-receipt.json", "crash.log",
                     "cold-recovery.log" if mode == "journaled" else "cold-refusal.log"))
    if mode == "historic":
        expected.add("qa02-exact-owner-receipt.json")
    elif mode == "journaled":
        expected.update(("intent.crash.bin", "intent.recovered-receipt.bin",
                         "intent-receipt.json", "second-cold-recovery-boot.log"))
    with zipfile.ZipFile(archive) as z:
        members = z.infolist()
        require(len(members) == len(expected) and
                {m.filename for m in members} == expected,
                "unrecognized, missing or duplicated ZIP member")
        require(sum(m.file_size for m in members) <= MAX_ARCHIVE_BYTES,
                "ZIP members exceed evidence budget")
        for m in members:
            kind = stat.S_IFMT(m.external_attr >> 16)
            require(not m.is_dir() and not m.flag_bits & 1 and
                    kind in (0, stat.S_IFREG), "unsafe ZIP entry")
        require(z.testzip() is None, "ZIP CRC validation failed")
        raw_files = {name: z.read(name) for name in expected}
    receipt = json.loads(raw_files["file-receipt.json"].decode("utf-8"))
    # Producer stores the intent metadata in its own disjoint receipt,
    # leaving the 4-file before/crash/after manifest unmodified.
    expected_receipt = set(LABELS)
    require(isinstance(receipt, dict) and set(receipt) == expected_receipt,
            "incorrect file-receipt population")
    files = {}
    for label in LABELS:
        stage_files = {stage: raw_files[f"{label}.{stage}.bin"] for stage in stages}
        measurements = receipt[label]
        require(isinstance(measurements, dict), "invalid file receipt")
        for stage, binary in stage_files.items():
            require(measurements.get(stage + "_sha256") == digest(binary) and
                    measurements.get(stage + "_bytes") == len(binary),
                    f"{label} {stage} declared SHA/length mismatch")
        require(measurements.get("changed_byte_count") ==
                difference_count(stage_files["before"], stage_files["after"]),
                f"{label} false change count")
        if mode != "historic":
            require(measurements.get("crash_changed_byte_count") ==
                    difference_count(stage_files["before"], stage_files["crash"]),
                    f"{label} false crash change count")
        files[label] = stage_files
    raw = files["raw-sram"]
    typed = files["typed-profile"]
    require(all(len(b) == 8192 for b in raw.values()),
            "raw SRAM is not exactly 8192 bytes")
    old_sram, old_gen = typed_stock_sram(typed["before"])
    require(old_sram == raw["before"], "baseline raw/typed mismatch")
    crash_raw = raw["after"] if mode == "historic" else raw["crash"]
    require(difference_count(raw["before"], crash_raw) > 0,
            "no genuine raw SRAM changed at the writer boundary")
    for label in ("selector", "roster"):
        require(all(v == files[label]["before"] for v in files[label].values()),
                f"{label} mutated during recovery")
    log = raw_files["crash.log"].decode("utf-8", errors="replace")
    require(log.count("UR_BALDOSA_NATIVE_PAUSE ARMED guest=1952 live_race=1") == 1 and
            log.count("UR_BALDOSA_NATIVE_PROFILE QA_CRASH_AFTER_RAW_WRITE exit=86 typed_checkpoint=0") == 1,
            "missing exact original guest crash boundary markers")
    if mode == "historic":
        require(SOURCE.fullmatch(source) is not None and
                SHA.fullmatch(exe) is not None,
                "external original source SHA and executable SHA are mandatory")
        meta = json.loads(raw_files["qa02-exact-owner-receipt.json"].decode("utf-8"))
        require(meta.get("schema") == "qa02-nominated-owner-real-win32-crash-byte-receipt/1" and
                meta.get("tested_source") == source and
                meta.get("original_candidate_exe_sha256") == exe and
                meta.get("native_process_result", {}).get("forced_process_exit_code") == 86,
                "original exact Windows source/PE report differs")
        cold = raw_files["cold-refusal.log"].decode("utf-8", errors="replace")
        require(typed["before"] == typed["after"] and
                "selected_profile_sram_not_initialized" in cold and
                "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM" not in cold,
                "historic negative cold refusal altered or silently repaired")
    elif mode == "unjournaled":
        require(typed["crash"] == typed["before"] == typed["after"] and
                raw["after"] == raw["crash"],
                "unjournaled snapshots mutated canonical typed or raw on refusal")
        cold = raw_files["cold-refusal.log"].decode("utf-8", errors="replace")
        require("selected_profile_sram_not_initialized" in cold and
                "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM" not in cold,
                "unjournaled cold retry silently promoted unknown raw")
    else:
        require(typed["crash"] == typed["before"] and
                raw["after"] == raw["crash"] and
                typed["after"] != typed["before"],
                "journaled stage bytes do not show a typed-only cold replay")
        next_sram, next_gen = typed_stock_sram(typed["after"])
        require(next_sram == raw["after"] and next_gen > old_gen,
                "cold typed checkpoint does not match exact source guest SRAM")
        cold = raw_files["cold-recovery.log"].decode("utf-8", errors="replace")
        require(cold.count("RECOVERY_RECONCILED exact_staged_guest_sram=1 no_records=1") == 1 and
                "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM" in cold and
                "UR_BALDOSA_NATIVE_PROFILE REJECTED" not in cold,
                "source-log cold restart lacks actual recovered guest boot")
        # The original Win32 intent carries complete old/new *typed* state,
        # not merely a boolean that the recovery producer can self-report.
        # Only those exact typed images may authorize replay.
        intent = raw_files["intent.crash.bin"]
        archived = raw_files["intent.recovered-receipt.bin"]
        info = json.loads(raw_files["intent-receipt.json"].decode("utf-8"))
        require(isinstance(info, dict) and
                set(info) == {"crash_sha256", "receipt_sha256", "bytes",
                              "byte_identical", "pending_retired"} and
                info["crash_sha256"] == digest(intent) and
                info["receipt_sha256"] == digest(archived) and
                info["bytes"] == len(intent) and
                info["byte_identical"] is True and
                info["pending_retired"] is True and intent == archived,
                "crash intent and recovered immutable receipt differ")
        marker = b"UR-BALDOSA-NATIVE-SRAM-INTENT/1\n"
        require(intent.startswith(marker) and len(intent) <= 100_000,
                "invalid durable prewrite-intent version or size")
        rest = intent[len(marker):]
        parts = rest.split(b"\n", 2)
        require(len(parts) == 3 and
                all(re.fullmatch(rb"[0-9]{1,8}", p) is not None for p in parts[:2]),
                "malformed typed-intent frame lengths")
        old_length, new_length = int(parts[0]), int(parts[1])
        require(old_length > 0 and new_length > 0 and
                old_length + new_length == len(parts[2]) and
                parts[2][:old_length] == typed["before"] and
                parts[2][old_length:] == typed["after"],
                "durable intent does not authorize exact before/after typed checkpoint")
        second = raw_files["second-cold-recovery-boot.log"].decode(
            "utf-8", errors="replace")
        require("UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM" in second and
                "UR_BALDOSA_NATIVE_PROFILE REJECTED" not in second and
                "UR_BALDOSA_NATIVE_PROFILE RECOVERY_RECONCILED" not in second,
                "second cold guest replay failed or re-published typed checkpoint")
    return {
        "schema": "qa02-independent-win32-fault-snapshot-check/1",
        "case": mode,
        "verified_outer_zip_sha256": expected_sha,
        "changed_guest_raw_bytes": difference_count(raw["before"], crash_raw),
        "reconciled_typed": mode == "journaled",
        "exact_intent_and_receipt_verified": mode == "journaled",
        "second_cold_source_boot_observed": mode == "journaled",
        "release_gate_credit": 0,
        "physical_test": False,
        "limits": "Independently validates byte receipts and source log markers only; does not independently execute Windows, bind source/PE, prove power-cut durability or physical hardware",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--zip", type=Path, required=True)
    p.add_argument("--sha256", required=True)
    p.add_argument("--case", choices=("historic", "unjournaled", "journaled"), required=True)
    p.add_argument("--source", default="")
    p.add_argument("--exe-sha256", default="")
    args = p.parse_args()
    try:
        result = inspect(args.zip, args.sha256, args.case,
                         source=args.source, exe=args.exe_sha256)
    except (ValueError, TypeError, KeyError, IndexError, zipfile.BadZipFile,
            UnicodeError, OSError) as e:
        p.exit(2, f"QA02_SNAPSHOT_REJECTED: {e}\n")
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
