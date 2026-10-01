#!/usr/bin/env python3
"""ROM-free tests for the UR-Recomp -> Mesen fixture adapter."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile

from tools.controller_input import ControllerRun, load_controller_runs

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
    # The promoted ordinary-2P corpus must remain consumable by the same Mesen
    # adapter: named checkpoints come from the script, controller ownership from
    # the neutral stream.
    two_player_script = ROOT / "tests" / "input" / "two-player-first-race-observe.script"
    two_player_input = ROOT / "tests" / "input" / "two-player-first-race.input"
    two_player_commands = mod.parse_fixture(two_player_script)
    two_player_dumps = [cmd["tag"] for cmd in two_player_commands if cmd["op"] == "dump"]
    assert "two-player-race-1220" in two_player_dumps
    assert "two-player-p1-post-1520" in two_player_dumps
    assert "two-player-p2-post-1570" in two_player_dumps
    assert "two-player-both-post-1620" in two_player_dumps

    two_player_runs = load_controller_runs(two_player_input)
    assert any(run.p2_mask and not run.p1_mask for run in two_player_runs)
    assert any(run.p1_mask and run.p2_mask for run in two_player_runs)

    assert len(commands) >= 20, len(commands)
    assert commands[0]["op"] == "until"
    assert commands[0]["address"] == 0x009F
    assert commands[0]["operator"] == "=="
    assert commands[0]["value"] == 0xD7
    assert commands[-1]["op"] == "quit"
    dumps = [cmd["tag"] for cmd in commands if cmd["op"] == "dump"]
    for required in [
        "main-menu-ready", "rider-select-ready", "tours-ready", "tracks-ready",
        "after-track-confirm", "now-playing-ready", "race-entered",
    ]:
        assert required in dumps, (required, dumps)

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

        # Neutral input-file mode must apply both controller masks before each
        # guest frame while preserving named dump timing.
        fake = FakeMesen()
        runner = mod.FixtureRunner(
            fake,
            Path(td) / "stream-dumps",
            controller_runs=[
                ControllerRun(0, 2, 0x080, 0),
                ControllerRun(1, 2, 0, 0x040),
            ],
        )
        runner.execute([
            {"op": "wait", "frames": 3, "line": 1},
            {"op": "dump", "tag": "stream-checkpoint", "line": 2},
            {"op": "quit", "line": 3},
        ])
        input_calls = [call for call in fake.calls if call[0] == "input.set"]
        assert input_calls[0] == (
            "input.set",
            {"port": 0, "subport": 0, "buttons": {"right": True}},
        )
        assert input_calls[1] == (
            "input.set",
            {"port": 1, "subport": 0, "buttons": {}},
        )
        assert (
            "input.set",
            {"port": 1, "subport": 0, "buttons": {"left": True}},
        ) in input_calls
        assert fake.frame == 3
        assert (Path(td) / "stream-dumps" / "stream-checkpoint.wram.bin").stat().st_size == 0x20000

        fake = FakeMesen()
        runner = mod.FixtureRunner(
            fake,
            Path(td) / "mixed-dumps",
            controller_runs=[ControllerRun(0, 1, 0x080, 0)],
        )
        try:
            runner.execute([{"op": "press", "button": "a", "frames": 1, "line": 1}])
        except RuntimeError as exc:
            assert "cannot be mixed" in str(exc)
        else:
            raise AssertionError("inline press accepted alongside neutral input stream")

    print("PASS: Mesen fixture parser and frame/input/dump semantics")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
