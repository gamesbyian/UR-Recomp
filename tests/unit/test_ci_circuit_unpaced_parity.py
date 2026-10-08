"""The opt-in Circuit unpaced probe proves every existing byte, not mere presence."""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class CircuitUnpacedParityProbeTest(unittest.TestCase):
    def test_original_paced_evidence_remains_authoritative(self):
        workflow = (ROOT / ".github/workflows/native-ui-evidence.yml").read_text()
        self.assertIn(
            "run_route ui-circuit-drive-capture ui-circuit-drive-capture.script "
            "ui-circuit-result-dumps 120 required || exit $?", workflow
        )
        probe = workflow.split("      - name: Probe unpaced Circuit capture byte parity", 1)[1].split(
            "      - name: Upload shard evidence", 1
        )[0]
        self.assertIn("if: matrix.shard == 'results-a'", probe)
        self.assertIn("DisableFrameDelay = 1", probe)
        self.assertIn('SNESRECOMP_USER_DATA_DIR="$PACED_USER"', probe)
        self.assertIn('SNESRECOMP_USER_DATA_DIR="$UNPACED_USER"', probe)
        self.assertIn("DisableFrameDelay = 0", probe)
        self.assertIn('SNESRECOMP_DUMP_DIR="$PACED"', probe)
        self.assertIn('SNESRECOMP_DUMP_DIR="$UNPACED"', probe)
        self.assertEqual(
            probe.count('timeout 120s xvfb-run -a "$EXE" "$ROM" --script "$SCRIPT"'), 2
        )

    def test_fail_closed_full_capture_file_set_and_sha256(self):
        workflow = (ROOT / ".github/workflows/native-ui-evidence.yml").read_text()
        probe = workflow.split("      - name: Probe unpaced Circuit capture byte parity", 1)[1].split(
            "      - name: Upload shard evidence", 1
        )[0]
        for invariant in (
            "root.rglob('*')",
            "hashlib.sha256(path.read_bytes()).hexdigest()",
            "if not a or not b",
            "name.endswith('.wram.bin')",
            "if set(a) != set(b)",
            "if mismatched:",
            "UR_CIRCUIT_PAIRED_UNPACED_PARITY PASS",
            "UR_CIRCUIT_BASELINE_ROOT_DIFFERENCE",
            'python3 - "$PACED" "$UNPACED" "$ORIGINAL"',
        ):
            self.assertIn(invariant, probe)
        self.assertLess(probe.index("if set(a) != set(b)"), probe.index("UR_CIRCUIT_PAIRED_UNPACED_PARITY PASS"))


if __name__ == "__main__":
    unittest.main()
