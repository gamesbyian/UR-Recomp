#!/usr/bin/env python3
"""Bind independently checked source movie images, source inputs and guest memory.

Runs AFTER the existing genuine original/native USA Bowl producer and QA
auditors. Reads their original bytes. Never starts a game, modifies an input
or performs course acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from qa01_bowl_source_movie_memory import OFFSETS, diff

SCHEMA = "UR-QA01-BOWL-JOINT-MOVIE-INPUT-MEMORY-SOURCE/1"
SIZES = {"wram": 0x20000, "sram": 8192}


def must(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def read(path: Path, size: int | None = None) -> bytes:
    must(path.is_file() and not path.is_symlink(),
         "missing or symlinked authentic original source byte file: " + str(path))
    actual = path.read_bytes()
    if size is not None:
        must(len(actual) == size, "incorrect authentic original memory extent: " + str(path))
    return actual


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def audit(root: Path) -> dict:
    primary_bytes = read(root / "bowl-report.json")
    raw_bytes = read(root / "bowl-independent-raw-audit.json")
    route_bytes = read(root / "bowl-source-input-identity.json")
    primary = json.loads(primary_bytes)
    raw = json.loads(raw_bytes)
    route = json.loads(route_bytes)
    producer_sha = digest(primary_bytes)
    must(primary.get("name") == "bowl" and
         primary.get("course_id") == "course:03" and
         primary.get("native_backend") == "pinned-baldosa",
         "unexpected original 2014 Bowl source guest identity")
    must(raw.get("producer_sha256") == producer_sha and
         raw.get("case") == "bowl" and
         raw.get("observed_raw_wram_sram_pairs") == 12 and
         raw.get("accepted_event_credit") == 0 and
         raw.get("independent_complete_usa_event_adjudication") == "HOLD",
         "original 48 raw guest image independent audit unbound to producer")
    supplied = route.get("route") or {}
    must(route.get("original_case") == "bowl" and
         route.get("original_producer_sha256") == producer_sha and
         route.get("usa_event_admissions") == 0 and
         supplied.get("original_2014_movie_controller_window_recomputed") is True and
         supplied.get("original_native_supplied_masks_and_durations_equal") is True and
         supplied.get("guest_controller_consumption_proven") is False and
         supplied.get("release_credit") == 0 and
         supplied.get("source_original_movie_window_sha256") ==
             primary.get("original_movie_window_sha256") and
         supplied.get("native_supplied_input_shift_exact") ==
             primary.get("native_frame_shift") and
         type(supplied.get("input_event_rows_per_guest")) is int and
         supplied["input_event_rows_per_guest"] > 0,
         "2014 source movie controller input proof missing or from different producer")
    movie = primary.get("bowl_source_movie_three_guest_memory") or {}
    must(movie.get("sample_offsets") == list(OFFSETS) and
         movie.get("sample_count") == len(OFFSETS) and
         movie.get("original_movie_controller_masks_modified") is False and
         movie.get("release_complete_event_credit") == 0,
         "authentic original 2014 movie source memory not captured")
    rows = movie.get("samples")
    must(isinstance(rows, list) and len(rows) == len(OFFSETS),
         "original movie three-guest raw capture is incomplete")
    counts = []
    for offset, row in zip(OFFSETS, rows):
        must(row.get("offset_from_source_movie_bowl_result") == offset and
             row.get("movie_absolute_host_frame") == 11985 + offset,
             "original 2014 movie frame/host identity changed")
        blocks = {}
        for side, subdir, tag, claim in (
            ("movie", "source", f"source-bowl-switcher-{offset:03d}",
             row.get("movie_original")),
            ("original", "replay/ref", f"bowl-next-switcher-{offset:03d}",
             (row.get("fresh_guests") or {}).get("original")),
            ("native", "replay/native", f"bowl-next-switcher-{offset:03d}",
             (row.get("fresh_guests") or {}).get("native")),
        ):
            must(isinstance(claim, dict), "missing original source/movie/guest memory metadata")
            blocks[side] = {}
            for kind, length in SIZES.items():
                path = root / "bowl" / subdir / f"{tag}.{kind}.bin"
                data = read(path, length)
                must(digest(data) == claim.get(kind + "_sha256"),
                     "original 2014 source/movie/guest memory SHA256 differs: " + str(path))
                blocks[side][kind] = data
        for guest in ("original", "native"):
            claim = row["fresh_guests"][guest]
            observed = {
                k: diff(blocks["movie"][k], blocks[guest][k]) for k in SIZES
            }
            for kind in SIZES:
                must(observed[kind] == claim.get(kind + "_source_vs_guest"),
                     "original 2014 source/movie/guest unmasked " + kind +
                     " difference receipt contradicted by primary raw bytes")
            counts.append({
                "source_movie_result_relative_frame": offset,
                "guest": guest,
                "source_movie_vs_guest_full_wram_differences":
                    observed["wram"]["different_byte_count"],
                "source_movie_vs_guest_full_sram_differences":
                    observed["sram"]["different_byte_count"],
            })
    return {
        "schema": SCHEMA,
        "original_producer_sha256": producer_sha,
        "independent_raw_guest_audit_sha256": digest(raw_bytes),
        "source_original_movie_controller_receipt_sha256": digest(route_bytes),
        "original_source_movie_sha256": primary["original_movie_sha256"],
        "actual_2014_movie_source_images_independently_rehashed": len(OFFSETS) * 2,
        "actual_fresh_guest_memory_images_independently_rehashed": len(OFFSETS) * 4,
        "same_producer_input_and_memory_evidence_proven": True,
        "source_movie_guest_full_byte_differences": counts,
        "guest_consumed_input_proven": False,
        "continuous_course_emulator_equivalence_proven": False,
        "shipping_windows_persistence_proven": False,
        "accepted_complete_usa_events": 0,
        "scope": "same-run original source input+movie+guest raw receipt identity only",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--artifact-root", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    try:
        result = audit(args.artifact_root)
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        p.exit(2, "QA01_BOWL_JOINT_SOURCE_PROVENANCE_INVALID: " + str(exc) + "\n")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="utf8")
    print("Authentic Bowl input and 2014 movie/guest memory linked to one producer; " +
          "accepted USA events: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
