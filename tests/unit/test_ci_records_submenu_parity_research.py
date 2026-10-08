"""Research-only Records-submenu pacing comparison preserves every capture."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
class RecordsSubmenusParityResearchTest(unittest.TestCase):
    def test_all_twelve_dumps_original_route_and_full_file_comparison(self):
        workflow=(ROOT/".github/workflows/native-ui-evidence.yml").read_text()
        sec=workflow.split("            results-b)",1)[1].split("            records)",1)[0]
        original="run_route ui-records-submenus ui-records-submenus.script ui-records-submenu-dumps 180"
        self.assertEqual(workflow.count(original),1)
        self.assertIn("UR_RECORDS_SUBMENU_SEED files=",sec)
        self.assertIn("UR_RECORDS_SUBMENU_PACING_PARITY PASS",sec)
        self.assertIn('cp -a "$RUNNER_TEMP/records-submenu-seed/."',sec)
        self.assertIn('grep -Fq "config dir anchored: $SNESRECOMP_USER_DATA_DIR"',sec)
        self.assertIn("hashlib.sha256(f.read_bytes()).hexdigest()",sec)
        self.assertLess(sec.index("UR_RECORDS_SUBMENU_SEED files="),sec.index(original))
        script=(ROOT/"tests/input/ui-records-submenus.script").read_text()
        self.assertEqual(sum(x.startswith("dump ") for x in script.splitlines()),12)
        self.assertIn('--dump-dir "$RUNNER_TEMP/ui-records-submenu-dumps"',workflow.split("  aggregate:",1)[1])
