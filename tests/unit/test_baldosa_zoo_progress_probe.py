"""Zoo progress probe preserves all original inputs and never claims a result."""
import importlib.util
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "zoo_probe", ROOT / "tools/baldosa_zoo_progress_probe.py")
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)
class ZooProgressProbeTest(unittest.TestCase):
    def test_preserve_driving_and_remove_only_final_wait(self):
        source = ("turbo on\nuntil16 0053 == F60C\nuntil 0E1F != 00\n"
                  "press left 6000\nuntil16 0053 == F60C\nwait 300\n"
                  "dump end\nquit\n")
        result = mod.progress_route(source)
        self.assertIn("until16 0053 == F60C\n", result)
        self.assertIn("press left 6000\n", result)
        self.assertIn("dump go\n", result)
        self.assertTrue(result.endswith("press left 6000\ndump after_drive\nquit\n"))
        self.assertNotIn("dump end", result)
        with self.assertRaises(ValueError):
            mod.progress_route("unrelated route\n")
if __name__ == "__main__":
    unittest.main()
