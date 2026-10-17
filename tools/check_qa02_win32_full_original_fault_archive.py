#!/usr/bin/env python3
"""Read-only independent audit of the complete 306-member original Win32 fault ZIP.

The external Actions SHA256 is required. Bounded source-only observations,
not a physical power cut, human input, release gate or source/PE attestation.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import re
import stat
from pathlib import Path
import zipfile

EXPECTED_FILENAME_ROSTER_SHA256 = "10fa7373def425c458ea8be8d8669686609d9f24d0c0473aa274bb1c7b7f9bb9"

EXPECTED_ROOTS = frozenset((
    "native_actual_win32_prewrite_dacl_denial",
    "native_intent_restart_recovery",
    "native_journaled_b_crash_then_a",
    "native_post_raw_pre_typed_crash",
    "native_prewrite_intent_abandon",
    "native_real_b_crash_healthy_a_recovery",
    "native_real_win32_live_postraw_typed_denial",
    "native_recovery_healthy_alternate",
    "native_three_profile_unrelated_damage",
    "native_two_original_windows_games",
    "native_typed_before_intent_recovery",
))
RECEIPT_COUNTS = {
    "native_post_raw_pre_typed_crash": 12,
    "native_intent_restart_recovery": 16,
    "native_intent_restart_recovery/native_postraw_recovery_dacl_denial": 18,
    "native_typed_before_intent_recovery": 16,
    "native_prewrite_intent_abandon": 17,
    "native_real_b_crash_healthy_a_recovery": 24,
    "native_journaled_b_crash_then_a": 32,
    "native_actual_win32_prewrite_dacl_denial": 12,
    "native_real_win32_live_postraw_typed_denial": 22,
    "native_three_profile_unrelated_damage": 29,
    "native_intent_restart_recovery/simulated_partial_raw_explicit_rollback": 13,
}
LABELS = ("raw-sram", "typed-profile", "selector", "roster")
ACTUAL_DENIAL = "native_actual_win32_prewrite_dacl_denial"
POSTRAW_DENIAL = "native_real_win32_live_postraw_typed_denial"
SHA_PATTERN = re.compile(r"[0-9a-f]{64}\Z")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def need(ok: bool, cause: str) -> None:
    if not ok:
        raise ValueError("QA02_FULL_WIN32_ARCHIVE_REJECTED: " + cause)


def audit_receipt(z: zipfile.ZipFile, path: str) -> tuple[str, int]:
    """Verify exact source binary SHA/size fields in one original receipt."""
    receipt = json.loads(z.read(path))
    need(isinstance(receipt, dict), "malformed receipt " + path)
    prefix = path.rsplit("/", 1)[0] + "/"
    group = path.split("/fault-bytes/", 1)[0]
    count = 0
    for label, metadata in receipt.items():
        need(type(metadata) is dict, "invalid receipt entry " + label)
        if "sha256" in metadata:
            if label.endswith(".bin"):
                member = prefix + label
            else:
                need(path.endswith("/second-cold-file-receipt.json"),
                     "unqualified bare receipt " + label)
                member = prefix + label + ".second-cold.bin"
            need(member in z.namelist(), "missing source member " + member)
            data = z.read(member)
            need(type(metadata.get("bytes")) is int and
                 metadata["bytes"] == len(data) and
                 metadata["sha256"] == sha(data),
                 "source SHA/size differs " + member)
            count += 1
        else:
            stages = [s for s in ("before", "crash", "after", "second-cold")
                      if s + "_sha256" in metadata]
            need(bool(stages), "no original source hashes " + label)
            for stage in stages:
                member = prefix + label + "." + stage + ".bin"
                need(member in z.namelist(), "missing staged object " + member)
                data = z.read(member)
                need(metadata[stage + "_sha256"] == sha(data) and
                     (stage + "_bytes" not in metadata or
                      (type(metadata[stage + "_bytes"]) is int and
                       metadata[stage + "_bytes"] == len(data))),
                     "staged original binary differs " + member)
                count += 1
    return group, count


def stock_sram(typed: bytes) -> bytes:
    fields = re.findall(rb"(?m)^stock_sram=([0-9a-f]{16384})\r?$", typed)
    need(len(fields) == 1 and typed.startswith(b"UR-HOST-PROFILE/5\n"),
         "typed original SRAM schema invalid")
    return bytes.fromhex(fields[0].decode("ascii"))


def audit(archive: Path, expected_sha256: str) -> dict:
    need(type(expected_sha256) is str and
         SHA_PATTERN.fullmatch(expected_sha256) is not None,
         "independent original Actions SHA256 required")
    need(archive.is_file() and not archive.is_symlink() and
         0 < archive.stat().st_size <= 2_000_000,
         "source ZIP missing/redirected/oversized")
    need(sha(archive.read_bytes()) == expected_sha256,
         "original Actions ZIP does not match pinned digest")
    with zipfile.ZipFile(archive) as z:
        infos = z.infolist()
        names = [item.filename for item in infos]
        need(len(names) == 306 and len(set(names)) == 306 and
             {name.split("/", 1)[0] for name in names} == EXPECTED_ROOTS and
             sha(("\n".join(sorted(names)) + "\n").encode("utf-8")) ==
             EXPECTED_FILENAME_ROSTER_SHA256,
             "original complete Windows fault inventory differs")
        need(sum(item.file_size for item in infos) <= 4_000_000 and
             z.testzip() is None, "original source ZIP CRC/size failure")
        for entry in infos:
            need(not entry.is_dir() and not (entry.flag_bits & 1) and
                 stat.S_IFMT(entry.external_attr >> 16) in (0, stat.S_IFREG) and
                 not entry.filename.startswith("/") and
                 not "\\" in entry.filename and
                 not any(p in (".", "..", "") for p in entry.filename.split("/")) and
                 not entry.filename.lower().endswith((".sfc", ".smc", ".rom", ".iso")),
                 "unsafe/linked/ROM source member " + entry.filename)
        counts: dict[str, int] = {}
        for name in names:
            if name.endswith(("/file-receipt.json", "/hashes.json",
                              "/second-cold-file-receipt.json")):
                group, value = audit_receipt(z, name)
                counts[group] = counts.get(group, 0) + value
        need(counts == RECEIPT_COUNTS, "original receipt groups/populations differ")
        # Independently prove the optional flat 19-object QA consumer export
        # reproduces exactly the full original fault archive bytes. Older
        # export versions had 18 members or an incompatible receipt schema.
        nested_root = "native_intent_restart_recovery/"
        flat = z.read(nested_root + "qa02-journaled-snapshot.zip")
        sidecar = z.read(nested_root + "qa02-journaled-snapshot.sha256")
        need(sidecar.decode("ascii").split()[:1] == [sha(flat)],
             "nested original QA19 sidecar SHA mismatch")
        expected_flat = {
            label + "." + stage + ".bin"
            for label in LABELS for stage in ("before", "crash", "after")
        } | {
            "file-receipt.json", "intent-receipt.json", "intent.crash.bin",
            "intent.recovered-receipt.bin", "cold-recovery.log", "crash.log",
            "second-cold-recovery-boot.log",
        }
        with zipfile.ZipFile(io.BytesIO(flat)) as inner:
            infos_flat = inner.infolist()
            need(len(infos_flat) == 19 and
                 {entry.filename for entry in infos_flat} == expected_flat and
                 inner.testzip() is None,
                 "optional flat QA19 original receipt shape invalid")
            for member in expected_flat:
                need(inner.read(member) ==
                     z.read(nested_root + "fault-bytes/" + member),
                     "flat QA19 differs from independently retained source " + member)

        def get(prefix: str, name: str) -> bytes:
            return z.read(prefix + "/fault-bytes/" + name + ".bin")
        def identical(prefix: str, labels: tuple[str, ...],
                      stages: tuple[str, ...]) -> None:
            for label in labels:
                items = [get(prefix, label + "." + stage) for stage in stages]
                need(all(x == items[0] for x in items),
                     "canonical byte drift " + prefix + ":" + label)

        # Real NTFS file/directory ACL refusal BEFORE guest SRAM publication.
        identical(ACTUAL_DENIAL, LABELS,
                  ("before", "denied", "second-cold"))
        old_raw = get(ACTUAL_DENIAL, "raw-sram.before")
        need(len(old_raw) == 8192 and
             stock_sram(get(ACTUAL_DENIAL, "typed-profile.before")) == old_raw,
             "pre-denial original raw/typed were not healthy")
        d = json.loads(z.read(ACTUAL_DENIAL + "/refusal.json"))
        need(d.get("schema") == "ur-baldosa-source-real-win32-prewrite-ntfs-dacl/1"
             and d.get("actual_os_write_denied") is True
             and d.get("raw_guest_save_write_attempted") is False
             and type(d.get("native_exit_code")) is int
             and d["native_exit_code"] == 8
             and d.get("real_disk_full_or_power_loss") is False
             and d.get("qa_gate_credit") == 0,
             "original source Windows pre-write refusal contract differs")
        denial_log = z.read(ACTUAL_DENIAL + "/actual-win32-denied-save.log")
        need(b"native_save_preflight_failed" in denial_log and
             denial_log.count(b"UR-BALDOSA-SAVE-FAILED:") == 1,
             "original executable did not warn about refusal")
        for i in (1, 2):
            cold = z.read(ACTUAL_DENIAL + f"/cold-boot-{i}.log")
            need(cold.count(b"first frame simulated") == 1,
                 "Windows post-denial cold process did not boot once")

        # Original first-party guest durable prewrite _Exit(84) cut.
        identical("native_prewrite_intent_abandon", LABELS,
                  ("before", "crash", "first-cold", "second-cold"))
        need(b"QA_CRASH_PRE_RAW exit=84" in
             z.read("native_prewrite_intent_abandon/crash.log"),
             "original prewrite crash marker absent")

        # Actual live Win32 typed-publication sharing denial AFTER raw write.
        p = POSTRAW_DENIAL
        stages = ("before", "native-postraw", "denied", "recovered", "second-cold")
        raw = [get(p, "raw-sram." + stage) for stage in stages]
        changed = sum(a != b for a, b in zip(raw[0], raw[1]))
        need(all(len(x) == 8192 for x in raw) and
             changed == 28 and raw[1] == raw[2] == raw[3] == raw[4],
             "native guest SRAM changed unexpectedly across denial/recovery")
        identical(p, ("roster", "selector"), stages)
        identical(p, ("typed-profile"), stages[:3])
        identical(p, ("typed-profile"), stages[-2:])
        need(stock_sram(get(p, "typed-profile.before")) == raw[0] and
             stock_sram(get(p, "typed-profile.recovered")) == raw[-1] and
             get(p, "intent.native-postraw") ==
             get(p, "intent.recovered-receipt"),
             "original durable typed recovery/intent does not match guest raw")
        live = z.read(p + "/live-original-after-raw-denied-typed.log")
        need(live.count(b"UR-BALDOSA-SAVE-FAILED:") == 1 and
             b"status=io_error" in live,
             "original post-raw refusal did not reach player-visible error")
        for name in ("first-clean-cold-replay.log", "second-clean-cold-replay.log"):
            need(b"first frame simulated" in z.read(p + "/" + name),
                 "original clean post-denial cold game missing")

        # After typed publication but before intent retirement: F3.
        p = "native_typed_before_intent_recovery"
        identical(p, ("typed-profile", "raw-sram"),
                  ("crash", "after", "second-cold"))
        need(stock_sram(get(p, "typed-profile.crash")) ==
             get(p, "raw-sram.crash"),
             "F3 committed raw/typed conflict")

        # Crashed B, alternate A remains healthy and untouched.
        p = "native_real_b_crash_healthy_a_recovery"
        identical(p, ("a-raw", "a-typed", "roster"),
                  ("crash", "selected", "after", "second-cold"))
        identical(p, ("b-raw", "b-typed"),
                  ("crash", "after", "second-cold"))
        need(get(p, "b-raw.selected") != get(p, "b-raw.crash") and
             stock_sram(get(p, "b-typed.crash")) ==
             get(p, "b-raw.selected"),
             "original B crash not preserved while selecting healthy A")

        partial = get("native_intent_restart_recovery/simulated_partial_raw_explicit_rollback",
                      "raw.synthetic-partial")
        need(len(partial) == 513, "source synthetic short raw was not 513 bytes")
    return {
        "schema": "UR-QA02-INDEPENDENT-EXACT-306-WIN32-FAULT-ARCHIVE/1",
        "source_original_actions_sha256": expected_sha256,
        "original_actions_zip_members": 306,
        "binary_original_sha_receipts_verified": sum(counts.values()),
        "nested_QA19_identical_to_original_fault_source": True,
        "original_receipt_groups_verified": len(counts),
        "genuine_ntfs_prewrite_denial_preserved_four_canonical_files": True,
        "original_native_guest_postraw_changed_bytes": changed,
        "genuine_os_sharing_denial_then_idempotent_recovery": True,
        "F0_prewrite_and_F3_posttyped_restarts_byte_stable": True,
        "damaged_B_preserved_healthy_A": True,
        "513_byte_partial_raw": "synthetically truncated fixture, not actual OS partial write",
        "product_PE_and_ZIP_bound_in_this_checker": False,
        "electrical_power_loss_or_disk_full_accepted": False,
        "physical_human_input_or_hardware_accepted": False,
        "release_gate_credit": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args()
    try:
        result = audit(args.zip, args.sha256)
    except (ValueError, OSError, KeyError, TypeError, UnicodeError,
            zipfile.BadZipFile, json.JSONDecodeError) as err:
        parser.exit(2, str(err) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
