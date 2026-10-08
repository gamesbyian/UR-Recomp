"""Keep byte-proven isolated Circuit acceleration inside required Native UI CI."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/native-ui-evidence.yml"


class IsolatedUnpacedCircuitAcceptanceTest(unittest.TestCase):
    def test_isolated_unpaced_capture_is_required_only_for_circuit(self):
        workflow = WORKFLOW.read_text()
        section = workflow.split("            results-a)", 1)[1].split("            results-b)", 1)[0]
        self.assertEqual(section.count("run_route ui-circuit-drive-capture "), 1)
        self.assertIn(
            'export SNESRECOMP_USER_DATA_DIR="$RUNNER_TEMP/ui-circuit-unpaced-user-data"',
            section,
        )
        self.assertIn('mkdir -p "$SNESRECOMP_USER_DATA_DIR" || exit $?', section)
        self.assertIn(
            "grep -Fqx 'DisableFrameDelay = 1' "
            '"$SNESRECOMP_USER_DATA_DIR/config.ini" || exit $?', section,
        )
        self.assertIn(
            "printf '[General]\\nDisableFrameDelay = 1\\n' > "
            '"$SNESRECOMP_USER_DATA_DIR/config.ini" || exit $?', section,
        )
        self.assertIn(
            "run_route ui-circuit-drive-capture ui-circuit-drive-capture.script "
            "ui-circuit-result-dumps 120 required || exit $?", section,
        )
        self.assertIn("              ) || exit $?", section)
        self.assertEqual(workflow.count("DisableFrameDelay = 1"), 1)
        self.assertNotIn("run_route ui-stunt-result-route ", workflow)

    def test_existing_eleven_frame_state_dumps_and_aggregate_retained(self):
        workflow = WORKFLOW.read_text()
        section = workflow.split("            results-a)", 1)[1].split("            results-b)", 1)[0]
        for tag in (
            "ui-circuit-track-selected", "ui-circuit-now-playing",
            "ui-circuit-entered", "ui-circuit-drive-start", "ui-circuit-drive-10",
            "ui-circuit-drive-20", "ui-circuit-drive-30", "ui-circuit-drive-40",
            "ui-circuit-drive-50", "ui-circuit-drive-60", "ui-circuit-terminal",
        ):
            self.assertIn(tag, section)
        self.assertIn('ui-circuit-result-dumps/$tag.wram.bin', section)
        aggregate = workflow.split("  aggregate:", 1)[1]
        self.assertIn('ui-circuit-result-dumps', aggregate)
        self.assertIn('check_result_screen_time.py', aggregate)
        script = (ROOT / "tests/input/ui-circuit-drive-capture.script").read_text()
        self.assertEqual(
            sum(line.lstrip().startswith("dump ") for line in script.splitlines()),
            11,
        )


if __name__ == "__main__":
    unittest.main()
