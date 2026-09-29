#!/usr/bin/env python3
"""Query SNESRecomp's trace debug server for writers to selected WRAM bytes."""

from __future__ import annotations

import argparse
import json
import socket
import time
from pathlib import Path

DEFAULT_ADDRS = (0x00C6, 0x00C8, 0x00C9, 0x01D1, 0x01D2, 0x01D3, 0x01D4)


def command(sock: socket.socket, reader, line: str) -> dict:
    sock.sendall((line + "\n").encode("ascii"))
    raw = reader.readline()
    if not raw:
        raise RuntimeError(f"debug server disconnected after command: {line}")
    return json.loads(raw)


def connect(host: str, port: int, timeout: float) -> tuple[socket.socket, object]:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        s = socket.socket()
        s.settimeout(2.0)
        try:
            s.connect((host, port))
            # The SNESRecomp debug server is command/response only: it does
            # not emit a greeting banner on connect. Waiting for one caused
            # each probe to time out, reconnect, and make the server drop the
            # previous client before any command could be sent.
            reader = s.makefile("r", encoding="utf-8", newline="\n")
            return s, reader
        except OSError as exc:
            last_error = exc
            s.close()
            time.sleep(0.1)
    raise RuntimeError(f"could not connect to {host}:{port}: {last_error}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=4377)
    ap.add_argument("--connect-timeout", type=float, default=20.0)
    ap.add_argument("--command-timeout", type=float, default=30.0)
    ap.add_argument("--max-frames", type=int, default=1400)
    ap.add_argument(
        "--coarse-until",
        type=int,
        default=900,
        help="step in batches until this many frames have been requested, then probe every frame",
    )
    ap.add_argument("--coarse-step", type=int, default=100)
    ap.add_argument("--address", action="append", type=lambda x: int(x, 0))
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()

    addrs = tuple(args.address) if args.address else DEFAULT_ADDRS
    sock, reader = connect(args.host, args.port, args.connect_timeout)
    sock.settimeout(args.command_timeout)
    try:
        reached = None
        stepped = 0

        # The shared route reaches race entry near native frame 984. Trace
        # builds are intentionally heavy, so avoid two TCP round trips for
        # every early frame. Batched step commands still execute every guest
        # frame and therefore preserve the frame-keyed input script.
        coarse_target = min(args.coarse_until, args.max_frames)
        while stepped < coarse_target:
            batch = min(args.coarse_step, coarse_target - stepped)
            result = command(sock, reader, f"step {batch}")
            if result.get("timeout"):
                raise RuntimeError(f"trace server timed out while stepping {batch} frames: {result}")
            stepped += batch

        state = command(sock, reader, "dump_ram 0x313 1")
        if int(state["hex"].replace(" ", ""), 16) == 1:
            reached = stepped

        while reached is None and stepped < args.max_frames:
            command(sock, reader, "step 1")
            stepped += 1
            state = command(sock, reader, "dump_ram 0x313 1")
            value = int(state["hex"].replace(" ", ""), 16)
            if value == 1:
                reached = stepped
                break

        if reached is None:
            raise RuntimeError(f"inRace did not become 1 within {args.max_frames} stepped frames")

        cpu_state = command(sock, reader, "get_cpu_state")
        report = {
            "in_race_step": reached,
            "cpu_state_at_in_race": cpu_state,
            "addresses": {},
        }
        print(f"inRace=1 after {reached} stepped frames")
        print(
            "cpu-at-inRace: "
            f"SP={cpu_state.get('sp')} PC={cpu_state.get('k')}:{cpu_state.get('pc')} "
            f"DP={cpu_state.get('dp')} DB={cpu_state.get('db')} "
            f"func={cpu_state.get('func')}"
        )

        for addr in addrs:
            result = command(sock, reader, f"wram_writes_at {addr:x} 0 999999 4096")
            if result.get("error") or result.get("ok") is False:
                raise RuntimeError(f"wram_writes_at unavailable for 0x{addr:04X}: {result}")
            writes = result.get("matches", [])
            current = command(sock, reader, f"dump_ram 0x{addr:x} 1")
            report["addresses"][f"0x{addr:04X}"] = {
                "current": current.get("hex", "").replace(" ", ""),
                "writes": writes,
            }
            print(f"0x{addr:04X}: current={current.get('hex','').strip()} writes={len(writes)}")
            for w in writes[-12:]:
                print(
                    "  "
                    f"f={w.get('f')} val={w.get('val')} "
                    f"old={w.get('old', w.get('before'))} "
                    f"func={w.get('func')} parent={w.get('parent')}"
                )

        if args.json_out:
            args.json_out.parent.mkdir(parents=True, exist_ok=True)
            args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return 0
    finally:
        try:
            reader.close()
        finally:
            sock.close()


if __name__ == "__main__":
    raise SystemExit(main())
