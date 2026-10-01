#!/usr/bin/env python3
"""Step a paused SNESRecomp trace host to a bounded frame and report selected WRAM writes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from trace_native_wram_writers import command, connect


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=4377)
    ap.add_argument("--connect-timeout", type=float, default=20.0)
    ap.add_argument("--command-timeout", type=float, default=45.0)
    ap.add_argument("--stop-frame", type=int, required=True)
    ap.add_argument("--coarse-step", type=int, default=25)
    ap.add_argument("--window-start", type=int, default=0)
    ap.add_argument("--address", action="append", required=True, type=lambda x: int(x, 0))
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()

    if args.stop_frame < 0 or args.window_start < 0 or args.window_start > args.stop_frame:
        raise SystemExit("invalid frame window")
    if args.coarse_step <= 0:
        raise SystemExit("--coarse-step must be positive")

    sock, reader = connect(args.host, args.port, args.connect_timeout)
    sock.settimeout(args.command_timeout)
    try:
        stepped = 0
        while stepped < args.stop_frame:
            batch = min(args.coarse_step, args.stop_frame - stepped)
            result = command(sock, reader, f"step {batch}")
            if result.get("timeout"):
                raise RuntimeError(f"trace server timed out while stepping {batch} frames: {result}")
            stepped += batch

        cpu_state = command(sock, reader, "get_cpu_state")
        report = {
            "stop_frame": stepped,
            "window_start": args.window_start,
            "cpu_state": cpu_state,
            "addresses": {},
        }
        print(
            f"stepped={stepped} PC={cpu_state.get('k')}:{cpu_state.get('pc')} "
            f"func={cpu_state.get('func')}"
        )

        for addr in args.address:
            result = command(sock, reader, f"wram_writes_at {addr:x} 0 {stepped + 1} 4096")
            if result.get("error") or result.get("ok") is False:
                raise RuntimeError(f"wram_writes_at unavailable for 0x{addr:04X}: {result}")
            writes = result.get("matches", [])
            window = [w for w in writes if int(w.get("f", -1)) >= args.window_start]
            current = command(sock, reader, f"dump_ram 0x{addr:x} 2")
            report["addresses"][f"0x{addr:04X}"] = {
                "current": current.get("hex", "").replace(" ", ""),
                "total_write_count": len(writes),
                "window_writes": window,
                "last_write_before_window": next(
                    (w for w in reversed(writes) if int(w.get("f", -1)) < args.window_start),
                    None,
                ),
            }
            print(
                f"0x{addr:04X}: current={current.get('hex','').strip()} "
                f"total={len(writes)} window={len(window)}"
            )
            for w in window:
                print(
                    "  "
                    f"f={w.get('f')} val={w.get('val')} old={w.get('old', w.get('before'))} "
                    f"scope={w.get('func')} parent={w.get('parent')}"
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
