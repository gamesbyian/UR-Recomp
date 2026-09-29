#!/usr/bin/env python3
"""Recover ROM-side source candidates feeding Uniracers' APU upload body.

Static retail bytes establish:
- $02:8298-$02:82A4: short transfer-state initializer.
- $02:82A5: JSR $82A9 / RTL public wrapper.
- $02:82A9: upload body. It stores X at DP $83, reads $03:0000,X,
  and later reaches the proven $2142/$2143 byte-transfer loop.

SNESRecomp's WRAM-write recorder exposes the 16-bit STX as paired byte writes
at $83/$84 sharing one block index.  This tool joins those pairs, correlates
them with immediate LDX seeds preceding static JSL $82:82A5 callsites, and
captures ROM windows for the resulting bank-03 source candidates.
"""
from __future__ import annotations

import argparse
import json
import socket
import time
from pathlib import Path

AUDIO_PAGE = 8000
AUDIO_RETAIN = 524288
FRAME_LO = 880
FRAME_HI = 983


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


def byte_before_block(writes: list[dict], block_idx: int) -> int | None:
    eligible = [w for w in writes if int(w.get("bi", -1)) <= block_idx]
    if not eligible:
        return None
    eligible.sort(key=lambda w: int(w.get("bi", -1)))
    return parse_hex(eligible[-1]["val"]) & 0xFF


def pointer_before_block(writers: dict, base_addr: int, block_idx: int) -> int | None:
    parts = []
    for off in range(3):
        row = writers.get("addresses", {}).get(f"0x{base_addr + off:04X}")
        if not row:
            return None
        value = byte_before_block(row.get("writes", []), block_idx)
        if value is None:
            return None
        parts.append(value)
    return parts[0] | (parts[1] << 8) | (parts[2] << 16)


def paired_dp83_values(writers: dict, frame_lo: int = FRAME_LO, frame_hi: int = FRAME_HI) -> list[dict]:
    lows = writers.get("addresses", {}).get("0x0083", {}).get("writes", [])
    highs = writers.get("addresses", {}).get("0x0084", {}).get("writes", [])
    hi_by_bi = {int(w.get("bi", -1)): w for w in highs}
    rows = []
    for lo in lows:
        bi = int(lo.get("bi", -1))
        hi = hi_by_bi.get(bi)
        if hi is None:
            continue
        frame = int(str(lo.get("f", "0")), 0)
        if not frame_lo <= frame <= frame_hi:
            continue
        low = parse_hex(lo["val"]) & 0xFF
        high = parse_hex(hi["val"]) & 0xFF
        x = low | (high << 8)
        rows.append({
            "frame": frame,
            "block_index": bi,
            "x_value": f"0x{x:04X}",
            "source_pointer_03x": f"0x{0x030000 | x:06X}",
            "low_scope": lo.get("func"),
            "high_scope": hi.get("func"),
        })
    rows.sort(key=lambda r: r["block_index"])
    return rows


def static_ldx_seeds(callsites: dict) -> list[dict]:
    rows = []
    for hit in callsites.get("patterns", {}).get("JSL_8282A5", []):
        context = bytes.fromhex(hit["context_hex"])
        context_start = int(hit["context_start_hex"], 16)
        call_off = int(hit["rom_offset_hex"], 16)
        rel = call_off - context_start
        seed = None
        if rel >= 3 and context[rel - 3] == 0xA2:
            seed = context[rel - 2] | (context[rel - 1] << 8)
        row = {
            "caller_rom_offset": hit["rom_offset_hex"],
            "caller_cpu_pc24": hit["cpu_pc24"],
            "x_seed": f"0x{seed:04X}" if seed is not None else None,
        }
        if seed is not None:
            source = 0x030000 | seed
            off = lorom_file_offset(source)
            row["source_pointer_03x"] = f"0x{source:06X}"
            row["source_file_offset"] = f"0x{off:06X}" if off is not None else None
        rows.append(row)
    return rows


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


def run_probe(sock, reader, writers: dict, callsites: dict) -> dict:
    live = paired_dp83_values(writers)
    static = static_ldx_seeds(callsites)
    if not live:
        raise RuntimeError("no paired DP $83/$84 writes found in first-race window")
    seeds = sorted({int(r["x_seed"], 16) for r in static if r.get("x_seed")})
    if not seeds:
        raise RuntimeError("no immediate LDX seeds found before JSL $82:82A5 callsites")

    first_x = int(live[0]["x_value"], 16)
    live_seed_matches = [s for s in seeds if (s >> 8) == (first_x >> 8) and s <= first_x]
    nearest_seed = max(live_seed_matches) if live_seed_matches else None

    source_windows = []
    for seed in seeds:
        source = 0x030000 | seed
        off = lorom_file_offset(source)
        if off is None:
            continue
        cart = command(sock, reader, f"dump_cart {off:x} 8192")
        source_windows.append({
            "x_seed": f"0x{seed:04X}",
            "source_pointer": f"0x{source:06X}",
            "source_file_offset": f"0x{off:06X}",
            "cart_len": int(cart.get("len", 0)),
            "cart_hex": cart.get("hex", ""),
        })

    comparisons = []
    for row in live:
        idx = row["block_index"]
        comparisons.append({
            **row,
            "dp00_pointer_before": (
                f"0x{p:06X}" if (p := pointer_before_block(writers, 0x0000, idx)) is not None else None
            ),
            "dp63_pointer_before": (
                f"0x{p:06X}" if (p := pointer_before_block(writers, 0x0063, idx)) is not None else None
            ),
        })

    audio_stats, audio_events = fetch_audio_events(sock, reader)
    return {
        "schema_version": 4,
        "static_interpretation": {
            "initializer": "02:8298-02:82A4",
            "transfer_wrapper": "02:82A5",
            "transfer_body": "02:82A9",
            "source_expression": "LDA $030000,X after STX $83",
        },
        "static_source_candidates": static,
        "live_x_progression": comparisons,
        "first_live_x": f"0x{first_x:04X}",
        "nearest_static_seed": f"0x{nearest_seed:04X}" if nearest_seed is not None else None,
        "source_cart_windows": source_windows,
        "audio_stats": audio_stats,
        "audio_events": audio_events,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--writers-json", type=Path, required=True)
    ap.add_argument("--callsites-json", type=Path, required=True)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=4377)
    ap.add_argument("--connect-timeout", type=float, default=20.0)
    ap.add_argument("--command-timeout", type=float, default=60.0)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    writers = json.loads(args.writers_json.read_text())
    callsites = json.loads(args.callsites_json.read_text())

    sock, reader = connect(args.host, args.port, args.connect_timeout)
    sock.settimeout(args.command_timeout)
    try:
        report = run_probe(sock, reader, writers, callsites)
    finally:
        reader.close()
        sock.close()

    print(
        f"live_pairs={len(report['live_x_progression'])} "
        f"first_x={report['first_live_x']} nearest_seed={report['nearest_static_seed']}"
    )
    for row in report["static_source_candidates"]:
        if row.get("x_seed"):
            print(
                f"  caller={row['caller_cpu_pc24']} X={row['x_seed']} "
                f"source={row['source_pointer_03x']} file={row['source_file_offset']}"
            )
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
