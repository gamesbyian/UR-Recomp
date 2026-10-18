#!/usr/bin/env python3
"""Independent original Actions Windows CMD R/T recovery archive verifier.

Read-only source byte audit. Original Actions ZIP and original packaged CMD
SHA256 pins are required. This does not prove human keyboard operation,
electrical interruption, NTFS disk-full or release readiness.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import stat
from pathlib import Path
import zipfile

CHOICES = ("R", "T")
LABELS = ("catalog", "raw", "selector", "typed")
STAGES = ("before", "after", "cold1", "cold2")
SHA = re.compile(r"[0-9a-f]{64}\Z")
TOTAL_LIMIT = 600_000


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError("QA02_INTERACTIVE_RT_REJECTED: " + reason)


def binary_members(choice: str) -> set[str]:
    return {f"{choice}/source-bytes/{stage}-{choice}.{label}.bin"
            for stage in STAGES for label in LABELS} | {
                f"{choice}/source-bytes/manual-{choice}.bin"}


def log_members(choice: str) -> set[str]:
    return {f"{choice}/fixture.log", f"{choice}/interactive-{choice}.log",
            f"{choice}/interactive-{choice}.key.log",
            f"{choice}/cold-{choice}-1.log", f"{choice}/cold-{choice}-2.log",
            f"{choice}/result.json"}


def stock(typed: bytes) -> bytes:
    require(typed.startswith(b"UR-HOST-PROFILE/5\n"), "typed source format")
    matches = re.findall(rb"(?m)^stock_sram=([0-9a-f]{16384})\r?$", typed)
    require(len(matches) == 1, "typed source SRAM hex missing/duplicated")
    raw = bytes.fromhex(matches[0].decode("ascii"))
    require(len(raw) == 8192, "typed stock SRAM decoded wrong")
    return raw


def audit(path: Path, external_sha: str, cmd_sha: str) -> dict:
    require(bool(SHA.fullmatch(external_sha)) and bool(SHA.fullmatch(cmd_sha)),
            "require independently pinned original ZIP and packaged CMD SHA")
    require(path.is_file() and not path.is_symlink() and
            0 < path.stat().st_size <= TOTAL_LIMIT,
            "original archive missing/redirected/too large")
    require(sha(path.read_bytes()) == external_sha,
            "original Actions artifact SHA differs")
    expected = {"interactive-rt-result.json"}
    for choice in CHOICES:
        expected |= binary_members(choice) | log_members(choice)
    require(len(expected) == 47, "internal source inventory drift")
    with zipfile.ZipFile(path) as zipped:
        infos = zipped.infolist()
        require(len(infos) == 47 and
                {entry.filename for entry in infos} == expected,
                "original member population, names or uniqueness differ")
        require(sum(entry.file_size for entry in infos) <= TOTAL_LIMIT,
                "uncompressed original archive budget exceeded")
        for entry in infos:
            mode = stat.S_IFMT(entry.external_attr >> 16)
            require(not entry.is_dir() and not (entry.flag_bits & 1) and
                    mode in (0, stat.S_IFREG) and entry.file_size > 0,
                    "unsafe/empty original member " + entry.filename)
        require(zipped.testzip() is None, "ZIP CRC error")
        bundle = json.loads(zipped.read("interactive-rt-result.json"))
        require(isinstance(bundle, dict) and
                bundle.get("schema") == "ur-win32-interactive-original-cmd-rt/1" and
                bundle.get("tested_choices") == ["R", "T"] and
                bundle.get("physical_operator") is False and
                type(bundle.get("release_gate_credit")) is int and
                bundle["release_gate_credit"] == 0 and
                isinstance(bundle.get("results"), dict) and
                set(bundle["results"]) == set(CHOICES),
                "root source result schema/scope invalid")
        counted = 0
        for choice in CHOICES:
            prefix = choice + "/"
            result = json.loads(zipped.read(prefix + "result.json"))
            require(bundle["results"][choice] == result,
                    "root/child results disagree for " + choice)
            require(result.get("schema") == "ur-win32-interactive-original-cmd-rt/1" and
                    result.get("choice") == choice and
                    result.get("exact_extracted_cmd_sha256") == cmd_sha and
                    result.get("actual_console_key_injected") is True and
                    result.get("original_cmd_recovery_committed_once") is True and
                    result.get("original_first_frame_after_relaunch") is True and
                    result.get("original_first_frame_on_two_cold_boots") is True and
                    result.get("legacy_raw_byte_changes") == 1 and
                    result.get("manual_archive_exact_previous_raw_and_typed") is True and
                    result.get("unchanged_catalog_and_selector") is True and
                    type(result.get("independent_release_gate_credit")) is int and
                    result["independent_release_gate_credit"] == 0,
                    "source return/choice/commit policy invalid " + choice)
            receipts = result.get("source_before_after_and_cold_bytes")
            source_files = binary_members(choice)
            require(type(receipts) is dict and
                    set(receipts) == {
                        name.removeprefix(prefix + "source-bytes/")
                        for name in source_files},
                    "binary receipt set incorrect " + choice)
            binary = {}
            for member in source_files:
                value = zipped.read(member)
                name = member.removeprefix(prefix + "source-bytes/")
                receipt = receipts[name]
                require(type(receipt) is dict and
                        type(receipt.get("bytes")) is int and
                        receipt["bytes"] == len(value) and
                        receipt.get("sha256") == sha(value),
                        "binary source digest/length mismatch " + member)
                binary[name] = value
                counted += 1

            def get(stage: str, name: str) -> bytes:
                return binary[f"{stage}-{choice}.{name}.bin"]

            before_raw = get("before", "raw")
            before_typed = get("before", "typed")
            after_raw = get("after", "raw")
            after_typed = get("after", "typed")
            committed = stock(before_typed)
            require(len(before_raw) == 8192 and
                    before_raw[:16] == committed[:16] and
                    sum(a != b for a, b in zip(before_raw, committed)) == 1,
                    "not one legitimate raw-vs-typed mismatch " + choice)
            require(stock(after_typed) == after_raw and len(after_raw) == 8192,
                    "repair did not make typed equal raw " + choice)
            for name in ("catalog", "selector"):
                require(get("before", name) == get("after", name),
                        "unrelated authority modified " + choice + " " + name)
            if choice == "R":
                require(after_raw == before_raw and after_typed != before_typed,
                        "keep raw did not exclusively promote typed")
            else:
                require(after_raw == committed and after_typed == before_typed,
                        "restore typed changed committed metadata or incorrect raw")
            for name in LABELS:
                require(get("after", name) == get("cold1", name) ==
                        get("cold2", name),
                        "first/second cold guest mutated " + choice + " " + name)
            archive = binary[f"manual-{choice}.bin"]
            header = (b"UR-BALDOSA-MANUAL-SRAM-RECOVERY/1\n" +
                      str(len(before_typed)).encode() + b"\n1\n8192\n")
            require(archive == header + before_typed + before_raw,
                    "manual archive differs from exact old raw/typed " + choice)
            console = zipped.read(
                prefix + f"interactive-{choice}.log").decode("utf-8")
            injector = zipped.read(
                prefix + f"interactive-{choice}.key.log").decode("utf-8")
            fixture = zipped.read(prefix + "fixture.log").decode("utf-8")
            require(console.count("Explicit recovery choice [R/T/S/Q]:") == 1 and
                    f"Explicit recovery choice [R/T/S/Q]: {choice}" in console and
                    console.count("UR-BALDOSA-STARTUP-PROFILE-REJECTED:") == 1 and
                    console.count("UR-BALDOSA-RECOVERY-COMMITTED:") == 1 and
                    console.count("first frame simulated") == 1 and
                    "UR-BALDOSA-RECOVERY-REFUSED:" not in console and
                    "UR-BALDOSA-RECOVERY-RETRY-FAILED:" not in console,
                    "original interactive console wrong " + choice)
            require(injector.replace("\r\n", "\n").lstrip().startswith("exit=0\n") and
                    "Traceback" not in injector and
                    "PermissionError" not in injector,
                    "actual Win32 console key injector refused " + choice)
            require("UR_BALDOSA_NATIVE_PROFILE_FIXTURE" in fixture and
                    "sram=8192" in fixture,
                    "original native fixture provenance missing " + choice)
            for cold in (1, 2):
                log = zipped.read(
                    prefix + f"cold-{choice}-{cold}.log").decode("utf-8")
                require(log.count("first frame simulated") == 1 and
                        "Explicit recovery choice [R/T/S/Q]:" not in log and
                        "UR-BALDOSA-STARTUP-PROFILE-REJECTED:" not in log,
                        "fresh original cold guest failed " +
                        choice + " " + str(cold))
    return {
        "schema": "ur-independent-original-win32-interactive-RT/1",
        "original_GitHub_Actions_ZIP_sha256": external_sha,
        "separately_pinned_CMD_sha256": cmd_sha,
        "original_binary_members_independently_checked": counted,
        "observed_actual_key_choices": ["R", "T"],
        "both_manual_archives_exact_prewrite_original_bytes": True,
        "both_first_and_second_cold_canonical_snapshots_identical": True,
        "physical_operator_verified": False,
        "actual_disk_full_or_electrical_power_loss_verified": False,
        "S_or_Q_in_this_archive": False,
        "release_gate_credit": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", required=True, type=Path)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--cmd-sha256", required=True)
    args = parser.parse_args()
    try:
        result = audit(args.zip, args.sha256, args.cmd_sha256)
    except (ValueError, OSError, TypeError, KeyError, UnicodeError,
            zipfile.BadZipFile, json.JSONDecodeError) as error:
        parser.exit(2, str(error) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
