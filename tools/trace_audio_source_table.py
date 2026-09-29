#!/usr/bin/env python3
"""Recover the ROM-side source candidates feeding Uniracers' APU upload code.

Static bytes establish two adjacent routines:
- $02:8298-$02:82A4 is a short initializer (clears DP $68/$6A/$6C).
- $02:82A5 is a JSR/RTL wrapper for the longer body at $02:82A9.
  That body stores X to DP $83, then reads `LDA $030000,X` before entering
  the known $2142/$2143 transport loop.

The $8298 body is interpreter-backed in the pinned generated project and does
not appear as its own cpu-trace block, so this probe uses WRAM write evidence
instead of inventing a generated-function boundary.  It treats live 16-bit
writes to DP $83 as candidate upload-entry X values, derives $03:XXXX source
addresses from them, preserves ROM windows with dump_cart, and also records
the older DP+$00 and DP+$63 state for comparison rather than assuming either
is the original source pointer.
"""
from __future__ import annotations

import argparse
import json
import socket
import time
from pathlib import Path

AUDIO_PAGE = 8000
AUDIO_RETAIN = 524288
TRANSFER_FRAME_LO = 900
TRANSFER_FRAME_HI = 983


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


def lorom_file_offset(cpu_addr: int) -> int | None:
    bank = (cpu_addr >> 16) & 0xFF
    addr = cpu_addr & 0xFFFF
    if addr < 0x8000:
        return None
    bank &= 0x7F
    if bank > 0x7D:
        return None
    return bank * 0x8000 + (addr - 0x8000)


def _write_value_for_byte(row: dict) -> int:
    return parse_hex(row["val"]) & 0xFF


def byte_before_block(writes: list[dict], block_idx: int) -> int | None:
    eligible = [w for w in writes if int(w.get("bi", -1)) <= block_idx]
    if not eligible:
        return None
    eligible.sort(key=lambda w: int(w.get("bi", -1)))
    return _write_value_for_byte(eligible[-1])


def pointer_before_block(writers: dict, base_addr: int, block_idx: int) -> int | None:
    parts = []
    for off in range(3):
        key = f"0x{base_addr + off:04X}"
        row = writers.get("addresses", {}).get(key)
        if not row:
            return None
        value = byte_before_block(row.get("writes", []), block_idx)
        if value is None:
            return None
        parts.append(value)
    return parts[0] | (parts[1] << 8) | (parts[2] << 16)


def transfer_seed_events(
    writers: dict,
    *,
    frame_lo: int = TRANSFER_FRAME_LO,
    frame_hi: int = TRANSFER_FRAME_HI,
) -> list[dict]:
    """Return exact 16-bit writes to DP $83 in the first-race upload window."""
    row = writers.get("addresses", {}).get("0x0083", {})
    out = []
    for w in row.get("writes", []):
        if str(w.get("adr", "")).lower() not in {"0x00083", "0x0083", "0x83"}:
            continue
        if int(w.get("w", 0)) != 2:
            continue
        frame = int(str(w.get("f", "0")), 0)
        if not (frame_lo <= frame <= frame_hi):
            continue
        x_value = parse_hex(w["val"]) & 0xFFFF
        source = 0x030000 | x_value
        out.append(
            {
                "frame": frame,
                "block_index": int(w.get("bi", -1)),
                "x_value": f"0x{x_value:04X}",
                "source_pointer_03x": f"0x{source:06X}",
                "source_file_offset": (
                    f"0x{lorom_file_offset(source):06X}"
                    if lorom_file_offset(source) is not None
                    else None
                ),
                "scope": w.get("func"),
                "parent": w.get("parent"),
                "raw_write": w,
            }
        )
    return out


def fetch_audio_events(sock, reader) -> tuple[dict, list[dict]]:
    stats = command(sock, reader, "audio_stats 0")
    head = int(stats.get("event_count", 0))
    cursor = max(0, head - AUDIO_RETAIN)
    events: list[dict] = []
    while cursor < head:
        result = command(sock, reader, f"audio_events {cursor} {AUDIO_PAGE} 2")
        scanned = int(result.get("scanned", 0))
        actual_first = int(result.get("first", cursor))
        events.extend(result.get("events", []))
        if scanned <= 0:
            break
        cursor = max(cursor, actual_first) + scanned
        if scanned < AUDIO_PAGE:
            break
    return stats, events


def run_probe(sock, reader, writers: dict) -> dict:
    seeds = transfer_seed_events(writers)
    if not seeds:
        raise RuntimeError("no 16-bit DP $83 writes found in first-race upload window")

    unique_sources: dict[int, dict] = {}
    for row in seeds:
        source = int(row["source_pointer_03x"], 16)
        off = lorom_file_offset(source)
        if off is None or source in unique_sources:
            continue
        cart = command(sock, reader, f"dump_cart {off:x} 8192")
        unique_sources[source] = {
            "source_pointer": f"0x{source:06X}",
            "source_file_offset": f"0x{off:06X}",
            "cart_len": int(cart.get("len", 0)),
            "cart_hex": cart.get("hex", ""),
        }

    comparisons = []
    for row in seeds:
        idx = row["block_index"]
        comparisons.append(
            {
                **{k: row[k] for k in (
                    "frame", "block_index", "x_value", "source_pointer_03x",
                    "source_file_offset", "scope", "parent"
                )},
                "dp00_pointer_before": (
                    f"0x{p:06X}" if (p := pointer_before_block(writers, 0x0000, idx)) is not None else None
                ),
                "dp63_pointer_before": (
                    f"0x{p:06X}" if (p := pointer_before_block(writers, 0x0063, idx)) is not None else None
                ),
            }
        )

    audio_stats, audio_events = fetch_audio_events(sock, reader)
    return {
        "schema_version": 3,
        "static_interpretation": {
            "initializer": "02:8298-02:82A4",
            "transfer_wrapper": "02:82A5",
            "transfer_body": "02:82A9",
            "source_expression": "LDA $030000,X after STX $83",
        },
        "transfer_seed_events": comparisons,
        "source_cart_windows": list(unique_sources.values()),
        "audio_stats": audio_stats,
        "audio_events": audio_events,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--writers-json", type=Path, required=True)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=4377)
    ap.add_argument("--connect-timeout", type=float, default=20.0)
    ap.add_argument("--command-timeout", type=float, default=60.0)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    writers = json.loads(args.writers_json.read_text())

    sock, reader = connect(args.host, args.port, args.connect_timeout)
    sock.settimeout(args.command_timeout)
    try:
        report = run_probe(sock, reader, writers)
    finally:
        reader.close()
        sock.close()

    print(f"transfer_seed_events={len(report['transfer_seed_events'])}")
    for row in report["transfer_seed_events"]:
        print(
            f"  f={row['frame']} bi={row['block_index']} X={row['x_value']} "
            f"source={row['source_pointer_03x']} file={row['source_file_offset']} "
            f"scope={row['scope']} parent={row['parent']}"
        )
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
