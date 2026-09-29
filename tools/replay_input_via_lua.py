#!/usr/bin/env python3
"""Replay a snesref-style frame-mask input file through SNESRecomp's Lua TCP bridge.

The input format is start-frame:duration:hex-mask. All 12 controller buttons are
explicitly set true/false every simulated frame so transitions are exact.
"""

from __future__ import annotations

import argparse
import json
import socket
import time
from pathlib import Path

BUTTONS = [
    ("B", 0x001), ("Y", 0x002), ("Select", 0x004), ("Start", 0x008),
    ("Up", 0x010), ("Down", 0x020), ("Left", 0x040), ("Right", 0x080),
    ("A", 0x100), ("X", 0x200), ("L", 0x400), ("R", 0x800),
]


def load_runs(path: Path) -> list[tuple[int, int, int]]:
    out = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.split(":")
        if len(parts) != 3:
            raise SystemExit(f"bad input line: {raw}")
        start, duration, mask = int(parts[0]), int(parts[1]), int(parts[2], 16)
        if start < 0 or duration < 1 or mask & ~0xFFF:
            raise SystemExit(f"bad input interval: {raw}")
        out.append((start, duration, mask))
    out.sort()
    prev_end = 0
    for start, duration, _ in out:
        if start < prev_end:
            raise SystemExit("overlapping input intervals are not supported")
        prev_end = start + duration
    return out


def connect(host: str, port: int, timeout: float):
    deadline = time.monotonic() + timeout
    last = None
    while time.monotonic() < deadline:
        s = socket.socket()
        s.settimeout(2.0)
        try:
            s.connect((host, port))
            return s, s.makefile("r", encoding="utf-8", newline="\n")
        except OSError as exc:
            last = exc
            s.close()
            time.sleep(0.1)
    raise RuntimeError(f"could not connect to Lua bridge: {last}")


def command(sock, reader, line: str) -> dict:
    sock.sendall((line + "\n").encode("ascii"))
    raw = reader.readline()
    if not raw:
        raise RuntimeError(f"Lua bridge disconnected after {line.split(' ',1)[0]}")
    return json.loads(raw)


def build_lua(runs: list[tuple[int,int,int]], frames: int, checkpoints: list[int]) -> str:
    run_rows = ",".join(f"{{{s},{d},{m}}}" for s,d,m in runs)
    cp_rows = ",".join(str(x) for x in sorted(set(checkpoints)))
    fields = ",".join(
        f'{name}={( "true" if bit else "false" )}' for name, bit in []
    )
    # Read compact semantic state directly in the running bridge. print() output
    # is collected by the TCP response stream and consumed by the Python client.
    return f"""
local runs={{{run_rows}}}
local cps={{{cp_rows}}}
local cp={{}}
for _,v in ipairs(cps) do cp[v]=true end
local ri=1
local function mask_at(f)
  while ri <= #runs and f >= runs[ri][1] + runs[ri][2] do ri=ri+1 end
  if ri <= #runs and f >= runs[ri][1] and f < runs[ri][1]+runs[ri][2] then
    return runs[ri][3]
  end
  return 0
end
local function put(m)
  joypad.set({{
    B=(m & 0x001) ~= 0, Y=(m & 0x002) ~= 0,
    Select=(m & 0x004) ~= 0, Start=(m & 0x008) ~= 0,
    Up=(m & 0x010) ~= 0, Down=(m & 0x020) ~= 0,
    Left=(m & 0x040) ~= 0, Right=(m & 0x080) ~= 0,
    A=(m & 0x100) ~= 0, X=(m & 0x200) ~= 0,
    L=(m & 0x400) ~= 0, R=(m & 0x800) ~= 0
  }},1)
end
local function s16(a)
  local v=mainmemory.read_u16_le(a)
  if v >= 0x8000 then return v-0x10000 end
  return v
end
local function snap(f)
  print(string.format(
    "SNAP %d menu=%02X inRace=%02X track=%d x=%d y=%d vx=%d vy=%d air=%d pitch=%d",
    f, mainmemory.read_u8(0x009F), mainmemory.read_u8(0x0313),
    mainmemory.read_u8(0x00CE), mainmemory.read_u16_le(0x0411),
    mainmemory.read_u16_le(0x0415), s16(0x04B7), s16(0x04BB),
    mainmemory.read_u8(0x0545), mainmemory.read_u16_le(0x04C7) & 0x3F))
end
for f=0,{frames-1} do
  if cp[f] then snap(f) end
  put(mask_at(f))
  emu.frameadvance()
end
snap({frames})
"""

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input_file", type=Path)
    ap.add_argument("--frames", type=int, required=True)
    ap.add_argument("--checkpoint", action="append", type=int, default=[])
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=4380)
    ap.add_argument("--connect-timeout", type=float, default=30.0)
    ap.add_argument("--run-timeout", type=float, default=180.0)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()

    runs = load_runs(args.input_file)
    lua = build_lua(runs, args.frames, args.checkpoint)
    sock, reader = connect(args.host, args.port, args.connect_timeout)
    sock.settimeout(5.0)
    output = []
    try:
        response = command(sock, reader, "run " + lua.encode("utf-8").hex())
        if not response.get("ok"):
            raise RuntimeError(response)
        deadline = time.monotonic() + args.run_timeout
        final = None
        while time.monotonic() < deadline:
            time.sleep(0.05)
            status = command(sock, reader, "status")
            text = status.get("output", "")
            if text:
                output.extend(x for x in text.splitlines() if x)
            if status.get("error"):
                raise RuntimeError(status["error"])
            if not status.get("running", False):
                final = status
                break
        if final is None:
            raise RuntimeError("Lua replay did not finish before timeout")
        record = {
            "frames": args.frames,
            "runs": len(runs),
            "checkpoints": sorted(set(args.checkpoint)),
            "snapshots": [x for x in output if x.startswith("SNAP ")],
            "status": final,
        }
        print("\n".join(record["snapshots"]))
        if args.json_out:
            args.json_out.parent.mkdir(parents=True, exist_ok=True)
            args.json_out.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        return 0
    finally:
        reader.close()
        sock.close()


if __name__ == "__main__":
    raise SystemExit(main())
