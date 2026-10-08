"""Contract for a clean-PC verifier that needs no development toolchain."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools" / "Test-URRecompPortable.ps1"
DOC = ROOT / "docs" / "WINDOWS-CLEAN-MACHINE-ACCEPTANCE.md"


class CleanMachineVerifierPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script = SCRIPT.read_text(encoding="utf-8")
        cls.instructions = DOC.read_text(encoding="utf-8")

    def test_uses_stock_windows_powershell_only(self):
        self.assertIn("#requires -Version 5.1", self.script)
        self.assertIn("Expand-Archive -LiteralPath", self.script)
        self.assertIn("Get-FileHash -LiteralPath", self.script)
        self.assertNotIn("Invoke-WebRequest", self.script)
        self.assertNotIn("Install-Module", self.script)
        self.assertNotIn("python.exe", self.script)

    def test_rejects_incomplete_or_untrusted_bundle_before_extraction(self):
        self.assertIn("Destination already exists", self.script)
        self.assertIn("Both the release ZIP and adjacent SHA-256 sidecar", self.script)
        self.assertIn("Invalid canonical ZIP checksum sidecar", self.script)
        self.assertIn("Release ZIP does not match", self.script)
        self.assertLess(
            self.script.index("Release ZIP does not match"),
            self.script.index("Expand-Archive -LiteralPath"),
        )

    def test_verifies_payload_and_preserves_immutable_package(self):
        for marker in (
            "PACKAGE-MANIFEST.json", "Get-FileHash -LiteralPath $member",
            "Incorrect extracted file SHA-256", "Incorrect extracted file size",
            "Unmanifested extracted file", "canonical package-relative ROM path",
            "Assert-PackageFiles -PackageRoot $packageRoot",
        ):
            self.assertIn(marker, self.script)
        self.assertEqual(
            self.script.count("Assert-PackageFiles -PackageRoot $packageRoot"),
            2,
        )

    def test_launch_is_optional_and_does_not_change_default_user_storage(self):
        self.assertIn("[switch]$Launch", self.script)
        self.assertIn("if ($Launch -or", self.script)
        self.assertIn("UR_RECOMP_USER_DATA_ROOT", self.script)
        self.assertIn("isolated-user-data", self.script)
        self.assertIn("unrelated launch working directory", self.script)
        self.assertIn("diagnostics\\startup.log", self.script)
        self.assertIn("real Windows", self.instructions)
        self.assertIn("no claim of a verified clean", self.instructions)


if __name__ == "__main__":
    unittest.main()
