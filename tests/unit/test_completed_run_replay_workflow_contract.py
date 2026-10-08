"""Guard the native saved-artifact replay path without running the heavyweight gate."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "completed-run-replay-acceptance.yml"


class CompletedRunReplayWorkflowContractTests(unittest.TestCase):
    def test_native_redrive_consumes_export_from_real_saved_record(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        export = text.index("- name: Rehydrate replay input from saved artifact")
        redrive = text.index("- name: Re-drive captured run in a fresh process")
        self.assertLess(export, redrive)
        slice_ = text[export:redrive]
        self.assertIn("completed_run_replay_rehydrate.cpp", slice_)
        self.assertIn('"$RUNNER_TEMP/original.urrun"', slice_)
        self.assertIn('"$RUNNER_TEMP/rehydrated.input"', slice_)
        self.assertIn('cmp "$RUNNER_TEMP/original.urrun.input" "$RUNNER_TEMP/rehydrated.input"', slice_)
        self.assertIn('SNESRECOMP_INPUT_FILE="$RUNNER_TEMP/rehydrated.input"', text[redrive:])
        self.assertNotIn('SNESRECOMP_INPUT_FILE="$ORIGINAL.input"', text[redrive:])

    def test_heavyweight_replay_gate_remains_manual_only(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        trigger = workflow.split("on:", 1)[1].split("concurrency:", 1)[0]
        self.assertIn("workflow_dispatch:", trigger)
        self.assertNotIn("pull_request:", trigger)
        self.assertNotIn("push:", trigger)


if __name__ == "__main__":
    unittest.main()
