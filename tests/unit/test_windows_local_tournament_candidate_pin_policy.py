"""Keep the manual Windows local-tournament reuse path candidate-bound."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/windows-local-tournament-package-acceptance.yml"


class WindowsLocalTournamentCandidatePinTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = WORKFLOW.read_text(encoding="utf-8")

    def test_reuses_existing_artifact_without_build_or_automatic_triggers(self):
        s = self.policy
        self.assertIn("  workflow_dispatch:", s)
        self.assertNotIn("  pull_request:", s)
        self.assertNotIn("  push:", s)
        self.assertIn("actions/download-artifact@v4", s)
        self.assertIn("run-id: ${{ inputs.smoke_run_id }}", s)
        self.assertNotIn("setup-cmake", s)
        self.assertNotIn("configure and build", s.lower())

    def test_external_pins_and_run_metadata_checked_before_download(self):
        s = self.policy
        for field in ("smoke_run_id", "candidate_commit_sha", "portable_zip_sha256"):
            self.assertRegex(s, rf"(?m)^      {field}:$")
        for token in (
            '[[ "$APPROVED_SHA" =~ ^[0-9a-f]{40}$ ]]',
            '[[ "$APPROVED_ZIP_SHA256" =~ ^[0-9a-f]{64}$ ]]',
            'gh api "repos/$GITHUB_REPOSITORY/actions/runs/$SMOKE_RUN_ID"',
            '"$conclusion" != "success"',
            '"$workflow_path" != ".github/workflows/windows-native-smoke.yml"',
            '"$built_branch" != "main"',
            '"$built_sha" != "$APPROVED_SHA"',
        ):
            self.assertIn(token, s)
        self.assertLess(s.index("- name: Refuse unapproved smoke-run candidate"),
                        s.index("- name: Download the smoke-built portable package"))

    def test_receipts_reverified_against_independent_pins_after_game_reopen(self):
        s = self.policy
        self.assertIn("verify_windows_tournament_acceptance_receipt.py", s)
        self.assertIn('--expected-source "$QA_APPROVED_SHA"', s)
        self.assertIn('--expected-zip-sha256 "$QA_APPROVED_ZIP_SHA256"', s)
        self.assertIn('--expected-harness-sha "$GITHUB_SHA"', s)
        self.assertIn('--expected-smoke-run-id "$QA_SMOKE_RUN_ID"', s)
        self.assertIn('echo "QA_SMOKE_RUN_ID=$SMOKE_RUN_ID" >> "$GITHUB_ENV"', s)
        self.assertLess(
            s.index('[[ "$SMOKE_RUN_ID" =~ ^[0-9]+$ ]]'),
            s.index('echo "QA_SMOKE_RUN_ID=$SMOKE_RUN_ID"'),
        )
        self.assertNotIn('--expected-smoke-run-id "${{ inputs.smoke_run_id }}"', s)
        self.assertIn("tournament-receipt-verification.log", s)
        self.assertIn('--output-envelope "$RUNNER_TEMP/tournament-qa-envelope.json"', s)
        self.assertIn('tools/evidence_contract.py "$RUNNER_TEMP/tournament-qa-envelope.json"', s)
        for retained in (
            "tournament-qa-envelope.json",
            "tournament-artifacts.log",
            "tournament-work/multiplayer-runs/*.urrun",
            "tournament-work/multiplayer-runs/*.urmatch",
            "tournament-work/user data/local-tournaments/",
        ):
            self.assertIn(retained, s)
        # Only the precise synthetic QA outputs are uploaded. Never publish
        # the private player's cartridge, mutable SRAM or a whole work root.
        self.assertNotIn("tournament-work/**", s)
        self.assertNotIn("tournament-work/user data/", s.split("path: |", 1)[1].replace(
            "tournament-work/user data/local-tournaments/", ""
        ))
        self.assertLess(s.index("run_windows_local_tournament_package_acceptance.sh"),
                        s.index("verify_windows_tournament_acceptance_receipt.py"))
        self.assertLess(s.index("verify_windows_tournament_acceptance_receipt.py"),
                        s.index("- name: Upload tournament evidence"))

    def test_uses_same_standalone_exact_zip_oracle_before_guest_route(self):
        s = self.policy
        for marker in (
            "Test-URRecompPortable.ps1",
            "-ExpectedSourceSha",
            "-ExpectedZipSha256",
            "UR_PORTABLE_EXACT_CANDIDATE_PIN_VERIFIED",
            "run_windows_local_tournament_package_acceptance.sh",
            "qa_harness_commit=%s",
            "backend=snesrecomp",
            "windows-tournament-candidate.txt",
        ):
            self.assertIn(marker, s)
        self.assertLess(s.index("UR_PORTABLE_EXACT_CANDIDATE_PIN_VERIFIED"),
                        s.index("- name: Packaged Local Tournament route"))
        self.assertIn("if: always()", s)


if __name__ == "__main__":
    unittest.main()
