"""Keep repeated HP seeded science lean without weakening product acceptance.

Source-policy checks only: native Windows qualification and actual science
still require successful source-bound Actions runs.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SMOKE = ROOT / ".github/workflows/windows-native-smoke.yml"
SCIENCE = ROOT / ".github/workflows/owner-hp-seeded-2p-research.yml"
PRODUCT = ROOT / ".github/workflows/owner-hp-main-windows-smoke.yml"
SCIENCE_GUARD = "if: ${{ !inputs.hp_seeded_2p || inputs.run_tournament_acceptance }}"
PRODUCT_ONLY = (
    "Extracted-package Win32 window and default renderer smoke",
    "QA-09 packaged Windows controller-only root and modal return",
    "QA-05 packaged Windows default-Return Restart audio and Start-input witness",
    "Package refresh preserves user data",
    "Legacy portable state migrates once",
    "Boot to main menu",
    "Representative package startup diagnostics",
)
SCIENCE_MUST_KEEP = (
    "Verify canonical ROM and package contracts",
    "Assemble and verify portable Windows package",
    "Independently verify portable ZIP with stock Windows PowerShell",
    "Clean-package boot and per-user state anchoring",
    "HP bounded independent offscreen package boot fanout",
    "HP unattended real two-player seeded gameplay research",
    "Preserve HP resource telemetry",
    "Verify archive-free Windows artifact upload policy",
    "Upload Windows evidence",
)


def step(source: str, name: str) -> str:
    marker = "      - name: " + name + "\n"
    if source.count(marker) != 1:
        raise AssertionError("missing or ambiguous workflow step: " + name)
    return source.split(marker, 1)[1].split("\n      - name:", 1)[0]


class HpScienceValidationScopeTests(unittest.TestCase):
    def test_only_repeated_product_steps_are_skipped_in_science_mode(self):
        source = SMOKE.read_text(encoding="utf-8")
        for name in PRODUCT_ONLY:
            with self.subTest(name=name):
                body = step(source, name)
                self.assertIn("        " + SCIENCE_GUARD + "\n", body)
                # The main, hosted and nominated tournament routes evaluate
                # this expression to true and keep the same code/expectations.
                self.assertEqual(body.count(SCIENCE_GUARD), 1)
        self.assertEqual(source.count("        " + SCIENCE_GUARD + "\n"),
                         len(PRODUCT_ONLY))

    def test_science_keeps_source_package_boot_fanout_and_results(self):
        source = SMOKE.read_text(encoding="utf-8")
        for name in SCIENCE_MUST_KEEP:
            with self.subTest(name=name):
                self.assertNotIn(SCIENCE_GUARD, step(source, name))
        self.assertIn("if: ${{ inputs.run_on_hp }}",
                      step(source, "HP bounded independent offscreen package boot fanout"))
        self.assertIn("if: inputs.hp_seeded_2p",
                      step(source, "HP unattended real two-player seeded gameplay research"))
        self.assertIn("if: always()", step(source, "Upload Windows evidence"))

    def test_science_is_only_trusted_main_and_product_caller_keeps_full_qa(self):
        caller = SCIENCE.read_text(encoding="utf-8")
        product = PRODUCT.read_text(encoding="utf-8")
        smoke = SMOKE.read_text(encoding="utf-8")
        for token in (
            "github.repository == 'gamesbyian/UR-Recomp'",
            "github.ref == 'refs/heads/main'",
            "github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'",
            "run_on_hp: true",
            "hp_seeded_2p: true",
            "hp_ninja_auto: true",
        ):
            with self.subTest(token=token):
                self.assertIn(token, caller)
        self.assertNotIn("hp_seeded_2p: true", product)
        self.assertIn("hp_ninja_auto: ${{ github.event_name == 'push' }}", product)
        self.assertIn("(!inputs.hp_seeded_2p ||", smoke)
        self.assertIn("(!inputs.run_on_hp ||", smoke)


if __name__ == "__main__":
    unittest.main()
