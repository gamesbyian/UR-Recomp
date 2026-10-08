"""The six Native UI shards must retain capture ownership after rebalancing."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/native-ui-evidence.yml"
PATHS = ROOT / ".github/ci/modern-native-ui-paths.txt"


class NativeUiPostPruneBalanceTest(unittest.TestCase):
    def test_each_independent_capture_has_one_owner(self):
        workflow = WORKFLOW.read_text()
        self.assertIn(
            "shard: [core, navigation, results-a, results-b, records, profiles]",
            workflow,
        )
        for route, target in (("ui-main-branches", "records"),
                              ("ui-league-table", "results-b")):
            run = f"run_route {route} {route}.script"
            self.assertEqual(workflow.count(run), 1)
            block = workflow.split(f"            {target})", 1)[1].split("              ;;", 1)[0]
            self.assertIn(run, block)
            self.assertIn(f"tests/input/{route}.script", PATHS.read_text().splitlines())

    def test_original_dump_roots_and_aggregate_contract_survive(self):
        workflow = WORKFLOW.read_text()
        self.assertIn(
            "run_route ui-main-branches ui-main-branches.script ui-branch-dumps 150",
            workflow,
        )
        self.assertIn(
            "run_route ui-league-table ui-league-table.script ui-league-dumps 90",
            workflow,
        )
        self.assertIn('ui-branch-dumps', workflow.split("      - name: Build UI atlas report", 1)[1])
        self.assertIn('ui-league-dumps', workflow.split("      - name: Build UI atlas report", 1)[1])
        self.assertIn(
            "ui-main-branches:ui-branch-dumps",
            workflow.split("      - name: Assert reset-separated routes captured every dump", 1)[1],
        )
        profiles = workflow.split("            profiles)", 1)[1].split("            *)", 1)[0]
        nav = workflow.split("            navigation)", 1)[1].split("            results-a)", 1)[0]
        self.assertNotIn("run_route ui-main-branches ", profiles)
        self.assertNotIn("run_route ui-league-table ", nav)


if __name__ == "__main__":
    unittest.main()
