"""Enforce the CI/manual boundary for bounded native UI captures."""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "tests/input"
WORKFLOW = ROOT / ".github/workflows/native-ui-evidence.yml"
MANIFEST = ROOT / ".github/ci/modern-native-ui-paths.txt"


def commands(filename: str) -> list[str]:
    return [
        line.strip()
        for line in (INPUT / filename).read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


class BoundedNativeUiResearchTest(unittest.TestCase):
    def test_splash_route_keeps_original_successful_prefix(self):
        full = commands("ui-ending-shortcut.script")
        bounded = commands("ui-splash-capture.script")
        cutoff = full.index("dump ui-splash-observed")
        self.assertEqual(bounded, full[:cutoff + 1] + ["quit"])
        self.assertIn("until 009F == 5B 1800", full)
        self.assertNotIn("until 009F == 5B 1800", bounded)

    def test_circuit_route_keeps_every_pre_result_capture(self):
        full = commands("ui-circuit-result-route.script")
        bounded = commands("ui-circuit-drive-capture.script")
        cutoff = full.index("dump ui-circuit-terminal")
        self.assertEqual(bounded, full[:cutoff + 1] + ["quit"])
        self.assertIn("until 009F == BC 1200", full)
        self.assertNotIn("until 009F == BC 1200", bounded)
        self.assertEqual(
            [line for line in bounded if line.startswith("dump ")],
            [
                "dump ui-circuit-track-selected",
                "dump ui-circuit-now-playing",
                "dump ui-circuit-entered",
                "dump ui-circuit-drive-start",
                "dump ui-circuit-drive-10",
                "dump ui-circuit-drive-20",
                "dump ui-circuit-drive-30",
                "dump ui-circuit-drive-40",
                "dump ui-circuit-drive-50",
                "dump ui-circuit-drive-60",
                "dump ui-circuit-terminal",
            ],
        )

    def test_required_automatic_routes_and_artifacts(self):
        workflow = WORKFLOW.read_text()
        for route, dump in (
            ("ui-splash-capture", "ui-ending-dumps"),
            ("ui-circuit-drive-capture", "ui-circuit-result-dumps"),
        ):
            self.assertIn(
                f"run_route {route} {route}.script {dump}", workflow
            )
            self.assertRegex(
                workflow,
                rf"run_route {route} {route}\.script [^\n]* required \|\| exit \$\?",
            )
        self.assertNotIn("run_route ui-ending-shortcut ", workflow)
        self.assertNotIn("run_route ui-circuit-result-route ", workflow)
        self.assertIn("ui-splash-observed.wram.bin", workflow)
        for line in commands("ui-circuit-drive-capture.script"):
            if line.startswith("dump "):
                tag = line.split()[1]
                self.assertIn(
                    f"ui-circuit-result-dumps/$tag.wram.bin", workflow
                )

    def test_six_shards_and_rebalance_keep_single_capture_owner(self):
        workflow = WORKFLOW.read_text()
        self.assertIn(
            "shard: [core, navigation, results-a, results-b, records, profiles]",
            workflow,
        )
        matches = list(re.finditer(r"run_route ui-main-branches ", workflow))
        self.assertEqual(len(matches), 1)
        profiles = workflow.split("            profiles)", 1)[1].split("            *)", 1)[0]
        self.assertIn("run_route ui-main-branches ", profiles)

    def test_router_ignores_retained_manual_probes(self):
        paths = MANIFEST.read_text().splitlines()
        self.assertIn("tests/input/ui-splash-capture.script", paths)
        self.assertIn("tests/input/ui-circuit-drive-capture.script", paths)
        self.assertNotIn("tests/input/ui-ending-shortcut.script", paths)
        self.assertNotIn("tests/input/ui-circuit-result-route.script", paths)


if __name__ == "__main__":
    unittest.main()
