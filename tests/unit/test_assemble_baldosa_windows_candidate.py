#!/usr/bin/env python3
"""Consumer-facing invariants for ROMless native Windows candidate."""
import json
import struct
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import assemble_baldosa_windows_candidate as candidate


def fake_x64_pe(path: Path) -> None:
    # Structural PE gate only: never claims this test fixture is executable.
    blob = bytearray(65537)
    blob[:2] = b"MZ"
    struct.pack_into("<I", blob, 0x3c, 128)
    blob[128:132] = b"PE\x00\x00"
    struct.pack_into("<H", blob, 132, 0x8664)
    struct.pack_into("<H", blob, 152, 0x20b)
    path.write_bytes(blob)


class BaldosaNativeWindowsCandidateTest(unittest.TestCase):
    def test_romless_archive_exact_contents_and_reproducibility(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            exe = root / candidate.EXE
            fake_x64_pe(exe)
            first = root / "candidate-1.zip"
            second = root / "candidate-2.zip"
            revision = "0123456789abcdef"
            a = candidate.create_candidate(exe, first, revision)
            b = candidate.create_candidate(exe, second, revision)
            self.assertEqual(a, b)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with zipfile.ZipFile(first) as archive:
                names = archive.namelist()
                self.assertEqual(
                    names,
                    sorted(candidate.PREFIX + name for name in (
                        candidate.EXE, candidate.LAUNCHER,
                        candidate.README, candidate.MANIFEST)))
                self.assertTrue(all(
                    zipfile.ZipInfo(name).filename.startswith(candidate.PREFIX)
                    for name in names))
                self.assertFalse(any(
                    name.lower().endswith((".sfc", ".smc", ".srm", ".urrun"))
                    for name in names))
                manifest = json.loads(archive.read(
                    candidate.PREFIX + candidate.MANIFEST))
                self.assertFalse(manifest["rom_bundled"])
                self.assertFalse(manifest["profile_data_bundled"])
                self.assertEqual(manifest["project_revision"], revision)
                for item in manifest["immutable_files"]:
                    payload = archive.read(candidate.PREFIX + item["path"])
                    self.assertEqual(len(payload), item["bytes"])
                    self.assertEqual(candidate.sha256(payload), item["sha256"])
                launcher = archive.read(
                    candidate.PREFIX + candidate.LAUNCHER).decode("utf-8")
                self.assertIn("SNESRECOMP_USER_DATA_DIR", launcher)
                self.assertIn("UR_BALDOSA_MODERN_ROOT=1", launcher)
                self.assertIn("UR_BALDOSA_MODERN_PROFILE_SELECT=1", launcher)
                self.assertIn("Get-FileHash", launcher)
                self.assertIn("UR-BALDOSA-STARTUP-ROM-MISSING", launcher)
                self.assertIn("--no-launcher", launcher)
                self.assertIn("$env:UR_BALDOSA_ROM", launcher)
                self.assertNotIn('copy /b', launcher.lower())
                readme = archive.read(
                    candidate.PREFIX + candidate.README).decode("utf-8")
                self.assertIn("NOT a completed remaster", readme)
                self.assertIn("historical runs read-only", readme)
                self.assertIn("source-confirmed 1P Race results", readme)
                self.assertIn("explicit recovery is not yet implemented", readme)
                self.assertNotIn("Practice, Records and Options are not yet", readme)
                self.assertIn(candidate.USA_SHA256, readme)
            with self.assertRaisesRegex(ValueError, "already exists"):
                candidate.create_candidate(exe, first, revision)

    def test_package_refuses_non_pe_missing_or_bad_revision(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            exe = root / candidate.EXE
            exe.write_bytes(b"not a native binary")
            for bad_revision in ("", " main", "main\n", "a" * 101):
                with self.subTest(bad_revision=bad_revision):
                    with self.assertRaises(ValueError):
                        candidate.payloads(exe, bad_revision)
            with self.assertRaises(ValueError):
                candidate.payloads(exe, "main")
            fake_x64_pe(exe)
            bad_name = root / "unexpected.exe"
            bad_name.write_bytes(exe.read_bytes())
            with self.assertRaisesRegex(ValueError, "non-symlink"):
                candidate.payloads(bad_name, "main")
            exe.unlink()
            exe.symlink_to(bad_name)
            with self.assertRaisesRegex(ValueError, "non-symlink"):
                candidate.payloads(exe, "main")

    def test_launcher_never_contains_rom_or_profile_data(self):
        script = candidate.launcher().decode("utf-8")
        self.assertTrue(script.startswith("@echo off\r\n"))
        self.assertIn("UR_EXECUTION_MODE=modern", script)
        self.assertIn("UR_BALDOSA_MODERN_INPUT=1", script)
        self.assertIn("UR_RECOMP_USER_DATA_ROOT", script)
        self.assertIn("APPDATA", script)
        self.assertIn("package-local user-data root", script)
        self.assertIn("UR-BALDOSA-STARTUP-ROM-INVALID", script)
        self.assertIn("if errorlevel 3", script)
        self.assertIn("if errorlevel 2", script)
        self.assertIn('if "%ERRORLEVEL%"=="7"', script)
        self.assertIn("UR-BALDOSA-STARTUP-PROFILE-REJECTED", script)
        self.assertIn("Preserve both the raw save and Modern profile files", script)
        self.assertIn("exit /b 7", script)
        self.assertLess(script.index('if "%ERRORLEVEL%"=="7"'),
                        script.index("exit /b %ERRORLEVEL%"))
        self.assertNotIn("powershell.exe -ExecutionPolicy Bypass", script)
        self.assertNotIn("certutil -addstore", script)


if __name__ == "__main__":
    unittest.main()
