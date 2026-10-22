"""Source-only contract for the manual same-run Windows tournament package.

The external nomination is checked against a fresh main revision and portable
ZIP digest. This cannot substitute for an executed packaged QA run.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
CALLER = ROOT / ".github/workflows/windows-local-tournament-package-acceptance.yml"
SMOKE = ROOT / ".github/workflows/windows-native-smoke.yml"


class WindowsLocalTournamentCandidatePinTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.caller = CALLER.read_text(encoding="utf-8")
        cls.smoke = SMOKE.read_text(encoding="utf-8")

    def test_manual_caller_exact_pins_without_cross_run_download(self):
        s = self.caller
        self.assertIn("  workflow_dispatch:", s)
        self.assertNotIn("  pull_request:", s)
        self.assertNotIn("  push:", s)
        self.assertIn("uses: ./.github/workflows/windows-native-smoke.yml", s)
        self.assertIn("run_tournament_acceptance: true", s)
        self.assertNotIn("actions/download-artifact", s)
        self.assertNotIn("smoke_run_id:", s)
        for name in ("candidate_commit_sha", "portable_zip_sha256"):
            self.assertIn("      " + name + ":", s)
            self.assertIn(name + ": ${{ inputs." + name + " }}", s)

    def test_source_pins_admitted_before_build_and_main_only(self):
        s = self.smoke
        start = s.index("- name: Validate independently nominated same-source tournament candidate")
        build = s.index("- name: Configure and build (Visual Studio, ClangCL, SDL3)")
        self.assertLess(start, build)
        for guard in (
            '[[ "$GITHUB_REF" == "refs/heads/main" ]]',
            '[[ "$QA_APPROVED_SHA" =~ ^[0-9a-f]{40}$ ]]',
            '[[ "$QA_APPROVED_ZIP_SHA256" =~ ^[0-9a-f]{64}$ ]]',
            '[[ "$GITHUB_SHA" == "$QA_APPROVED_SHA" ]]',
            'if: inputs.run_tournament_acceptance',
        ):
            self.assertIn(guard, s)

    def test_same_run_package_oracle_and_sha_precede_guest_route(self):
        s = self.smoke
        independent = s.index("- name: Independently verify portable ZIP with stock Windows PowerShell")
        optional = s.index("- name: Same-run packaged Local Tournament acceptance")
        captured = s.index("run_windows_local_tournament_package_acceptance.sh", optional)
        compare = s.index('test "$ACTUAL_ZIP_SHA256" = "$QA_APPROVED_ZIP_SHA256"', optional)
        self.assertLess(independent, optional)
        self.assertLess(compare, captured)
        self.assertIn("Test-URRecompPortable.ps1", s)
        self.assertIn("verify-archive-checksum", s)
        self.assertIn('ACTUAL_ZIP_SHA256="$(sha256sum "$PACKAGE_ARCHIVE"', s)
        self.assertIn('test "$QA_APPROVED_SHA" = "$GITHUB_SHA"', s)
        self.assertIn('test -d "$TEST_PACKAGE"', s)

    def test_exact_candidate_receipt_and_limited_upload(self):
        s = self.smoke
        optin = s[s.index("- name: Same-run packaged Local Tournament acceptance"):
                  s.index("- name: Upload Windows evidence")]
        self.assertIn("verify_windows_tournament_acceptance_receipt.py", optin)
        for guard in (
            '--expected-source "$QA_APPROVED_SHA"',
            '--expected-zip-sha256 "$QA_APPROVED_ZIP_SHA256"',
            '--expected-harness-sha "$GITHUB_SHA"',
            '--expected-smoke-run-id "$QA_SMOKE_RUN_ID"',
            'QA_SMOKE_RUN_ID: ${{ github.run_id }}',
            'tools/evidence_contract.py "$RUNNER_TEMP/tournament-qa-envelope.json"',
        ):
            self.assertIn(guard, optin)
        self.assertLess(optin.index("run_windows_local_tournament_package_acceptance.sh"),
                        optin.index("verify_windows_tournament_acceptance_receipt.py"))
        upload = optin[optin.index("- name: Upload same-run tournament evidence"):]
        self.assertIn("if: ${{ always() && inputs.run_tournament_acceptance }}", upload)
        for marker in (
            "tournament-qa-envelope.json", "tournament-artifacts.log",
            "tournament-work/multiplayer-runs/*.urrun",
            "tournament-work/multiplayer-runs/*.urmatch",
            "tournament-work/user data/local-tournaments/",
        ):
            self.assertIn(marker, upload)
        self.assertNotIn("PACKAGE_ARCHIVE", upload)
        self.assertNotIn("UR-Recomp-Windows-x64.zip", upload)
        self.assertNotIn("tournament-work/**", upload)


if __name__ == "__main__":
    unittest.main()
