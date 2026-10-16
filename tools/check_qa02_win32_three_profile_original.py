#!/usr/bin/env python3
"""Independent byte audit of an ORIGINAL Windows three-profile Actions ZIP.

The third profile's damage is deliberately injected by a QA fixture, not
original guest execution, NTFS partial IO, a power cut, or a human-operated UI.
Source/PE/ZIP identity must be separately bound from the SAME Actions run.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import stat
import zipfile

PREFIX = "native_three_profile_unrelated_damage/"
SNAP = PREFIX + "fault-bytes/"
LABELS = ("a-raw", "a-typed", "b-raw", "b-typed", "c-raw", "selector", "roster")
STAGES = ("before", "damaged", "after", "second-cold")
LOGS = ("damaged-a-refusal.log", "invalid-c-selection.log",
        "explicit-b-selection.log", "healthy-b-cold-1.log", "healthy-b-cold-2.log")
BLOB_NAMES = {f"{name}.{stage}.bin" for name in LABELS for stage in STAGES}
BLOB_NAMES.add("c-typed.original-then-absent.bin")
REQUIRED = {SNAP + n for n in BLOB_NAMES | {"file-receipt.json"}} | {
    PREFIX + n for n in LOGS}


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError("QA02_THREE_PROFILE_REJECTED: " + reason)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify(original_zip: Path, sha256: str) -> dict:
    require(re.fullmatch(r"[a-f0-9]{64}", sha256) is not None,
            "exact lower-case original Actions SHA256 required")
    require(original_zip.is_file() and not original_zip.is_symlink() and
            0 < original_zip.stat().st_size <= 2_000_000,
            "source-original evidence missing, symlinked or oversized")
    original = original_zip.read_bytes()
    require(digest(original) == sha256, "original Actions ZIP hash mismatch")
    with zipfile.ZipFile(io.BytesIO(original)) as z:
        info = z.infolist()
        names = [x.filename for x in info]
        require(len(names) == len(set(names)) and REQUIRED <= set(names),
                "missing three-profile evidence member or duplicate ZIP entry")
        require(sum(x.file_size for x in info) <= 7_000_000,
                "original ZIP exceeds evidence budget")
        for x in info:
            kind = stat.S_IFMT(x.external_attr >> 16)
            require(not x.is_dir() and not (x.flag_bits & 1) and
                    kind in (0, stat.S_IFREG) and
                    not x.filename.startswith("/") and
                    not re.search(r"(^|/)\.\.?(/|$)", x.filename) and
                    "\\" not in x.filename and
                    not x.filename.lower().endswith((".sfc", ".smc", ".rom", ".iso")),
                    "unsafe or ROM-containing original member")
        require(z.testzip() is None, "original ZIP member CRC mismatch")
        receipt = json.loads(z.read(SNAP + "file-receipt.json").decode("utf-8"))
        require(isinstance(receipt, dict) and set(receipt) == BLOB_NAMES,
                "noncanonical three-profile binary receipt roster")
        blobs = {}
        for n in sorted(BLOB_NAMES):
            data = z.read(SNAP + n)
            meta = receipt[n]
            require(isinstance(meta, dict) and
                    set(meta) == {"sha256", "bytes"} and
                    meta["sha256"] == digest(data) and
                    meta["bytes"] == len(data),
                    "binary SHA256 or length mismatch: " + n)
            blobs[n] = data
        logs = {n: z.read(PREFIX + n).decode("utf-8", "replace") for n in LOGS}

    get = lambda label, stage: blobs[f"{label}.{stage}.bin"]
    raw = {p: get(p + "-raw", "before") for p in ("a", "b", "c")}
    require(all(len(v) == 8192 for v in raw.values()) and
            len(set(raw.values())) == 3, "not three distinct original 8KiB saves")
    require(len(blobs["c-typed.original-then-absent.bin"]) > 8192,
            "missing original pre-damage C typed save")
    damaged = get("a-raw", "damaged")
    require(len(damaged) == 8192 and
            sum(a != b for a, b in zip(raw["a"], damaged)) == 1 and
            damaged[0x0711] == raw["a"][0x0711] ^ 0x35,
            "selected A synthetic damage does not match known 1-byte fixture cut")
    require(get("a-raw", "after") == damaged ==
            get("a-raw", "second-cold"), "damaged A silently repaired")
    for label in ("a-typed", "b-raw", "b-typed", "c-raw", "roster"):
        require(all(get(label, stage) == get(label, "before") for stage in STAGES),
                "unrelated canonical file changed: " + label)
    require(get("selector", "before") == get("selector", "damaged") and
            get("selector", "after") == get("selector", "second-cold") and
            get("selector", "after") != get("selector", "before"),
            "selected B selector update missing or repeated")
    for pid in ("native-ci-rider", "native-ci-second", "native-ci-third"):
        require(pid.encode() in get("roster", "before"),
                "roster missing third distinct canonical racer: " + pid)
    require(b"native-ci-rider" in get("selector", "before") and
            b"native-ci-second" in get("selector", "after"),
            "selector transition not A to B")
    require("selected_profile_sram_not_initialized" in logs["damaged-a-refusal.log"] and
            "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM" not in logs["damaged-a-refusal.log"],
            "damaged selected A boot was not refused")
    require("completed=1" not in logs["invalid-c-selection.log"] and
            "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM" not in logs["invalid-c-selection.log"],
            "unauthorized damaged C selection succeeded")
    require("choice=healthy" in logs["explicit-b-selection.log"] and
            "completed=1" in logs["explicit-b-selection.log"] and
            "native-ci-second" in logs["explicit-b-selection.log"] and
            "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM" not in logs["explicit-b-selection.log"],
            "explicit healthy B selection not demonstrated")
    for i in (1, 2):
        log = logs[f"healthy-b-cold-{i}.log"]
        require("UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM" in log and
                "native-ci-second" in log and
                "UR_BALDOSA_NATIVE_PROFILE REJECTED" not in log and
                "UR_BALDOSA_NATIVE_PROFILE RECOVERY_RECONCILED" not in log,
                "fresh cold B guest log absent or repeated recovery")
    return {
        "schema": "UR-QA02-ORIGINAL-THREE-PROFILE-SNAPSHOT/1",
        "source_original_actions_zip_sha256": sha256,
        "canonical_binary_objects_verified": len(BLOB_NAMES),
        "source_logs_checked": len(LOGS),
        "three_distinct_registered_raw_sram_files": True,
        "selected_A_one_byte_damage_is_synthetic": True,
        "preserved_unrelated_C": True,
        "C_typed_removal": "old typed bytes exported; absence in live root is producer-reported",
        "only_selector_changed_to_B_and_two_cold_boot_logs": True,
        "complete_QA02_release_gate_credit": 0,
        "real_NTFS_partial_write_or_power_loss_verified": False,
        "actual_two_pad_audio_display_verified": False,
        "limitations": "Original ZIP source, PE and package binding needs separate same-run receipts; "
                       "Windows exit codes and actual removed C typed file are producer-reported; "
                       "not a real human-operated packaged recovery menu."
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-zip", required=True, type=Path)
    p.add_argument("--sha256", required=True)
    args = p.parse_args()
    try:
        result = verify(args.original_zip, args.sha256)
    except (ValueError, TypeError, KeyError, OSError, UnicodeError,
            zipfile.BadZipFile) as exc:
        p.exit(2, str(exc) + "\n")
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
