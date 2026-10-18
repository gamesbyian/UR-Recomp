#!/usr/bin/env python3
"""ROM-free original USA 2014 Bowl source movie / fresh Snes9x / native crosswalk.

Independently reopen an authentic original Actions ZIP. Relate *observed*
unmasked WRAM differences to value-identical SRAM differences at a candidate
byte displacement, retaining unmatched differences. This proves no SRAM
copy instruction, byte writer, emulation timing, or complete USA event.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from zipfile import BadZipFile, ZipFile

SCHEMA = "UR-QA01-2014-BOWL-SOURCE-SRAM-CROSSWALK/1"
OFFSETS = (334, 339, 340, 341, 342, 343, 344, 354)
OFFSET_CANDIDATE = 0xE6B
SIZES = {"wram": 131072, "sram": 8192}


def require(value: bool, reason: str) -> None:
    if not value:
        raise ValueError(reason)


def read_exact(archive: ZipFile, name: str, size: int) -> bytes:
    try:
        info = archive.getinfo(name)
    except KeyError as exc:
        raise ValueError("missing true source movie/guest memory: " + name) from exc
    require(not name.startswith("/") and ".." not in Path(name).parts,
            "unsafe original archive member name")
    require(info.file_size == size, "truncated or oversized original memory " + name)
    data = archive.read(info)
    require(len(data) == size, "incomplete original archive member " + name)
    return data


def pair(source: dict[str, bytes], guest: dict[str, bytes]) -> dict:
    """Every WRAM and SRAM byte is counted; matched differences are NOT masked."""
    w = [(i, a, b) for i, (a, b) in enumerate(
        zip(source["wram"], guest["wram"]))
        if a != b]
    s = [(i, a, b) for i, (a, b) in enumerate(
        zip(source["sram"], guest["sram"]))
        if a != b]
    mapped = [(i, a, b) for i, a, b in w
              if i + OFFSET_CANDIDATE < len(source["sram"])
              and source["sram"][i + OFFSET_CANDIDATE] == a
              and guest["sram"][i + OFFSET_CANDIDATE] == b]
    matched = {i for i, _, _ in mapped}
    untouched = [(i, a, b) for i, a, b in w if i not in matched]
    return {
        "all_wram_bytes_compared": len(source["wram"]),
        "all_sram_bytes_compared": len(source["sram"]),
        "unmasked_wram_different_byte_count": len(w),
        "unmasked_sram_different_byte_count": len(s),
        "wram_differences_matching_sram_at_plus_0xE6B": len(mapped),
        "wram_differences_not_matching_that_sram_mapping": len(untouched),
        "first_16_unmatched_wram_differences": [
            {"wram_address": ("7E:" if i < 0x10000 else "7F:") +
             f"{i % 0x10000:04X}", "source_byte": a, "guest_byte": b}
            for i, a, b in untouched[:16]
        ],
        "first_16_sram_mapped_wram_differences": [
            {"wram_address": f"7E:{i:04X}",
             "corresponding_sram_offset": f"0x{i + OFFSET_CANDIDATE:04X}",
             "source_byte": a, "guest_byte": b}
            for i, a, b in mapped[:16]
        ],
        "memory_writes_or_causal_mirroring_proven": False,
        "masked_or_waived_wram_bytes": 0,
    }


def verify_claimed_pair(observed: dict, claimed: dict) -> None:
    require(observed["unmasked_wram_different_byte_count"] ==
            claimed.get("wram_source_vs_guest", {}).get("different_byte_count"),
            "raw source/movie versus guest WRAM contradicts original producer")
    require(observed["unmasked_sram_different_byte_count"] ==
            claimed.get("sram_source_vs_guest", {}).get("different_byte_count"),
            "raw source/movie versus guest SRAM contradicts original producer")


def audit(path: Path, expected_zip_sha256: str) -> dict:
    require(len(expected_zip_sha256) == 64 and all(
        c in "0123456789abcdef" for c in expected_zip_sha256),
        "expected original ZIP SHA256 must be lowercase 64-digit hex")
    require(path.is_file() and not path.is_symlink(),
            "missing or symlinked genuine GitHub Actions archive")
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    require(actual == expected_zip_sha256, "original source movie ZIP SHA mismatch")
    try:
        with ZipFile(path) as archive:
            names = archive.namelist()
            require(len(set(names)) == len(names), "duplicate original archive member")
            report_bytes = archive.read("bowl-report.json")
            report = json.loads(report_bytes)
            event = report.get("original_source_event", {})
            require(report.get("name") == "bowl" and
                    report.get("course_id") == "course:03" and
                    report.get("native_backend") == "pinned-baldosa" and
                    event.get("original_entry_frame") == 8620 and
                    event.get("original_result_frame") == 11985,
                    "wrong authentic 2014 USA Bowl source event")
            evidence = report.get("bowl_source_movie_three_guest_memory", {})
            require(evidence.get("sample_offsets") == list(OFFSETS) and
                    evidence.get("sample_count") == len(OFFSETS) and
                    evidence.get("original_movie_controller_masks_modified") is False and
                    evidence.get("release_complete_event_credit") == 0,
                    "not an exact eight-point 2014 source-unaltered observation")
            original = evidence.get("samples")
            require(isinstance(original, list) and len(original) == len(OFFSETS),
                    "missing complete original three-guest evidence")
            pairs = []
            for offset, row in zip(OFFSETS, original):
                require(row.get("offset_from_source_movie_bowl_result") == offset and
                        row.get("movie_absolute_host_frame") == 11985 + offset,
                        "original source movie host frame is not independently registered")
                blocks = {}
                for side, prefix, claimed in (
                    ("movie", f"bowl/source/source-bowl-switcher-{offset:03d}",
                     row.get("movie_original", {})),
                    ("original", f"bowl/replay/ref/bowl-next-switcher-{offset}",
                     row.get("fresh_guests", {}).get("original", {})),
                    ("native", f"bowl/replay/native/bowl-next-switcher-{offset}",
                     row.get("fresh_guests", {}).get("native", {})),
                ):
                    require(isinstance(claimed, dict),
                            "missing actual original/native/movie capture claim")
                    if side != "movie":
                        clocks = report.get("comparison", {}).get(
                            "terminal_result_guest_frame", {})
                        expected = report["reference_entry" if side == "original"
                                          else "native_entry"] + clocks[
                                              "reference_relative" if side == "original"
                                              else "native_relative"] + offset
                        require(claimed.get("absolute_host_frame") == expected,
                                "fresh source-guest frame does not match actual result clock")
                    blocks[side] = {}
                    for kind, length in SIZES.items():
                        raw = read_exact(archive, f"{prefix}.{kind}.bin", length)
                        require(hashlib.sha256(raw).hexdigest() ==
                                claimed.get(kind + "_sha256"),
                                "original movie/guest " + kind +
                                " hash disagrees with producer: " + prefix)
                        blocks[side][kind] = raw
                comparison = {}
                for first, second, key in (
                    ("movie", "original", "movie_vs_fresh_original"),
                    ("movie", "native", "movie_vs_native"),
                    ("original", "native", "fresh_original_vs_native"),
                ):
                    result = pair(blocks[first], blocks[second])
                    if first == "movie":
                        verify_claimed_pair(result, row["fresh_guests"][second])
                    comparison[key] = result
                pairs.append({
                    "source_movie_relative_result_offset": offset,
                    "source_movie_absolute_host_frame": 11985 + offset,
                    "cross_guest_pairs": comparison,
                })
            return {
                "schema": SCHEMA,
                "actual_original_zip_sha256": actual,
                "original_producer_sha256":
                    hashlib.sha256(report_bytes).hexdigest(),
                "source_2014_movie_sha256": report["original_movie_sha256"],
                "native_guest_sha256": report["native_executable_sha256"],
                "source_event": "USA original Bowl 2014, course:03",
                "registered_original_movie_samples": len(pairs),
                "candidate_wram_to_sram_offset": "0x0E6B",
                "candidate_displacement_selected_for_diagnostic_only": True,
                "all_128k_wram_and_8k_sram_bytes_compared_unmasked": True,
                "temporal_observations": pairs,
                "independent_first_writer_or_copy_direction_proven": False,
                "continuous_full_gameplay_proven": False,
                "release_usa_event_admissions": 0,
            }
    except (BadZipFile, KeyError, json.JSONDecodeError) as exc:
        raise ValueError("invalid genuine source-movie archive or original JSON") from exc


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-zip", type=Path, required=True)
    p.add_argument("--expected-zip-sha256", required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    try:
        result = audit(args.original_zip, args.expected_zip_sha256)
    except (OSError, ValueError, TypeError) as exc:
        p.exit(2, "QA01_BOWL_MOVIE_SRAM_CROSSWALK_INVALID: " + str(exc) + "\n")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    first = result["temporal_observations"][0]["cross_guest_pairs"]
    print("Verified real eight original-source triplets; first sampled original movie" +
          " vs fresh Snes9x: " +
          str(first["movie_vs_fresh_original"][
              "wram_differences_matching_sram_at_plus_0xE6B"]) +
          "/" + str(first["movie_vs_fresh_original"][
              "unmasked_wram_different_byte_count"]) +
          " candidate SRAM-corresponding unmasked WRAM differences; USA event admission 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
