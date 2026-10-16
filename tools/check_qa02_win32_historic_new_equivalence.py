#!/usr/bin/env python3
"""Independent exact-byte equivalence between old P0 and new Win32 evidence.

Requires TWO externally SHA-pinned original GitHub Actions ZIP envelopes.
Reuses the historic negative and 39-file new recovery strict verifiers.
Proves the later producer's raw/typed source boundary is identical to the
original crash, never that the release is ready or that Windows was run here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import zipfile

from check_qa02_win32_fault_snapshots import inspect, difference_count
from check_qa02_win32_original_fault_envelope import audit, NEG, POS, LABELS


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError("QA02_CROSS_SOURCE_REJECTED: " + reason)


def compare(historical: pathlib.Path, historical_sha: str,
            historical_source: str, historical_exe_sha: str,
            newer: pathlib.Path, newer_sha: str) -> dict:
    old_check = inspect(historical, historical_sha, "historic",
                        source=historical_source, exe=historical_exe_sha)
    new_check = audit(newer, newer_sha)
    matched = {}
    with zipfile.ZipFile(historical) as old, zipfile.ZipFile(newer) as new:
        # Every historical old/raw/typed/selector/catalog before and after
        # byte stream must exactly match the new unjournaled crash pathway.
        for label in LABELS:
            for stage in ("before", "after"):
                name = f"{label}.{stage}.bin"
                original = old.read(name)
                latest = new.read(NEG + name)
                require(original == latest,
                        "old negative vs new unjournaled mismatch: " + name)
                matched[name] = hashlib.sha256(original).hexdigest()

        # Independent journal mode uses exactly that same guest at exactly
        # that same prewrite boundary, then only typed commits on cold boot.
        for label in LABELS:
            name = f"{label}.before.bin"
            require(old.read(name) == new.read(POS + name),
                    "journal baseline changed: " + name)
        require(new.read(POS + "raw-sram.crash.bin") ==
                old.read("raw-sram.after.bin"),
                "new journaled raw crash does not equal old original raw crash")
        require(new.read(POS + "raw-sram.after.bin") ==
                old.read("raw-sram.after.bin"),
                "new journaled raw changed after recovery")
        require(new.read(POS + "typed-profile.crash.bin") ==
                old.read("typed-profile.after.bin"),
                "new journaled typed sidecar changed before raw-crash cut")
        for label in ("selector", "roster"):
            for stage in ("crash", "after"):
                require(new.read(POS + f"{label}.{stage}.bin") ==
                        old.read(f"{label}.after.bin"),
                        "journal selector/catalog mutated: " + label + "/" + stage)
        raw_delta = difference_count(old.read("raw-sram.before.bin"),
                                     old.read("raw-sram.after.bin"))
        require(raw_delta == old_check["changed_guest_raw_bytes"] ==
                new_check["cases"]["unjournaled"]["changed_guest_raw_bytes"] ==
                new_check["cases"]["journaled"]["changed_guest_raw_bytes"],
                "different old/new original raw edit counts")
    return {
        "schema": "UR-QA02-EXACT-ORIGINAL-NEGATIVE-POSITIVE-BYTE-EQUIVALENCE/1",
        "historical_original_actions_zip_sha256": historical_sha,
        "new_original_actions_zip_sha256": newer_sha,
        "historical_source": historical_source,
        "historical_executable_sha256": historical_exe_sha,
        "independently_identical_old_negative_new_unjournaled_files": 8,
        "historic_file_sha256": matched,
        "new_journaled_raw_crash_identical_to_original": True,
        "new_journaled_recovered_typed_equals_exact_guest_raw":
            new_check["cases"]["journaled"]["reconciled_typed"],
        "raw_changed_byte_count": raw_delta,
        "release_gate_credit": 0,
        "physical_hardware_verified": False,
        "limits": ("New source/ZIP/PE and PR-merge identity remain bound through "
                   "separate same-run candidate receipt; 3+ profile locking, "
                   "interactive menu, real OS partial I/O and power cuts "
                   "still require independent candidate-bound testing."),
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--historical-zip", type=pathlib.Path, required=True)
    p.add_argument("--historical-sha256", required=True)
    p.add_argument("--historical-source", required=True)
    p.add_argument("--historical-exe-sha256", required=True)
    p.add_argument("--new-zip", type=pathlib.Path, required=True)
    p.add_argument("--new-sha256", required=True)
    a = p.parse_args()
    try:
        result = compare(a.historical_zip, a.historical_sha256,
                         a.historical_source, a.historical_exe_sha256,
                         a.new_zip, a.new_sha256)
    except (ValueError, KeyError, TypeError, OSError,
            zipfile.BadZipFile, UnicodeError) as exc:
        p.exit(2, str(exc) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
