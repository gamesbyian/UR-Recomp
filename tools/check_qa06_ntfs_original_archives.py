#!/usr/bin/env python3
"""Independently inspect archived original-Windows real-NTFS fault evidence.

No execution or physical hardware assertions. Expected wrapper SHA pins must
come from independently maintained QA, not from the producer's own manifests.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import zipfile
from pathlib import Path

HEX40 = re.compile(r"[0-9a-f]{40}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
KINDS = ("raw", "typed", "catalog", "selector")
MAX_ARCHIVE_BYTES = 8 * 1024 * 1024


def require(ok: bool, why: str) -> None:
    if not ok:
        raise ValueError("QA06_NTFS_ARCHIVE_REJECTED: " + why)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def open_original(path: Path, expected: str) -> zipfile.ZipFile:
    require(HEX64.fullmatch(expected) is not None, "uncanonical outer digest")
    require(path.is_file() and not path.is_symlink(), "missing or redirected archive")
    require(0 < path.stat().st_size <= MAX_ARCHIVE_BYTES, "unbounded archive")
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for buf in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(buf)
    require(hasher.hexdigest() == expected, "external Actions wrapper hash mismatch")
    archive = None
    try:
        archive = zipfile.ZipFile(path)
        members = archive.infolist()
        require(0 < len(members) <= 1000, "archive member count")
        seen = set()
        total = 0
        for info in members:
            name = info.filename
            components = name.split("/")
            require(name not in seen and all(part not in ("", ".", "..") for part in components)
                    and not name.startswith("/") and "\\" not in name,
                    "duplicate or unsafe ZIP path")
            seen.add(name)
            mode = stat.S_IFMT(info.external_attr >> 16)
            require(not info.is_dir() and not info.flag_bits & 1
                    and mode in (0, stat.S_IFREG), "directory, symlink or encrypted entry")
            require(0 < info.file_size <= 1024 * 1024, "unexpected member size")
            total += info.file_size
            require(total <= 16 * 1024 * 1024, "unbounded expanded population")
        require(archive.testzip() is None, "ZIP CRC failure")
        return archive
    except Exception:
        if archive is not None:
            archive.close()
        raise


def parsed(archive: zipfile.ZipFile, name: str) -> dict:
    obj = json.loads(archive.read(name))
    require(type(obj) is dict, "invalid JSON object: " + name)
    return obj


def verified_bytes(archive: zipfile.ZipFile, entries: dict) -> dict[str, bytes]:
    require(type(entries) is dict and entries, "missing original-byte manifest")
    actual = {x.filename.removeprefix("source-bytes/") for x in archive.infolist()
              if x.filename.startswith("source-bytes/")}
    require(actual == set(entries), "missing/extra original raw file")
    result = {}
    for filename, rec in entries.items():
        require(type(filename) is str and type(rec) is dict, "malformed member receipt")
        require(type(rec.get("bytes")) is int and rec["bytes"] > 0
                and type(rec.get("sha256")) is str
                and HEX64.fullmatch(rec["sha256"]) is not None,
                "malformed size/SHA receipt")
        raw = archive.read("source-bytes/" + filename)
        require(len(raw) == rec["bytes"] and sha(raw) == rec["sha256"],
                "source byte mismatch: " + filename)
        result[filename] = raw
    return result


def fnv1a32(raw: bytes) -> str:
    """Guest BOOT_SRAM's actual byte-level FNV-1a32, not a producer digest."""
    result = 0x811C9DC5
    for value in raw:
        result = ((result ^ value) * 0x01000193) & 0xFFFFFFFF
    return f"{result:08x}"


def require_boot_log(archive: zipfile.ZipFile, filename: str, raw: bytes, *,
                     reconciled: bool) -> None:
    text = archive.read(filename).decode("utf-8", "replace")
    assert_line = ("UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM "
                   "profile=native-ci-rider bytes=8192 fnv=" + fnv1a32(raw))
    require(text.count(assert_line) == 1, "original guest boot raw SRAM digest mismatch: " + filename)
    marker = "UR_BALDOSA_NATIVE_PROFILE RECOVERY_RECONCILED"
    require((marker in text) is reconciled, "cold-process recovery chronology differs: " + filename)
    require("UR_BALDOSA_GUEST_SNAPSHOT frame=1" in text,
            "cold-process never executed guest frame: " + filename)


def stage(raw: dict[str, bytes], name: str) -> dict[str, bytes]:
    values = {k: raw[name + "." + k + ".bin"] for k in KINDS}
    require(len(values["raw"]) == 8192, "raw SRAM must be exactly 8192 bytes")
    return values


def typed_stock(typed: bytes) -> tuple[bytes, int]:
    lines = typed.decode("ascii").splitlines()
    require(lines and lines[0] == "UR-HOST-PROFILE/5", "unknown typed codec")
    sram = [line.removeprefix("stock_sram=") for line in lines
            if line.startswith("stock_sram=")]
    gen = [line.removeprefix("generation=") for line in lines
           if line.startswith("generation=")]
    require(len(sram) == len(gen) == 1 and len(sram[0]) == 16384
            and sram[0].lower() == sram[0]
            and re.fullmatch(r"[0-9a-f]+", sram[0]) is not None
            and gen[0].isdigit(), "bad typed raw/generation")
    return bytes.fromhex(sram[0]), int(gen[0])


def inspect(pre_path: Path, post_path: Path, *, pre_sha: str, post_sha: str,
            source_sha: str, cmd_sha: str) -> dict:
    require(HEX40.fullmatch(source_sha) is not None
            and HEX64.fullmatch(cmd_sha) is not None,
            "missing external source or packaged CMD identity")
    with open_original(pre_path, pre_sha) as pre, open_original(post_path, post_sha) as post:
        pre_report, post_report = parsed(pre, "result.json"), parsed(post, "result.json")
        substrate = parsed(pre, "real-ntfs-substrate.json")
        pre_process = parsed(pre, "full-process.json")
        post_process = parsed(post, "full-postraw-result.json")
        exhaustion = parsed(post, "filler-exhaustion.json")
        require(substrate.get("tested_commit") == source_sha and
                pre_report.get("original_cmd_sha256") == cmd_sha and
                pre_process.get("original_full_ntfs_cmd_sha256") == cmd_sha and
                parsed(pre, "candidate.json").get("cmd_sha256") == cmd_sha and
                post_report.get("original_cmd_sha256") == cmd_sha,
                "cross-archive source/CMD binding conflict")
        before = verified_bytes(pre, pre_report["exact_before_full_two_cold_binary_members"])
        after = verified_bytes(post, post_report["actual_source_bytes"])
        require(len(before) == 16 and len(after) == 22, "unexpected NTFS source-byte coverage")
        baseline = stage(before, "before")
        for point in ("actual-full", "cold1", "cold2"):
            require(stage(before, point) == baseline, "pre-intent baseline changed at " + point)
        require(typed_stock(baseline["typed"])[0] == baseline["raw"],
                "pre-intent typed SRAM not equal raw")
        require(substrate.get("actual_ephemeral_ntfs_vhdx") is True and
                substrate.get("fresh_process_os_error") == 112 and
                pre_process.get("native_cmd_exit") == 8 and
                pre_process.get("real_ntfs_pre_intent_durable_allocation_refused") is True and
                pre_report.get("actual_native_cmd_exit8_during_original_guest_save") is True,
                "pre-intent original Win32 full-volume proof absent")
        require(stage(after, "before") == baseline,
                "separate original NTFS trials lack common starting population")
        postraw = stage(after, "postraw")
        denied = stage(after, "denied")
        recovered = stage(after, "recovered")
        cold2 = stage(after, "cold2")
        require(postraw["raw"] != baseline["raw"] and
                all(postraw[k] == baseline[k] for k in ("typed", "catalog", "selector")),
                "post-raw boundary not isolated from typed/roster/selector")
        require(denied == postraw, "NTFS denial changed forbidden files")
        require(all(recovered[k] == postraw[k] for k in ("raw", "catalog", "selector"))
                and recovered["typed"] != postraw["typed"] and cold2 == recovered,
                "once-only recovery or second cold restart diverged")
        old_sram, old_generation = typed_stock(baseline["typed"])
        new_sram, new_generation = typed_stock(recovered["typed"])
        require(old_sram == baseline["raw"] and new_sram == recovered["raw"]
                and new_generation == old_generation + 1,
                "raw/typed SRAM or recovery generation mismatch")
        require(after["intent.postraw.bin"] == after["intent.recovery-receipt.bin"],
                "forensic durable intent modified")
        require(post_process.get("native_exit") == 8 and
                post_process.get("full_volume", {}).get("first_process_real_ntfs_full") is True
                and post_process["full_volume"].get("second_process_win32_error") == 112
                and post_report.get("two_fresh_original_Windows_cold_boots") is True
                and post_report.get("recovery_intent_reconciled_once") is True,
                "post-raw Win32 full volume or cold recovery proof absent")
        require(exhaustion.get("guest_postraw_typed_failure_proven") is False
                and any(x.get("python_errno") == 28 or x.get("python_winerror") in (112, 39)
                        for x in exhaustion.get("events", [])),
                "filler exhaustion proof absent/misattributed")
        # Tie guest-consumed SRAM bytes to archived raw files on both sides
        # of each actual Windows original-CMD fault, not just JSON assertions.
        for name in ("warm.log", "cold-1.log", "cold-2.log"):
            require_boot_log(pre, name, baseline["raw"], reconciled=False)
        require_boot_log(post, "cold-1-original-CMD.log",
                         recovered["raw"], reconciled=True)
        require_boot_log(post, "cold-2-original-CMD.log",
                         cold2["raw"], reconciled=False)
        before_guest = pre.read("full-ntfs-original-CMD.log").decode("utf-8", "replace")
        failed_guest = post.read("real-postraw-full-original-CMD.log").decode("utf-8", "replace")
        error_probe = post.read("second-process-112.log").decode("ascii").strip()
        require("UR_BALDOSA_NATIVE_PROFILE REJECTED reason=native_sram_intent_not_durable"
                in before_guest and "UR-BALDOSA-SAVE-FAILED" in before_guest,
                "pre-intent original guest refusal absent")
        require("QA_POSTRAW_TYPED_GATE native_raw_written=1 typed_not_attempted=1"
                in failed_guest
                and "CHECKPOINT profile=native-ci-rider status=io_error" in failed_guest
                and "UR-BALDOSA-SAVE-FAILED" in failed_guest,
                "postraw original guest boundary/refusal absent")
        require(error_probe == "exit=112", "independent real Win32 112 process log missing")
        changed = sum(a != b for a, b in zip(baseline["raw"], postraw["raw"]))
        return {
            "schema": "ur-qa06-independent-real-ntfs-original-consumer/1",
            "source_sha": source_sha, "pre_outer_sha256": pre_sha,
            "post_outer_sha256": post_sha, "original_cmd_sha256": cmd_sha,
            "pre_intent_exact_original_bytes": len(before),
            "post_raw_exact_original_bytes": len(after),
            "raw_changed_positions": changed,
            "actual_guest_boot_before_fnv1a32": fnv1a32(baseline["raw"]),
            "actual_guest_boot_recovered_fnv1a32": fnv1a32(recovered["raw"]),
            "guest_boot_sram_consumed_bytes_verified": True,
            "original_guest_native_fault_logs_verified": True,
            "recovered_typed_generation": new_generation,
            "fresh_boots_after_ntfs_fault": 2,
            "windows_original_process_executed_here": False,
            "physical_hardware_tested_here": False,
            "electrical_power_loss_tested_here": False,
            "release_gate_credit": 0,
            "disposition": "source-bounded archived real-NTFS positive; release HOLD",
        }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pre", required=True, type=Path)
    p.add_argument("--post", required=True, type=Path)
    p.add_argument("--expected-pre-sha256", required=True)
    p.add_argument("--expected-post-sha256", required=True)
    p.add_argument("--source-sha", required=True)
    p.add_argument("--cmd-sha256", required=True)
    args = p.parse_args()
    report = inspect(args.pre, args.post, pre_sha=args.expected_pre_sha256,
                     post_sha=args.expected_post_sha256,
                     source_sha=args.source_sha, cmd_sha=args.cmd_sha256)
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
