"""Contract for a clean-PC verifier that needs no development toolchain."""
from pathlib import Path
import hashlib
import json
import zipfile
import shutil
import subprocess
import tempfile
import unittest

from tools import assemble_windows_package as package

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools" / "Test-URRecompPortable.ps1"
DOC = ROOT / "docs" / "WINDOWS-CLEAN-MACHINE-ACCEPTANCE.md"


class CleanMachineVerifierPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script = SCRIPT.read_text(encoding="utf-8")
        cls.instructions = DOC.read_text(encoding="utf-8")

    def test_powershell_script_parses_when_pwsh_is_available(self):
        # Linux tooling CI ordinarily has pwsh; parse the *real* PowerShell
        # file instead of using a Python imitation of PowerShell syntax.
        pwsh = shutil.which("pwsh")
        if pwsh is None:
            self.skipTest("PowerShell executable unavailable on this host")
        quoted = str(SCRIPT).replace("'", "''")
        command = (
            "$tokens=$null; $parseErrors=$null; "
            "[System.Management.Automation.Language.Parser]::ParseFile("
            f"'{quoted}', [ref]$tokens, [ref]$parseErrors) | Out-Null; "
            "if ($parseErrors.Count -gt 0) { "
            "$parseErrors | Out-String | Write-Output; exit 1 }"
        )
        proc = subprocess.run(
            [pwsh, "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_real_powershell_verifies_synthetic_release_bundle(self):
        pwsh = shutil.which("pwsh")
        if pwsh is None:
            self.skipTest("PowerShell executable unavailable on this host")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build = root / "build"
            build.mkdir()
            (build / package.EXE_NAME).write_bytes(b"synthetic executable")
            (build / package.ROM_CONFIG_NAME).write_bytes(b"generated rom config")
            catalog = build / "mods" / "preloaded" / "packages"
            catalog.mkdir(parents=True)
            (catalog / "catalog.json").write_bytes(b"{}\n")
            rom = root / package.ROM_NAME
            rom.write_bytes(b"synthetic rom data")
            output = root / "assembled"
            package.assemble(build, rom, output, "synthetic-clean-machine-test")
            archive = root / "UR-Recomp-Windows-x64.zip"
            checksum = root / "UR-Recomp-Windows-x64.zip.sha256"
            package.create_archive(output, archive)
            package.write_archive_checksum(archive, checksum)
            destination = root / "fresh install with spaces"
            cmd = [
                pwsh, "-NoProfile", "-NonInteractive",
                "-File", str(SCRIPT), "-Archive", str(archive),
                "-Checksum", str(checksum), "-Destination", str(destination),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("UR_PORTABLE_ARCHIVE_VERIFIED", result.stdout)
            self.assertIn("UR_PORTABLE_MANIFEST_VERIFIED", result.stdout)
            self.assertIn("UR_PORTABLE_CLEAN_MACHINE_PACKAGE_OK", result.stdout)
            self.assertTrue(
                (destination / package.ARCHIVE_ROOT / package.EXE_NAME).is_file()
            )
            # A second extraction to the same location must refuse overlay.
            again = subprocess.run(cmd, capture_output=True, text=True, check=False)
            self.assertNotEqual(again.returncode, 0)
            self.assertIn("Destination already exists", again.stderr)
            # Re-sign a deliberately invalid ZIP with a self-consistent
            # manifest and checksum. The verifier must independently enforce
            # that legacy mutable mod selections are never shipped.
            mutable_path = "mods/preloaded/state.toml"
            mutable_bytes = b"enabled = true\\n"
            (output / mutable_path).write_bytes(mutable_bytes)
            manifest_path = output / "PACKAGE-MANIFEST.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["files"].append({
                "path": mutable_path,
                "size": len(mutable_bytes),
                "sha256": hashlib.sha256(mutable_bytes).hexdigest(),
            })
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zipped:
                for member in sorted(output.rglob("*")):
                    if member.is_file():
                        zipped.write(member, f"{package.ARCHIVE_ROOT}/{member.relative_to(output).as_posix()}")
            checksum.write_text(
                f"{hashlib.sha256(archive.read_bytes()).hexdigest()}  {archive.name}\\n",
                encoding="ascii",
            )
            forged_destination = root / "signed mutable state must fail"
            forged_cmd = cmd[:-1] + [str(forged_destination)]
            forged = subprocess.run(
                forged_cmd, capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(forged.returncode, 0)
            self.assertIn("Mutable mod-selection state must not be shipped", forged.stderr)
            # Bad checksum must be rejected before extraction creates its root.
            checksum.write_text(
                "0" * 64 + "  " + archive.name + "\n",
                encoding="ascii", newline="\n",
            )
            bad_destination = root / "must remain absent"
            bad_cmd = cmd[:-1] + [str(bad_destination)]
            tampered = subprocess.run(
                bad_cmd, capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(tampered.returncode, 0)
            self.assertIn("Release ZIP does not match", tampered.stderr)
            self.assertFalse(bad_destination.exists())

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

    def test_mutable_legacy_mod_state_is_rejected_by_standalone_verifier(self):
        # The assembler excludes this old package-local selection file. The
        # offline verifier must independently reject a forged, self-consistent
        # archive/manifest instead of treating it as ordinary mods/** data.
        self.assertIn("if ($relative -ceq 'mods/preloaded/state.toml')", self.script)
        self.assertIn(
            'Mutable mod-selection state must not be shipped in the package',
            self.script,
        )
        self.assertLess(
            self.script.index("if ($relative -ceq 'mods/preloaded/state.toml')"),
            self.script.index('Get-FileHash -LiteralPath $member'),
        )

    def test_success_artifact_contains_standalone_verifier(self):
        workflow = (ROOT / ".github/workflows/windows-native-smoke.yml").read_text()
        copy = workflow.index('cp "$GITHUB_WORKSPACE/tools/Test-URRecompPortable.ps1"')
        upload = workflow.index("- name: Upload portable Windows package")
        self.assertLess(copy, upload)
        consumer_upload = workflow[upload:]
        for item in (
            "UR-Recomp-Windows-x64.zip",
            "UR-Recomp-Windows-x64.zip.sha256",
            "Test-URRecompPortable.ps1",
            "if: success()",
        ):
            self.assertIn(item, consumer_upload)
        self.assertIn("includes", self.instructions)
        self.assertIn("Test-URRecompPortable.ps1", self.instructions)

    def test_launch_is_optional_and_does_not_change_default_user_storage(self):
        self.assertIn("[switch]$Launch", self.script)
        self.assertIn("if ($Launch -or", self.script)
        self.assertIn("UR_RECOMP_USER_DATA_ROOT", self.script)
        self.assertIn("isolated-user-data", self.script)
        self.assertIn("unrelated launch working directory", self.script)
        self.assertIn("diagnostics\\startup.log", self.script)
        self.assertIn("actual Windows desktop", self.instructions)
        self.assertIn("no claim of a verified clean", self.instructions.lower())


if __name__ == "__main__":
    unittest.main()
