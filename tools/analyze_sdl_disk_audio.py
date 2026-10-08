#!/usr/bin/env python3
"""Validate captured *host-output* PCM from SDL3's disk audio device.

Use SDL_AUDIO_DRIVER=disk and SDL_AUDIO_DISK_OUTPUT_FILE=<absolute path>.
The disk driver writes headerless PCM in its negotiated device format. This
tool gets that format from SDL's own log, instead of interpreting arbitrary
bytes as signed 16-bit audio. It measures actual bytes sent to the playback
backend, not SPC/APU state, and does not claim sample-exact emulator fidelity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import struct
from pathlib import Path

DISK_LOG_RE = re.compile(
    r"Writing to file \[([^\]\r\n]+)\],\s*format=([A-Za-z0-9]+)\s+"
    r"channels=(\d+)\s+freq=(\d+)\."
)
CHANNELS = 2
FRAME_BYTES = CHANNELS * 2
CHUNK_BYTES = FRAME_BYTES * 16384


def parse_disk_format(log_path: Path) -> dict:
    log = log_path.read_text(encoding="utf-8", errors="replace")
    matches = DISK_LOG_RE.findall(log)
    if len(matches) != 1:
        raise ValueError("expected exactly one SDL disk playback format announcement")
    destination, fmt, channels, frequency = matches[0]
    if fmt not in ("S16LE", "S16"):
        raise ValueError(f"unsupported disk PCM format {fmt}; require S16LE")
    if int(channels) != CHANNELS:
        raise ValueError(f"unsupported disk PCM channels {channels}; require stereo")
    rate = int(frequency)
    if not 8000 <= rate <= 192000:
        raise ValueError(f"invalid SDL disk sample rate {frequency}")
    return {
        "destination": destination,
        "format": fmt,
        "channels": CHANNELS,
        "sample_rate": rate,
    }


def analyze(
    log_path: Path,
    pcm_path: Path,
    *,
    min_duration_seconds: float = 1.0,
    min_rms: float = 50.0,
    min_nonzero_fraction: float = 0.001,
    tail_seconds: float = 0.5,
    min_tail_rms: float | None = None,
) -> dict:
    if not all(math.isfinite(x) and x >= 0 for x in (
        min_duration_seconds, min_rms, min_nonzero_fraction
        , tail_seconds, *( [min_tail_rms] if min_tail_rms is not None else [] )
    )) or min_nonzero_fraction > 1 or not 0 < tail_seconds <= 5:
        raise ValueError("invalid audio acceptance thresholds")
    fmt = parse_disk_format(log_path)
    # Reject stale/unrelated raw samples even when their amplitude and format
    # are plausible. SDL logs the actual destination when opening the device.
    if Path(fmt["destination"]).resolve() != pcm_path.resolve():
        raise ValueError("SDL disk capture destination does not match PCM input")
    byte_count = pcm_path.stat().st_size
    if not byte_count or byte_count % FRAME_BYTES:
        raise ValueError("missing or incomplete stereo signed-16 PCM frames")
    frames = byte_count // FRAME_BYTES
    duration = frames / fmt["sample_rate"]
    if duration < min_duration_seconds:
        raise ValueError(f"SDL disk capture too short: {duration:.3f}s")

    digest = hashlib.sha256()
    sum_squares = [0, 0]
    peaks = [0, 0]
    nonzero = [0, 0]
    clipped = [0, 0]
    with pcm_path.open("rb") as inp:
        while chunk := inp.read(CHUNK_BYTES):
            if len(chunk) % FRAME_BYTES:
                raise ValueError("incomplete stereo PCM frame")
            digest.update(chunk)
            for left, right in struct.iter_unpack("<hh", chunk):
                for ch, sample in enumerate((left, right)):
                    magnitude = abs(sample)
                    sum_squares[ch] += sample * sample
                    peaks[ch] = max(peaks[ch], magnitude)
                    nonzero[ch] += sample != 0
                    clipped[ch] += sample in (-32768, 32767)

    channel_rms = [math.sqrt(s / frames) for s in sum_squares]
    rms = math.sqrt(sum(sum_squares) / (2 * frames))
    fraction = sum(nonzero) / (2 * frames)
    if rms < min_rms or fraction < min_nonzero_fraction:
        raise ValueError(
            f"SDL disk playback is silent/insufficient: rms={rms:.2f} "
            f"nonzero={fraction:.6f}"
        )

    # A loud opening can hide a completely silent race-ending capture.
    # Examine the *device-output* tail independently, without claiming that
    # its absolute PCM offsets map precisely to any guest frame.
    tail_frames = min(frames, max(1, round(fmt["sample_rate"] * tail_seconds)))
    with pcm_path.open("rb") as inp:
        inp.seek(-tail_frames * FRAME_BYTES, 2)
        tail = inp.read(tail_frames * FRAME_BYTES)
    tail_samples = struct.iter_unpack("<hh", tail)
    tail_squares = 0
    tail_nonzero = 0
    tail_peak = 0
    for left, right in tail_samples:
        for sample in (left, right):
            tail_squares += sample * sample
            tail_nonzero += sample != 0
            tail_peak = max(tail_peak, abs(sample))
    tail_rms = math.sqrt(tail_squares / (2 * tail_frames))
    tail_fraction = tail_nonzero / (2 * tail_frames)
    if min_tail_rms is not None and (
        tail_rms < min_tail_rms or tail_fraction < min_nonzero_fraction
    ):
        raise ValueError(
            f"SDL disk playback tail silent/insufficient: "
            f"rms={tail_rms:.2f} nonzero={tail_fraction:.6f}"
        )

    return {
        "schema_version": 1,
        "tail_pcm_frames": tail_frames,
        "tail_duration_seconds": round(tail_frames / fmt["sample_rate"], 6),
        "tail_rms": round(tail_rms, 6),
        "tail_peak": tail_peak,
        "tail_nonzero_fraction": round(tail_fraction, 8),
        "audio_origin": "sdl3-disk-playback",
        "device_format": fmt["format"],
        "channels": fmt["channels"],
        "sample_rate": fmt["sample_rate"],
        "pcm_frames": frames,
        "duration_seconds": round(duration, 6),
        "pcm_bytes": byte_count,
        "pcm_sha256": digest.hexdigest(),
        "rms": round(rms, 6),
        "peak": max(peaks),
        "nonzero_fraction": round(fraction, 8),
        "channel_rms": [round(x, 6) for x in channel_rms],
        "channel_peaks": peaks,
        "clipped_fraction": round(sum(clipped) / (2 * frames), 8),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("sdl_log", type=Path)
    ap.add_argument("raw_pcm", type=Path)
    ap.add_argument("--min-duration-seconds", type=float, default=1.0)
    ap.add_argument("--min-rms", type=float, default=50.0)
    ap.add_argument("--min-nonzero-fraction", type=float, default=0.001)
    ap.add_argument("--tail-seconds", type=float, default=0.5)
    ap.add_argument("--min-tail-rms", type=float)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    report = analyze(
        args.sdl_log, args.raw_pcm,
        min_duration_seconds=args.min_duration_seconds,
        min_rms=args.min_rms,
        min_nonzero_fraction=args.min_nonzero_fraction,
        tail_seconds=args.tail_seconds,
        min_tail_rms=args.min_tail_rms,
    )
    print(
        f"SDL_DISK_AUDIO_CAPTURE PASS frames={report['pcm_frames']} "
        f"rate={report['sample_rate']} rms={report['rms']:.2f} "
        f"nonzero={report['nonzero_fraction']:.4f} "
        f"sha256={report['pcm_sha256']}"
    )
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
