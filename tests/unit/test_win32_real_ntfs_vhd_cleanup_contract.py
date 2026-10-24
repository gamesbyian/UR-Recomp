"""Source-bound guard for original-game disposable NTFS VHDX teardown.

These checks protect fail-closed ordering; they are not a Windows DiskPart
execution test or evidence of physical disk, power-loss or release acceptance.
"""
from pathlib import Path
import unittest


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "tools"
    / "baldosa_win32_real_ntfs_diskfull_game.ps1"
)


class Win32RealNtfsVhdCleanupContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SCRIPT.read_text(encoding="utf-8")

    def test_diskpart_exit_code_is_captured_and_reported(self):
        helper = self.source.split("function Invoke-OnlyOriginalVHD", 1)[1].split(
            "function Invoke-OriginalPhase", 1
        )[0]
        self.assertLess(
            helper.index("$diskpartExitCode = $LASTEXITCODE"),
            helper.index("if ($diskpartExitCode -ne 0"),
        )
        self.assertIn("'; output=' + $text", helper)

    def test_detach_is_verified_before_backing_file_cleanup(self):
        cleanup = self.source.rsplit("\nfinally {", 1)[1]
        for required in (
            "$detachDiagnostic = $null",
            "Invoke-OnlyOriginalVHD @(",
            "Get-DiskImage -ImagePath $disk -ErrorAction Stop",
            "if ($diskImage.Attached -ne $false)",
            "FAIL_CLOSED: cannot verify disposable VHDX detach",
            "FAIL_CLOSED: disposable VHDX remains attached",
            "Write-Warning ('DiskPart reported an error but disposable VHDX is verified detached:",
        ):
            self.assertIn(required, cleanup)
        self.assertLess(
            cleanup.index("if ($diskImage.Attached -ne $false)"),
            cleanup.index("Remove-Item -LiteralPath $root"),
        )

    def test_diskpart_failure_cannot_bypass_image_state_check(self):
        cleanup = self.source.rsplit("\nfinally {", 1)[1]
        first_query = cleanup.index("Get-DiskImage -ImagePath $disk")
        detach = cleanup.index("Invoke-OnlyOriginalVHD @(")
        diagnostic = cleanup.index("$detachDiagnostic = [string]$_")
        second_query = cleanup.index("Get-DiskImage -ImagePath $disk", first_query + 1)
        fail_closed = cleanup.index("if ($diskImage.Attached -ne $false)")
        self.assertLess(first_query, detach)
        self.assertLess(detach, diagnostic)
        self.assertLess(diagnostic, second_query)
        self.assertLess(second_query, fail_closed)
        self.assertLess(fail_closed, cleanup.index("Remove-Item -LiteralPath $root"))
        self.assertIn("throw ('FAIL_CLOSED: disposable VHDX remains attached:", cleanup)

    def test_partially_created_vhd_is_checked_even_when_setup_failed(self):
        cleanup = self.source.rsplit("\nfinally {", 1)[1]
        self.assertIn("$diskExists = Test-Path -LiteralPath $disk -PathType Leaf", cleanup)
        self.assertIn("if ($diskExists) {", cleanup)
        self.assertNotIn("if ($attached) {", cleanup)
        self.assertIn("FAIL_CLOSED: expected disposable VHDX backing missing", cleanup)
        self.assertLess(
            cleanup.index("if ($diskExists) {"),
            cleanup.index("Get-DiskImage -ImagePath $disk"),
        )


if __name__ == "__main__":
    unittest.main()
