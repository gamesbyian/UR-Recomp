#!/usr/bin/env python3
"""Independent ROM-free temporal census of a retained genuine QA-01 Bowl ZIP.

Reads only original 12-pair 128 KiB WRAM/8 KiB SRAM source observations.
No byte masking, phase shifts, emulator execution or USA event admission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from zipfile import BadZipFile, ZipFile

SCHEMA = "ur-qa01-bowl-raw-temporal-census/1"
OFFSETS = (334, 338, 339, 340, 341, 342, 343, 344, 345, 346, 349, 354)
SHA = re.compile(r"[0-9a-f]{64}\Z")
MEMORY_SIZES = {"sram": 8192, "wram": 131072}


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def original_bytes(archive: ZipFile, name: str, exact_length: int) -> bytes:
    try:
        data = archive.read(name)
    except KeyError as exc:
        raise ValueError("missing authentic source capture: " + name) from exc
    require(len(data) == exact_length, "wrong original guest byte length: " + name)
    return data


def audit(path: Path, expected_archive_sha256: str) -> dict:
    require(SHA.fullmatch(expected_archive_sha256) is not None,
            "expected original archive SHA256 must be 64 lowercase hex characters")
    require(path.is_file() and not path.is_symlink(), "missing original GitHub archive")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    require(digest == expected_archive_sha256, "original GitHub ZIP SHA256 mismatch")
    try:
        with ZipFile(path) as archive:
            names = archive.namelist()
            require(len(names) == len(set(names)), "duplicate original ZIP member paths")
            producer_bytes = archive.read("bowl-report.json")
            producer = json.loads(producer_bytes)
            independently_checked = json.loads(
                archive.read("bowl-independent-raw-audit.json"))
            require(hashlib.sha256(producer_bytes).hexdigest() ==
                    independently_checked.get("producer_sha256"),
                    "original producer hash differs from independent raw audit")
            source = producer.get("original_source_event") or {}
            handoff = producer.get("bowl_next_switcher_handoff") or {}
            require(
                producer.get("name") == "bowl" and
                producer.get("course_id") == "course:03" and
                source.get("original_entry_frame") == 8620 and
                source.get("original_result_frame") == 11985 and
                handoff.get("source_next_switcher_entry_offset") == 342 and
                handoff.get("source_controller_masks_modified") is False,
                "wrong or unanchored genuine original USA Bowl source")
            require(handoff.get("sample_offsets") == list(OFFSETS),
                    "noncanonical Bowl post-result sample offsets")
            require(
                independently_checked.get("case") == "bowl" and
                independently_checked.get("observed_raw_wram_sram_pairs") ==
                    len(OFFSETS) and
                independently_checked.get("accepted_event_credit") == 0 and
                independently_checked.get(
                    "independent_complete_usa_event_adjudication") == "HOLD",
                "original independent raw auditor missing or claims admission")
            claimed = handoff.get("samples")
            checked = independently_checked.get("checked_samples")
            require(isinstance(claimed, list) and len(claimed) == len(OFFSETS) and
                    isinstance(checked, list) and len(checked) == len(OFFSETS),
                    "incomplete genuine source observation population")
            temporal = []
            sram_signatures = []
            correlations = {(0xC6, 0xEF6): True, (0xC6, 0xF31): True,
                            (0xC8, 0xF33): True}
            for offset, row, checked_row in zip(OFFSETS, claimed, checked):
                require(row.get("offset_from_observed_bowl_result") == offset and
                        checked_row.get("offset") == offset,
                        "mismatched original report/raw observation offset")
                guests = row.get("fresh_guests") or {}
                memory = {}
                for side, label in (("ref", "original"), ("native", "native")):
                    guest = guests.get(label) or {}
                    require(guest.get("actual_host_frame") == 4683 + offset - 334,
                            "original/native guest frame does not match real source host")
                    memory[label] = {}
                    for kind, size in MEMORY_SIZES.items():
                        member = (
                            f"bowl/replay/{side}/bowl-next-switcher-{offset}.{kind}.bin")
                        image = original_bytes(archive, member, size)
                        require(hashlib.sha256(image).hexdigest() ==
                                guest.get(f"{kind}_sha256"),
                                "original guest " + kind +
                                " hash contradicts genuine producer: " + member)
                        memory[label][kind] = image
                sr, sn = memory["original"]["sram"], memory["native"]["sram"]
                wr, wn = memory["original"]["wram"], memory["native"]["wram"]
                sdiff = [(i, sr[i], sn[i]) for i in range(len(sr))
                         if sr[i] != sn[i]]
                wdiff = [i for i in range(len(wr)) if wr[i] != wn[i]]
                require(
                    len(sdiff) == row.get("full_sram_differing_byte_count") and
                    len(wdiff) == (row.get("full_wram_byte_difference") or {}).get(
                        "differing_byte_count") and
                    len(wdiff) == checked_row.get("unmasked_wram_differing_bytes") and
                    bool(sdiff) is not checked_row.get("full_sram_equal"),
                    "source-producer or independent raw census disagrees with bytes")
                sram_signatures.append(sdiff)
                for wram_addr, sram_offset in correlations:
                    if (wr[wram_addr] != sr[sram_offset] or
                            wn[wram_addr] != sn[sram_offset]):
                        correlations[wram_addr, sram_offset] = False
                temporal.append({
                    "source_result_relative_offset": offset,
                    "original_native_same_absolute_host_frame":
                        4683 + offset - 334,
                    "full_128k_wram_differing_bytes": len(wdiff),
                    "full_8192_sram_differing_bytes": len(sdiff),
                    "first_16_wram_differing_addresses": [
                        ("7E:" if i < 65536 else "7F:") + f"{i % 65536:04X}"
                        for i in wdiff[:16]],
                    "named_movie_original_native_states_equal":
                        row.get("triplet_named_states_equal"),
                    "all_original_wram_sram_bytes_compared": True,
                })
            count = sum(r["full_128k_wram_differing_bytes"] for r in temporal)
            require(count == independently_checked.get(
                "raw_unmasked_wram_differing_byte_occurrences"),
                "unmasked WRAM aggregate conflicts with original auditor")
            require(all(len(s) > 0 for s in sram_signatures),
                    "source-linked archived SRAM negative unexpectedly disappears")
            return {
                "schema": SCHEMA,
                "archive_sha256_independently_verified": digest,
                "original_producer_report_sha256":
                    hashlib.sha256(producer_bytes).hexdigest(),
                "original_usa_rom_sha256": producer["rom_sha256"],
                "original_movie_sha256": producer["original_movie_sha256"],
                "native_guest_executable_sha256":
                    producer["native_executable_sha256"],
                "source_event": "original USA 2014 Bowl course:03",
                "source_movie_bowl_result_frame": 11985,
                "source_movie_switcher_entry_frame": 12327,
                "source_result_to_switcher_frames": 342,
                "samples_and_raw_memory_verified": len(temporal),
                "full_128k_wram_differing_occurrences": count,
                "sram_differences_same_addresses_values_all_samples":
                    all(s == sram_signatures[0] for s in sram_signatures[1:]),
                "sram_differences_at_first_sample": [
                    {"offset": f"0x{i:04X}",
                     "original_byte": original, "native_byte": native}
                    for i, original, native in sram_signatures[0]],
                "observed_wram_sram_equal_value_correlations_all_samples": [
                    {"wram_address": f"7E:{w:04X}", "sram_offset": f"0x{s:04X}"}
                    for (w, s), yes in sorted(correlations.items()) if yes],
                "causal_mirror_or_writer_proven": False,
                "temporal_observations": temporal,
                "continuous_unsampled_state_or_complete_event_proven": False,
                "usa_event_admissions": 0,
                "scope": "read-only same-host sampled bytes; no CPU/APU/input writer attribution",
            }
    except (BadZipFile, KeyError, json.JSONDecodeError) as exc:
        raise ValueError("unreadable original ZIP or producer report: " + str(exc)) from exc


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--archive", type=Path, required=True)
    ap.add_argument("--expected-sha256", required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    try:
        result = audit(args.archive, args.expected_sha256)
    except (OSError, ValueError) as exc:
        ap.exit(2, "QA01_BOWL_TEMPORAL_CENSUS_INVALID: " + str(exc) + "\n")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="utf8")
    print("Verified source-authentic original/native 48 handoff memory files; " +
          str(result["full_128k_wram_differing_occurrences"]) +
          " unmasked sampled WRAM differences; USA event admissions: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
