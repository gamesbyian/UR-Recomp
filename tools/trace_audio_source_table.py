#!/usr/bin/env python3
"""Recover the live ROM-side source feeding Uniracers' APU upload loop.

The transfer body at CPU $xx:8298 is currently interpreter-backed in the pinned
SNESRecomp project, so this probe deliberately does not require a generated
`bank_*_8298_*` function. It combines existing observability instead:

- `trace_get_v2` to find retained CPU block entries whose low PC is $8298;
- `wram_writes_at` evidence, captured by `trace_native_wram_writers.py`,
  to reconstruct direct-page pointer bytes immediately before each hit;
- `dump_cart` to preserve bounded ROM windows for recovered LoROM pointers;
- the always-on `audio_events` ring for CPU-write/apply/SPC-read correlation.

The host should already have been driven through the deterministic first-race
fixture and left running/paused for this observer to reconnect.
"""
from __future__ import annotations

import argparse
import json
import socket
import time
from pathlib import Path

TARGET_ADDR16 = 0x8298
TRACE_PAGE = 4096
AUDIO_PAGE = 8000
AUDIO_RETAIN = 524288


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


def fetch_cpu_window(sock, reader, target_addr16: int = TARGET_ADDR16, *, max_pages: int = 128) -> dict:
    collected: dict[int, dict] = {}
    before_idx: int | None = None
    found_page: int | None = None
    for page in range(max_pages):
        line = f"trace_get_v2 count={TRACE_PAGE} event=0"
        if before_idx is not None:
            line += f" before_idx={before_idx}"
        result = command(sock, reader, line)
        rows = result.get("events", [])
        if not rows:
            break
        for row in rows:
            collected[int(row["idx"])] = row
        if any((parse_hex(row["pc24"]) & 0xFFFF) == target_addr16 for row in rows):
            found_page = page
        oldest_idx = min(int(row["idx"]) for row in rows)
        before_idx = oldest_idx
        if found_page is not None and page > found_page:
            break
        if oldest_idx == 0:
            break

    ordered = [collected[i] for i in sorted(collected)]
    hits = [row for row in ordered if (parse_hex(row["pc24"]) & 0xFFFF) == target_addr16]
    neighborhoods = []
    pos_by_idx = {int(row["idx"]): i for i, row in enumerate(ordered)}
    for hit in hits:
        pos = pos_by_idx[int(hit["idx"])]
        lo, hi = max(0, pos - 24), min(len(ordered), pos + 49)
        neighborhoods.append({"entry": hit, "events": ordered[lo:hi]})
    return {"events_collected": len(ordered), "target_hits": len(hits), "hits": hits, "neighborhoods": neighborhoods}


def _write_value_for_byte(row: dict) -> int:
    value = parse_hex(row["val"])
    return value & 0xFF


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
    cpu = fetch_cpu_window(sock, reader)
    if not cpu["hits"]:
        raise RuntimeError("no retained CPU trace hit with low PC $8298")

    d_values = sorted({parse_hex(row["D"]) for row in cpu["hits"]})
    if d_values != [0]:
        raise RuntimeError(f"expected observed transfer hits to use D=0; saw {[hex(v) for v in d_values]}")

    runtime_pcs = sorted({parse_hex(row["pc24"]) for row in cpu["hits"]})
    captures = []
    unique_ptrs: dict[int, dict] = {}
    for row in cpu["hits"]:
        idx = int(row["idx"])
        entry = pointer_before_block(writers, 0x0000, idx)
        work = pointer_before_block(writers, 0x0063, idx)
        cap = {
            "block_index": idx,
            "frame": row.get("f"),
            "pc24": f"0x{parse_hex(row['pc24']):06X}",
            "D": f"0x{parse_hex(row['D']):04X}",
            "entry_stream_pointer": f"0x{entry:06X}" if entry is not None else None,
            "working_pointer_63": f"0x{work:06X}" if work is not None else None,
        }
        for role, ptr in (("entry_stream", entry), ("working_63", work)):
            if ptr is None:
                continue
            off = lorom_file_offset(ptr)
            cap[role + "_file_offset"] = f"0x{off:06X}" if off is not None else None
            if off is not None and ptr not in unique_ptrs:
                cart = command(sock, reader, f"dump_cart {off:x} 1024")
                unique_ptrs[ptr] = {
                    "roles": [role],
                    "source_pointer": f"0x{ptr:06X}",
                    "source_file_offset": f"0x{off:06X}",
                    "cart_len": int(cart.get("len", 0)),
                    "cart_hex": cart.get("hex", ""),
                }
            elif ptr in unique_ptrs and role not in unique_ptrs[ptr]["roles"]:
                unique_ptrs[ptr]["roles"].append(role)
        captures.append(cap)

    audio_stats, audio_events = fetch_audio_events(sock, reader)
    return {
        "schema_version": 2,
        "target_addr16": "0x8298",
        "runtime_pcs": [f"0x{x:06X}" for x in runtime_pcs],
        "observed_D_values": [f"0x{x:04X}" for x in d_values],
        "cpu_trace": cpu,
        "captures": captures,
        "source_cart_windows": list(unique_ptrs.values()),
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

    print(f"runtime_pcs={report['runtime_pcs']} D={report['observed_D_values']} hits={len(report['captures'])}")
    for row in report["captures"]:
        if row.get("entry_stream_pointer") or row.get("working_pointer_63"):
            print(f"  idx={row['block_index']} frame={row.get('frame')} entry={row.get('entry_stream_pointer')} work63={row.get('working_pointer_63')}")
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
