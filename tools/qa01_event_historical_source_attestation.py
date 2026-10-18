#!/usr/bin/env python3
"""Reopen canonical 2014 SMV and independently reconstruct QA01 event input.

The source event entry and resulting controller-window SHA are known original
guest observations. A long-enough 2014 movie span is selected ONLY when the
raw source-window SHA from the producer matches exactly. The result is passed
to the already existing supplied-controller transport validator. This
does NOT establish what controller inputs the guest CPU actually consumed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import extract_historical_smv_scene_window as movie

SOURCE_2014_ARCHIVE_SHA256 = (
    "06dce29e9d36997fc2a1fac4bab72180ab6c8096366cfcf05780c1b2dea4b442"
)
SOURCE_EVENT_ANCHORS = {
    "zoom-zoo": ("course:02", 3190, 8353),
    "bowl": ("course:03", 8620, 11985),
    "switcher": ("course:04", 12327, 17030),
}
MAX_FOLLOWTHROUGH = 2048


def select_source_controller_length(movie_bytes: bytes, metadata: dict,
                                    movie_entry: int, source_duration: int,
                                    claimed_raw_window_sha256: str) -> int:
    """Identify a unique *existing* 2014-movie span by source raw SHA.

    Producer options choose bounded post-result followthrough; the original
    event report provides the immutable hash, but not that length. Probe
    possible exact raw byte lengths. Never change controller masks or infer
    guest entry from frame-zero movie timing.
    """
    if (type(movie_entry) is not int or type(source_duration) is not int
            or source_duration < 601 or movie_entry < 0):
        raise ValueError("invalid source-2014 original movie event duration/entry")
    if (not isinstance(claimed_raw_window_sha256, str)
            or len(claimed_raw_window_sha256) != 64
            or any(c not in "0123456789abcdef"
                   for c in claimed_raw_window_sha256)):
        raise ValueError("missing exact original 2014 source-controller SHA256")
    frame_count = metadata.get("sample_count")
    controller_offset = metadata.get("controller_data_offset")
    if (type(frame_count) is not int or type(controller_offset) is not int
            or frame_count <= movie_entry + source_duration
            or controller_offset < 64):
        raise ValueError("original 2014 movie metadata cannot cover source event")
    # Original movie.window performs strict SMV header/CRC/NTSC/controller
    # validation AFTER one unique matching source segment length is found.
    start = controller_offset + movie_entry * 2
    low = source_duration + 1
    high = min(
        source_duration + MAX_FOLLOWTHROUGH,
        movie.LIMIT,
        frame_count - movie_entry,
    )
    if high < low or start + 2 * high > len(movie_bytes):
        raise ValueError("truncated original SMV controller stream")
    matches = [
        n for n in range(low, high + 1)
        if hashlib.sha256(movie_bytes[start:start + 2 * n]).hexdigest()
            == claimed_raw_window_sha256
    ]
    if len(matches) != 1:
        raise ValueError(
            "no unique unmodified 2014 source controller window matches producer digest"
        )
    return matches[0]


def source_window(report: dict, movie_path: Path, meta_path: Path) -> dict:
    """Reopen pinned original SMV and independently rebuild authentic P1 masks."""
    case = report.get("name")
    if case not in SOURCE_EVENT_ANCHORS:
        raise ValueError("case lacks independently known 2014 USA source event anchor")
    course, frame_entry, frame_result = SOURCE_EVENT_ANCHORS[case]
    event = report.get("original_source_event")
    if (not isinstance(event, dict) or report.get("course_id") != course
            or event.get("original_entry_frame") != frame_entry
            or event.get("original_result_frame") != frame_result
            or event.get("source_active_frames_to_result") !=
                frame_result - frame_entry):
        raise ValueError("source-original movie course/result event identity is altered")
    if not movie_path.is_file() or movie_path.is_symlink():
        raise ValueError("missing or symlinked canonical 2014 SMV")
    actual_archive_sha = hashlib.sha256(movie_path.read_bytes()).hexdigest()
    if (actual_archive_sha != SOURCE_2014_ARCHIVE_SHA256 or
            report.get("original_movie_sha256") != SOURCE_2014_ARCHIVE_SHA256):
        raise ValueError("not the exact immutable source 2014 SMV bytes")
    if not meta_path.is_file() or meta_path.is_symlink():
        raise ValueError("missing canonical 2014 SMV metadata")
    metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    data, _ = movie.read_movie(movie_path)
    n = select_source_controller_length(
        data, metadata, frame_entry, frame_result - frame_entry,
        report.get("original_movie_window_sha256"))
    observed = movie.window(data, metadata, frame_entry, n)
    if observed["raw_controller_window_sha256"] != report[
            "original_movie_window_sha256"]:
        raise ValueError("original 2014 SMV source controller digest changed")
    return observed
