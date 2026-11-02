#!/usr/bin/env python3
"""Capture SNESRecomp's always-on audio event ring from the debug server.

This client does not advance the guest. It is intended to reconnect to a paused
trace build after another probe has driven the desired deterministic route.
"""
from __future__ import annotations

import argparse
import json
import socket
import time
from pathlib import Path


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


def page_events(command_fn, *, first: int, page_size: int, event_filter: int,
                stop_at: int | None = None) -> tuple[list[dict], dict]:
    """Fetch event slots, optionally ending at an immutable stats snapshot.

    A live DSP producer can keep returning full pages indefinitely. Strict
    capture passes the pre-scan event head as stop_at, limiting both the
    number of requests and the source interval independently of production.
    """
    if (type(first) is not int or first < 0 or
            type(page_size) is not int or page_size <= 0 or
            (stop_at is not None and
             (type(stop_at) is not int or stop_at < first))):
        raise ValueError("invalid DSP event scan bounds")
    events: list[dict] = []
    cursor = first
    last_meta: dict = {}
    contiguous = True
    while stop_at is None or cursor < stop_at:
        request_size = (page_size if stop_at is None else
                        min(page_size, stop_at - cursor))
        result = command_fn(f"audio_events {cursor} {request_size} {event_filter}")
        last_meta = dict(result)
        page = result.get("events", [])
        scanned = int(result.get("scanned", len(page)))
        returned_first = int(result.get("first", cursor))
        # The native server emits integer scanned/first/oldest fields. Keep
        # generic best-effort collection, but never certify a coerced or
        # missing counter as complete source-owned ring coverage.
        if (type(result.get("scanned")) is not int or
                type(result.get("first")) is not int or
                type(result.get("oldest")) is not int):
            contiguous = False
        # Preserve the generic collector's historic best-effort behavior,
        # but expose absolute scan coverage for strict KON evidence consumers.
        # The native server separately reports returned=len(serialized events)
        # and scanned=absolute ring slots. A mismatch could hide a voice-7
        # KON despite a seemingly contiguous scanned interval.
        if (returned_first != cursor or scanned < 0 or scanned > request_size
                or not isinstance(page, list) or len(page) > scanned
                or type(result.get("returned")) is not int
                or result["returned"] != len(page)):
            contiguous = False
        if page:
            events.extend(page)
        if scanned <= 0:
            break
        cursor = max(cursor, returned_first) + scanned
        if scanned < request_size:
            break
    last_meta["_client_scan_end"] = cursor
    last_meta["_client_contiguous"] = contiguous
    return events, last_meta


def capture(command_fn, *, page_size: int = 8000, event_filter: int = 0) -> dict:
    stats = command_fn("audio_stats 5")
    head = stats.get("event_count")
    if type(head) is not int or head < 0:
        raise ValueError("malformed audio_stats event_count")
    events, meta = page_events(
        command_fn,
        first=0,
        page_size=page_size,
        event_filter=event_filter,
        stop_at=head,
    )
    oldest = int(meta.get("oldest", 0)) if meta else 0
    return {
        "schema_version": 1,
        "event_filter": event_filter,
        "event_head": head,
        "oldest_available": oldest,
        "last_scanned_event_index": meta.get("_client_scan_end", 0),
        "event_pages_contiguous": meta.get("_client_contiguous", False),
        "events_returned": len(events),
        "stats": stats,
        "events": events,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=4377)
    ap.add_argument("--connect-timeout", type=float, default=20.0)
    ap.add_argument("--command-timeout", type=float, default=45.0)
    ap.add_argument("--page-size", type=int, default=8000)
    ap.add_argument("--filter", type=int, default=0, dest="event_filter")
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()

    sock, reader = connect(args.host, args.port, args.connect_timeout)
    sock.settimeout(args.command_timeout)
    try:
        report = capture(
            lambda line: command(sock, reader, line),
            page_size=args.page_size,
            event_filter=args.event_filter,
        )
    finally:
        reader.close()
        sock.close()

    print(
        "audio events: "
        f"head={report['event_head']} "
        f"oldest={report['oldest_available']} "
        f"returned={report['events_returned']} "
        f"filter={report['event_filter']}"
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
