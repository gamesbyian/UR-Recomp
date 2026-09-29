#!/usr/bin/env python3
"""ROM-free tests for the UR-Recomp -> Mesen fixture adapter."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "run_fixture_mesen.py"
FIXTURE = ROOT / "tests" / "input" / "reach-first-race.script"

spec = importlib.util.spec_from_file_location("run_fixture_mesen", TOOL)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


class FakeMesen:
    def __init__(self):
        self.frame = 0
        self.memory = bytearray(0x20000)
        self.calls = []

    def tool(self, name, **kwargs):
        self.calls.append((name, kwargs))
        if name == "run.step_frames":
            self.frame += kwargs["frames"]
            return {"status": {"frame": self.frame}}
        if name == "input.set":
            return {"buttons": kwargs["buttons"]}
        if name == "cpu.read_memory":
            address = kwargs["address"]
            length = kwargs["length"]
            return {"bytes": list(self.memory[address:address + length])}
        raise AssertionError(name)


def main() -> int:
    commands = mod.parse_fixture(FIXTURE)
    assert len(commands) == 20, len(commands)
    assert commands[0] == {
        "op": "until", "address": 0x009F, "operator": "==",
        "value": 0xD7, "timeout": 3600, "line": 9
    }
    assert commands[-1]["op"] == "quit"

    with tempfile.TemporaryDirectory() as td:
        bad = Path(td) / "bad.script"
        bad.write_text("poke 009F D7\n", encoding="utf-8")
        try:
            mod.parse_fixture(bad)
        except ValueError as exc:
            assert "unsupported fixture command" in str(exc)
        else:
            raise AssertionError("unsupported fixture command was accepted")

        fake = FakeMesen()
        runner = mod.FixtureRunner(fake, Path(td) / "dumps")
        runner.execute([
            {"op": "press", "button": "a", "frames": 2, "line": 1},
            {"op": "dump", "tag": "checkpoint", "line": 2},
            {"op": "quit", "line": 3},
        ])
        assert fake.frame == 3, fake.frame
        assert fake.calls[0][0] == "input.set"
        assert fake.calls[1][0] == "run.step_frames"
        assert fake.calls[1][1]["reset"] is True
        assert fake.calls[2] == ("input.set", {"port": 0, "subport": 0, "buttons": {}})
        assert (Path(td) / "dumps" / "checkpoint.wram.bin").stat().st_size == 0x20000

    print("PASS: Mesen fixture parser and frame/input/dump semantics")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
