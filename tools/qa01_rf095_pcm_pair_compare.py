#!/usr/bin/env python3
"""Inspect the *executed* RF095 Zoo audio pair without inventing clock parity.

Reads the untouched QA01 case artifact. The full original WAV is essential:
RF095's bounded receipt only publishes 6445..6452, while native audio occupies
6447..6457. It is invalid to compare those published short snippets as if they
represented equal output stages, or to infer a release pass from correlation.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import re
import struct
import sys
import wave
import zipfile
from pathlib import Path

ROOT = "work/zoom-zoo/replay/"
FILES = {
    "wav": ROOT + "snesref_audio.wav",
    "reference_map": ROOT + "rf095-original-map.csv",
    "native_pcm": ROOT + "rf095-native.pcm",
    "native_map": ROOT + "rf095-native-map.csv",
    "receipt": "qa01-rf095-pcm-receipt.json",
}
ORIGINAL_START, ORIGINAL_END = 6445, 6457
NATIVE_START, NATIVE_END = 6447, 6457
SOURCE_SHA = re.compile(r"[0-9a-f]{40}\Z")


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def parse_map(raw: bytes, start: int, end: int) -> dict[int, int]:
    if not raw or len(raw) > 750000 or not raw.endswith(b"\n"):
        raise ValueError("missing, oversized or unterminated sample map")
    try:
        lines = raw.decode("ascii").replace("\r\n", "\n").split("\n")
    except UnicodeDecodeError as exc:
        raise ValueError("non-ASCII sample map") from exc
    if lines[-1] != "" or lines[0] != "frame,samples":
        raise ValueError("invalid sample map header or terminator")
    rows: dict[int, int] = {}
    previous_frame, previous_samples = -1, -1
    for line in lines[1:-1]:
        cols = line.split(",")
        if (len(cols) != 2 or
                any(not c.isascii() or not c.isdecimal() for c in cols)):
            raise ValueError("invalid sample map row")
        frame, sample = map(int, cols)
        if frame <= previous_frame or sample < previous_samples:
            raise ValueError("unordered or regressing sample map")
        rows[frame] = sample
        previous_frame, previous_samples = frame, sample
    if not all(i in rows for i in range(start, end + 1)):
        raise ValueError("sample map misses requested frames")
    if rows[end] <= rows[start]:
        raise ValueError("sample map has empty requested interval")
    return rows


def sample_pairs(raw: bytes) -> list[tuple[int, int]]:
    if len(raw) % 4:
        raise ValueError("truncated stereo PCM")
    return list(struct.iter_unpack("<hh", raw))


def pearson(original: list[tuple[int, int]],
            native: list[tuple[int, int]], lag: int, channel: int) -> float | None:
    """Positive lag skips original samples; no resampling or time-warping."""
    old_start, new_start = max(0, lag), max(0, -lag)
    length = min(len(original) - old_start, len(native) - new_start)
    if length < 200:
        return None
    old = (row[channel] for row in original[old_start:old_start + length])
    new = (row[channel] for row in native[new_start:new_start + length])
    sx = sy = sxx = syy = sxy = 0
    for x, y in zip(old, new):
        sx += x
        sy += y
        sxx += x * x
        syy += y * y
        sxy += x * y
    xx = length * sxx - sx * sx
    yy = length * syy - sy * sy
    if xx <= 0 or yy <= 0:
        return None
    return (length * sxy - sx * sy) / math.sqrt(xx * yy)


def onset(samples: list[tuple[int, int]], rows: dict[int, int],
          start: int, end: int) -> dict | None:
    first = next((i for i, (l, r) in enumerate(samples) if l or r), None)
    if first is None:
        return None
    absolute = rows[start] + first
    for frame in range(start, end):
        if rows[frame] <= absolute < rows[frame + 1]:
            size = rows[frame + 1] - rows[frame]
            return {
                "guest_frame": frame,
                "within_frame_sample": absolute - rows[frame],
                "fraction_of_frame": round((absolute - rows[frame]) / size, 6),
                "sample_index_in_extracted_window": first,
            }
    raise ValueError("sample onset cannot be bound to a producer frame")


def analyze(archive: Path, source_sha: str, max_lag: int = 512) -> dict:
    if not SOURCE_SHA.fullmatch(source_sha):
        raise ValueError("exact source SHA is required")
    if not 0 <= max_lag <= 2048:
        raise ValueError("lag search must be bounded to 0..2048")
    if not archive.is_file() or archive.is_symlink():
        raise ValueError("artifact must be a regular ZIP")
    with zipfile.ZipFile(archive) as z:
        members = z.namelist()
        if len(members) != len(set(members)):
            raise ValueError("duplicate artifact ZIP members")
        if any(name not in members for name in FILES.values()):
            raise ValueError("RF095 primary artifact member missing")
        if any(z.getinfo(name).file_size > 64 * 1024 * 1024
               for name in FILES.values()):
            raise ValueError("RF095 artifact member exceeds size bound")
        raw = {key: z.read(name) for key, name in FILES.items()}
    receipt = json.loads(raw["receipt"])
    if receipt.get("schema") != "ur-qa01-rf095-source-registered-pcm/1":
        raise ValueError("unexpected producer receipt schema")
    expected = {
        "wav": receipt["original"]["wav_sha256"],
        "reference_map": receipt["original"]["map_sha256"],
        "native_pcm": receipt["native"]["raw_sha256"],
        "native_map": receipt["native"]["map_sha256"],
    }
    for key, sha in expected.items():
        if digest(raw[key]) != sha:
            raise ValueError("RF095 source/receipt hash mismatch: " + key)
    ref = parse_map(raw["reference_map"], ORIGINAL_START, ORIGINAL_END)
    nat = parse_map(raw["native_map"], NATIVE_START, NATIVE_END)
    if (ref[ORIGINAL_START] != receipt["original"]["first_sample_index"] or
            any(ref[int(f)] != s
                for f, s in receipt["original"]["frame_sample_indices"].items()) or
            any(nat[int(f)] != s
                for f, s in receipt["native"]["frame_sample_indices"].items())):
        raise ValueError("primary frame map disagrees with receipt")
    if nat[NATIVE_START] != 0:
        raise ValueError("native sample capture did not begin at its map zero")
    with wave.open(io.BytesIO(raw["wav"]), "rb") as wav:
        if (wav.getnchannels(), wav.getsampwidth(), wav.getcomptype()) != (2, 2, "NONE"):
            raise ValueError("original WAV must be uncompressed stereo PCM16")
        if wav.getframerate() != receipt["original"]["sample_rate"]:
            raise ValueError("original WAV sample rate is not receipt-bound")
        if wav.getnframes() != ref[max(ref)]:
            raise ValueError("original WAV and map disagree on total samples")
        wav.setpos(ref[ORIGINAL_START])
        original_bytes = wav.readframes(ref[ORIGINAL_END] - ref[ORIGINAL_START])
    if len(original_bytes) != (ref[ORIGINAL_END] - ref[ORIGINAL_START]) * 4:
        raise ValueError("original window is truncated")
    if len(raw["native_pcm"]) != nat[NATIVE_END] * 4:
        raise ValueError("native PCM and map sample counts differ")
    original = sample_pairs(original_bytes)
    native = sample_pairs(raw["native_pcm"])
    if not original or not native:
        raise ValueError("empty producer audio")
    best: tuple[float, int, list[float]] | None = None
    for lag in range(-max_lag, max_lag + 1):
        channels = [pearson(original, native, lag, i) for i in (0, 1)]
        if any(c is None for c in channels):
            continue
        mean = sum(channels) / 2
        if best is None or mean > best[0]:
            best = (mean, lag, channels)
    if best is None:
        raise ValueError("no informative stereo correlation interval")
    return {
        "schema": "ur-qa01-rf095-exploratory-waveform-alignment/1",
        "source_sha_claim": source_sha,
        "artifact_sha256": digest(archive.read_bytes()),
        "original_wav_sha256": expected["wav"],
        "native_pcm_sha256": expected["native_pcm"],
        "original_guest_frames": [ORIGINAL_START, ORIGINAL_END],
        "native_guest_frames": [NATIVE_START, NATIVE_END],
        "original_extracted_sample_frames": len(original),
        "native_sample_frames": len(native),
        "original_first_nonzero": onset(original, ref, ORIGINAL_START, ORIGINAL_END),
        "native_first_nonzero": onset(native, nat, NATIVE_START, NATIVE_END),
        "searched_lag_sample_frames": [-max_lag, max_lag],
        "best_original_minus_native_lag_sample_frames": best[1],
        "aligned_pearson_left": round(best[2][0], 6),
        "aligned_pearson_right": round(best[2][1], 6),
        "waveform_parity_proven": False,
        "clock_equivalence_proven": False,
        "output_stage_equivalence_proven": False,
        "independent_provenance_verified": False,
        "usa_course_credit": 0,
        "release_gate_credit": 0,
        "next_discriminator": "Independently bind producer identity; register semantic KON and compare equivalent output stages and onsets before deciding whether any residual difference is player-audible.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--max-lag", type=int, default=512)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = analyze(args.artifact, args.source_sha, args.max_lag)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        if args.out.exists() or args.out.is_symlink():
            raise SystemExit("refusing to overwrite preexisting report")
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
