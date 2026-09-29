#!/usr/bin/env python3
"""Trace CPU writes to the SNES APU I/O ports through SNESRecomp debug_server."""
from __future__ import annotations

import argparse
import json
import socket
import time
from collections import Counter, defaultdict
from pathlib import Path

APU_PORT_LO = 0x2140
APU_PORT_HI_EXCLUSIVE = 0x2144
RACE_ACTIVE_WRAM = 0x0313


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


def _hex_field(value) -> int:
    if isinstance(value, int):
        return value
    text = str(value).strip().lower()
    if text.startswith("0x"):
        return int(text, 16)
    return int(text, 16)


def _frame_field(value) -> int:
    if isinstance(value, int):
        return value
    text = str(value).strip().lower()
    return int(text, 0)


def normalize_events(raw_log: list[dict]) -> list[dict]:
    out = []
    for index, item in enumerate(raw_log):
        address = _hex_field(item["adr"])
        if not APU_PORT_LO <= address < APU_PORT_HI_EXCLUSIVE:
            continue
        out.append(
            {
                "seq": index,
                "frame": _frame_field(item["f"]),
                "address": address,
                "address_hex": f"0x{address:04X}",
                "port": address - APU_PORT_LO,
                "value": _hex_field(item["val"]) & 0xFF,
                "value_hex": f"0x{_hex_field(item['val']) & 0xFF:02X}",
            }
        )
    return out


def group_bursts(events: list[dict], max_frame_gap: int = 1) -> list[dict]:
    if not events:
        return []
    bursts: list[list[dict]] = [[events[0]]]
    for event in events[1:]:
        if event["frame"] - bursts[-1][-1]["frame"] > max_frame_gap:
            bursts.append([event])
        else:
            bursts[-1].append(event)

    result = []
    for index, burst in enumerate(bursts):
        counts = Counter(event["address_hex"] for event in burst)
        result.append(
            {
                "index": index,
                "start_frame": burst[0]["frame"],
                "end_frame": burst[-1]["frame"],
                "frame_span": burst[-1]["frame"] - burst[0]["frame"] + 1,
                "event_count": len(burst),
                "per_port_counts": dict(sorted(counts.items())),
                "events": [
                    {
                        "frame": event["frame"],
                        "address_hex": event["address_hex"],
                        "value_hex": event["value_hex"],
                    }
                    for event in burst
                ],
            }
        )
    return result


def summarize(events: list[dict], race_active_frame: int | None) -> dict:
    by_port: dict[str, dict] = {}
    for address in range(APU_PORT_LO, APU_PORT_HI_EXCLUSIVE):
        rows = [event for event in events if event["address"] == address]
        values = Counter(event["value_hex"] for event in rows)
        by_port[f"0x{address:04X}"] = {
            "writes": len(rows),
            "unique_values": len(values),
            "value_counts": dict(sorted(values.items())),
        }

    by_frame: dict[int, list[str]] = defaultdict(list)
    for event in events:
        by_frame[event["frame"]].append(
            f"{event['address_hex']}={event['value_hex']}"
        )

    return {
        "schema_version": 1,
        "range": {
            "start_hex": f"0x{APU_PORT_LO:04X}",
            "end_exclusive_hex": f"0x{APU_PORT_HI_EXCLUSIVE:04X}",
        },
        "race_active_frame": race_active_frame,
        "event_count": len(events),
        "first_frame": events[0]["frame"] if events else None,
        "last_frame": events[-1]["frame"] if events else None,
        "frames_with_writes": len(by_frame),
        "ports": by_port,
        "bursts_max_frame_gap_1": group_bursts(events),
        "frame_signatures": [
            {"frame": frame, "writes": writes}
            for frame, writes in sorted(by_frame.items())
        ],
        "events": events,
    }


def read_wram_byte(sock: socket.socket, reader, address: int) -> int:
    result = command(sock, reader, f"dump_ram 0x{address:x} 1")
    raw = result.get("hex", "").replace(" ", "")
    if not raw:
        raise RuntimeError(f"empty WRAM read at 0x{address:04X}")
    return int(raw, 16)


def run_trace(
    sock: socket.socket,
    reader,
    *,
    coarse_until: int,
    coarse_step: int,
    max_frames: int,
) -> dict:
    command(sock, reader, "trace_reg_reset")
    command(
        sock,
        reader,
        f"trace_reg {APU_PORT_LO:x} {APU_PORT_HI_EXCLUSIVE:x}",
    )

    stepped = 0
    race_active_frame: int | None = None
    coarse_target = min(coarse_until, max_frames)
    while stepped < coarse_target:
        batch = min(coarse_step, coarse_target - stepped)
        command(sock, reader, f"step {batch}")
        stepped += batch

    if read_wram_byte(sock, reader, RACE_ACTIVE_WRAM) == 1:
        race_active_frame = stepped

    while race_active_frame is None and stepped < max_frames:
        command(sock, reader, "step 1")
        stepped += 1
        if read_wram_byte(sock, reader, RACE_ACTIVE_WRAM) == 1:
            race_active_frame = stepped
            break

    trace = command(sock, reader, "get_reg_trace nostack")
    events = normalize_events(trace.get("log", []))
    report = summarize(events, race_active_frame)
    report["stepped_frames"] = stepped
    report["trace_entries_reported"] = trace.get("entries")
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=4377)
    ap.add_argument("--connect-timeout", type=float, default=20.0)
    ap.add_argument("--command-timeout", type=float, default=45.0)
    ap.add_argument("--coarse-until", type=int, default=900)
    ap.add_argument("--coarse-step", type=int, default=25)
    ap.add_argument("--max-frames", type=int, default=1800)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()

    sock, reader = connect(args.host, args.port, args.connect_timeout)
    sock.settimeout(args.command_timeout)
    try:
        report = run_trace(
            sock,
            reader,
            coarse_until=args.coarse_until,
            coarse_step=args.coarse_step,
            max_frames=args.max_frames,
        )
    finally:
        reader.close()
        sock.close()

    print(
        "APU port writes: "
        f"events={report['event_count']} "
        f"frames={report['frames_with_writes']} "
        f"race_active_frame={report['race_active_frame']} "
        f"bursts={len(report['bursts_max_frame_gap_1'])}"
    )
    for address, row in report["ports"].items():
        print(
            f"  {address}: writes={row['writes']} "
            f"unique_values={row['unique_values']}"
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
