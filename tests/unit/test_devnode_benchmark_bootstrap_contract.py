"""Fail-closed contracts for the manual-only HP runner Python bootstrap."""
from pathlib import Path
import re
import unittest

SCRIPT = (Path(__file__).resolve().parents[2] / "tools" /
          "devnode_benchmark" / "prepare_python.ps1")
EXPECTED_SHA256 = "4acbed6dd1c744b0376e3b1cf57ce906f9dc9e95e68824584c8099a63025a3c3"


class DevnodeBootstrapContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SCRIPT.read_text(encoding="utf-8")

    def test_runner_identity_precedes_download_and_execution(self):
        source = self.source
        identity = source.index("$env:RUNNER_NAME -ne 'hpmini-ur-recomp'")
        self.assertLess(identity, source.index("Invoke-WebRequest"))
        self.assertLess(identity, source.index("& $exe -c"))
        self.assertIn("throw 'Refusing to attribute HP benchmark", source)

    def test_official_archive_sha256_checked_on_download_and_reuse(self):
        source = self.source
        self.assertIn(EXPECTED_SHA256, source)
        self.assertIn("Get-FileHash -LiteralPath $download -Algorithm SHA256", source)
        self.assertIn("Get-FileHash -LiteralPath $zip -Algorithm SHA256", source)
        self.assertLess(source.index("Get-FileHash -LiteralPath $zip"),
                        source.index("Expand-Archive"))
        self.assertEqual(len(re.findall(r"SHA-256.*mismatch|SHA-256 differs", source)), 2)

    def test_untrusted_extracted_interpreter_is_never_reused(self):
        source = self.source
        self.assertNotIn("if (-not (Test-Path -LiteralPath $exe", source)
        self.assertLess(source.index("Expand-Archive"), source.index("& $exe -c"))
        self.assertIn("Remove-Item -LiteralPath $target -Recurse -Force", source)
        self.assertIn("Move-Item -LiteralPath $staging -Destination $target", source)


if __name__ == "__main__":
    unittest.main()
