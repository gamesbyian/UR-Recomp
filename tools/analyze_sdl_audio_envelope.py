#!/usr/bin/env python3
"""Bounded SDL3 device-output pause/transition envelope, without retaining PCM.

The final N seconds are divided into W-ms buckets, oldest to newest. For
each, measure real-device left/right RMS, peak and largest adjacent-sample
jump. All timestamps are relative to the *end* of the captured device stream,
not guest frame timestamps; SDL buffering/latency is not phase-calibrated.
These measurements are descriptive, not automatic click/fade acceptance.
"""
from __future__ import annotations

import argparse
import json
import math
import struct
from pathlib import Path

from tools.analyze_sdl_disk_audio import FRAME_BYTES, parse_disk_format

MAX_WINDOWS = 1000


def extract_envelope(
    log_path: Path, pcm_path: Path, *, last_seconds: float = 3.0,
    window_ms: int = 100,
) -> dict:
    if (
        isinstance(last_seconds, bool) or not isinstance(last_seconds, (int, float))
        or not math.isfinite(last_seconds) or not 1 <= last_seconds <= 10
        or isinstance(window_ms, bool) or not isinstance(window_ms, int)
        or not 10 <= window_ms <= 500
    ):
        raise ValueError("invalid audio envelope window settings")
    fmt = parse_disk_format(log_path)
    if Path(fmt["destination"]).resolve() != pcm_path.resolve():
        raise ValueError("SDL disk capture destination does not match PCM input")
    count = pcm_path.stat().st_size
    if count < FRAME_BYTES or count % FRAME_BYTES:
        raise ValueError("missing or incomplete stereo PCM data")
    total_frames = count // FRAME_BYTES
    rate = fmt["sample_rate"]
    window_frames = max(1, round(rate * window_ms / 1000))
    requested = max(1, round(rate * last_seconds))
    captured = min(total_frames, requested)
    if (captured + window_frames - 1) // window_frames > MAX_WINDOWS:
        raise ValueError("too many audio envelope windows")

    windows = []
    # Seek straight to bounded tail: no whole-file materialization, no upload.
    with pcm_path.open("rb") as source:
        source.seek((total_frames - captured) * FRAME_BYTES)
        prior = None
        left = captured
        first = total_frames - captured
        while left:
            n = min(window_frames, left)
            data = source.read(n * FRAME_BYTES)
            if len(data) != n * FRAME_BYTES:
                raise ValueError("short PCM read in audio envelope")
            sum_squares = [0, 0]
            peaks = [0, 0]
            steps = [0, 0]
            zero_samples = [0, 0]
            for values in struct.iter_unpack("<hh", data):
                for channel, sample in enumerate(values):
                    sum_squares[channel] += sample * sample
                    peaks[channel] = max(peaks[channel], abs(sample))
                    zero_samples[channel] += sample == 0
                    if prior is not None:
                        steps[channel] = max(steps[channel], abs(sample - prior[channel]))
                prior = values
            start = first
            first += n
            left -= n
            rms = [math.sqrt(total / n) for total in sum_squares]
            windows.append({
                "start_seconds_before_end": round((total_frames - start) / rate, 6),
                "end_seconds_before_end": round((total_frames - first) / rate, 6),
                "frames": n,
                "rms": [round(value, 6) for value in rms],
                "combined_rms": round(math.sqrt(sum(sum_squares) / (2 * n)), 6),
                "peak": peaks,
                "peak_adjacent_step": steps,
                "zero_fraction": [round(value / n, 8) for value in zero_samples],
            })

    return {
        "schema_version": 1,
        "audio_origin": "sdl3-disk-playback",
        "measurement": "device stream relative to end; guest/device offset not calibrated",
        "device_format": fmt["format"],
        "channels": fmt["channels"],
        "sample_rate": rate,
        "total_pcm_frames": total_frames,
        "captured_tail_frames": captured,
        "captured_tail_seconds": round(captured / rate, 6),
        "window_ms": window_ms,
        "windows": windows,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("sdl_log", type=Path)
    ap.add_argument("raw_pcm", type=Path)
    ap.add_argument("--last-seconds", type=float, default=3.0)
    ap.add_argument("--window-ms", type=int, default=100)
    ap.add_argument("--json-out", required=True, type=Path)
    args = ap.parse_args()
    result = extract_envelope(
        args.sdl_log, args.raw_pcm, last_seconds=args.last_seconds,
        window_ms=args.window_ms,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        "SDL_AUDIO_ENVELOPE PASS "
        f"windows={len(result['windows'])} "
        f"tail_s={result['captured_tail_seconds']} "
        f"window_ms={result['window_ms']} "
        "origin=sdl3-disk-playback"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
