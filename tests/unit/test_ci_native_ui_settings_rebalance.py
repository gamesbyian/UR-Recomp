"""Keep Modern settings persistence acceptance independent when rebalancing CI."""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/native-ui-evidence.yml"


class ModernSettingsShardBalanceTest(unittest.TestCase):
    def test_host_settings_test_is_only_on_records_after_proven_capture(self):
        workflow = WORKFLOW.read_text()
        start = "      - name: Modern settings persistence acceptance"
        end = "      - name: Internal Render Scale compositor acceptance"
        self.assertEqual(workflow.count(start), 1)
        section = workflow.split(start, 1)[1].split(end, 1)[0]
        self.assertIn("if: matrix.shard == 'records'", section)
        for expected in (
            'STATE="$RUNNER_TEMP/host-state-v6.txt"',
            'SAVE_LOG="$RUNNER_TEMP/host-state-save.log"',
            'DUMPS="$RUNNER_TEMP/host-state-dumps"',
            'UR_HOST_STATE_PATH="$STATE"',
            "UR-HOST-STATE/6",
        ):
            self.assertIn(expected, section)
        self.assertIn('host-state-v6.txt', workflow.split("      - name: Upload shard evidence", 1)[1])

    def test_render_scale_pair_still_shares_state_in_core(self):
        workflow = WORKFLOW.read_text()
        for name in (
            "Internal Render Scale compositor acceptance",
            "Internal Render Scale fallback-frame acceptance",
        ):
            part = workflow.split(f"      - name: {name}", 1)[1].split("      - name:", 1)[0]
            self.assertIn("if: matrix.shard == 'core'", part)
            self.assertIn('STATE="$RUNNER_TEMP/render-scale-2x.state"', part)
        self.assertIn("run_route race-smoke reach-first-race.script", workflow)
        self.assertIn("run_route ui-circuit-drive-capture ui-circuit-drive-capture.script", workflow)
        self.assertIn("  aggregate:", workflow)


if __name__ == "__main__":
    unittest.main()
