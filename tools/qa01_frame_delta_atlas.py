#!/usr/bin/env python3
"""Independently build a *noncausal* WRAM/SRAM timeline from retained QA01 raw.

Reopens the project's independently verified original/native raw source bytes.
Never fills absent equal-frame bytes from a hash. Reports each missing interior
raw frame explicitly. Never calls a frame-level difference a consumed CPU value.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import qa01_frame_fingerprint as frames
import qa01_verify_frame_capture as independent

SCHEMA = "ur-qa01-independent-frame-delta-atlas/1"


def address(kind: str, offset: int) -> str:
    if kind == "sram":
        return f"SRAM:{offset:04X}"
    return ("7E:" if offset < 65536 else "7F:") + f"{offset % 65536:04X}"


def atlas(report: dict, root: Path, max_deltas: int = 10000) -> dict:
    frames.must(type(max_deltas) is int and 0 < max_deltas <= 1000000,
                "invalid explicit unmasked atlas budget")
    verdict = independent.verify(report, root)
    start, end = report["coverage"]["start"], report["coverage"]["end"]
    frames.must(end - start + 1 <= 200,
                "atlas is a bounded diagnostic, not a 1.34GiB whole-race materializer")
    indexed = {(x["relative_frame"], x["kind"], x["guest"]): x
               for x in report["raw_retained_members"]}
    census: dict[str, dict] = {}
    timeline = []
    previous = None
    independently_reopened = 0
    equals_unavailable = []
    total = {"wram": 0, "sram": 0}
    for row in report["rows"]:
        rel = row["relative_frame"]
        have_raw = all((rel, kind, guest) in indexed
                       for kind in ("wram", "sram")
                       for guest in ("original", "native"))
        if not have_raw:
            # The independent validator proved omitted pairs have zero
            # reported byte deltas, but it could not independently reopen
            # those missing source images. Never fabricate their transitions.
            frames.must(all(row["types"][kind]["unmasked_differing_byte_count"] == 0
                            for kind in ("wram", "sram")),
                        "different raw pair omitted from temporal observation")
            timeline.append({
                "relative_frame": rel,
                "original_actual_host_frame": row["original_actual_host_frame"],
                "native_actual_host_frame": row["native_actual_host_frame"],
                "raw_scope": "equal_by_digest_only_source_pair_not_reopened",
                "original_native_observed_deltas": None,
                "intra_guest_changes_since_previous": None,
            })
            equals_unavailable.append(rel)
            previous = None
            continue
        independently_reopened += 1
        snapshots: dict[str, dict[str, bytes]] = {"original": {}, "native": {}}
        observations = []
        transition = {"original": {}, "native": {}}
        for kind, size in (("wram", frames.WRAM), ("sram", frames.SRAM)):
            for guest in ("original", "native"):
                member = indexed[rel, kind, guest]["member"]
                data = frames.raw(root / member, size)
                frames.must(frames.digest(data) ==
                            row["types"][kind][guest + "_sha256"],
                            "raw temporal source member hash changed")
                snapshots[guest][kind] = data
            a, b = snapshots["original"][kind], snapshots["native"][kind]
            for index, (u, v) in enumerate(zip(a, b)):
                if u == v:
                    continue
                frames.must(len(observations) < max_deltas,
                            "explicit unmasked frame delta budget exceeded")
                name = address(kind, index)
                observations.append({"address": name, "original_hex": f"{u:02X}",
                                     "native_hex": f"{v:02X}"})
                member = census.setdefault(name, {
                    "first_observed_relative_frame": rel, "occurrences": 0,
                    "frames": [],
                })
                member["occurrences"] += 1
                member["frames"].append(rel)
                total[kind] += 1
            if previous is not None and rel == previous[0] + 1:
                for guest in ("original", "native"):
                    now = snapshots[guest][kind]
                    prior = previous[1][guest][kind]
                    transition[guest][kind] = sum(x != y for x, y in zip(now, prior))
            else:
                for guest in ("original", "native"):
                    transition[guest][kind] = None
        # No raw predecessor means *no measured transition*, not a
        # synthetic collection of per-bank zero changes or inferred values.
        if previous is None or rel != previous[0] + 1:
            transition = None
        timeline.append({
            "relative_frame": rel,
            "original_actual_host_frame": row["original_actual_host_frame"],
            "native_actual_host_frame": row["native_actual_host_frame"],
            "raw_scope": "both_actual_guest_images_independently_reopened",
            "original_native_observed_deltas": observations,
            "intra_guest_changes_since_previous": transition,
        })
        previous = (rel, snapshots)
    frames.must(total == report["full_unmasked_differing_byte_occurrences"],
                "unmasked census differs from original full report")
    frames.must(independently_reopened == verdict["verified_raw_frames"] and
                len(equals_unavailable) ==
                verdict["digest_only_equal_frames_not_independently_reopened"],
                "raw digest-only provenance inconsistent with independent verifier")
    return {
        "schema": SCHEMA,
        "fingerprint_report_canonical_sha256":
            verdict["fingerprint_report_canonical_sha256"],
        "source_identity": report["source_identity"],
        "window": {"start": start, "end": end},
        "full_original_native_raw_frame_pairs_independently_reopened":
            independently_reopened,
        "equal_digest_only_frame_pairs_not_independently_reopened":
            equals_unavailable,
        "unmasked_original_native_byte_occurrences": total,
        "per_address_occurrences": dict(sorted(census.items())),
        "timeline": timeline,
        "first_genuinely_consumed_CPU_or_SPC_divergence_proven": False,
        "race_before_window_or_between_frame_instruction_parity_proven": False,
        "accepted_USA_events": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fingerprints", required=True, type=Path)
    parser.add_argument("--retained-raw", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--max-deltas-per-frame", type=int, default=10000)
    args = parser.parse_args()
    frames.must(not args.output.exists(), "refuse overwrite of independently reviewed atlas")
    result = atlas(json.loads(args.fingerprints.read_text()), args.retained_raw,
                   max_deltas=args.max_deltas_per_frame)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("QA01 source-bound raw delta atlas: noncausal; zero USA event credit")


if __name__ == "__main__":
    main()
