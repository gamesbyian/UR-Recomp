#!/usr/bin/env python3
"""Independent source-authentic RF064 read-coverage audit, NOT event acceptance.

Reopens the pinned original/native binaries, actual replay log and primary
producer receipts. In particular, a real post-call value is not evidence that
a separate observed getset read occurred when its source ordinal did not move.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import zipfile

import qa01_rf064_original_pull_return_report as rf064

SCHEMA = "ur-qa01-independent-rf064-source-read-coverage/1"
DEFAULT_DIGESTS = {
    "case": "7891a24124c67f414e9b00ed2bb1dbe2e59e4a2b6c50b558e920c25d885e63ea",
    "binaries": "04c35a59e3d05979c26b0530f98432de5daa069c91bc69b5d2dab07cb31ca8f7",
    "aggregate": "99a2707620fa80c91bb9d135491072db1b40b8acee2fce684363d0ef1cecd6d8",
}
LOG = "work/zoom-zoo/replay/reference.log"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def classify(pulls: list[dict], buses: list[dict], verified: dict) -> dict:
    """Independently distinguish missing bus-read coverage from true ambiguity."""
    kinds = Counter(row["kind"] for row in buses)
    pkinds = Counter(row["kind"] for row in pulls)
    require(set(kinds) <= {"rb", "rw", "wb", "ww"} and
            set(pkinds) <= {"pullB", "pullW"}, "invalid executed source operation kind")
    require(sum(pkinds.values()) == verified["post_call_actual_original_pull_count"]
            and sum(kinds.values()) == verified["sequenced_original_bus_entries"],
            "source return/bus counts differ from independently parsed log")
    gaps = [int(row["after"]) - int(row["before"]) for row in pulls]
    require(all(gap >= 0 for gap in gaps), "source bus ordinals regressed during pull")
    zero, one, multiple = (sum(gap == value for gap in gaps)
                           for value in (0, 1, 2))
    multiple = sum(gap > 1 for gap in gaps)
    require(one == verified["actual_returns_with_unique_source_bus_entry"]
            and zero + multiple == verified["ambiguous_or_reentrant_original_pulls"],
            "RF064 unique/ambiguous report contradicts real bus-ordinal deltas")
    read_entries = kinds["rb"] + kinds["rw"]
    write_entries = kinds["wb"] + kinds["ww"]
    if zero == len(pulls) and read_entries == 0:
        reason = "original_getset_read_path_not_observed"
    elif one == len(pulls) and verified["original_return_join_all_qualified"] is True:
        reason = "bounded_postcall_read_entries_joined"
    else:
        reason = "incomplete_or_mixed_original_read_attribution"
    return {
        "actual_post_call_pull_kinds": dict(pkinds),
        "original_shared_getset_bus_kinds": dict(kinds),
        "source_getset_read_entries": read_entries,
        "source_getset_write_entries": write_entries,
        "pulls_with_no_getset_ordinal_increase": zero,
        "pulls_with_exactly_one_getset_ordinal_increase": one,
        "pulls_with_multiple_getset_ordinal_increases": multiple,
        "real_post_call_values_attributed_to_actual_bus_reads": one,
        "reason": reason,
    }


def zip_open(path: Path, digest: str) -> zipfile.ZipFile:
    require(sha256(path.read_bytes()) == digest, "wrong exact ZIP provenance: " + path.name)
    z = zipfile.ZipFile(path)
    infos = z.infolist()
    require(len(infos) <= 1000 and len(infos) == len(set(x.filename for x in infos))
            and all(not x.filename.startswith("/") and ".." not in
                    Path(x.filename).parts and x.file_size <= 40_000_000
                    for x in infos) and z.testzip() is None,
            "unsafe, corrupt or duplicated original evidence ZIP: " + path.name)
    return z


def audit(case: Path, binaries: Path, aggregate: Path, *,
          expected: dict | None = None) -> dict:
    pins = DEFAULT_DIGESTS if expected is None else expected
    with zip_open(case, pins["case"]) as zc, zip_open(binaries, pins["binaries"]) as zb, zip_open(aggregate, pins["aggregate"]) as za:
        original_bytes = zc.read(LOG)
        actual_original_log = sha256(original_bytes)
        require(actual_original_log == zc.read("rf064-original-log-sha256.txt").
                decode("utf8").split()[0], "RF064 source log differs from its pinned report")
        raw = original_bytes.decode("utf8")
        independently = rf064.check(raw)
        require(independently == json.loads(zc.read("rf064-original-pulls.json")),
                "original consumed-return verifier does not reproduce from retained log")
        pull_rows = rf064.extract(raw, rf064.PULL)
        bus_rows = rf064.extract(raw, rf064.BUS)
        classification = classify(pull_rows, bus_rows, independently)

        manifest = zc.read("SHA256SUMS")
        require(manifest == zb.read("SHA256SUMS"),
                "native/original executables belong to different producer run")
        binary_hashes = {}
        for line in manifest.decode("ascii").splitlines():
            digest, member = line.split()
            require(member in ("native", "snesref", "snes9x_libretro.so")
                    and member not in binary_hashes and
                    sha256(zb.read(member)) == digest,
                    "actual native/original executable byte hash differs from manifest")
            binary_hashes[member] = digest
        require(set(binary_hashes) == {"native", "snesref", "snes9x_libretro.so"},
                "incomplete source-executable lineage")
        producer_bytes = zc.read("producer-report.json")
        producer = json.loads(producer_bytes)
        campaign = json.loads(za.read("campaign-result.json"))
        primary = json.loads(za.read("qa01-primary-artifact-audit.json"))
        require(campaign["completed"] == campaign["selected_cases"] == 1
                and campaign["release_admissions"] == 0
                and primary["release_admissions"] == 0,
                "aggregate claims unsupported USA event credit")
        case_info = campaign["results"][0]
        evidence = case_info["evidence"]
        require(case_info["case"] == "zoom-zoo" and
                evidence["producer_sha256"] == sha256(producer_bytes) and
                evidence["core_sha256"] == producer["reference_core_sha256"] ==
                    binary_hashes["snes9x_libretro.so"] and
                evidence["native_sha256"] == producer["native_executable_sha256"] ==
                    binary_hashes["native"] and
                evidence["original_movie_window_sha256"] ==
                    primary["cases"][0]["source_supplied_controller_route"][
                        "source_original_movie_window_sha256"] and
                evidence["terminal_guest_relative_frames"] ==
                    {"reference_relative": 5163, "native_relative": 5163} and
                evidence["next_bowl_bounded"]["fresh_original_entry_offset"] ==
                evidence["next_bowl_bounded"]["fresh_native_entry_offset"] == 267,
                "source-original/native ELF/gameplay witness not pinned to these artifacts")
        return {
            "schema": SCHEMA,
            "case_sha256": pins["case"],
            "binaries_sha256": pins["binaries"],
            "aggregate_sha256": pins["aggregate"],
            "verified_original_log_sha256": actual_original_log,
            "verified_original_native_executables": binary_hashes,
            "verified_actual_case_producer_sha256": sha256(producer_bytes),
            "verified_original_nmi_stack": independently[
                "original_post_nmi_unmasked_stack"],
            **classification,
            "original_result_relative": 5163,
            "native_result_relative": 5163,
            "next_bowl_original_native_relative": 267,
            "source_return_to_read_complete_causality": False,
            "actual_guest_joypad_CPU_reads_proven": False,
            "native_direct_read_guest_PC_join_proven": False,
            "shipping_windows_disk_persistence_proven": False,
            "accepted_USA_events": 0,
            "release_QA_gates": 0,
            "adjudication": "HOLD",
        }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case", type=Path, required=True)
    ap.add_argument("--binaries", type=Path, required=True)
    ap.add_argument("--aggregate", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    decision = audit(args.case, args.binaries, args.aggregate)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print("RF064 actual original return coverage rechecked; no full event admitted")


if __name__ == "__main__":
    main()
