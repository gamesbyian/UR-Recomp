"""Temporary, fail-closed proof of paced vs unpaced Records capture equivalence."""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/native-ui-evidence.yml"


class RecordsPacingParityExperimentTest(unittest.TestCase):
    def test_authoritative_route_stays_first_and_unchanged(self):
        workflow = WORKFLOW.read_text()
        records = workflow.split("            records)", 1)[1].split("            profiles)", 1)[0]
        original = "run_route ui-records-explore ui-records-explore.script ui-records-explore-dumps 180"
        self.assertEqual(workflow.count(original), 1)
        self.assertLess(records.index(original), records.index("for pacing in paced unpaced; do"))
        self.assertIn("run_route ui-main-branches ui-main-branches.script ui-branch-dumps 150", records)
        self.assertIn("ui-records-explore:ui-records-explore-dumps", workflow.split("  aggregate:", 1)[1])

    def test_fresh_root_pair_has_only_pacing_difference(self):
        workflow = WORKFLOW.read_text()
        records = workflow.split("            records)", 1)[1].split("            profiles)", 1)[0]
        self.assertIn('export SNESRECOMP_USER_DATA_DIR="$RUNNER_TEMP/ui-records-$pacing-user"', records)
        self.assertIn('if [ "$pacing" = unpaced ]; then delay=1; fi', records)
        self.assertIn("printf '[General]\\nDisableFrameDelay = %s\\n'", records)
        self.assertIn(
            'run_route "ui-records-$pacing" ui-records-explore.script '
            '"ui-records-$pacing-dumps" 180 required || exit $?', records,
        )
        self.assertIn('grep -Fq "config dir anchored: $SNESRECOMP_USER_DATA_DIR"', records)

    def test_compares_every_byte_and_all_twelve_wram_checkpoints(self):
        workflow = WORKFLOW.read_text()
        records = workflow.split("            records)", 1)[1].split("            profiles)", 1)[0]
        for invariant in (
            'python3 - "$RUNNER_TEMP/ui-records-paced-dumps" "$RUNNER_TEMP/ui-records-unpaced-dumps" "$RUNNER_TEMP/ui-records-explore-dumps"',
            'original = hashes(Path(sys.argv[3]))',
            'UR_RECORDS_PACING_CONTROL baseline_drift=',
            'UR_RECORDS_PACING_SHA256 paced=',
            "hashlib.sha256(p.read_bytes()).hexdigest()",
            'for direction in ("down", "up", "left", "right", "a", "b")',
            'for side in ("before", "after")',
            "if set(a) != set(b):",
            "if mismatches:",
            "UR_RECORDS_PACING_PARITY PASS",
        ):
            self.assertIn(invariant, records)
        script = (ROOT / "tests/input/ui-records-explore.script").read_text()
        self.assertEqual(sum(s.lstrip().startswith("dump ") for s in script.splitlines()), 12)
        self.assertEqual(sum(s.strip() == "reset" for s in script.splitlines()), 5)


if __name__ == "__main__":
    unittest.main()
