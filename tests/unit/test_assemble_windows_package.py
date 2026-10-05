import json
import pathlib
import subprocess
import sys
import tempfile
import zipfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "assemble_windows_package.py"


class WindowsPackageTests(unittest.TestCase):
    def make_inputs(self, root: pathlib.Path):
        build = root / "build"
        build.mkdir()
        (build / "UniracersSNESRecomp.exe").write_bytes(b"exe")
        (build / "rom.cfg").write_text("rom config\n")
        mods = build / "mods" / "preloaded" / "packages"
        mods.mkdir(parents=True)
        (mods / "catalog.json").write_text("{}\n")
        rom = root / "Uniracers_USA.sfc"
        rom.write_bytes(b"rom")
        return build, rom

    def run_tool(self, *args, check=True):
        return subprocess.run(
            [sys.executable, str(TOOL), *map(str, args)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=check,
        )

    def test_assemble_verify_and_clean_stale_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            build, rom = self.make_inputs(root)
            package = root / "package"
            package.mkdir()
            (package / "stale.txt").write_text("stale")

            result = self.run_tool(
                "assemble",
                "--build-dir", build,
                "--rom", rom,
                "--output", package,
                "--source-revision", "abc123",
            )
            self.assertIn("WINDOWS_PACKAGE_ASSEMBLED", result.stdout)
            self.assertFalse((package / "stale.txt").exists())
            self.assertTrue((package / "run-uniracers.cmd").is_file())
            launcher = (package / "run-uniracers.cmd").read_text()
            self.assertIn(
                '"UniracersSNESRecomp.exe" "Uniracers_USA.sfc" %*',
                launcher,
            )
            self.assertIn(
                "UR-STARTUP-ROM-MISSING: packaged ROM is missing",
                launcher,
            )
            self.assertIn("UR-STARTUP-RUNTIME-DATA", launcher)
            self.assertIn("UR-STARTUP-SAVE-ROOT", launcher)
            self.assertIn(
                "set \"UR_RECOMP_USER_DATA_ROOT=%APPDATA%\\gamesbyian\\UR-Recomp\"",
                launcher,
            )
            self.assertIn(
                "set \"SNESRECOMP_USER_DATA_DIR=%UR_RECOMP_USER_DATA_ROOT%\"",
                launcher,
            )
            self.assertIn(
                "set \"SNESRECOMP_MOD_STATE_PATH=%UR_RECOMP_USER_DATA_ROOT%\\mod-state.toml\"",
                launcher,
            )
            self.assertIn(
                'if exist "config.ini" if not exist '
                '"%UR_RECOMP_USER_DATA_ROOT%\\config.ini"',
                launcher,
            )
            self.assertIn(
                'if exist "keybinds.ini" if not exist '
                '"%UR_RECOMP_USER_DATA_ROOT%\\keybinds.ini"',
                launcher,
            )
            self.assertIn(
                'if exist "saves\\" if not exist '
                '"%UR_RECOMP_USER_DATA_ROOT%\\saves\\"',
                launcher,
            )
            self.assertIn(
                'if exist "mods\\preloaded\\state.toml" if not exist '
                '"%UR_RECOMP_USER_DATA_ROOT%\\mod-state.toml"',
                launcher,
            )
            self.assertIn("exit /b %ERRORLEVEL%", launcher)

            manifest = json.loads(
                (package / "PACKAGE-MANIFEST.json").read_text()
            )
            self.assertEqual(
                manifest["package_format"],
                "ur-recomp-windows-x64-portable-v1",
            )
            self.assertEqual(manifest["source_revision"], "abc123")
            paths = {entry["path"] for entry in manifest["files"]}
            self.assertIn("UniracersSNESRecomp.exe", paths)
            self.assertIn("Uniracers_USA.sfc", paths)
            self.assertIn("mods/preloaded/packages/catalog.json", paths)

            verify = self.run_tool("verify", "--package", package)
            self.assertIn("WINDOWS_PACKAGE_VERIFIED", verify.stdout)

            archive1 = root / "package-1.zip"
            archive2 = root / "package-2.zip"
            archived = self.run_tool(
                "archive", "--package", package, "--output", archive1
            )
            self.assertIn("WINDOWS_PACKAGE_ARCHIVED", archived.stdout)
            self.run_tool(
                "archive", "--package", package, "--output", archive2
            )
            self.assertEqual(archive1.read_bytes(), archive2.read_bytes())
            verified_archive = self.run_tool(
                "verify-archive", "--archive", archive1
            )
            self.assertIn(
                "WINDOWS_PACKAGE_ARCHIVE_VERIFIED",
                verified_archive.stdout,
            )
            with zipfile.ZipFile(archive1) as package_zip:
                names = package_zip.namelist()
            self.assertIn(
                "UR-Recomp-Windows-x64/PACKAGE-MANIFEST.json", names
            )
            self.assertIn(
                "UR-Recomp-Windows-x64/UniracersSNESRecomp.exe", names
            )

            (package / "Uniracers_USA.sfc").write_bytes(b"tampered")
            failed = self.run_tool(
                "verify", "--package", package, check=False
            )
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn(
                "package contents do not match", failed.stderr
            )

    def test_missing_required_input_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            build, rom = self.make_inputs(root)
            (build / "rom.cfg").unlink()
            result = self.run_tool(
                "assemble",
                "--build-dir", build,
                "--rom", rom,
                "--output", root / "package",
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("required package input missing", result.stderr)


if __name__ == "__main__":
    unittest.main()
