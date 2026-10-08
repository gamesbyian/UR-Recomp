"""Post-balance Native UI routing must preserve every capture and gate."""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/native-ui-evidence.yml"


class NativeUiCriticalPathSwapTest(unittest.TestCase):
    def test_unique_independent_route_owners(self):
        workflow = WORKFLOW.read_text()
        nav = workflow.split("            navigation)", 1)[1].split("            results-a)", 1)[0]
        results = workflow.split("            results-a)", 1)[1].split("            results-b)", 1)[0]
        self.assertEqual(workflow.count("run_route ui-race-result-route "), 1)
        self.assertEqual(workflow.count("run_route ui-options-submenus "), 1)
        self.assertIn(
            "run_route ui-race-result-route ui-race-result-route.script ui-race-result-dumps 180", nav,
        )
        self.assertIn(
            "run_route ui-options-submenus ui-options-submenus.script ui-options-submenu-dumps 180", results,
        )
        self.assertIn(
            "run_route ui-circuit-drive-capture ui-circuit-drive-capture.script "
            "ui-circuit-result-dumps 120 required || exit $?", results,
        )

    def test_unchanged_aggregate_looks_up_same_dirs(self):
        workflow = WORKFLOW.read_text()
        aggregate = workflow.split("  aggregate:", 1)[1]
        self.assertIn("ui-options-submenus:ui-options-submenu-dumps", aggregate)
        self.assertIn('check_result_screen_time.py', aggregate)
        self.assertIn('--dump-dir "$RUNNER_TEMP/ui-race-result-dumps"', aggregate)
        self.assertIn('--dump-dir "$RUNNER_TEMP/ui-options-submenu-dumps"', aggregate)
        self.assertIn("ui-main-branches:ui-branch-dumps", aggregate)
        self.assertIn(
            "shard: [core, navigation, results-a, results-b, records, profiles]",
            workflow,
        )


if __name__ == "__main__":
    unittest.main()
