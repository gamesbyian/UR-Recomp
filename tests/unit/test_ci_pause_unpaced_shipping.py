"""Pause route acceleration preserves authoritative capture and root evidence."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[2]
class PauseShippingTest(unittest.TestCase):
    def test_required_capture_and_cloned_state(self):
        w=(ROOT/".github/workflows/native-ui-evidence.yml").read_text()
        nav=w.split("            navigation)",1)[1].split("            results-a)",1)[0]
        for x in ("for state in config.ini keybinds.ini saves/save.srm; do",
                  "run_route ui-pause-route ui-pause-route.script ui-pause-dumps 90 required",
                  'grep -Fq "config dir anchored: $SNESRECOMP_USER_DATA_DIR"',
                  "UR_PAUSE_CLONED_UNPACED_ROOT PASS"):
            self.assertIn(x,nav)
        self.assertEqual(w.count("run_route ui-pause-route "),1)
        self.assertIn('--dump-dir "$RUNNER_TEMP/ui-pause-dumps"',w.split("  aggregate:",1)[1])
        self.assertEqual(sum(x.startswith("dump ") for x in (ROOT/"tests/input/ui-pause-route.script").read_text().splitlines()),3)
