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
import os
import re
import shutil
import tempfile
import wave
from pathlib import Path, PureWindowsPath

from capture_audio_events import capture, command, connect

SHA40 = re.compile(r"[0-9a-f]{40}\Z")


def kon_candidates(events: list[dict]) -> list[int]:
    """Native sample indices of every DSP write setting voice-7 KON bit."""
    found = []
    for e in events:
        if e.get("t") == "reg" and e.get("adr") == "0x4c":
            value = e.get("val")
            if type(value) is not str or not re.fullmatch(r"0x[0-9a-f]{2}", value):
                raise ValueError("malformed native KON register value")
            # DSP $4C is a voice bitmask. $81 and $FF also key voice 7.
            if int(value, 16) & 0x80:
                index = e.get("s")
                if type(index) is not int or index < 0:
                    raise ValueError("malformed native KON sample index")
                found.append(index)
    return found


def validate_output_separation(wav_path: Path, json_path: Path) -> None:
    """Reject equivalent paths before connecting or producing either artifact."""
    if wav_path.resolve(strict=False) == json_path.resolve(strict=False):
        raise ValueError("WAV and JSON output paths must be distinct")


def validate_event_ring_coverage(report: dict) -> None:
    """Offline KON uniqueness needs the entire pre-capture DSP event history.

    The generic event collector can silently begin at the ring's `oldest`
    index after overwrite. A retained single KON is then not evidence that
    another KON was absent from the requested PCM window.
    """
    if not isinstance(report, dict) or not isinstance(report.get('stats'), dict):
        raise ValueError('malformed native DSP event-ring snapshot')
    oldest = report.get('oldest_available')
    head = report.get('event_head')
    stats_head = report['stats'].get('event_count')
    if (type(oldest) is not int or type(head) is not int or
            type(stats_head) is not int or oldest < 0 or head < 0 or
            stats_head != head):
        raise ValueError('malformed native DSP event-ring counters')
    if oldest != 0:
        raise ValueError('native DSP event-ring history overwritten; use live armed capture')
    scan_end = report.get('last_scanned_event_index')
    if (report.get('event_pages_contiguous') is not True or
            type(scan_end) is not int or scan_end < head):
        raise ValueError('incomplete or discontinuous native DSP event-ring scan')
    events = report.get('events')
    if (not isinstance(events, list) or
            type(report.get('events_returned')) is not int or
            report['events_returned'] != len(events)):
        raise ValueError('malformed native DSP event-ring census')


def wav_command_path(wav_path: Path) -> str:
    """Return a JSON-safe server path without changing the local file target.

    The pinned debug server interpolates its path into JSON without escaping.
    Native WindowsPath uses backslashes, so send Windows-compatible forward
    slashes; do not rewrite a legitimate POSIX backslash filename silently.
    """
    path = str(wav_path)
    if isinstance(wav_path, PureWindowsPath):
        path = path.replace("\\", "/")
    if ('"' in path or "\\" in path or any(ord(c) < 32 for c in path)):
        raise ValueError("audio_wav destination cannot be represented safely in native JSON")
    # The pinned server parses audio_wav with sscanf("%511s ..."). A longer
    # token is truncated BEFORE it opens the path with "wb", potentially
    # overwriting a foreign file sharing that prefix. Bound encoded bytes,
    # not Unicode code points, before any command can reach the server.
    try:
        encoded = path.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValueError("audio_wav destination cannot be encoded as UTF-8") from exc
    if len(encoded) > 511:
        raise ValueError("audio_wav destination exceeds server's 511-byte path token")
    # The shared capture_audio_events.command sends ASCII, while the pinned
    # native producer opens paths with narrow fopen (Windows active codepage).
    # Neither transport nor filesystem semantics can promise Unicode paths.
    # Refuse before issuing the destructive server-side WAV write; a future
    # Unicode-capable staging route must independently prove safe relocation.
    try:
        path.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError("audio_wav debug transport requires an ASCII server-local path") from exc
    return path


def publish_wav_no_replace(staged_path: Path, wav_path: Path) -> None:
    """Publish staged WAV without opening an existing destination for writing."""
    try:
        os.link(staged_path, wav_path)
    except FileExistsError as exc:
        raise ValueError("refusing to replace WAV created during capture") from exc
    except OSError:
        # Hard links are unavailable on some volumes. Exclusive creation
        # preserves a destination created by another process, even a symlink.
        try:
            with staged_path.open("rb") as src, wav_path.open("xb") as dst:
                shutil.copyfileobj(src, dst)
                dst.flush()
                os.fsync(dst.fileno())
        except FileExistsError as exc:
            raise ValueError("refusing to replace WAV created during capture") from exc
    # A failed publication leaves no plausible success receipt. A partial
    # exclusively created fallback file is retained rather than deleting an
    # uncertain pathname after an exception.
    if hashlib.sha256(staged_path.read_bytes()).digest() != hashlib.sha256(wav_path.read_bytes()).digest():
        raise ValueError("published WAV differs from captured staging bytes")


def capture_kon_pcm(command_fn, *, events: list[dict], produced: int,
                    kon_sample_index: int, wav_path: Path,
                    before: int = 4096, after: int = 32768) -> dict:
    """Fail closed on missing/ambiguous KON or clamped, stale, malformed PCM."""
    if any(type(v) is not int for v in (produced, kon_sample_index, before, after)):
        raise ValueError("sample counters must be integers")
    if not 1 <= before <= 64000 or not 1 <= after <= 64000:
        raise ValueError("bounded pre/post KON sample windows required")
    candidates = kon_candidates(events)
    # The RF094 target is the literal $4C=$80 write. A combined bitmask
    # cannot substitute for it, but must invalidate a single-KON window.
    exact = [e.get("s") for e in events if e.get("t") == "reg"
             and e.get("adr") == "0x4c" and e.get("val") == "0x80"]
    start = kon_sample_index - before
    count = before + after
    # A distinct voice-7 key-on inside the WAV slice makes this an ambiguous
    # single-KON witness even if the selected sample index occurs only once.
    if (exact.count(kon_sample_index) != 1 or
            candidates.count(kon_sample_index) != 1 or
            any(start <= sample < start + count and sample != kon_sample_index
                for sample in candidates)):
        raise ValueError("selected $4C=$80 KON missing or ambiguous in actual event ring")
    if start < 0 or produced < start + count:
        raise ValueError("KON PCM window not yet fully produced")
    if not wav_path.is_absolute() or any(c.isspace() for c in str(wav_path)):
        raise ValueError("audio_wav requires absolute whitespace-free server-local path")
    if wav_path.exists() or wav_path.is_symlink():
        raise ValueError("refusing to reuse or overwrite an existing WAV")
    if not wav_path.parent.is_dir() or wav_path.parent.is_symlink():
        raise ValueError("WAV destination parent must be an existing real directory")
    # The pinned native server uses fopen("wb") and cannot enforce O_EXCL.
    # Give it a fresh, non-preexisting name inside a per-attempt directory,
    # then publish to the requested destination with no-replace semantics.
    # This protects foreign destination bytes against concurrent creation.
    with tempfile.TemporaryDirectory(prefix=".qa01-kon-", dir=wav_path.parent) as stage_dir:
        staged_path = Path(stage_dir) / "audio.wav"
        wire_path = wav_command_path(staged_path)
        response = command_fn(f"audio_wav {wire_path} {start} {count}")
        if (response.get("ok") is not True or response.get("start") != start or
                response.get("count") != count or response.get("path") != wire_path):
            raise ValueError("audio_wav returned clamped/mismatched native PCM slice")
        if not staged_path.is_file() or staged_path.is_symlink():
            raise ValueError("audio_wav did not create a real staged WAV")
        with wave.open(str(staged_path), "rb") as wav:
            if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate(),
                    wav.getcomptype(), wav.getnframes()) != (2, 2, 32040, "NONE", count):
                raise ValueError("native PCM WAV format/sample count mismatch")
            pcm = wav.readframes(count)
        if len(pcm) != count * 4:
            raise ValueError("short decoded native stereo PCM")
        # Pinned producer emits a fixed 44-byte header plus four bytes/frame.
        if staged_path.stat().st_size != 44 + count * 4:
            raise ValueError("unexpected native WAV length")
        publish_wav_no_replace(staged_path, wav_path)
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
    try:
        validate_output_separation(args.wav_out, args.json_out)
    except ValueError as exc:
        ap.error(str(exc))
    if args.json_out.exists() or args.json_out.is_symlink():
        ap.error("refusing to overwrite existing evidence JSON")
    sock, reader = connect(args.host, args.port, 20)
    sock.settimeout(45)
    try:
        report = capture(lambda line: command(sock, reader, line), event_filter=1)
        validate_event_ring_coverage(report)
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
    with args.json_out.open("x", encoding="utf-8") as receipt_file:
        receipt_file.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"QA01 native DSP KON PCM captured: {result['sample_frames']} samples, "
          f"KON at +{result['kon_offset_frames']}, WAV sha256={result['wav_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
