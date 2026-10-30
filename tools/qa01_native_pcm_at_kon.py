#!/usr/bin/env python3
"""Capture genuine native DSP PCM around an executed KON, without a new emulator hook.

Uses the pinned snesrecomp debug server's existing audio_events and audio_wav
commands. The sample index is the native DSP producer clock, not SDL output
wall time, a frame number, or a calibrated original-Snes9x clock. Run against
an already-paused trace build after the deterministic Zoo->Bowl route.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import wave
from pathlib import Path

from capture_audio_events import capture, command, connect

SHA40 = re.compile(r"[0-9a-f]{40}\Z")


def kon_candidates(events: list[dict]) -> list[int]:
    """Native sample indices of actual DSP voice-7 key-on writes ($4C=$80)."""
    found = []
    for e in events:
        if e.get("t") == "reg" and e.get("adr") == "0x4c" and e.get("val") == "0x80":
            index = e.get("s")
            if type(index) is not int or index < 0:
                raise ValueError("malformed native KON sample index")
            found.append(index)
    return found


def capture_kon_pcm(command_fn, *, events: list[dict], produced: int,
                    kon_sample_index: int, wav_path: Path,
                    before: int = 4096, after: int = 32768) -> dict:
    """Fail closed on missing/ambiguous KON or clamped, stale, malformed PCM."""
    if any(type(v) is not int for v in (produced, kon_sample_index, before, after)):
        raise ValueError("sample counters must be integers")
    if not 1 <= before <= 64000 or not 1 <= after <= 64000:
        raise ValueError("bounded pre/post KON sample windows required")
    candidates = kon_candidates(events)
    if candidates.count(kon_sample_index) != 1:
        raise ValueError("selected $4C=$80 KON missing or ambiguous in actual event ring")
    start = kon_sample_index - before
    count = before + after
    if start < 0 or produced < start + count:
        raise ValueError("KON PCM window not yet fully produced")
    if not wav_path.is_absolute() or any(c.isspace() for c in str(wav_path)):
        raise ValueError("audio_wav requires absolute whitespace-free server-local path")
    if wav_path.exists() or wav_path.is_symlink():
        raise ValueError("refusing to reuse or overwrite an existing WAV")
    if not wav_path.parent.is_dir() or wav_path.parent.is_symlink():
        raise ValueError("WAV destination parent must be an existing real directory")
    response = command_fn(f"audio_wav {wav_path} {start} {count}")
    if (response.get("ok") is not True or response.get("start") != start or
            response.get("count") != count or response.get("path") != str(wav_path)):
        raise ValueError("audio_wav returned clamped/mismatched native PCM slice")
    if not wav_path.is_file() or wav_path.is_symlink():
        raise ValueError("audio_wav did not create a real local WAV")
    with wave.open(str(wav_path), "rb") as wav:
        if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate(),
                wav.getcomptype(), wav.getnframes()) != (2, 2, 32040, "NONE", count):
            raise ValueError("native PCM WAV format/sample count mismatch")
        pcm = wav.readframes(count)
    if len(pcm) != count * 4:
        raise ValueError("short decoded native stereo PCM")
    return {
        "schema": "ur-qa01-native-kon-pcm/1",
        "authority": "native DSP producer audio_trace ring; not host SDL device",
        "clock": "native_dsp_sample_index",
        "kon_register": "0x4c", "kon_value": "0x80",
        "kon_sample_index": kon_sample_index,
        "start_sample_index": start, "sample_frames": count,
        "kon_offset_frames": before, "before_frames": before, "after_frames": after,
        "sample_rate_hz": 32040, "channels": 2, "sample_format": "signed_pcm16_le",
        "wav_sha256": hashlib.sha256(wav_path.read_bytes()).hexdigest(),
        "pcm_sha256": hashlib.sha256(pcm).hexdigest(),
        "wav_bytes": wav_path.stat().st_size,
        "source_to_binary_identity_independently_verified": False,
        "original_native_audio_parity_proven": False,
        "usa_event_credit": 0, "windows_release_gate_credit": 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=4377)
    ap.add_argument("--kon-sample-index", type=int, required=True,
                    help="Exact s field of the executed voice-7 reg $4C=$80 event")
    ap.add_argument("--before", type=int, default=4096)
    ap.add_argument("--after", type=int, default=32768)
    ap.add_argument("--wav-out", required=True, type=Path)
    ap.add_argument("--json-out", required=True, type=Path)
    ap.add_argument("--source-sha", required=True,
                    help="Claimed Git source SHA; verify executable binding separately")
    ap.add_argument("--native-executable", required=True, type=Path)
    args = ap.parse_args()
    if args.host not in ("127.0.0.1", "localhost", "::1"):
        ap.error("audio_wav writes on the debug-server host: loopback only")
    if not SHA40.fullmatch(args.source_sha):
        ap.error("--source-sha must be a 40-digit lowercase Git SHA")
    if not args.native_executable.is_file() or args.native_executable.is_symlink():
        ap.error("real native executable required for binary provenance")
    if args.json_out.exists() or args.json_out.is_symlink():
        ap.error("refusing to overwrite existing evidence JSON")
    sock, reader = connect(args.host, args.port, 20)
    sock.settimeout(45)
    try:
        report = capture(lambda line: command(sock, reader, line), event_filter=1)
        result = capture_kon_pcm(
            lambda line: command(sock, reader, line),
            events=report["events"], produced=report["stats"]["produced"],
            kon_sample_index=args.kon_sample_index,
            wav_path=args.wav_out.absolute(), before=args.before, after=args.after,
        )
    finally:
        reader.close()
        sock.close()
    result["source_sha_claim"] = args.source_sha
    result["native_executable_sha256"] = hashlib.sha256(args.native_executable.read_bytes()).hexdigest()
    result["event_head"] = report["event_head"]
    result["kon_candidates_in_retained_event_ring"] = kon_candidates(report["events"])
    result["producer_sample_count_before_capture"] = report["stats"]["produced"]
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"QA01 native DSP KON PCM captured: {result['sample_frames']} samples, "
          f"KON at +{result['kon_offset_frames']}, WAV sha256={result['wav_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
