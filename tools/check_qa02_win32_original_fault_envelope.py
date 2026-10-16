#!/usr/bin/env python3
"""Read-only independent QA of ONE source-original Actions Win32 fault ZIP.

The external SHA256 must describe the GitHub Actions artifact ZIP itself.
This tool audits both cases and their five supplemental logs with a strict
whole-archive member allowlist. Derived internal case ZIP hashes are explicitly
not substitutes for the whole original artifact hash. No ROM, game simulation,
release gate credit, source/PE identity or physical hardware is certified.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import pathlib
import stat
import tempfile
import zipfile

from check_qa02_win32_fault_snapshots import inspect

LABELS = ("raw-sram", "typed-profile", "selector", "roster")
NEG = "native_post_raw_pre_typed_crash/fault-bytes/"
POS = "native_intent_restart_recovery/fault-bytes/"
EXTRA = {
    "native_post_raw_pre_typed_crash/explicit-recovery-native-command.log",
    "native_post_raw_pre_typed_crash/explicit-recovery-fresh-boot.log",
    "native_recovery_healthy_alternate/damaged-source-refusal.log",
    "native_recovery_healthy_alternate/explicit-healthy-selection.log",
    "native_recovery_healthy_alternate/fresh-healthy-guest.log",
}
MAX_ENTRIES = 39
MAX_UNCOMPRESSED = 1_000_000
RECEIPTS = ("file-receipt.json", "crash.log")


def reject_unless(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError("QA02_ENVELOPE_REJECTED: " + reason)


def contents(mode: str) -> set[str]:
    names = {f"{name}.{stage}.bin" for name in LABELS
             for stage in ("before", "crash", "after")}
    names.update(RECEIPTS)
    if mode == "unjournaled":
        names.add("cold-refusal.log")
    else:
        names.update(("cold-recovery.log", "intent-receipt.json",
                      "intent.crash.bin", "intent.recovered-receipt.bin",
                      "second-cold-recovery-boot.log"))
    return names


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def audit(archive: pathlib.Path, expected_sha256: str) -> dict:
    reject_unless(len(expected_sha256) == 64 and
                  all(c in "0123456789abcdef" for c in expected_sha256),
                  "external original artifact digest required")
    reject_unless(archive.is_file() and not archive.is_symlink() and
                  0 < archive.stat().st_size <= MAX_UNCOMPRESSED,
                  "original Actions artifact missing/oversized/redirected")
    original = archive.read_bytes()
    reject_unless(sha256(original) == expected_sha256,
                  "source original Actions ZIP SHA256 mismatch")
    expected = ({NEG + name for name in contents("unjournaled")} |
                {POS + name for name in contents("journaled")} | EXTRA)
    reject_unless(len(expected) == MAX_ENTRIES,
                  "internal whole-artifact inventory drift")
    with zipfile.ZipFile(io.BytesIO(original)) as source:
        entries = source.infolist()
        reject_unless(len(entries) == MAX_ENTRIES and
                      {entry.filename for entry in entries} == expected,
                      "missing, unexpected or duplicate original ZIP member")
        reject_unless(sum(e.file_size for e in entries) <= MAX_UNCOMPRESSED,
                      "original fault evidence uncompressed budget exceeded")
        for entry in entries:
            kind = stat.S_IFMT(entry.external_attr >> 16)
            reject_unless(not entry.is_dir() and not (entry.flag_bits & 1) and
                          kind in (0, stat.S_IFREG),
                          "unsafe original ZIP entry")
        reject_unless(source.testzip() is None, "original artifact CRC mismatch")

        # Preserve source-original SHA above; smaller derived per-case archives
        # exist only to reuse the strict independently tested leaf consumer.
        detail = {}
        with tempfile.TemporaryDirectory(prefix="qa02-fault-envelope-") as tmp:
            for mode, prefix in (("unjournaled", NEG), ("journaled", POS)):
                case_zip = pathlib.Path(tmp) / (mode + ".zip")
                with zipfile.ZipFile(case_zip, "w", zipfile.ZIP_STORED) as result:
                    for name in sorted(contents(mode)):
                        result.writestr(name, source.read(prefix + name))
                derived_hash = sha256(case_zip.read_bytes())
                inspected = inspect(case_zip, derived_hash, mode)
                detail[mode] = {
                    "derived_case_zip_sha256_NOT_GITHUB_ORIGINAL": derived_hash,
                    **inspected,
                }

        # The new intent and legacy non-intent case use the SAME original
        # source guest route; raw before, raw crash and raw after must agree
        # completely. No fabricated SRAM changes for the positive path.
        for stage in ("before", "crash", "after"):
            name = f"raw-sram.{stage}.bin"
            reject_unless(source.read(NEG + name) == source.read(POS + name),
                          "original guest SRAM differs across fault cases")
        outside = {name: source.read(name).decode("utf-8", errors="replace")
                   for name in sorted(EXTRA)}
        reject_unless(
            "UR_BALDOSA_RECOVERY_CHOICE choice=raw" in outside[
                "native_post_raw_pre_typed_crash/explicit-recovery-native-command.log"],
            "original executable explicit legacy raw selection missing")
        reject_unless(
            "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM" in outside[
                "native_post_raw_pre_typed_crash/explicit-recovery-fresh-boot.log"],
            "original executable recovered fresh guest missing")
        reject_unless(
            "UR_BALDOSA_RECOVERY_CHOICE choice=healthy" in outside[
                "native_recovery_healthy_alternate/explicit-healthy-selection.log"],
            "original executable separate healthy selection missing")
        reject_unless(
            "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM" in outside[
                "native_recovery_healthy_alternate/fresh-healthy-guest.log"],
            "original executable separate healthy guest missing")
    return {
        "schema": "UR-QA02-SOURCE-ORIGINAL-WIN32-FAULT-ENVELOPE/1",
        "source_original_GitHub_Actions_ZIP_SHA256": expected_sha256,
        "source_original_member_count": MAX_ENTRIES,
        "source_original_crc_and_allowlist_checked": True,
        "same_original_guest_raw_bytes_both_modes": True,
        "cases": detail,
        "supplemental_win32_logs_checked": len(EXTRA),
        "release_gate_credit": 0,
        "physical_hardware_tested": False,
        "limitations": ("Original artifact SHA is verified independently. "
                        "Source run, original PE and ZIP identity must be "
                        "bound from separate same-run GitHub evidence. "
                        "Power-loss durability and interactive Windows "
                        "hardware remain unverified."),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", type=pathlib.Path, required=True)
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args()
    try:
        result = audit(args.zip, args.sha256)
    except (ValueError, TypeError, KeyError, IndexError, UnicodeError,
            OSError, zipfile.BadZipFile) as exc:
        parser.exit(2, str(exc) + "\n")
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
