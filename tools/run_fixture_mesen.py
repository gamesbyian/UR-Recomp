#!/usr/bin/env python3
"""Replay the project fixture grammar through mesen-for-ai.

Requires a bootstrapped mesen-for-ai checkout and MESEN_BIN pointing at a
compatible Mesen/MesenCE binary. The JSON-RPC protocol remains owned by the
pinned mesen-for-ai client; this file only adapts UR-Recomp fixture semantics.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MESEN_REPO = ROOT / ".tools" / "src" / "mesen-for-ai"
CLIENT = Path("skills/mesen-emulator/scripts/mesen_client.py")


def parse_fixture(path: Path) -> list[dict]:
    commands: list[dict] = []
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        op = parts[0].lower()
        try:
            if op == "wait" and len(parts) == 2:
                commands.append({"op": "wait", "frames": int(parts[1], 0), "line": lineno})
            elif op == "press" and len(parts) == 3:
                commands.append({"op": "press", "button": parts[1].lower(), "frames": int(parts[2], 0), "line": lineno})
            elif op == "dump" and len(parts) == 2:
                commands.append({"op": "dump", "tag": parts[1], "line": lineno})
            elif op == "quit" and len(parts) == 1:
                commands.append({"op": "quit", "line": lineno})
            elif op == "until" and len(parts) == 5 and parts[2] in {"==", "!="}:
                commands.append({
                    "op": "until",
                    "address": int(parts[1], 16),
                    "operator": parts[2],
                    "value": int(parts[3], 16),
                    "timeout": int(parts[4], 0),
                    "line": lineno,
                })
            else:
                raise ValueError("unsupported fixture command")
        except ValueError as exc:
            raise ValueError(f"{path}:{lineno}: {line!r}: {exc}") from exc
    if not commands:
        raise ValueError(f"{path}: fixture contains no commands")
    return commands


def load_mesen_class(repo: Path):
    client = repo / CLIENT
    if not client.is_file():
        raise FileNotFoundError(
            f"mesen-for-ai client not found at {client}; run bootstrap_toolchain.py --tool mesen-for-ai"
        )
    spec = importlib.util.spec_from_file_location("ur_mesen_client", client)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load mesen-for-ai client from {client}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Mesen


class FixtureRunner:
    def __init__(self, mesen, dump_dir: Path):
        self.mesen = mesen
        self.dump_dir = dump_dir
        self.frame = 0
        self.started = False

    def step(self, frames: int) -> None:
        if frames < 0:
            raise ValueError("negative frame count")
        if frames == 0:
            return
        result = self.mesen.tool("run.step_frames", frames=frames, reset=not self.started)
        self.started = True
        self.frame = int(result["status"]["frame"])

    def read_byte(self, address: int) -> int:
        result = self.mesen.tool(
            "cpu.read_memory", memoryType="snesWorkRam", address=address, length=1
        )
        return int(result["bytes"][0])

    def dump_wram(self, tag: str) -> Path:
        self.dump_dir.mkdir(parents=True, exist_ok=True)
        out = self.dump_dir / f"{tag}.wram.bin"
        data = bytearray()
        for address in range(0, 0x20000, 0x1000):
            result = self.mesen.tool(
                "cpu.read_memory", memoryType="snesWorkRam", address=address, length=0x1000
            )
            data.extend(result["bytes"])
        if len(data) != 0x20000:
            raise RuntimeError(f"expected 131072 WRAM bytes, got {len(data)}")
        out.write_bytes(data)
        print(f"dump {tag}: frame={self.frame} bytes={len(data)}")
        return out

    def execute(self, commands: list[dict]) -> None:
        for command in commands:
            op = command["op"]
            if op == "wait":
                self.step(command["frames"])
            elif op == "press":
                self.mesen.tool(
                    "input.set", port=0, subport=0, buttons={command["button"]: True}
                )
                self.step(command["frames"])
                self.mesen.tool("input.set", port=0, subport=0, buttons={})
                self.step(1)  # shared fixture grammar includes one trailing idle frame
            elif op == "until":
                waited = 0
                while True:
                    actual = self.read_byte(command["address"])
                    matches = actual == command["value"]
                    if command["operator"] == "!=":
                        matches = not matches
                    if matches:
                        print(
                            "until %04X %s %02X ok frame=%d waited=%d"
                            % (command["address"], command["operator"], command["value"], self.frame, waited)
                        )
                        break
                    if waited >= command["timeout"]:
                        raise RuntimeError(
                            "until %04X %s %02X timed out after %d frames (actual=%02X)"
                            % (command["address"], command["operator"], command["value"], waited, actual)
                        )
                    self.step(1)
                    waited += 1
            elif op == "dump":
                self.dump_wram(command["tag"])
            elif op == "quit":
                return
            else:
                raise AssertionError(op)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", nargs="?")
    ap.add_argument("--script", required=True)
    ap.add_argument("--dump-dir", default="analysis/mesen-fixture-dumps")
    ap.add_argument("--mesen-for-ai-repo", default=os.environ.get("MESEN_FOR_AI_REPO", str(DEFAULT_MESEN_REPO)))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    commands = parse_fixture(Path(args.script))
    if args.dry_run:
        print(json.dumps(commands, indent=2))
        return 0
    if not args.rom:
        ap.error("rom is required unless --dry-run is used")

    mesen_repo = Path(args.mesen_for_ai_repo).resolve()
    Mesen = load_mesen_class(mesen_repo)
    with Mesen(repo=str(mesen_repo)) as mesen:
        mesen.load_rom(str(Path(args.rom).resolve()), timeout=180)
        FixtureRunner(mesen, Path(args.dump_dir)).execute(commands)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
