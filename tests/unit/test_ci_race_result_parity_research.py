"""The optional Race-result pacing experiment cannot weaken shipping evidence."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[2]
class RaceResultPacingResearchTest(unittest.TestCase):
    def test_original_route_and_eighteen_state_proof_retained(self):
        w=(ROOT/".github/workflows/native-ui-evidence.yml").read_text()
        nav=w.split("            navigation)",1)[1].split("            results-a)",1)[0]
        route="run_route ui-race-result-route ui-race-result-route.script ui-race-result-dumps 180"
        self.assertEqual(w.count(route),1)
        self.assertLess(nav.index(route),nav.index("for pacing in paced unpaced; do"))
        for x in ("UR_RACE_RESULT_PACING_PARITY PASS",
                  'grep -Fq "config dir anchored: $SNESRECOMP_USER_DATA_DIR"',
                  "if differ:", "hashlib.sha256(p.read_bytes()).hexdigest()",
                  "if len(required) != 18"):
            self.assertIn(x,nav)
        self.assertIn("ui-race-result-route:ui-race-result-dumps",w.split("  aggregate:",1)[1])
        script=(ROOT/"tests/input/ui-race-result-route.script").read_text()
        self.assertEqual(sum(x.startswith("dump ") for x in script.splitlines()),18)
        self.assertIn("UR_RECORDS_ISOLATED_CONFIG_ROOT PASS",w)
