"""Keep provisional Rename capture isolated, required and unmodified."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class ShippingUnpacedRenameAcceptanceTest(unittest.TestCase):
    def test_required_rename_capture_uses_isolated_guest_config(self):
        workflow=(ROOT/".github/workflows/native-ui-evidence.yml").read_text()
        sec=workflow.split("            profiles)",1)[1].split("            *)",1)[0]
        self.assertEqual(workflow.count("run_route ui-rename-editor-explore "),1)
        for expected in (
            'SNESRECOMP_USER_DATA_DIR="$RUNNER_TEMP/ui-rename-unpaced-user-data"',
            "printf '[General]\\nDisableFrameDelay = 1\\n'",
            "grep -Fqx 'DisableFrameDelay = 1'",
            "run_route ui-rename-editor-explore ui-rename-editor-explore.script ui-rename-editor-dumps 180 required || exit $?",
            'grep -Fq "config dir anchored: $SNESRECOMP_USER_DATA_DIR"',
            "UR_RENAME_ISOLATED_CONFIG_ROOT PASS",
            "run_route ui-name-league-route ui-name-league-route.script ui-name-league-dumps 120",
        ):
            self.assertIn(expected,sec)

    def test_original_five_branch_capture_dumps_and_atlas_are_preserved(self):
        w=(ROOT/".github/workflows/native-ui-evidence.yml").read_text()
        script=(ROOT/"tests/input/ui-rename-editor-explore.script").read_text()
        self.assertEqual(sum(x.lstrip().startswith("dump ") for x in script.splitlines()),11)
        self.assertEqual(sum(x.strip()=="reset" for x in script.splitlines()),4)
        self.assertIn("ui-rename-editor-explore:ui-rename-editor-dumps",w.split("  aggregate:",1)[1])
        self.assertIn("UR_RECORDS_ISOLATED_CONFIG_ROOT PASS",w)
        self.assertIn("UR_CIRCUIT_ISOLATED_CONFIG_ROOT PASS",w)


if __name__=="__main__":
    unittest.main()
