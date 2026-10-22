"""ROM-free source contract for opt-in same-run Windows Local Tournament path.

The legacy independently nominated, prior-smoke-run path remains unchanged.
This exploratory path must not silently become an automatic CI/release gate.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SMOKE = ROOT / ".github/workflows/windows-native-smoke.yml"
SAME_RUN = ROOT / ".github/workflows/windows-local-tournament-same-run.yml"
LEGACY = ROOT / ".github/workflows/windows-local-tournament-package-acceptance.yml"

class SameRunTournamentSourceContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.smoke = SMOKE.read_text(encoding="utf-8")
        cls.same = SAME_RUN.read_text(encoding="utf-8")
        cls.legacy = LEGACY.read_text(encoding="utf-8")

    def test_legacy_independent_pin_and_download_workflow_is_preserved(self):
        self.assertIn("actions/download-artifact@v4", self.legacy)
        self.assertIn("verify-archive-checksum", self.legacy)
        self.assertIn("run_windows_local_tournament_package_acceptance.sh", self.legacy)
        self.assertNotIn("run_tournament_acceptance: true", self.legacy)

    def test_experimental_wrapper_is_manual_and_source_bound(self):
        s = self.same
        self.assertIn("  workflow_dispatch:", s)
        self.assertNotIn("  push:", s)
        self.assertNotIn("  pull_request:", s)
        self.assertIn("candidate_commit_sha:", s)
        self.assertIn("portable_zip_sha256:", s)
        self.assertIn("uses: ./.github/workflows/windows-native-smoke.yml", s)
        self.assertIn("run_tournament_acceptance: true", s)
        self.assertNotIn("actions/download-artifact", s)
        self.assertNotIn("ur-recomp-windows-x64-portable", s)

    def test_same_run_rechecks_nominated_main_commit_and_inner_zip(self):
        s = self.smoke
        for token in (
            '[[ "$GITHUB_REF" == "refs/heads/main" ]]',
            '[[ "$GITHUB_SHA" == "$QA_APPROVED_SHA" ]]',
            '[[ "$QA_APPROVED_ZIP_SHA256" =~ ^[0-9a-f]{64}$ ]]',
            'ACTUAL_ZIP_SHA256="$(sha256sum "$PACKAGE_ARCHIVE"',
            'test "$ACTUAL_ZIP_SHA256" = "$QA_APPROVED_ZIP_SHA256"',
            'run_windows_local_tournament_package_acceptance.sh',
            'verify_windows_tournament_acceptance_receipt.py',
            'tools/evidence_contract.py',
        ):
            self.assertIn(token, s)
        self.assertLess(s.index("Validate independently nominated same-source"),
                        s.index("Verify canonical ROM and package contracts"))
        self.assertLess(s.index("Same-run packaged Local Tournament acceptance"),
                        s.index("Upload same-run tournament evidence"))

    def test_opt_in_archive_upload_excludes_sensitive_bytes(self):
        s = self.smoke
        start = s.index("      - name: Upload same-run tournament evidence")
        end = s.index("      - name: Upload Windows evidence", start)
        step = s[start:end]
        self.assertIn("inputs.run_tournament_acceptance", step)
        self.assertIn("tournament-qa-envelope.json", step)
        for forbidden in (
            "UR-Recomp-Windows-x64.zip",
            "Uniracers_USA.sfc",
            "*.urrun",
            "*.urmatch",
            "*.urfixture",
            "tournament-work/**",
            "user-data/",
            "multiplayer-runs/",
        ):
            self.assertNotIn(forbidden, step)

if __name__ == "__main__":
    unittest.main()
