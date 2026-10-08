"""Automatic Native UI must not burn time on empty research probes."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/native-ui-evidence.yml"
MANIFEST = ROOT / ".github/ci/modern-native-ui-paths.txt"

MANUAL = (
    "ui-vs-handoff",
    "ui-record-high",
    "ui-record-player",
    "ui-record-group",
)


class ZeroDumpUiProbePolicyTest(unittest.TestCase):
    def test_repeated_timeout_probes_remain_manual_only(self):
        workflow = WORKFLOW.read_text()
        selected = MANIFEST.read_text().splitlines()
        for name in MANUAL:
            self.assertTrue((ROOT / "tests/input" / f"{name}.script").is_file())
            self.assertNotIn(f"run_route {name} ", workflow)
            self.assertNotIn(f"tests/input/{name}.script", selected)
        self.assertNotIn("run_route \"ui-record-$name\"", workflow)

    def test_authoritative_coverage_remains_automatic(self):
        workflow = WORKFLOW.read_text()
        paths = MANIFEST.read_text().splitlines()
        for route in ("ui-main-branches", "ui-records-submenus", "ui-records-explore"):
            self.assertIn(f"run_route {route} ", workflow)
            self.assertIn(f"tests/input/{route}.script", paths)
        main_branches = (ROOT / "tests/input/ui-main-branches.script").read_text()
        self.assertIn("dump ui-vs-entry", main_branches)
        submenu = (ROOT / "tests/input/ui-records-submenus.script").read_text()
        for label in ("ui-record-high-entry", "ui-record-player-entry", "ui-record-group-entry"):
            self.assertIn(f"dump {label}", submenu)
        self.assertIn("ui-records-submenus:ui-records-submenu-dumps", workflow)
        # Aggregate must still include both authoritative producer directories.
        self.assertIn('ui-branch-dumps', workflow)
        self.assertIn('ui-records-submenu-dumps', workflow)
        self.assertIn('ui-records-explore-dumps', workflow)


if __name__ == "__main__":
    unittest.main()
