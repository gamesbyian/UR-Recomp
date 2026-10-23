#!/usr/bin/env python3
"""ROM-free audit of *declared* live capture timeline metadata.

Input must be supplied by independently instrumented source presentation/audio
and capture taps. Self-reported JSON can never prove actual video, hardware
presentation, an encoded movie, or original/native game equivalence.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


class TimelineError(ValueError):
    """A proposed complete-race live capture cannot be admitted."""


def _integer(value: object, label: str, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise TimelineError(f"invalid {label}")
    return value


def audit_timeline(record: object) -> dict:
    """Check complete attempt/frame/audio coverage, never encoded-video status."""
    if type(record) is not dict:
        raise TimelineError("invalid witness envelope")
    attempt, profile = record.get("attempt"), record.get("profile")
    if type(attempt) is not str or not attempt or type(profile) is not str or not profile:
        raise TimelineError("missing attempt/profile identity")
    entry = _integer(record.get("entry_pts_ns"), "race entry timestamp")
    exit_pts = _integer(record.get("exit_pts_ns"), "race exit timestamp", entry + 1)
    first_frame = _integer(record.get("first_frame"), "first frame")
    first_source_id = _integer(record.get("first_source_present_id"), "first source ID")
    start_cursor = _integer(record.get("audio_device_entry_cursor"), "audio entry cursor")
    end_cursor = _integer(record.get("audio_device_exit_cursor"), "audio exit cursor", start_cursor)
    frames = record.get("frames")
    if type(frames) is not list or not frames:
        raise TimelineError("no presented frames")
    next_audio = 0
    previous_pts = -1
    previous_guest_frame = first_frame
    for i, frame in enumerate(frames):
        if type(frame) is not dict:
            raise TimelineError("invalid frame envelope")
        if frame.get("attempt") != attempt or frame.get("profile") != profile:
            raise TimelineError("cross-attempt/profile frame")
        guest_frame = _integer(frame.get("frame"), "frame number")
        # Allow 120-Hz/variable-refresh duplicate presentations of 60-Hz guest
        # frames, but never drop a guest tick or repeat a source presentation ID.
        if (i == 0 and guest_frame != first_frame) or (
            i > 0 and not previous_guest_frame <= guest_frame <= previous_guest_frame + 1
        ):
            raise TimelineError("missing/out-of-order guest frame")
        previous_guest_frame = guest_frame
        if _integer(frame.get("source_present_id"), "source present ID") != first_source_id + i:
            raise TimelineError("missing/duplicate source presentation")
        pts = _integer(frame.get("captured_pts_ns"), "capture timestamp")
        source_pts = _integer(frame.get("source_pts_ns"), "source timestamp")
        if pts != source_pts or pts <= previous_pts:
            raise TimelineError("source/capture presentation clock mismatch")
        if _integer(frame.get("audio_first_sample"), "audio sample offset") != next_audio:
            raise TimelineError("audio sample gap/overlap")
        samples = _integer(frame.get("audio_samples"), "audio sample count", 1)
        next_audio += samples
        previous_pts = pts
    if frames[0]["captured_pts_ns"] != entry:
        raise TimelineError("recording did not start at race entry")
    if previous_pts >= exit_pts:
        raise TimelineError("terminal event precedes final presented frame")
    if end_cursor - start_cursor != next_audio:
        raise TimelineError("audio device cursor mismatch")
    # Source clocks and 48 kHz stereo audio spans are correlated to a 5 ms
    # tolerance, using integer arithmetic to avoid floating point drift.
    tolerance = 5_000_000 * 48_000
    for frame in frames:
        delta_ns = frame["captured_pts_ns"] - entry
        sample = frame["audio_first_sample"]
        if abs(delta_ns * 48_000 - sample * 1_000_000_000) > tolerance:
            raise TimelineError("frame/audio clock drift")
    if abs((exit_pts - entry) * 48_000 - next_audio * 1_000_000_000) > tolerance:
        raise TimelineError("audio tail does not match race exit")
    return {"attempt": attempt, "profile": profile, "frames": len(frames),
            "audio_samples_48k_stereo": next_audio,
            "source_timeline_consistent": True,
            "independent_observation_authenticated": False,
            "encoded_video_verified": False,
            "release_gate_credit": False}


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise TimelineError("duplicate JSON key")
        result[key] = value
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("witness", type=Path)
    args = parser.parse_args()
    try:
        obj = json.loads(args.witness.read_text(encoding="utf-8"),
                         object_pairs_hook=_unique_pairs,
                         parse_constant=lambda value: (_ for _ in ()).throw(TimelineError("nonfinite JSON")))
        print(json.dumps(audit_timeline(obj), sort_keys=True))
        return 0
    except (OSError, UnicodeError, ValueError) as exc:
        print(json.dumps({"status": "invalid-witness", "reason": str(exc),
                          "release_gate_credit": False}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
