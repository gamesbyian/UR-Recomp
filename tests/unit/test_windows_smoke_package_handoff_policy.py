"""ROM-free cross-workflow contract for an exact smoke-built portable ZIP.

The manual tournament consumer presently downloads a successful Windows smoke
package by Actions artifact name and run ID. Removing the provider upload
without redesigning the consumer strands that QA route, even if the smoke
workflow itself remains green. This tests source plumbing, not actual Windows
execution or permission to publish retail game data.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
SMOKE = ROOT / ".github/workflows/windows-native-smoke.yml"
TOURNAMENT = ROOT / ".github/workflows/windows-local-tournament-package-acceptance.yml"
SMOKE_RUN = "${{ inputs.smoke_run_id }}"
ZIP = "${{ runner.temp }}/UR-Recomp-Windows-x64.zip"
CHECKSUM = ZIP + ".sha256"


def steps(source):
    """Split job-level named Actions steps, ignoring comments and plain text."""
    matches = list(re.finditer(r"(?m)^      - name: ([^\n]+)$", source))
    return [(m.group(1), source[m.start():matches[i + 1].start()
                                 if i + 1 < len(matches) else len(source)])
            for i, m in enumerate(matches)]


def scalar(step, key, indent):
    found = re.search(rf"(?m)^{' ' * indent}{re.escape(key)}: ([^\n]+)$", step)
    return found.group(1).strip() if found else None


def upload_paths(step):
    found = re.search(r"(?m)^          path: \|\n((?:^            [^\n]+\n)+)", step)
    return {line.strip() for line in found.group(1).splitlines()} if found else set()


def validate_handoff(smoke, tournament):
    """Cross-check exact-run downloads against the producing artifact.

    Return zero only when that download contract is no longer present.
    Another delivery/acceptance architecture would need its OWN proof.
    """
    wanted = []
    for _, step in steps(tournament):
        if (scalar(step, "uses", 8) == "actions/download-artifact@v4"
                and scalar(step, "run-id", 10) == SMOKE_RUN):
            name = scalar(step, "name", 10)
            if not name:
                raise ValueError("smoke-run consumer lacks a literal artifact name")
            wanted.append(name)
    if not wanted:
        return 0
    uploads = [body for _, body in steps(smoke)
               if scalar(body, "uses", 8) == "actions/upload-artifact@v4"]
    for name in wanted:
        matches = [body for body in uploads if scalar(body, "name", 10) == name]
        if len(matches) != 1:
            raise ValueError(f"no unique smoke-run upload for {name}")
        body = matches[0]
        if scalar(body, "if", 8) != "success()":
            raise ValueError("portable artifact upload must be success-gated")
        if not {ZIP, CHECKSUM}.issubset(upload_paths(body)):
            raise ValueError("portable artifact must include ZIP and checksum")
    return len(wanted)


class SmokePackageConsumerContract(unittest.TestCase):
    @staticmethod
    def fixtures():
        provider = ("      - name: Upload portable Windows package\n"
                    "        if: success()\n"
                    "        uses: actions/upload-artifact@v4\n"
                    "        with:\n"
                    "          name: ur-recomp-windows-x64-portable\n"
                    "          path: |\n"
                    f"            {ZIP}\n"
                    f"            {CHECKSUM}\n")
        consumer = ("      - name: Download smoke-built package\n"
                    "        uses: actions/download-artifact@v4\n"
                    "        with:\n"
                    "          name: ur-recomp-windows-x64-portable\n"
                    f"          run-id: {SMOKE_RUN}\n")
        return provider, consumer

    def test_live_cross_workflow_contract(self):
        # The legacy ZIP transfer is gone, but its replacement must actually
        # compile and verify the original package in this *same* Windows job.
        smoke = SMOKE.read_text(encoding="utf-8")
        tournament = TOURNAMENT.read_text(encoding="utf-8")
        self.assertEqual(validate_handoff(smoke, tournament), 0)
        self.assertNotIn("actions/download-artifact@", tournament)
        self.assertNotIn("actions/upload-artifact@", tournament)
        for marker in (
            "uses: ./.github/workflows/windows-native-smoke.yml",
            "run_tournament_acceptance: true",
            "candidate_commit_sha: ${{ inputs.candidate_commit_sha }}",
            "portable_zip_sha256: ${{ inputs.portable_zip_sha256 }}",
        ):
            self.assertIn(marker, tournament)
        for marker in (
            "Check approved same-run tournament source identity",
            '[[ "$GITHUB_REF" == "refs/heads/main" ]]',
            '[[ "$GITHUB_SHA" == "$QA_APPROVED_SHA" ]]',
            'test "$ACTUAL_ZIP_SHA256" = "$QA_APPROVED_ZIP_SHA256"',
            "Same-run packaged Local Tournament acceptance",
            "run_windows_local_tournament_package_acceptance.sh",
            "verify_windows_tournament_acceptance_receipt.py",
            "tools/evidence_contract.py",
        ):
            self.assertIn(marker, smoke)
        self.assertLess(smoke.index("Check approved same-run tournament source identity"),
                        smoke.index("Verify canonical ROM and package contracts"))
        self.assertLess(smoke.index("Same-run packaged Local Tournament acceptance"),
                        smoke.index("Verify archive-free Windows artifact upload policy"))

    def test_negative_missing_upload_and_different_artifact_name(self):
        provider, consumer = self.fixtures()
        self.assertEqual(validate_handoff(provider, consumer), 1)
        for bad in (
            provider.replace("actions/upload-artifact@v4", "actions/checkout@v4"),
            provider.replace("ur-recomp-windows-x64-portable", "renamed-zip"),
            provider.replace(f"            {ZIP}\n", ""),
            provider.replace(f"            {CHECKSUM}\n", ""),
            provider.replace("if: success()", "if: always()"),
        ):
            with self.subTest(bad=bad[:90]):
                with self.assertRaises(ValueError):
                    validate_handoff(bad, consumer)
        with self.assertRaisesRegex(ValueError, "no unique smoke-run upload"):
            validate_handoff(provider, consumer.replace(
                "ur-recomp-windows-x64-portable", "different-download"))

    def test_removed_cross_run_download_is_not_automatically_approved(self):
        provider, consumer = self.fixtures()
        reworked = consumer.replace("actions/download-artifact@v4",
                                    "actions/checkout@v4")
        # Only THIS former dependency becomes inapplicable. This does not
        # attest to a real replacement package, emulator, or release gate.
        self.assertEqual(validate_handoff(provider, reworked), 0)


if __name__ == "__main__":
    unittest.main()
