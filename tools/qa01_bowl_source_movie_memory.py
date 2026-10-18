#!/usr/bin/env python3
"""Opt-in original 2014 Bowl source MOVIE vs fresh original/native memory.

An additional source-guest witness, not source-time normalization, acceptance
or a patch to either emulation core. Each of eight actual movie frames has its
own raw 128KiB WRAM and 8KiB SRAM. Fresh original/native compare from separate
result-relative clocks, retaining observed differences without exclusions.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

SOURCE_RESULT = 11985
NEXT_SWITCHER = 12327
OFFSETS = (334, 339, 340, 341, 342, 343, 344, 354)
SCHEMA = "UR-QA01-BOWL-SOURCE-MOVIE-THREE-GUEST-MEMORY/1"
WRAM_SIZE = 0x20000
SRAM_SIZE = 8192


class SourceMovieMemoryError(ValueError):
    pass


def source_movie_scan_script(horizon: int) -> str:
    """Include real intermediate source dumps without changing SMV controls."""
    if type(horizon) is not int or not 12500 <= horizon <= 24000:
        raise SourceMovieMemoryError("source horizon must contain full handoff")
    last = 0
    lines = []
    for offset in OFFSETS:
        target = SOURCE_RESULT + offset
        if target <= last or target >= horizon:
            raise SourceMovieMemoryError("invalid original movie capture horizon")
        lines.extend((f"wait {target - last}",
                      f"dump source-bowl-switcher-{offset:03d}"))
        last = target
    lines.extend((f"wait {horizon - last}", "dump source-horizon", "quit"))
    return "\n".join(lines) + "\n"


def raw_image(folder: Path, tag: str, kind: str, size: int) -> bytes:
    path = folder / f"{tag}.{kind}.bin"
    if not path.is_file() or path.is_symlink():
        raise SourceMovieMemoryError(f"missing actual source/guest {kind} dump: {path}")
    value = path.read_bytes()
    if len(value) != size:
        raise SourceMovieMemoryError(f"truncated real source/guest {kind} dump: {path}")
    return value


def diff(source: bytes, guest: bytes) -> dict:
    """Compare every original SRAM/WRAM byte, with no hidden exclusions."""
    if len(source) != len(guest):
        raise SourceMovieMemoryError("cannot compare different memory sizes")
    changed = [i for i, (a, b) in enumerate(zip(source, guest)) if a != b]
    return {
        "all_bytes_examined": len(source),
        "excluded_bytes": 0,
        "different_byte_count": len(changed),
        "byte_exact": not changed,
        "first_16_difference_offsets": changed[:16],
        "first_16_difference_values": [
            {"offset": i, "source_movie_byte": source[i], "fresh_guest_byte": guest[i]}
            for i in changed[:16]],
    }


def observe_movie_guest_memory(
        movie_dir: Path, reference_dir: Path, native_dir: Path,
        movie_log: str, reference_log: str, native_log: str,
        source_states: dict[int, dict], source_proof: dict, reference_entry: int,
        native_entry: int, reference_result_relative: int,
        native_result_relative: int, *, observed_dump_frame,
        decode_sram) -> dict:
    """Test exact movie host tags, true loaded memory and honest clock axes."""
    if (not isinstance(source_proof, dict)
            or source_proof.get("source_result_host_frame") != SOURCE_RESULT
            or source_proof.get("source_next_switcher_entry_host_frame") != NEXT_SWITCHER
            or source_proof.get("source_result_to_next_active_entry_frames") != 342
            or source_proof.get("source_active_eight_consecutive_frames") is not True
            or source_proof.get("source_controller_masks_modified") is not False):
        raise SourceMovieMemoryError("not the authenticated 2014 Bowl→Switcher source")
    if (any(type(v) is not int or v < 0 for v in
            (reference_entry, native_entry, reference_result_relative,
             native_result_relative))):
        raise SourceMovieMemoryError("invalid independently observed fresh clocks")
    samples = []
    for offset in OFFSETS:
        movie_frame = SOURCE_RESULT + offset
        movie_tag = f"source-bowl-switcher-{offset:03d}"
        movie_host = observed_dump_frame(movie_log, movie_tag)
        if movie_host != movie_frame:
            raise SourceMovieMemoryError("source movie dump registered at wrong host frame")
        source_wram = raw_image(movie_dir, movie_tag, "wram", WRAM_SIZE)
        source_sram = raw_image(movie_dir, movie_tag, "sram", SRAM_SIZE)
        source_named = {
            "menu": source_wram[0x9F],
            "track": source_wram[0xCE],
            "in_race": source_wram[0x313]}
        trace_state = source_states.get(movie_frame)
        if (not isinstance(trace_state, dict)
                or any(type(trace_state.get(k)) is not int or
                       trace_state[k] != v for k, v in source_named.items())):
            raise SourceMovieMemoryError(
                f"original source trace differs from actual movie dump at {movie_frame}")
        source_rank = decode_sram(movie_dir / f"{movie_tag}.sram.bin", 2)
        guests = {}
        for side, directory, log, entry, relative in (
                ("original", reference_dir, reference_log,
                 reference_entry, reference_result_relative),
                ("native", native_dir, native_log,
                 native_entry, native_result_relative)):
            tag = f"bowl-next-switcher-{offset:03d}"
            observed = observed_dump_frame(log, tag)
            expected = entry + relative + offset
            if observed != expected:
                raise SourceMovieMemoryError(f"{side} fresh guest host clock mismatch")
            guest_wram = raw_image(directory, tag, "wram", WRAM_SIZE)
            guest_sram = raw_image(directory, tag, "sram", SRAM_SIZE)
            named = {k: guest_wram[i] for k, i in
                     (("menu", 0x9F), ("track", 0xCE), ("in_race", 0x313))}
            record = decode_sram(directory / f"{tag}.sram.bin", 2)
            guests[side] = {
                "absolute_host_frame": observed,
                "named_state": named,
                "named_fields_different_from_movie": [
                    k for k in source_named if source_named[k] != named[k]],
                "wram_sha256": hashlib.sha256(guest_wram).hexdigest(),
                "sram_sha256": hashlib.sha256(guest_sram).hexdigest(),
                "wram_source_vs_guest": diff(source_wram, guest_wram),
                "sram_source_vs_guest": diff(source_sram, guest_sram),
                "crawler_bowl_rank0": record["crawler_record_three_ranks"][0],
                "ranked_checksum_matches": record["record_table_checksum_matches_at_sample"],
            }
        samples.append({
            "offset_from_source_movie_bowl_result": offset,
            "movie_absolute_host_frame": movie_frame,
            "movie_original": {
                "named_state": source_named,
                "wram_sha256": hashlib.sha256(source_wram).hexdigest(),
                "sram_sha256": hashlib.sha256(source_sram).hexdigest(),
                "crawler_bowl_rank0": source_rank["crawler_record_three_ranks"][0],
                "ranked_checksum_matches": source_rank["record_table_checksum_matches_at_sample"],
            },
            "fresh_guests": guests,
        })
    return {
        "schema": SCHEMA,
        "source_original_bowl_result_movie_frame": SOURCE_RESULT,
        "source_original_next_switcher_movie_frame": NEXT_SWITCHER,
        "movie_source_fresh_guest_clocks_independent": True,
        "original_movie_controller_masks_modified": False,
        "raw_source_sram_wram_bytes_retained_separately": True,
        "sample_offsets": list(OFFSETS),
        "sample_count": len(samples),
        "first_movie_vs_fresh_original_named_difference_offset": next(
            (row["offset_from_source_movie_bowl_result"] for row in samples
             if row["fresh_guests"]["original"]["named_fields_different_from_movie"]),
            None),
        "first_movie_vs_fresh_native_named_difference_offset": next(
            (row["offset_from_source_movie_bowl_result"] for row in samples
             if row["fresh_guests"]["native"]["named_fields_different_from_movie"]),
            None),
        "first_movie_vs_fresh_original_raw_wram_difference_offset": next(
            (row["offset_from_source_movie_bowl_result"] for row in samples
             if not row["fresh_guests"]["original"]["wram_source_vs_guest"]["byte_exact"]),
            None),
        "all_source_and_fresh_ranked_bowl_scores_764": all(
            side["crawler_bowl_rank0"]["value_word"] == 764
            and side["ranked_checksum_matches"]
            for row in samples for side in (
                row["movie_original"], row["fresh_guests"]["original"],
                row["fresh_guests"]["native"])),
        "samples": samples,
        "every_source_or_guest_gameplay_frame_proven": False,
        "cpu_spc_causality_proven": False,
        "shipping_windows_candidate_proven": False,
        "cold_disk_durability_proven": False,
        "release_complete_event_credit": 0,
    }
