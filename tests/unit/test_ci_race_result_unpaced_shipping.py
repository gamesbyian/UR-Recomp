"""Required Race-result evidence stays complete under isolated unpaced execution."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]

class RaceResultShippingTest(unittest.TestCase):
    def test_clones_exact_proven_state_and_requires_native_root(self):
        workflow = (ROOT / ".github/workflows/native-ui-evidence.yml").read_text()
        nav = workflow.split("            navigation)",1)[1].split("            results-a)",1)[0]
        for item in (
            "for state in config.ini keybinds.ini saves/save.srm; do",
            'test -f "$src"',
            'cp "$src" "$SNESRECOMP_USER_DATA_DIR/$state"',
            "DisableFrameDelay = 1",
            "run_route ui-race-result-route ui-race-result-route.script ui-race-result-dumps 180 required",
            'grep -Fq "config dir anchored: $SNESRECOMP_USER_DATA_DIR"',
            "UR_RACE_RESULT_CLONED_UNPACED_ROOT PASS",
        ):
            self.assertIn(item, nav)
        self.assertEqual(workflow.count("run_route ui-race-result-route "),1)
        self.assertIn('--dump-dir "$RUNNER_TEMP/ui-race-result-dumps"',workflow.split("  aggregate:",1)[1])
        self.assertIn("UR_RENAME_ISOLATED_CONFIG_ROOT PASS",workflow)
        self.assertIn("UR_RECORDS_ISOLATED_CONFIG_ROOT PASS",workflow)
        self.assertIn("UR_CIRCUIT_ISOLATED_CONFIG_ROOT PASS",workflow)

    def test_unchanged_race_capture_has_all_eighteen_checkpoints(self):
        script=(ROOT / "tests/input/ui-race-result-route.script").read_text()
        self.assertEqual(sum(line.startswith("dump ") for line in script.splitlines()),18)
