#!/usr/bin/env python3
"""Independent read-only QA of original hosted Windows interactive CMD Q.

External artifact SHA and CMD SHA are mandatory. This audits original
canonical binary stages and console evidence, not physical user input,
R/T/S recovery, original-game parity or release acceptance.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import stat
import zipfile

STATES = ("catalog", "raw", "selector", "typed")
BINS = {f"source-bytes/{stage}.{name}.bin"
        for stage in ("before-Q", "after-Q") for name in STATES}
EXTRAS = {"interactive-console.log", "key-injection.log",
          "original-fixture.log", "interactive-q-result.json"}
MEMBERS = BINS | EXTRAS
HASH = re.compile(r"[0-9a-f]{64}\Z")
LIMIT = 300_000


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def need(value: bool, why: str) -> None:
    if not value:
        raise ValueError("QA02_INTERACTIVE_Q_REJECTED: " + why)


def audit(path: Path, external_sha: str, cmd_sha: str) -> dict:
    need(bool(HASH.fullmatch(external_sha)) and bool(HASH.fullmatch(cmd_sha)),
         "require independently pinned Actions ZIP and original CMD SHA")
    need(path.is_file() and not path.is_symlink() and 0 < path.stat().st_size <= LIMIT,
         "original Actions artifact unavailable, redirected or oversized")
    need(sha(path.read_bytes()) == external_sha, "original Actions ZIP SHA changed")
    with zipfile.ZipFile(path) as zipped:
        infos = zipped.infolist()
        need(len(infos) == len(MEMBERS) and
             {entry.filename for entry in infos} == MEMBERS,
             "original archive member set/uniqueness differs")
        need(sum(entry.file_size for entry in infos) <= LIMIT,
             "original decompressed bytes exceed limit")
        for entry in infos:
            mode = stat.S_IFMT(entry.external_attr >> 16)
            need(not entry.is_dir() and not (entry.flag_bits & 1) and
                 mode in (0, stat.S_IFREG) and entry.file_size > 0,
                 "unsafe, encrypted or empty member " + entry.filename)
        need(zipped.testzip() is None, "original ZIP member CRC failure")
        binary = {name: zipped.read(name) for name in BINS}
        for name in STATES:
            need(binary[f"source-bytes/before-Q.{name}.bin"] ==
                 binary[f"source-bytes/after-Q.{name}.bin"],
                 "Q modified original canonical " + name)
        raw = binary["source-bytes/before-Q.raw.bin"]
        typed = binary["source-bytes/before-Q.typed.bin"]
        need(len(raw) == 8192 and typed.startswith(b"UR-HOST-PROFILE/5\n"),
             "canonical native 8192-byte/typed version mismatch")
        matches = re.findall(rb"(?m)^stock_sram=([0-9a-f]{16384})\r?$", typed)
        need(len(matches) == 1, "original typed profile lacks one full 8192-byte stock SRAM")
        committed = bytes.fromhex(matches[0].decode("ascii"))
        need(committed[:16] == raw[:16] and
             sum(a != b for a, b in zip(committed, raw)) == 1,
             "legacy raw is not the one-byte genuine mismatch from typed")
        result_bytes = zipped.read("interactive-q-result.json")
        result = json.loads(result_bytes)
        canon = (json.dumps(result, indent=2, sort_keys=True) + "\n").encode()
        need(result_bytes in (canon, canon.replace(b"\n", b"\r\n")),
             "noncanonical Q result JSON")
        need(result.get("schema") == "ur-win32-interactive-original-cmd-q/1" and
             result.get("genuine_win32_console_key_event") == "Q" and
             type(result.get("child_process_exit_code")) is int and
             result["child_process_exit_code"] == 7 and
             result.get("original_persisted_bytes_equal_after_Q") is True and
             result.get("eight_original_before_after_binary_members") is True and
             result.get("legacy_raw_signature_preserved") is True and
             result.get("manual_repair_archive_created") is False and
             result.get("second_guest_or_default_fallback") is False and
             type(result.get("independent_qa_release_credit")) is int and
             result["independent_qa_release_credit"] == 0,
             "source return-code or Q refusal contract invalid")
        need(result.get("exact_extracted_cmd_sha256") == cmd_sha,
             "source-executed CMD does not match separately pinned package")
        receipts = result.get("source_bytes_sha256")
        need(isinstance(receipts, dict) and set(receipts) ==
             {name.removeprefix("source-bytes/") for name in BINS},
             "before/after binary source SHA receipts incomplete")
        for member in BINS:
            name = member.removeprefix("source-bytes/")
            meta = receipts[name]
            need(type(meta) is dict and
                 type(meta.get("bytes")) is int and meta["bytes"] == len(binary[member]) and
                 meta.get("sha256") == sha(binary[member]),
                 "original receipt missing or does not match " + member)
        final = result.get("typed_raw_selector_catalog_sha256")
        need(type(final) is dict and set(final) == set(STATES) and
             all(final[name] == sha(binary[f"source-bytes/after-Q.{name}.bin"])
                 for name in STATES), "final canonical SHA map differs from original bytes")
        log = zipped.read("interactive-console.log").decode("utf-8")
        keylog = zipped.read("key-injection.log").decode("utf-8")
        fixture = zipped.read("original-fixture.log").decode("utf-8")
        need(log.count("Explicit recovery choice [R/T/S/Q]:") == 1 and
             log.count("UR-BALDOSA-STARTUP-PROFILE-REJECTED:") == 1 and
             "Q: Exit without changing any saved data." in log and
             "UR-BALDOSA-RECOVERY-COMMITTED:" not in log and
             "UR-BALDOSA-FIRST-RACER:" not in log and
             "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM" not in log and
             "ERROR: Access is denied." not in log,
             "source original CMD choice prompt or guest refusal missing")
        need(keylog.lstrip().startswith("exit=0\n") and
             "Traceback" not in keylog and "PermissionError" not in keylog,
             "actual Win32 console key injector did not succeed")
        need("UR_BALDOSA_NATIVE_PROFILE_FIXTURE" in fixture and
             "sram=8192" in fixture, "genuine original fixture setup absent")
    return {
        "schema": "ur-independent-original-win32-interactive-Q/1",
        "actions_original_artifact_sha256": external_sha,
        "externally_pinned_actual_CMD_sha256": cmd_sha,
        "original_binary_snapshots_independently_rehashed": 8,
        "raw_changed_bytes_vs_committed_typed_before_Q": 1,
        "original_canonical_snapshot_sets_byte_identical_after_Q": True,
        "source_reported_exit_code": 7,
        "source_reported_real_console_key_event": "Q",
        "injection_log_reports_success": True,
        "operator_physically_typed_Q": False,
        "R_T_S_accepted": False,
        "clean_machine_or_physical_equipment_accepted": False,
        "source_or_PE_identity_verified_by_this_consumer": False,
        "release_gate_credit": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", required=True, type=Path)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--cmd-sha256", required=True)
    args = parser.parse_args()
    try:
        report = audit(args.zip, args.sha256, args.cmd_sha256)
    except (ValueError, OSError, UnicodeError, KeyError, TypeError,
            zipfile.BadZipFile, json.JSONDecodeError) as error:
        parser.exit(2, str(error) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
