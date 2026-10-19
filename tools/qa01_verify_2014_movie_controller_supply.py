#!/usr/bin/env python3
"""Read original 2014 Zoo SMV bytes and independently bind guest input files.

Only the *supplied* controller masks are verified. No CPU joypad polling, guest
opcode ordering, native frame equivalence, or QA01 event acceptance is implied.
This pins one real historical Zoom Zoo movie span, not an arbitrary fixture.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import extract_historical_smv_scene_window as smv
import qa01_verify_supplied_controller_streams as inputs


SCHEMA = "ur-qa01-original-2014-zoo-movie-controller-supply/1"
PINNED_MOVIE_CONTAINER_SHA256 = (
    "06dce29e9d36997fc2a1fac4bab72180ab6c8096366cfcf05780c1b2dea4b442"
)
PINNED_RAW_WINDOW_SHA256 = (
    "7b03f40e3401d844c16c7c4e1cc7375e5419f33882793c8187dcebc88dbc8c93"
)
MOVIE_RACE_ENTRY = 3190
MOVIE_RACE_RESULT = 8353
SOURCE_RACE_RESULT_RELATIVE = 5163
SOURCE_WINDOW_FRAMES = SOURCE_RACE_RESULT_RELATIVE + 280 + 6


def require(value: bool, why: str) -> None:
    if not value:
        raise ValueError(why)


def canonical(data: list[dict]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def audit(baseline: dict, captured: dict, files: dict[str, Path],
          movie: Path, metadata: Path) -> dict:
    # A forged JSON reviewer is insufficient; re-open the four supplied
    # Snes9x/Baldosa event files before opening the independent movie bytes.
    supplied = inputs.audit(baseline, captured, files)
    require(baseline.get("name") == captured.get("name") == "zoom-zoo"
            and baseline.get("course_id") == captured.get("course_id") ==
                "course:02", "not original source Zoom Zoo course:02")
    for tag, record in (("off", baseline), ("on", captured)):
        event = record.get("original_source_event")
        require(type(event) is dict and
                event.get("original_entry_frame") == MOVIE_RACE_ENTRY and
                event.get("original_result_frame") == MOVIE_RACE_RESULT and
                event.get("source_active_frames_to_result") ==
                    SOURCE_RACE_RESULT_RELATIVE and
                record.get("zoo_next_bowl_handoff") is not None and
                record.get("original_movie_sha256") ==
                    PINNED_MOVIE_CONTAINER_SHA256 and
                record.get("original_movie_window_sha256") ==
                    PINNED_RAW_WINDOW_SHA256,
                tag + " does not name exact pinned 2014 Zoo movie window")
    require(movie.is_file() and not movie.is_symlink() and
            metadata.is_file() and not metadata.is_symlink(),
            "missing/symlinked original archive or pinned source metadata")
    archive_data = movie.read_bytes()
    archive_sha = hashlib.sha256(archive_data).hexdigest()
    require(archive_sha == PINNED_MOVIE_CONTAINER_SHA256,
            "original 2014 movie container SHA256 is not source-authentic")
    meta = json.loads(metadata.read_text(encoding="utf-8"))
    require(type(meta) is dict and
            meta.get("path") ==
                "reference/imported/tas-bots/dessyreqt-4250-submission.smv" and
            meta.get("container") == "zip" and
            meta.get("contained_name") == "100% run.smv" and
            meta.get("container_size_bytes") == len(archive_data),
            "unqualified 2014 original SMV metadata")
    source_data, member = smv.read_movie(movie)
    require(member == meta["contained_name"] and
            len(source_data) == meta["smv_size_bytes"],
            "original SMV container member or decompressed length differs")
    window = smv.window(source_data, meta, MOVIE_RACE_ENTRY, SOURCE_WINDOW_FRAMES)
    require(window["raw_controller_window_sha256"] == PINNED_RAW_WINDOW_SHA256
            and window["movie_frame_range"] ==
                [MOVIE_RACE_ENTRY, MOVIE_RACE_ENTRY + SOURCE_WINDOW_FRAMES - 1],
            "actual 2014 movie controller bytes do not match source window")
    derived = [
        {"start_relative_to_actual_guest_entry": part["start"],
         "duration_frames": part["duration"],
         "nonzero_mask_hex": f"{int(part['mask'], 16):03x}"}
        for part in window["relative_input_segments"] if int(part["mask"], 16)
    ]
    require(derived == supplied["normalized_segments"] and
            len(derived) == supplied["normalized_segment_population"] and
            hashlib.sha256(canonical(derived).encode("ascii")).hexdigest() ==
                supplied["normalized_segment_sha256"],
            "actual original movie pad events differ from supplied original/native input files")
    return {
        "schema": SCHEMA,
        "source_git_sha": supplied["repository_source_sha"],
        "original_2014_movie_container_sha256": archive_sha,
        "original_2014_decompressed_SMV_member": member,
        "actual_movie_window_controller_sha256":
            window["raw_controller_window_sha256"],
        "original_movie_race_entry_frame": MOVIE_RACE_ENTRY,
        "original_movie_result_frame": MOVIE_RACE_RESULT,
        "movie_window_inclusive_frame_range": window["movie_frame_range"],
        "source_window_frames_independently_decoded": SOURCE_WINDOW_FRAMES,
        "source_movie_nonzero_input_segments": len(derived),
        "supplied_original_native_guest_segments_independently_reopened":
            supplied["normalized_segment_population"],
        "exact_movie_to_guest_supplied_controller_segments_equal": True,
        "normalized_input_segments_sha256": supplied["normalized_segment_sha256"],
        "original_guest_real_input_poll_consumption_proven": False,
        "native_guest_real_input_poll_consumption_proven": False,
        "entire_race_CPU_SPC_causality_or_parity_proven": False,
        "full_USA_events_accepted": 0,
        "release_QA_gates_awarded": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ("baseline", "captured", "off-original-input",
                  "off-native-input", "on-original-input", "on-native-input",
                  "movie", "movie-metadata", "output"):
        parser.add_argument("--" + field, type=Path, required=True)
    a = parser.parse_args()
    require(not a.output.exists(), "refuse to overwrite original source receipt")
    result = audit(
        json.loads(a.baseline.read_text()), json.loads(a.captured.read_text()),
        {"off_original": a.off_original_input,
         "off_native": a.off_native_input,
         "on_original": a.on_original_input,
         "on_native": a.on_native_input},
        a.movie, a.movie_metadata)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print("Original 2014 movie to both actual supplied guest input streams: qualified; CPU polls unknown, 0/45")


if __name__ == "__main__":
    main()
