#!/usr/bin/env python3
"""Live, bounded DSP-ring capture of the first voice-7 KON after arming.

The pinned debug server explicitly disables pause. Arm this watcher BEFORE
executing the relevant route. The first $4C=$80 event after arming is a
candidate, not independently verified as the Zoo fourth-command consequence.
The server writes the WAV locally; no guest or APU semantics are modified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

from capture_audio_events import command, connect
from qa01_native_pcm_at_kon import capture_kon_pcm, validate_output_separation, SHA40


def _nonnegative_int(value, label: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"invalid {label} from native debug server")
    return value


def watch_first_kon(command_fn, *, wav_path: Path, before: int = 4096,
                    after: int = 32768, capacity: int = 65536,
                    timeout: float = 45.0, interval: float = 0.02,
                    clock=time.monotonic, sleep=time.sleep, capture_fn=capture_kon_pcm) -> dict:
    """Arm at current event head; reject loss, ambiguous KON and PCM overwrite.

    capacity must be no larger than the actual compiled PCM ring. Default
    conservatively assumes SMALL; use FULL only with independent build proof.
    """
    if type(capacity) is not int or capacity < before + after:
        raise ValueError("PCM ring capacity must cover requested sample window")
    if not 0 < timeout <= 600 or not 0 < interval <= 1:
        raise ValueError("bounded live timeout and polling interval required")
    if not 1 <= before <= 64000 or not 1 <= after <= 64000:
        raise ValueError("bounded pre/post KON sample windows required")
    armed = command_fn("audio_stats 0")
    cursor = _nonnegative_int(armed.get("event_count"), "event_count")
    arm_cursor = cursor
    arm_produced = _nonnegative_int(armed.get("produced"), "arm produced samples")
    deadline = clock() + timeout
    candidate = None
    while clock() < deadline:
        page = command_fn(f"audio_events {cursor} 8000 1")
        oldest = _nonnegative_int(page.get("oldest"), "event oldest")
        first = _nonnegative_int(page.get("first"), "event first")
        scanned = _nonnegative_int(page.get("scanned"), "event scanned")
        if oldest > cursor or first != cursor or scanned > 8000:
            raise ValueError("live DSP event ring overrun or discontinuous page")
        events = page.get("events")
        if not isinstance(events, list):
            raise ValueError("malformed live DSP event page")
        for event in events:
            if not isinstance(event, dict):
                raise ValueError("malformed DSP register event")
            if (event.get("t") == "reg" and event.get("adr") == "0x4c"
                    and event.get("val") == "0x80"):
                sample = _nonnegative_int(event.get("s"), "KON sample index")
                if candidate is not None:
                    raise ValueError("multiple voice-7 KON events since live arm")
                candidate = {"s": sample, "t": "reg", "adr": "0x4c", "val": "0x80"}
        cursor += scanned
        stats = command_fn("audio_stats 0")
        produced = _nonnegative_int(stats.get("produced"), "produced samples")
        observed_head = _nonnegative_int(stats.get("event_count"), "event_count")
        if observed_head < cursor:
            raise ValueError("live DSP event count regressed behind scanned cursor")
        if candidate is not None:
            start = candidate["s"] - before
            if start < 0:
                raise ValueError("KON lacks requested pre-event PCM")
            # Events before the arm cursor are intentionally not scanned. If
            # the pre-KON PCM slice predates arming, an earlier voice-7 KON
            # could be inside it without appearing in the selected event set.
            if start < arm_produced:
                raise ValueError("pre-KON PCM window predates live arm; earlier KON not excluded")
            if produced - start > capacity:
                raise ValueError("live PCM ring retention window already expired")
            if produced >= candidate["s"] + after:
                # A later KON may have arrived between audio_events and stats.
                # Drain every event through the observed stats high-water mark
                # before accepting the completed PCM window.
                if observed_head > cursor:
                    continue
                result = capture_fn(command_fn, events=[candidate], produced=produced,
                                    kon_sample_index=candidate["s"], wav_path=wav_path,
                                    before=before, after=after)
                # audio_wav is a separate server command. The producer can
                # advance between the pre-WAV stats and its PCM snapshot.
                # Drain the post-WAV event high-water mark before accepting a
                # single-KON receipt, including events that arrived *during*
                # the WAV request. A rejected attempt may leave a WAV, but no
                # successful JSON receipt is published by main().
                post = command_fn("audio_stats 0")
                post_head = _nonnegative_int(post.get("event_count"), "event_count")
                post_produced = _nonnegative_int(post.get("produced"), "produced samples")
                if post_head < cursor or post_produced < produced:
                    raise ValueError("post-WAV native audio counters regressed")
                while cursor < post_head:
                    limit = min(8000, post_head - cursor)
                    page = command_fn(f"audio_events {cursor} {limit} 1")
                    oldest = _nonnegative_int(page.get("oldest"), "event oldest")
                    first = _nonnegative_int(page.get("first"), "event first")
                    scanned = _nonnegative_int(page.get("scanned"), "event scanned")
                    if oldest > cursor or first != cursor or not 1 <= scanned <= limit:
                        raise ValueError("post-WAV DSP event ring overrun or discontinuous page")
                    events = page.get("events")
                    if not isinstance(events, list):
                        raise ValueError("malformed post-WAV DSP event page")
                    for event in events:
                        if not isinstance(event, dict):
                            raise ValueError("malformed post-WAV DSP register event")
                        if (event.get("t") == "reg" and event.get("adr") == "0x4c"
                                and event.get("val") == "0x80"):
                            _nonnegative_int(event.get("s"), "KON sample index")
                            raise ValueError("multiple voice-7 KON events since live arm")
                    cursor += scanned
                result.update({
                    "selection": "first_voice7_kon_after_live_arm_unverified_route",
                    "arm_event_count": arm_cursor,
                    "arm_produced_samples": arm_produced,
                    "last_scanned_event_count": cursor,
                    "post_wav_event_count": post_head,
                    "post_wav_produced_samples": post_produced,
                    "assumed_pcm_ring_capacity": capacity,
                    "produced_samples_before_wav_request": produced,
                    "retention_margin_frames_before_wav_request": capacity - (produced - start),
                    "target_zoo_command_link_independently_verified": False,
                })
                return result
        sleep(interval)
    raise TimeoutError("no complete retained voice-7 KON PCM window before live timeout")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=4377)
    ap.add_argument("--before", type=int, default=4096)
    ap.add_argument("--after", type=int, default=32768)
    ap.add_argument("--pcm-ring-capacity", type=int, default=65536)
    ap.add_argument("--timeout", type=float, default=45.0)
    ap.add_argument("--wav-out", type=Path, required=True)
    ap.add_argument("--json-out", type=Path, required=True)
    ap.add_argument("--source-sha", required=True)
    ap.add_argument("--native-executable", type=Path, required=True)
    args = ap.parse_args()
    if args.host not in ("127.0.0.1", "localhost", "::1"):
        ap.error("server-side WAV capture requires loopback")
    if not SHA40.fullmatch(args.source_sha):
        ap.error("40-character lowercase Git source SHA required")
    if not args.native_executable.is_file() or args.native_executable.is_symlink():
        ap.error("real native executable required")
    wav = args.wav_out.absolute()
    receipt = args.json_out.absolute()
    try:
        validate_output_separation(wav, receipt)
    except ValueError as exc:
        ap.error(str(exc))
    if wav.exists() or wav.is_symlink() or receipt.exists() or receipt.is_symlink():
        ap.error("refusing to overwrite existing WAV or receipt")
    if not wav.parent.is_dir() or wav.parent.is_symlink():
        ap.error("WAV parent must exist and not be a symlink")
    sock, reader = connect(args.host, args.port, 20)
    sock.settimeout(10)
    try:
        result = watch_first_kon(
            lambda line: command(sock, reader, line), wav_path=wav,
            before=args.before, after=args.after,
            capacity=args.pcm_ring_capacity, timeout=args.timeout)
    finally:
        reader.close()
        sock.close()
    result["source_sha_claim"] = args.source_sha
    result["native_executable_sha256"] = hashlib.sha256(args.native_executable.read_bytes()).hexdigest()
    result["source_to_binary_identity_independently_verified"] = False
    receipt.parent.mkdir(parents=True, exist_ok=True)
    with receipt.open("x", encoding="utf-8") as out:
        out.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"Captured live candidate KON {result['kon_sample_index']} at {result['sample_frames']} PCM frames")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
