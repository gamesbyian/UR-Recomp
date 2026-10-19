#!/usr/bin/env python3
"""Independent ROM-free verifier of retained QA01 frame-capture raw evidence.

Rechecks raw source/native bytes against the frame fingerprint producer report.
A correct capture is still not original-guest input, clock or Windows QA proof.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import qa01_frame_fingerprint as frames


def canonical_sha256(data: object) -> str:
    """Stable evidence binding, independent of pretty-printed JSON whitespace."""
    raw = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode("ascii")).hexdigest()


def verify(report: dict, raw_root: Path) -> dict:
    frames.must(type(report) is dict and report.get("schema") == frames.SCHEMA,
                "invalid frame capture report")
    frames.validate_identity(report.get("source_identity"))
    # This offline schema has no signed original input polls, independent guest
    # frame acknowledgments, or Windows cold-disk execution. The producer may
    # not mint either external attestation through a self-reported flag.
    frames.must(report.get("producer_binary_and_executed_input_independently_verified") is False
                and report.get("windows_disk_persistence_proven") is False,
                "unsupported external provenance/persistence attestation")
    coverage = report.get("coverage")
    frames.must(type(coverage) is dict and
                all(type(coverage.get(x)) is int
                    for x in ("start", "end", "required_frames",
                              "observed_original_frames", "observed_native_frames")),
                "invalid coverage fields")
    start, end = coverage["start"], coverage["end"]
    frames.must(0 <= start <= end and end - start < 20000 and
                coverage["required_frames"] == end - start + 1 and
                coverage["observed_original_frames"] == end - start + 1 and
                coverage["observed_native_frames"] == end - start + 1 and
                coverage.get("continuous_at_declared_frame_phase") is True,
                "incomplete source/native frame population")
    rows = report.get("rows")
    frames.must(type(rows) is list and len(rows) == end - start + 1,
                "missing raw producer frame rows")
    identity = report["source_identity"]
    chain = hashlib.sha256()
    required_frames = {start, end}
    counts = {"wram": 0, "sram": 0}
    earliest = {"wram": None, "sram": None}
    for rel, row in enumerate(rows, start):
        frames.must(type(row) is dict and row.get("relative_frame") == rel and
                    row.get("original_actual_host_frame") == identity["original_frame_origin"] + rel
                    and row.get("native_actual_host_frame") == identity["native_frame_origin"] + rel,
                    "incorrect or shifted paired host frame")
        kinds = row.get("types")
        frames.must(type(kinds) is dict and set(kinds) == {"wram", "sram"},
                    "WRAM/SRAM digest population incomplete")
        for kind, size in (("wram", frames.WRAM), ("sram", frames.SRAM)):
            item = kinds[kind]
            frames.must(type(item) is dict and item.get("full_image_bytes_per_guest") == size
                        and type(item.get("unmasked_differing_byte_count")) is int
                        and 0 <= item["unmasked_differing_byte_count"] <= size,
                        "invalid image length or unequal-byte count")
            pair_digests = {}
            for guest in ("original", "native"):
                sha = item.get(guest + "_sha256")
                frames.must(type(sha) is str and frames.HEX64.fullmatch(sha),
                            "missing true source/guest digest")
                pair_digests[guest] = sha
                chain.update(bytes.fromhex(sha))
            count = item["unmasked_differing_byte_count"]
            # Every row, including digest-only interior frames, must agree
            # logically: equal SHA256 implies zero differences; unequal
            # SHA256 implies at least one unmasked differing byte. Recomputing
            # the chain alone cannot detect a self-consistent forged row.
            frames.must((pair_digests["original"] == pair_digests["native"]) == (count == 0),
                        "reported digest/count inconsistency")
            counts[kind] += count
            if count and earliest[kind] is None:
                earliest[kind] = rel
            if count:
                required_frames.add(rel)
    frames.must(report.get("frame_pair_digest_chain_sha256") == chain.hexdigest(),
                "frame digest-chain contents changed")
    frames.must(report.get("full_unmasked_differing_byte_occurrences") == counts,
                "total unmasked difference count changed")
    frames.must(report.get("first_differing_relative_frame") == earliest,
                "first differing frame metadata changed")
    frames.must(report.get("accepted_USA_events") == 0 and
                coverage.get("between_frame_opcode_semantics_proven") is False,
                "capture report attempted unsupported course promotion")
    entries = report.get("raw_retained_members")
    frames.must(type(entries) is list and entries and
                report.get("raw_retained_scope") == "all differing frames plus first and final pair",
                "producer omitted original raw byte retention")
    expected = {(rel, kind, guest) for rel in required_frames
                for kind in ("wram", "sram") for guest in ("original", "native")}
    observed = {}
    frames.must(raw_root.is_dir() and not raw_root.is_symlink(),
                "missing trustworthy retained raw directory")
    for entry in entries:
        frames.must(type(entry) is dict, "malformed raw evidence member")
        rel, kind, guest = (entry.get(x) for x in
                            ("relative_frame", "kind", "guest"))
        frames.must(type(rel) is int and kind in ("wram", "sram")
                    and guest in ("original", "native") and (rel, kind, guest) in expected
                    and (rel, kind, guest) not in observed,
                    "duplicated/foreign/missing raw evidence identity")
        member = f"{guest}-relative-{rel:06d}-{kind}.bin"
        frames.must(entry.get("member") == member and
                    entry.get("actual_host_frame") == identity[guest + "_frame_origin"] + rel,
                    "raw member filename or host identity incorrect")
        data = frames.raw(raw_root / member,
                          frames.WRAM if kind == "wram" else frames.SRAM)
        sha = frames.digest(data)
        frames.must(sha == entry.get("sha256") and
                    sha == rows[rel - start]["types"][kind][guest + "_sha256"],
                    "actual original/native raw image hash mismatch")
        observed[rel, kind, guest] = data
    frames.must(set(observed) == expected, "some differing or boundary raw images missing")
    # Recompute exact byte differences, not only image digests.
    for rel in required_frames:
        for kind in ("wram", "sram"):
            a, b = (observed[rel, kind, who] for who in ("original", "native"))
            count = sum(x != y for x, y in zip(a, b))
            frames.must(count == rows[rel - start]["types"][kind]["unmasked_differing_byte_count"],
                        "retained raw pair disagrees with producer's per-frame byte count")
    actual_files = {p.name for p in raw_root.iterdir()}
    frames.must(actual_files == {x["member"] for x in entries},
                "unmanifested raw evidence file or missing member")
    return {
        "schema": "ur-qa01-independent-frame-capture-audit/1",
        "source_sha": identity["source_sha"],
        # These fields bind the auditor's already re-opened raw bytes to the
        # *exact* producer report and its immutable input/frame identity. A
        # downstream preflight must rehash its supplied producer JSON before
        # matching this receipt; a bare matching source SHA is insufficient.
        # Hashing a JSON report does NOT authenticate its publisher or prove
        # the claimed source input/guest executed, and does not re-open any
        # deliberately unretained digest-only interior frame.
        "fingerprint_report_canonical_sha256": canonical_sha256(report),
        "frame_source_identity": dict(identity),
        "verified_relative_frame_window": {
            "start": start, "end": end,
            "required_frames": len(rows),
            "observation_phase": identity["observation_phase"],
            "original_frame_origin": identity["original_frame_origin"],
            "native_frame_origin": identity["native_frame_origin"],
        },
        "retained_raw_manifest_canonical_sha256": canonical_sha256(
            sorted(entries, key=lambda item: item["member"])),
        "verified_raw_frames": len(required_frames),
        "digest_only_equal_frames_not_independently_reopened": len(rows) - len(required_frames),
        "verified_raw_files": len(observed),
        "verified_differing_byte_occurrences": counts,
        "source_memory_bytes_independently_recomputed_for_retained_frames": True,
        "whole_race_opcode_equivalence_proven": False,
        "actual_guest_frame_acknowledgments_verified": False,
        "original_input_consumption_verified": False,
        "complete_USA_events_accepted": 0,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--report", type=Path, required=True)
    ap.add_argument("--retained-raw", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    r = verify(json.loads(args.report.read_text()), args.retained_raw)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(r, sort_keys=True, indent=2) + "\n")
    print("QA01 independent raw-frame verification: successful, zero event credit")


if __name__ == "__main__":
    main()
