"""ROM-free exact-frame comparison for batched headless Mesen input replay."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from controller_input import ControllerRun, masks_at
from run_fixture_mesen import FixtureRunner, MASK_BUTTONS


BUTTON_BITS = dict(MASK_BUTTONS)


class FakeMesen:
    def __init__(self):
        self.controllers = [{}, {}]
        self.frames = []
        self.calls = []

    def tool(self, name, **args):
        if name == "input.set":
            self.controllers[args["port"]] = args["buttons"]
            return {}
        if name == "run.step_frames":
            count = args["frames"]
            self.calls.append(count)
            for _ in range(count):
                self.frames.append(tuple(
                    sum(BUTTON_BITS[b] for b, pressed in seat.items() if pressed)
                    for seat in self.controllers
                ))
            return {"status": {"frame": len(self.frames)}}
        if name == "cpu.read_memory":
            return {"bytes": [int(len(self.frames) >= 5)]}
        raise AssertionError(name)


class MesenBatchTests(unittest.TestCase):
    def test_long_stable_input_uses_only_two_step_rpc_calls(self):
        client = FakeMesen()
        runner = FixtureRunner(client, Path("."), [ControllerRun(10, 90, 0x001)])
        runner.step(100)
        self.assertEqual(client.calls, [10, 90])
        self.assertEqual(len(client.frames), 100)
        self.assertEqual(client.frames[:10], [(0, 0)] * 10)
        self.assertEqual(client.frames[10:], [(1, 0)] * 90)

    def test_mixed_seats_and_idle_gaps_are_frame_exact(self):
        runs = [
            ControllerRun(0, 7, 0x001),
            ControllerRun(4, 5, 0, 0x002),
            ControllerRun(12, 3, 0x004, 0x008),
        ]
        client = FakeMesen()
        runner = FixtureRunner(client, Path("."), runs)
        runner.step(5)
        runner.step(15)
        self.assertEqual(client.frames, [masks_at(runs, frame) for frame in range(20)])
        self.assertEqual(runner.frame, 20)
        self.assertLess(len(client.calls), 20)

    def test_conditional_until_remains_frame_by_frame(self):
        client = FakeMesen()
        runner = FixtureRunner(client, Path("."), [ControllerRun(0, 20, 0x001)])
        runner.execute([
            {"op": "until", "address": 0x55, "operator": "==", "value": 1,
             "timeout": 10},
            {"op": "quit"},
        ])
        self.assertEqual(len(client.frames), 5)
        self.assertEqual(client.calls, [1] * 5)

    def test_no_input_file_keeps_original_single_bulk_call(self):
        client = FakeMesen()
        runner = FixtureRunner(client, Path("."))
        runner.step(20)
        self.assertEqual(client.calls, [20])

    def test_declared_frame_progress_must_be_observed(self):
        class Stalled(FakeMesen):
            def tool(self, name, **args):
                if name == "run.step_frames":
                    return {"status": {"frame": 0}}
                return super().tool(name, **args)
        runner = FixtureRunner(Stalled(), Path("."), [ControllerRun(0, 20, 1)])
        with self.assertRaisesRegex(RuntimeError, "did not advance"):
            runner.step(20)


if __name__ == "__main__":
    unittest.main()
