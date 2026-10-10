#!/usr/bin/env python3
"""Reject incomplete native continuous captures before publishing any footage.

Require a completed host marker, contiguous present IDs, exact decoded FFV1
frame count, output geometry, and an explicitly provided guest-CRC control pair.
Only then allow an editorial MP4 to be encoded from the captured lossless master.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def probe(path: Path) -> dict:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
         "-show_entries", "stream=codec_name,width,height,r_frame_rate,nb_read_frames",
         "-of", "json", str(path)], check=True, capture_output=True, text=True)
    streams = json.loads(result.stdout)["streams"]
    if len(streams) != 1:
        raise ValueError("Expected one video stream")
    return streams[0]


def validate(master: Path, frames: Path, log: Path, control: Path,
             recorded: Path, expected: int, output: Path,
             rom_sha: str, git_sha: str, route: str,
             min_start: int = 1990, logical_width: int = 342) -> dict:
    if not (600 <= expected <= 1200):
        raise ValueError("Expected count outside accepted capture window")
    raw = frames.read_text().splitlines()
    if raw[0] != "ordinal\tguest_frame\twidth\theight":
        raise ValueError("Unknown frame-index schema")
    rows = [line.split("\t") for line in raw[1:]]
    if len(rows) != expected or any(len(r) != 4 for r in rows):
        raise ValueError("Incomplete/invalid sidecar")
    parsed = [tuple(map(int, row)) for row in rows]
    start = parsed[0][1]
    if start < min_start:
        raise ValueError("Capture begins before expected post-GO window")
    sizes = {(w, h) for _, _, w, h in parsed}
    if len(sizes) != 1:
        raise ValueError("Drawable changed dimensions during capture")
    for ordinal, (n, frame, _, _) in enumerate(parsed):
        if n != ordinal or frame != start + ordinal:
            raise ValueError(f"Frame discontinuity at ordinal {ordinal}")
    marker = re.findall(
        r"UR_NATIVE_VIDEO_END actual=(\d+) expected=(\d+) last=(\d+) "
        r"ffmpeg_status=(\d+) status=(\S+)", log.read_text())
    if len(marker) != 1 or marker[0] != (
        str(expected), str(expected), str(start + expected - 1), "0", "complete"
    ):
        raise ValueError("No single successful native recorder completion marker")
    source = probe(master)
    width, height = next(iter(sizes))
    if (source["codec_name"] != "ffv1"
            or (source["width"], source["height"]) != (width, height)
            or source["r_frame_rate"] != "60/1"
            or int(source["nb_read_frames"]) != expected):
        raise ValueError("Lossless master does not match indexed frame count/shape")
    if control.read_bytes() != recorded.read_bytes():
        raise ValueError("Capture changed guest WRAM CRC trace")
    if not re.fullmatch(r"[0-9a-f]{64}", rom_sha):
        raise ValueError("ROM SHA-256 required")
    if not re.fullmatch(r"[0-9a-f]{40}", git_sha):
        raise ValueError("Full repository commit SHA required")
    result = {
        "status": "verified_consecutive_host_presentations",
        "warning": "60-fps encoded cadence describes consecutive host presentations, "
                   "not independently certified 60-Hz guest timing",
        "git_commit": git_sha,
        "rom_sha256": rom_sha,
        "route": route,
        "guest_frame_start": start,
        "guest_frame_end": start + expected - 1,
        "consecutive_host_presentations": expected,
        "dimensions": {"actual_sdl_drawable": [width, height],
                       "logical_source": [logical_width, 224]},
        "master": {"codec": "ffv1", "fps_nominal": "60/1",
                   "sha256": sha(master)},
        "control_guest_crc_sha256": sha(control),
        "recorded_guest_crc_sha256": sha(recorded),
        "index_sha256": sha(frames),
        "host_log_sha256": sha(log),
        "dropped_or_skipped_host_frame_ids": 0,
    }
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    for name in ("master", "frames", "log", "control-crc", "recorded-crc", "out"):
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--count", type=int, required=True)
    p.add_argument("--rom-sha256", required=True)
    p.add_argument("--git-sha", required=True)
    p.add_argument("--route", required=True)
    p.add_argument("--min-start", type=int, default=1990)
    p.add_argument("--logical-width", type=int, choices=(256, 342), default=342)
    a = p.parse_args()
    print(json.dumps(validate(a.master, a.frames, a.log, a.control_crc,
                              a.recorded_crc, a.count, a.out,
                              a.rom_sha256, a.git_sha, a.route, a.min_start, a.logical_width), indent=2))


if __name__ == "__main__":
    main()
