#!/usr/bin/env python3
"""Capture the live CPU-side source feeding Uniracers' APU stream transfer.

Uses only existing SNESRecomp trace-build observability:
- function-boundary low-WRAM snapshots,
- the always-on CPU block trace ring,
- the always-on audio port-event ring,
- live cartridge reads.

The host should be launched paused with tests/input/reach-first-race.script.
"""
from __future__ import annotations

import argparse
import json
import socket
import time
from pathlib import Path

TARGET_PC24 = 0x828298
RACE_ACTIVE_WRAM = 0x0313
TRACE_PAGE = 4096
AUDIO_PAGE = 8000


def command(sock: socket.socket, reader, line: str) -> dict:
    sock.sendall((line + "\n").encode("ascii"))
    raw = reader.readline()
    if not raw:
        raise RuntimeError(f"debug server disconnected after command: {line}")
    result = json.loads(raw)
    if result.get("error") or result.get("ok") is False:
        raise RuntimeError(f"debug command failed: {line}: {result}")
    return result


def connect(host: str, port: int, timeout: float):
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        sock = socket.socket()
        sock.settimeout(2.0)
        try:
            sock.connect((host, port))
            return sock, sock.makefile("r", encoding="utf-8", newline="\n")
        except OSError as exc:
            last_error = exc
            sock.close()
            time.sleep(0.1)
    raise RuntimeError(f"could not connect to {host}:{port}: {last_error}")


def parse_hex(value) -> int:
    if isinstance(value, int):
        return value
    return int(str(value), 16)


def parse_blob_hex(text: str) -> bytes:
    return bytes.fromhex(text.replace(" ", "").strip())


def generated_variant_name(pc24: int, m_flag: int, x_flag: int) -> str:
    return (
        f"bank_{(pc24 >> 16) & 0xFF:02X}_{pc24 & 0xFFFF:04X}"
        f"_M{int(m_flag)}X{int(x_flag)}"
    )


def lorom_file_offset(cpu_addr: int) -> int | None:
    """Map a conventional LoROM high-half CPU address to file offset."""
    bank = (cpu_addr >> 16) & 0xFF
    addr = cpu_addr & 0xFFFF
    if addr < 0x8000:
        return None
    bank &= 0x7F
    if bank > 0x7D:
        return None
    return bank * 0x8000 + (addr - 0x8000)


def source_pointer_from_snapshot(
    snapshot: bytes,
    snapshot_start: int,
    d_register: int,
) -> int | None:
    """Read the 24-bit pointer addressed by [$63] with the captured D value."""
    ptr_addr = (d_register + 0x63) & 0xFFFF
    rel = ptr_addr - snapshot_start
    if rel < 0 or rel + 3 > len(snapshot):
        return None
    lo, hi, bank = snapshot[rel : rel + 3]
    return lo | (hi << 8) | (bank << 16)


def fetch_audio_events(sock, reader, first: int, end: int) -> list[dict]:
    events: list[dict] = []
    cursor = first
    while cursor < end:
        result = command(sock, reader, f"audio_events {cursor} {AUDIO_PAGE} 2")
        scanned = int(result.get("scanned", 0))
        actual_first = int(result.get("first", cursor))
        events.extend(result.get("events", []))
        if scanned <= 0:
            break
        cursor = max(cursor, actual_first) + scanned
        if scanned < AUDIO_PAGE:
            break
    return events


def fetch_cpu_window(
    sock,
    reader,
    target_pc24: int,
    *,
    max_pages: int = 96,
    context_before: int = 24,
    context_after: int = 48,
) -> dict:
    """Walk the block ring backward until target entry plus older context exists."""
    collected: dict[int, dict] = {}
    before_idx: int | None = None
    found_page: int | None = None
    pages_scanned = 0

    for page in range(max_pages):
        line = f"trace_get_v2 count={TRACE_PAGE} event=0"
        if before_idx is not None:
            line += f" before_idx={before_idx}"
        result = command(sock, reader, line)
        rows = result.get("events", [])
        pages_scanned += 1
        if not rows:
            break
        for row in rows:
            collected[int(row["idx"])] = row
        if any(parse_hex(row["pc24"]) == target_pc24 for row in rows):
            found_page = page
        oldest_idx = min(int(row["idx"]) for row in rows)
        before_idx = oldest_idx
        # Once target was found, scan one additional older page so the
        # chronological neighborhood includes caller-side blocks.
        if found_page is not None and page > found_page:
            break
        if oldest_idx == 0:
            break

    ordered = [collected[i] for i in sorted(collected)]
    target_positions = [
        i for i, row in enumerate(ordered)
        if parse_hex(row["pc24"]) == target_pc24
    ]
    neighborhoods = []
    for pos in target_positions:
        lo = max(0, pos - context_before)
        hi = min(len(ordered), pos + context_after + 1)
        neighborhoods.append(
            {
                "target_index": int(ordered[pos]["idx"]),
                "entry": ordered[pos],
                "events": ordered[lo:hi],
            }
        )
    return {
        "pages_scanned": pages_scanned,
        "events_collected": len(ordered),
        "target_hits": len(target_positions),
        "neighborhoods": neighborhoods,
    }


def read_wram_byte(sock, reader, address: int) -> int:
    result = command(sock, reader, f"dump_ram {address:x} 1")
    raw = result.get("hex", "")
    if not raw:
        raise RuntimeError(f"empty WRAM read at 0x{address:04X}")
    return int(raw, 16)


def fetch_snapshot(
    sock,
    reader,
    call_idx: int,
    d_register: int,
    *,
    flank: int = 0x40,
    length: int = 0x80,
) -> dict:
    dp_start = (d_register + flank) & 0xFFFF
    if dp_start + length > 0x2000:
        # Snapshot storage is the low 8KB only; keep the failure explicit.
        return {
            "call_idx": call_idx,
            "available": False,
            "reason": "direct-page window lies outside function snapshot slice",
            "D": f"0x{d_register:04X}",
        }
    result = command(
        sock,
        reader,
        f"func_snap_get_n {call_idx} {dp_start:x} {length}",
    )
    blob = parse_blob_hex(result["hex"])
    pointer = source_pointer_from_snapshot(blob, dp_start, d_register)
    return {
        "call_idx": call_idx,
        "frame": result.get("frame"),
        "available": True,
        "D": f"0x{d_register:04X}",
        "snapshot_start": f"0x{dp_start:04X}",
        "snapshot_len": len(blob),
        "snapshot_hex": blob.hex(),
        "source_pointer": f"0x{pointer:06X}" if pointer is not None else None,
        "source_file_offset": (
            f"0x{lorom_file_offset(pointer):06X}"
            if pointer is not None and lorom_file_offset(pointer) is not None
            else None
        ),
    }


def run_probe(
    sock,
    reader,
    *,
    snapshot_function: str,
    coarse_until: int,
    coarse_step: int,
    max_frames: int,
) -> dict:
    initial_audio = command(sock, reader, "audio_stats 0")
    initial_audio_head = int(initial_audio.get("event_count", 0))
    command(sock, reader, f"func_snap_set {snapshot_function}")

    stepped = 0
    coarse_target = min(coarse_until, max_frames)
    while stepped < coarse_target:
        batch = min(coarse_step, coarse_target - stepped)
        command(sock, reader, f"step {batch}")
        stepped += batch

    race_active_frame: int | None = None
    if read_wram_byte(sock, reader, RACE_ACTIVE_WRAM) == 1:
        race_active_frame = stepped
    while race_active_frame is None and stepped < max_frames:
        command(sock, reader, "step 1")
        stepped += 1
        if read_wram_byte(sock, reader, RACE_ACTIVE_WRAM) == 1:
            race_active_frame = stepped
            break

    cpu_window = fetch_cpu_window(sock, reader, TARGET_PC24)
    if not cpu_window["neighborhoods"]:
        raise RuntimeError(
            f"target PC 0x{TARGET_PC24:06X} not found in retained CPU block trace"
        )

    entry = cpu_window["neighborhoods"][-1]["entry"]
    d_register = parse_hex(entry["D"])
    observed_variant = generated_variant_name(
        TARGET_PC24,
        int(entry["m_flag"]),
        int(entry["x_flag"]),
    )

    snap_count = command(sock, reader, "func_snap_count")
    count = int(snap_count.get("count", 0))
    snapshots = []
    for call_idx in range(max(1, count - 15), count + 1):
        snapshots.append(fetch_snapshot(sock, reader, call_idx, d_register))

    final_audio = command(sock, reader, "audio_stats 0")
    final_audio_head = int(final_audio.get("event_count", 0))
    audio_events = fetch_audio_events(
        sock, reader, initial_audio_head, final_audio_head
    )

    unique_pointers: dict[int, dict] = {}
    for snap in snapshots:
        ptr_text = snap.get("source_pointer")
        off_text = snap.get("source_file_offset")
        if not ptr_text or not off_text:
            continue
        pointer = int(ptr_text, 16)
        offset = int(off_text, 16)
        if pointer in unique_pointers:
            continue
        # Keep this bounded. The source may be a packet stream; 512 bytes is
        # enough to identify headers and cross-correlate with the transfer.
        cart = command(sock, reader, f"dump_cart {offset:x} 512")
        unique_pointers[pointer] = {
            "source_pointer": ptr_text,
            "source_file_offset": off_text,
            "cart_len": int(cart.get("len", 0)),
            "cart_hex": cart.get("hex", ""),
        }

    return {
        "schema_version": 1,
        "target_pc24": f"0x{TARGET_PC24:06X}",
        "requested_snapshot_function": snapshot_function,
        "observed_variant": observed_variant,
        "snapshot_function_matches_observed": (
            snapshot_function == observed_variant
        ),
        "stepped_frames": stepped,
        "race_active_frame": race_active_frame,
        "cpu_trace": cpu_window,
        "snapshot_count": count,
        "snapshots": snapshots,
        "audio_event_range": {
            "first": initial_audio_head,
            "end": final_audio_head,
            "events_returned": len(audio_events),
        },
        "audio_events": audio_events,
        "source_cart_windows": list(unique_pointers.values()),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--snapshot-function", required=True)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=4377)
    ap.add_argument("--connect-timeout", type=float, default=20.0)
    ap.add_argument("--command-timeout", type=float, default=60.0)
    ap.add_argument("--coarse-until", type=int, default=900)
    ap.add_argument("--coarse-step", type=int, default=25)
    ap.add_argument("--max-frames", type=int, default=1800)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()

    sock, reader = connect(args.host, args.port, args.connect_timeout)
    sock.settimeout(args.command_timeout)
    try:
        report = run_probe(
            sock,
            reader,
            snapshot_function=args.snapshot_function,
            coarse_until=args.coarse_until,
            coarse_step=args.coarse_step,
            max_frames=args.max_frames,
        )
    finally:
        reader.close()
        sock.close()

    print(
        f"target={report['target_pc24']} "
        f"variant={report['observed_variant']} "
        f"snapshot_calls={report['snapshot_count']} "
        f"audio_events={report['audio_event_range']['events_returned']} "
        f"race_active_frame={report['race_active_frame']}"
    )
    for snap in report["snapshots"]:
        if snap.get("source_pointer"):
            print(
                f"  call={snap['call_idx']} frame={snap.get('frame')} "
                f"source={snap['source_pointer']} "
                f"file={snap.get('source_file_offset')}"
            )

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
