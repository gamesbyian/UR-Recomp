"""Zoo progression probe leaves the upstream controller blocks intact."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "zoo_probe", ROOT / "tools/baldosa_zoo_progress_probe.py")
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class ZooProgressProbeTest(unittest.TestCase):
    SOURCE = (
        "turbo on\nuntil16 0053 == F60C\nuntil 0E1F != 00\n"
        "press left 300\npress left+up 20\npress left+x 20\n"
        "press left 6000\nuntil16 0053 == F60C\nwait 300\n"
        "dump end\nquit\n"
    )

    def test_preserves_every_input_block_and_removes_only_final_wait(self):
        result = mod.progress_route(self.SOURCE)
        self.assertIn("until16 0053 == F60C\n", result)
        self.assertIn("press left 6000\n", result)
        self.assertEqual(result.count("dump go"), 1)
        self.assertEqual(result.count("dump after_first_left"), 1)
        self.assertEqual(result.count("dump before_long_left"), 1)
        self.assertEqual(result.count("dump after_drive"), 1)
        self.assertTrue(result.endswith("press left 6000\ndump after_drive\nquit\n"))
        # All pressed buttons, their original order and frame counts survive.
        def presses(text):
            return [line for line in text.splitlines()
                    if line.startswith("press ")]
        self.assertEqual(presses(result), presses(self.SOURCE))
        self.assertEqual(
            result.split("dump after_drive")[0].count("wait "), 0
        )
        self.assertNotIn("dump end", result)
        self.assertNotIn("until16 0053 == F60C\nwait 300\ndump end", result)

    def test_rejects_unrecognized_or_changed_upstream_route(self):
        with self.assertRaises(ValueError):
            mod.progress_route("unrelated route\n")
        with self.assertRaises(ValueError):
            mod.progress_route(self.SOURCE.replace("press left+x 20\n", ""))
        with self.assertRaises(ValueError):
            mod.progress_route(self.SOURCE.replace("press left 300\n", ""))


if __name__ == "__main__":
    unittest.main()
