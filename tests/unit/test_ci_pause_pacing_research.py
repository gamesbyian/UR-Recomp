"""Guard the research-only three-checkpoint native Pause pacing proof."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]

class PausePacingResearchTest(unittest.TestCase):
    def test_preserves_original_capture_and_all_dump_checks(self):
        wf=(ROOT/".github/workflows/native-ui-evidence.yml").read_text()
        nav=wf.split("            navigation)",1)[1].split("            results-a)",1)[0]
        original="run_route ui-pause-route ui-pause-route.script ui-pause-dumps 90"
        self.assertEqual(wf.count(original),1)
        self.assertLess(nav.index("UR_PAUSE_SEED files="),nav.index(original))
        self.assertLess(nav.index(original),nav.index("for pacing in paced unpaced; do"))
        for item in ("UR_PAUSE_PACING_PARITY PASS",
                     'cp -a "$RUNNER_TEMP/ui-pause-seed/."',
                     'grep -Fq "config dir anchored: $SNESRECOMP_USER_DATA_DIR"',
                     "hashlib.sha256(p.read_bytes()).hexdigest()",
                     "if drift" if False else "baseline_drift="):
            self.assertIn(item,nav)
        self.assertIn('--dump-dir "$RUNNER_TEMP/ui-pause-dumps"',wf.split("  aggregate:",1)[1])
        script=(ROOT/"tests/input/ui-pause-route.script").read_text()
        self.assertEqual(sum(s.startswith("dump ") for s in script.splitlines()),3)
        self.assertIn("UR_RACE_RESULT_CLONED_UNPACED_ROOT PASS",wf)
