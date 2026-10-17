#!/usr/bin/env python3
"""Independent read-only QA of original Win32 packaged invalid-S refusal.

Requires pinned original GitHub Actions ZIP and packaged CMD digests.
No human keyboard, power-cut, OS disk-full or release gate credit is inferred.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import stat
import zipfile

LABELS = ("a-raw", "a-typed", "b-raw", "b-typed",
          "c-raw", "catalog", "selector")
STAGES = ("before-invalid-S", "after-invalid-S", "cold-Q-after-invalid-S")
SOURCE = {f"source-bytes/{stage}.{label}.bin"
          for stage in STAGES for label in LABELS}
SOURCE.add("source-bytes/unrelated-C-original-typed.bin")
OTHER = {"invalid-S-result.json", "invalid-S.log",
         "cold-Q-after-invalid-S.log", "fixture.log",
         "invalid-S-key.injection.log", "invalid-S-profile.injection.log",
         "cold-Q-key.injection.log"}
EXPECTED = SOURCE | OTHER
SHA = re.compile(r"[0-9a-f]{64}\Z")
MAX_BYTES = 500_000


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError("QA02_INVALID_S_REJECTED: " + reason)


def stock(typed: bytes, identity: str) -> bytes:
    require(typed.startswith(b"UR-HOST-PROFILE/5\n") and
            typed.count(b"profile=" + identity.encode() + b"\n") == 1,
            "wrong original typed profile identity " + identity)
    matches = re.findall(rb"(?m)^stock_sram=([0-9a-f]{16384})\r?$", typed)
    require(len(matches) == 1, "missing/duplicate complete typed SRAM")
    return bytes.fromhex(matches[0].decode("ascii"))


def audit(path: Path, original_sha: str, cmd_sha: str) -> dict:
    require(type(original_sha) is str and type(cmd_sha) is str and
            SHA.fullmatch(original_sha) is not None and
            SHA.fullmatch(cmd_sha) is not None,
            "require external original Actions and CMD SHA256s")
    require(path.is_file() and not path.is_symlink() and
            0 < path.stat().st_size <= MAX_BYTES and
            digest(path.read_bytes()) == original_sha,
            "original Actions ZIP missing, redirected, oversized or mismatched")
    with zipfile.ZipFile(path) as z:
        info = z.infolist()
        require(len(info) == 29 and len(EXPECTED) == 29 and
                {i.filename for i in info} == EXPECTED and
                sum(i.file_size for i in info) <= MAX_BYTES and
                z.testzip() is None,
                "original ZIP inventory, uniqueness, size or CRC invalid")
        for item in info:
            mode = stat.S_IFMT(item.external_attr >> 16)
            require(not item.is_dir() and not (item.flag_bits & 1) and
                    mode in (0, stat.S_IFREG) and item.file_size > 0 and
                    not item.filename.startswith("/") and
                    not "\\" in item.filename,
                    "unsafe original source member " + item.filename)
        report_bytes = z.read("invalid-S-result.json")
        report = json.loads(report_bytes)
        require(isinstance(report, dict) and
                report_bytes in ((json.dumps(report, indent=2, sort_keys=True) +
                                  "\n").encode(),) and
                report.get("schema") ==
                "ur-win32-interactive-original-cmd-invalid-s/1" and
                report.get("exact_original_extracted_cmd_sha256") == cmd_sha and
                report.get("invalid_requested_profile") in (
                    "native-ci-no-such-racer", "native-ci-second") and
                report.get("registered_target_corrupt_sram", False) in (
                    False, True) and
                type(report.get("registered_target_corrupt_sram", False)) is bool and
                (report.get("registered_target_corrupt_sram", False) is
                 (report.get("invalid_requested_profile") == "native-ci-second")) and
                report.get("real_win32_console_keys") ==
                ["S", "literal target+Enter", "cold Q"] and
                all(report.get(key) is True for key in (
                    "no_canonical_data_mutated",
                    "refusal_before_any_guest_frame",
                    "second_original_cold_process_rejected_damaged_A_exit_7",
                    "unrelated_C_typed_remained_absent")) and
                report.get("human_operator") is False and
                type(report.get("release_gate_credit")) is int and
                report["release_gate_credit"] == 0,
                "original report scope, CMD provenance or choice not qualified")
        target = report["invalid_requested_profile"]
        registered = report.get("registered_target_corrupt_sram", False)
        receipts = report.get("source_bytes_sha256")
        require(type(receipts) is dict and
                set(receipts) ==
                {name.removeprefix("source-bytes/") for name in SOURCE},
                "original SHA receipt set wrong")
        binary: dict[str, bytes] = {}
        for member in SOURCE:
            value = z.read(member)
            key = member.removeprefix("source-bytes/")
            meta = receipts[key]
            require(type(meta) is dict and
                    set(meta) == {"bytes", "sha256"} and
                    type(meta["bytes"]) is int and
                    meta["bytes"] == len(value) and
                    meta["sha256"] == digest(value),
                    "source byte receipt mismatch " + member)
            binary[key] = value

        def get(stage: str, label: str) -> bytes:
            return binary[f"{stage}.{label}.bin"]

        for name in LABELS:
            old = get(STAGES[0], name)
            require(get(STAGES[1], name) == old and
                    get(STAGES[2], name) == old,
                    "invalid choice/cold exit mutated " + name)
        a = get(STAGES[0], "a-raw")
        b = get(STAGES[0], "b-raw")
        c = get(STAGES[0], "c-raw")
        require(all(len(x) == 8192 for x in (a, b, c)) and
                len({a, b, c}) == 3,
                "original three racers lack distinct 8192-byte SRAM")
        typed_a = stock(get(STAGES[0], "a-typed"), "native-ci-rider")
        typed_b = stock(get(STAGES[0], "b-typed"), "native-ci-second")
        typed_c = stock(binary["unrelated-C-original-typed.bin"],
                        "native-ci-third")
        require(typed_c == c and
                typed_a[:16] == a[:16] and
                (typed_b == b if not registered else
                 (typed_b[:16] == b[:16] and
                  [i for i, (x, y) in enumerate(zip(typed_b, b))
                   if x != y] == [0x0699] and
                  b[0x0699] == (typed_b[0x0699] ^ 0x52))) and
                [i for i, (x, y) in enumerate(zip(typed_a, a))
                 if x != y] == [0x0711] and
                a[0x0711] == (typed_a[0x0711] ^ 0x35),
                "real source fixture A mismatch / B/C healthy state incorrect")
        selector = get(STAGES[0], "selector")
        catalog = get(STAGES[0], "catalog")
        require(selector.startswith(b"UR-HOST-STATE/6\n") and
                selector.count(b"profile=native-ci-rider\n") == 1 and
                b"native-ci-no-such-racer" not in selector and
                catalog.startswith(b"UR-PROFILE-CATALOG/1\n") and
                b"native-ci-no-such-racer" not in catalog and
                all(catalog.count(x + b"|") == 1 for x in (
                    b"native-ci-rider", b"native-ci-second",
                    b"native-ci-third")),
                "invalid ID was registered or source selector changed")
        for logfile in ("invalid-S-key.injection.log",
                        "invalid-S-profile.injection.log",
                        "cold-Q-key.injection.log"):
            log = z.read(logfile).decode("utf-8").replace("\r\n", "\n")
            require(log.lstrip().startswith("exit=0\n") and
                    "Traceback" not in log and "PermissionError" not in log,
                    "real Win32 console injector did not succeed: " + logfile)
        start = z.read("invalid-S.log").decode("utf-8")
        cold = z.read("cold-Q-after-invalid-S.log").decode("utf-8")
        fixture = z.read("fixture.log").decode("utf-8")
        require(fixture.count("UR_BALDOSA_NATIVE_PROFILE_FIXTURE") == 3 and
                start.count("Explicit recovery choice [R/T/S/Q]: S") == 1 and
                start.count("Healthy registered profile ID:") == 1 and
                start.count("UR-BALDOSA-STARTUP-PROFILE-REJECTED:") == 1 and
                start.count("UR-BALDOSA-RECOVERY-REFUSED:") == 1 and
                "choice=healthy status=3" in start and
                f"next_profile={target} completed=0" in start and
                start.count("UR-BALDOSA-RECOVERY-COMMITTED:") == 0 and
                "UR_BALDOSA_NATIVE_PROFILE APPLIED" not in start and
                "first frame simulated" not in start and
                cold.count("Explicit recovery choice [R/T/S/Q]: Q") == 1 and
                cold.count("UR-BALDOSA-STARTUP-PROFILE-REJECTED:") == 1 and
                "UR-BALDOSA-RECOVERY-COMMITTED:" not in cold and
                "UR_BALDOSA_NATIVE_PROFILE APPLIED" not in cold and
                "first frame simulated" not in cold,
                "actual original CMD refused incorrectly or booted guest")
    return {
        "schema": "ur-independent-original-win32-invalid-S/1",
        "original_actions_zip_sha256": original_sha,
        "original_packaged_cmd_sha256": cmd_sha,
        "original_binary_sha_and_length_receipts": len(SOURCE),
        "canonical_before_refused_cold_files_byte_identical": 21,
        "S_key_profile_text_and_followup_Q_console_receipts": 3,
        "invalid_target_refused_without_guest_frame": True,
        "invalid_target_type": (
            "registered_corrupt_raw" if registered else "unregistered_profile"),
        "registered_corrupt_B_one_byte": registered,
        "third_typed_on_disk_absence_independently_verified": False,
        "physical_human_operator_tested": False,
        "real_storage_fault_tested_by_this_subtest": False,
        "release_gate_credit": 0,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--zip", required=True, type=Path)
    p.add_argument("--sha256", required=True)
    p.add_argument("--cmd-sha256", required=True)
    args = p.parse_args()
    try:
        result = audit(args.zip, args.sha256, args.cmd_sha256)
    except (ValueError, TypeError, KeyError, OSError, UnicodeError,
            zipfile.BadZipFile, json.JSONDecodeError) as exc:
        p.exit(2, str(exc) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
