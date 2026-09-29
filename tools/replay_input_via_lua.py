#!/usr/bin/env python3
"""Replay deterministic P1/P2 controller input through SNESRecomp's Lua bridge."""

from __future__ import annotations

import argparse
import json
import socket
import time
from pathlib import Path

from controller_input import ControllerRun, load_controller_runs
from uniracers_state import PLAYER1_FIELDS

BUTTONS = [
    ("B", 0x001), ("Y", 0x002), ("Select", 0x004), ("Start", 0x008),
    ("Up", 0x010), ("Down", 0x020), ("Left", 0x040), ("Right", 0x080),
    ("A", 0x100), ("X", 0x200), ("L", 0x400), ("R", 0x800),
]


def load_runs(path: Path) -> list[ControllerRun]:
    try:
        return load_controller_runs(path)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc


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


def build_lua(runs: list[ControllerRun], frames: int, checkpoints: list[int]) -> str:
    run_rows = ",".join(
        f"{{{run.start},{run.duration},{run.p1_mask},{run.p2_mask}}}" for run in runs
    )
    cp_rows = ",".join(str(x) for x in sorted(set(checkpoints)))
    addr = {name: field.addr for name, field in PLAYER1_FIELDS.items()}
    return f"""
local runs={{{run_rows}}}
local cps={{{cp_rows}}}
local cp={{}}
for _,v in ipairs(cps) do cp[v]=true end
local function masks_at(f)
  local p1=0
  local p2=0
  for _,r in ipairs(runs) do
    if f >= r[1] and f < r[1]+r[2] then
      p1 = p1 | r[3]
      p2 = p2 | r[4]
    end
  end
  return p1,p2
end
local function put(m,controller)
  joypad.set({{
    B=(m & 0x001) ~= 0, Y=(m & 0x002) ~= 0,
    Select=(m & 0x004) ~= 0, Start=(m & 0x008) ~= 0,
    Up=(m & 0x010) ~= 0, Down=(m & 0x020) ~= 0,
    Left=(m & 0x040) ~= 0, Right=(m & 0x080) ~= 0,
    A=(m & 0x100) ~= 0, X=(m & 0x200) ~= 0,
    L=(m & 0x400) ~= 0, R=(m & 0x800) ~= 0
  }},controller)
end
local function s16(a)
  local v=mainmemory.read_u16_le(a)
  if v >= 0x8000 then return v-0x10000 end
  return v
end
local function snap(f)
  print(string.format(
    "SNAP %d menu=%02X inRace=%02X track=%d x=%d y=%d vx=%d vy=%d air=%d pitch=%d",
    f, mainmemory.read_u8(0x009F), mainmemory.read_u8(0x{addr["in_race"]:04X}),
    mainmemory.read_u8(0x{addr["track"]:04X}), mainmemory.read_u16_le(0x{addr["x_pos"]:04X}),
    mainmemory.read_u16_le(0x{addr["y_pos"]:04X}), s16(0x{addr["x_speed"]:04X}), s16(0x{addr["y_speed"]:04X}),
    mainmemory.read_u8(0x{addr["air"]:04X}), mainmemory.read_u8(0x{addr["pitch"]:04X}) & 0x3F))
end
for f=0,{frames-1} do
  if cp[f] then snap(f) end
  local p1,p2=masks_at(f)
  put(p1,1)
  put(p2,2)
  emu.frameadvance()
end
put(0,1)
put(0,2)
snap({frames})
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "input_file",
        type=Path,
        help="start:duration:p1-mask[:p2-mask] deterministic input stream",
    )
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
            text_output = status.get("output", "")
            if text_output:
                output.extend(x for x in text_output.splitlines() if x)
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
            "players": 2 if any(run.p2_mask for run in runs) else 1,
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
