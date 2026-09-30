#!/usr/bin/env python3
"""Reduce snesref WAV output around named script checkpoints.

This deliberately uses coarse PCM metrics for cross-core evidence. Exact WAV
hashes are retained, but independent SNES audio implementations are not required
to produce bit-identical samples.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import struct
import wave
from pathlib import Path

DUMP_RE = re.compile(r"script f=(\d+) dump ([^ ]+)")
TIMING_RE = re.compile(r"core timing: fps=([0-9.]+) sample_rate=([0-9.]+)")


def parse_log(path: Path) -> tuple[float, float, dict[str, int]]:
    fps = sample_rate = None
    checkpoints: dict[str, int] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = TIMING_RE.search(line)
        if m:
            fps = float(m.group(1))
            sample_rate = float(m.group(2))
        m = DUMP_RE.search(line)
        if m:
            checkpoints[m.group(2)] = int(m.group(1))
    if fps is None or sample_rate is None:
        raise ValueError(f"{path}: missing core timing")
    return fps, sample_rate, checkpoints


def window_metrics(wav_path: Path, center_frame: int, fps: float, radius_frames: int = 30) -> dict:
    with wave.open(str(wav_path), "rb") as w:
        if w.getnchannels() != 2 or w.getsampwidth() != 2:
            raise ValueError("expected stereo 16-bit PCM")
        rate = w.getframerate()
        center = round(center_frame * rate / fps)
        radius = round(radius_frames * rate / fps)
        start = max(0, center - radius)
        end = min(w.getnframes(), center + radius)
        w.setpos(start)
        raw = w.readframes(end - start)
    samples = struct.unpack("<" + "h" * (len(raw) // 2), raw) if raw else ()
    if not samples:
        rms = peak = 0.0
        nonzero = 0
    else:
        peak = max(abs(x) for x in samples)
        rms = math.sqrt(sum(x*x for x in samples) / len(samples))
        nonzero = sum(1 for x in samples if x)
    return {
        "guest_frame": center_frame,
        "radius_guest_frames": radius_frames,
        "pcm_frames": end - start,
        "rms": round(rms, 6),
        "peak": peak,
        "nonzero_fraction": nonzero / len(samples) if samples else 0.0,
        "window_sha256": hashlib.sha256(raw).hexdigest(),
    }


def analyze(log: Path, wav_path: Path, tags: list[str]) -> dict:
    fps, declared_rate, checkpoints = parse_log(log)
    rows = {}
    for tag in tags:
        if tag not in checkpoints:
            raise ValueError(f"{log}: missing checkpoint {tag}")
        rows[tag] = window_metrics(wav_path, checkpoints[tag], fps)
    raw = wav_path.read_bytes()
    return {
        "schema_version": 1,
        "fps": fps,
        "declared_sample_rate": declared_rate,
        "wav_sha256": hashlib.sha256(raw).hexdigest(),
        "wav_bytes": len(raw),
        "checkpoints": rows,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("log", type=Path)
    ap.add_argument("wav", type=Path)
    ap.add_argument("--tag", action="append", default=[])
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    tags = args.tag or ["main-menu-ready", "now-playing-ready", "race-entered"]
    report = analyze(args.log, args.wav, tags)
    for tag, row in report["checkpoints"].items():
        print(f"{tag}: frame={row['guest_frame']} rms={row['rms']:.2f} peak={row['peak']} nonzero={row['nonzero_fraction']:.4f}")
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
