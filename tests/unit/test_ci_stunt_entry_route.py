"""The automatic Stunt entry oracle must match the manual result probe's entry."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


def commands(name: str) -> list[str]:
    return [
        line.strip()
        for line in (ROOT / "tests/input" / name).read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


class StuntEntryRouteTest(unittest.TestCase):
    def test_bounded_entry_matches_manual_probe_without_result_wait(self):
        manual = commands("ui-stunt-result-route.script")
        entry = commands("ui-stunt-entry-route.script")
        self.assertIn("turbo on", manual)
        self.assertIn("until 009F == 18 20000", manual)
        self.assertIn("dump ui-stunt-entered", entry)
        self.assertEqual(entry, manual[:manual.index("turbo on")] + ["quit"])
        self.assertEqual(
            [line for line in entry if line.startswith("dump ")],
            [
                "dump ui-stunt-track-selected",
                "dump ui-stunt-now-playing",
                "dump ui-stunt-entered",
            ],
        )

    def test_automatic_workflow_enforces_captures(self):
        workflow = (ROOT / ".github/workflows/native-ui-evidence.yml").read_text()
        self.assertIn(
            "run_route ui-stunt-entry-route ui-stunt-entry-route.script "
            "ui-stunt-result-dumps 90 required || exit $?", workflow
        )
        self.assertNotIn(
            "run_route ui-stunt-result-route ui-stunt-result-route.script", workflow
        )
        for tag in ("ui-stunt-track-selected", "ui-stunt-now-playing", "ui-stunt-entered"):
            self.assertIn(f"ui-stunt-result-dumps/$tag.wram.bin", workflow)

        paths = (ROOT / ".github/ci/modern-native-ui-paths.txt").read_text()
        self.assertIn("tests/input/ui-stunt-entry-route.script", paths.splitlines())


if __name__ == "__main__":
    unittest.main()
