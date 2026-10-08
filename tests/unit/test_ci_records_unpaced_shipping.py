"""The accepted Records capture must use byte-proven isolated unpaced execution."""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/native-ui-evidence.yml"


class ShippingUnpacedRecordsAcceptanceTest(unittest.TestCase):
    def test_required_records_process_consumes_its_verified_root(self):
        workflow = WORKFLOW.read_text()
        records = workflow.split("            records)", 1)[1].split("            profiles)", 1)[0]
        self.assertEqual(workflow.count("run_route ui-records-explore "), 1)
        for invariant in (
            'export SNESRECOMP_USER_DATA_DIR="$RUNNER_TEMP/ui-records-unpaced-user-data"',
            'mkdir -p "$SNESRECOMP_USER_DATA_DIR" || exit $?',
            "printf '[General]\\nDisableFrameDelay = 1\\n'",
            "grep -Fqx 'DisableFrameDelay = 1'",
            'run_route ui-records-explore ui-records-explore.script ui-records-explore-dumps 180 required || exit $?',
            'grep -Fq "config dir anchored: $SNESRECOMP_USER_DATA_DIR"',
            '"$RUNNER_TEMP/ui-records-explore.log" || {',
            "UR_RECORDS_ISOLATED_CONFIG_ROOT PASS",
            "              ) || exit $?",
            "run_route ui-main-branches ui-main-branches.script ui-branch-dumps 150",
        ):
            self.assertIn(invariant, records)
        self.assertNotIn("ui-records-pacing-", records)
        self.assertNotIn("run_route ui-records-paced ", records)

    def test_all_existing_six_reset_dumps_remain_required_by_aggregate(self):
        script = (ROOT / "tests/input/ui-records-explore.script").read_text()
        self.assertEqual(sum(s.lstrip().startswith("dump ") for s in script.splitlines()), 12)
        self.assertEqual(sum(s.strip() == "reset" for s in script.splitlines()), 5)
        workflow = WORKFLOW.read_text()
        self.assertIn("ui-records-explore:ui-records-explore-dumps", workflow.split("  aggregate:", 1)[1])
        self.assertIn("UR_CIRCUIT_ISOLATED_CONFIG_ROOT PASS", workflow)
        self.assertIn("shard: [core, navigation, results-a, results-b, records, profiles]", workflow)

    def test_host_settings_retains_one_owner_and_original_authority(self):
        workflow = WORKFLOW.read_text()
        start = "      - name: Modern settings persistence acceptance"
        self.assertEqual(workflow.count(start), 1)
        section = workflow.split(start, 1)[1].split(
            "      - name: Internal Render Scale compositor acceptance", 1
        )[0]
        self.assertIn("if: matrix.shard == 'records'", section)
        self.assertIn('STATE="$RUNNER_TEMP/host-state-v6.txt"', section)
        self.assertIn('UR_HOST_STATE_PATH="$STATE"', section)
        self.assertIn("UR-HOST-STATE/6", section)


if __name__ == "__main__":
    unittest.main()
