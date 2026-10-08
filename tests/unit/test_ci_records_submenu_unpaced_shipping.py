"""Records-submenus accelerated capture must keep twelve original checkpoints."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[2]
class RecordsSubmenuShippingTest(unittest.TestCase):
    def test_proven_seed_and_config_root(self):
        wf=(ROOT/".github/workflows/native-ui-evidence.yml").read_text()
        section=wf.split("            results-b)",1)[1].split("            records)",1)[0]
        for s in ("for state in config.ini keybinds.ini saves/save.srm; do",
                  'test -f "$src"',
                  'cp "$src" "$SNESRECOMP_USER_DATA_DIR/$state"',
                  "DisableFrameDelay = 1",
                  "run_route ui-records-submenus ui-records-submenus.script ui-records-submenu-dumps 180 required",
                  'grep -Fq "config dir anchored: $SNESRECOMP_USER_DATA_DIR"',
                  "UR_RECORDS_SUBMENU_CLONED_UNPACED_ROOT PASS"):
            self.assertIn(s,section)
        self.assertEqual(wf.count("run_route ui-records-submenus "),1)
        self.assertIn('--dump-dir "$RUNNER_TEMP/ui-records-submenu-dumps"',wf.split("  aggregate:",1)[1])
    def test_all_original_checkpoints_preserved(self):
        lines=(ROOT/"tests/input/ui-records-submenus.script").read_text().splitlines()
        self.assertEqual(sum(x.startswith("dump ") for x in lines),12)
