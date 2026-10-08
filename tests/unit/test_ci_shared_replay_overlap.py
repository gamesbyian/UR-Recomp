"""The paced and unpaced replay oracle may overlap, but may never weaken parity."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/modern-shared-native-acceptance.yml"


class SharedReplayOverlapCiTest(unittest.TestCase):
    def test_two_independent_reference_processes_before_comparison(self):
        source = WORKFLOW.read_text()
        body = source.split("      - name: Capture completed Dragster run", 1)[1].split(
            "      - name: Re-drive captured run in a fresh process", 1
        )[0]
        self.assertEqual(body.count("timeout 180s xvfb-run -n "), 2)
        self.assertIn('timeout 180s xvfb-run -n 90 "$EXE" "$ROM"', body)
        self.assertIn('timeout 180s xvfb-run -n 91 "$EXE" "$ROM"', body)
        self.assertIn('SNESRECOMP_USER_DATA_DIR="$PACED_USER"', body)
        self.assertIn('UR_RUN_RECORD_CAPTURE_PATH="$RECORD"', body)
        self.assertIn('UR_RUN_RECORD_CAPTURE_PATH="$PACED_RECORD"', body)
        self.assertIn('>"$LOG" 2>&1 &', body)
        self.assertIn('>"$PACED_LOG" 2>&1 &', body)
        self.assertLess(body.index('printf \'[General]'), body.index('ORIGINAL_PID=$!'))
        self.assertLess(body.index('ORIGINAL_PID=$!'), body.index('PACED_PID=$!'))
        self.assertLess(body.index('PACED_PID=$!'), body.index('wait "$ORIGINAL_PID"'))
        self.assertLess(body.index('wait "$PACED_PID"'), body.index('g++ -std=c++17'))

    def test_concurrent_captures_never_share_mod_state(self):
        # Concurrent processes sharing mods/preloaded/state.toml race on its
        # fixed .tmp name ("cannot publish mod state").
        source = WORKFLOW.read_text()
        body = source.split("      - name: Capture completed Dragster run", 1)[1].split(
            "      - name: Re-drive captured run in a fresh process", 1
        )[0]
        self.assertIn('SNESRECOMP_MOD_STATE_PATH="$UNPACED_MOD_STATE"', body)
        self.assertIn('SNESRECOMP_MOD_STATE_PATH="$PACED_MOD_STATE"', body)
        unpaced = body.split("ORIGINAL_PID=$!", 1)[0].rsplit("SDL_AUDIODRIVER=dummy", 1)[1]
        paced = body.split("PACED_PID=$!", 1)[0].rsplit("SDL_AUDIODRIVER=dummy", 1)[1]
        self.assertIn("UNPACED_MOD_STATE", unpaced)
        self.assertIn("PACED_MOD_STATE", paced)

    def test_fail_closed_with_both_logs_and_exact_semantic_oracle(self):
        source = WORKFLOW.read_text()
        body = source.split("      - name: Capture completed Dragster run", 1)[1].split(
            "      - name: Re-drive captured run in a fresh process", 1
        )[0]
        for expected in (
            'wait "$ORIGINAL_PID" || original_status=$?',
            'wait "$PACED_PID" || paced_status=$?',
            'cat "$LOG"',
            'cat "$PACED_LOG"',
            'if [ "$original_status" -ne 0 ] || [ "$paced_status" -ne 0 ]; then',
            'test -s "$RECORD.input"',
            'test -s "$RECORD.urghost"',
            'test -s "$PACED_RECORD"',
            '"$RUNNER_TEMP/compare-runs" "$PACED_RECORD" "$RECORD"',
            'UR_RUN_REPLAY_COMPARE PASS course=course:01',
            'UR_COMPLETED_RUN_UNPACED_PROOF=semantic_record_equal',
        ):
            self.assertIn(expected, body)
        self.assertLess(
            body.index('if [ "$original_status" -ne 0 ]'),
            body.index('"$RUNNER_TEMP/compare-runs" "$PACED_RECORD" "$RECORD"'),
        )


if __name__ == "__main__":
    unittest.main()
