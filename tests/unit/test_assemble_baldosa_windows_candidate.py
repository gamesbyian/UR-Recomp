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
                # A Windows-produced ROM-free ZIP is now reproducible with
                # exactly the same central-directory creator bytes on Linux.
                self.assertEqual(
                    [item.create_system for item in archive.infolist()],
                    [0] * len(names),
                )
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
                self.assertIn("Quick Practice enters the original courses", readme)
                self.assertIn("secret Hunter stays closed", readme)
                self.assertIn("Practice cannot publish career Records or runs", readme)
                self.assertIn("Options changes Display, VSync and Volume", readme)
                self.assertIn("options-v1.txt", readme)
                self.assertNotIn("native Options remain pending", readme)
                self.assertNotIn("Practice and Options are not yet integrated", readme)
                self.assertIn("scripted-input native Windows 1P Race", readme)
                self.assertIn("reopened it in a fresh game", readme)
                self.assertIn("2P Race also published a paired match", readme)
                self.assertIn("strict original/native event", readme)
                self.assertNotIn("played 2P fresh-process", readme)
                self.assertNotIn("a real complete Windows event and fresh-process", readme)
                self.assertIn("FIRST-TIME RACER SETUP", readme)
                self.assertIn("gamepad X or keyboard X", readme)
                self.assertIn("automatically restarts the game ONCE", readme)
                self.assertIn("INTERRUPTED FIRST-CREATE RECOVERY", readme)
                self.assertIn("explicitly choose the SAME preset", readme)
                self.assertIn("General recovery of a corrupt", readme)
                self.assertIn("save exits with code 8", readme)
                self.assertIn("exits 7 without a second prompt", readme)
                self.assertNotIn("explicit recovery is not yet implemented", readme)
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
        # Textual package-path checks are insufficient when a junction
        # outside the bundle resolves back into the extracted executable.
        self.assertIn("[IO.FileAttributes]::ReparsePoint", script)
        self.assertIn("Get-Item -LiteralPath $walk", script)
        self.assertIn("GetDirectoryName($walk)", script)
        self.assertLess(script.index("ReparsePoint"),
                        script.index("Get-FileHash"))
        self.assertIn("package-local user-data root", script)
        self.assertIn("UR-BALDOSA-STARTUP-ROM-INVALID", script)
        self.assertIn("if errorlevel 3", script)
        self.assertIn("if errorlevel 2", script)
        self.assertIn('if "%ERRORLEVEL%"=="7"', script)
        self.assertIn('if "%ERRORLEVEL%"=="8" goto UR-BALDOSA-SAVE-FAILURE', script)
        self.assertIn('if "%ERRORLEVEL%"=="9" goto UR-BALDOSA-SWITCH-FAILURE', script)
        self.assertIn("UR-BALDOSA-SWITCH-FAILED: The current racer was saved", script)
        self.assertIn("exit /b 9", script)
        self.assertIn(':UR-BALDOSA-SAVE-FAILURE', script)
        self.assertIn("UR-BALDOSA-SAVE-FAILED: This game session", script)
        self.assertIn("exit /b 8", script)
        self.assertLess(script.index('if "%ERRORLEVEL%"=="8"'),
                        script.index("exit /b %ERRORLEVEL%"))
        self.assertIn("UR-BALDOSA-STARTUP-PROFILE-REJECTED", script)
        self.assertIn("Preserve both the raw save and Modern profile files", script)
        self.assertIn("exit /b 7", script)
        self.assertLess(script.index('if "%ERRORLEVEL%"=="7"'),
                        script.index("exit /b %ERRORLEVEL%"))
        self.assertEqual(script.count("exit /b %ERRORLEVEL%"), 1)
        self.assertIn('set "UR_BALDOSA_FIRST_RACER_RELAUNCH=0"', script)
        self.assertIn(':UR-BALDOSA-NATIVE-START', script)
        self.assertIn('goto UR-BALDOSA-REBOOT-FIRST-RACER', script)
        self.assertIn('goto UR-BALDOSA-NATIVE-START', script)
        self.assertIn('if not "%~1"=="" set "UR_BALDOSA_FIRST_RACER_RELAUNCH=0"', script)
        # One original first-racer restart and one consented recovery restart,
        # both through the same game process entrypoint. No unbounded loop.
        self.assertEqual(script.count('goto UR-BALDOSA-NATIVE-START'), 2)
        self.assertIn(':UR-BALDOSA-RECOVERY-MENU', script)
        self.assertIn('choice.exe /c RTSQ /n', script)
        self.assertIn("May include newer progress", script)
        self.assertIn("May lose recent progress", script)
        self.assertIn("Safest if uncertain", script)
        self.assertIn('UR_BALDOSA_RECOVERY_ACTION=raw', script)
        self.assertIn('UR_BALDOSA_RECOVERY_ACTION=typed', script)
        self.assertIn('UR_BALDOSA_RECOVERY_ACTION=healthy', script)
        # A successful repair launches exactly one fresh original process.
        # Another refusal must not re-open an unbounded recovery menu.
        self.assertIn('set "UR_BALDOSA_RECOVERY_ATTEMPTED=0"', script)
        self.assertIn('set "UR_BALDOSA_RECOVERY_ATTEMPTED=1"', script)
        self.assertIn('if "%UR_BALDOSA_RECOVERY_ATTEMPTED%"=="1"', script)
        self.assertIn("UR-BALDOSA-RECOVERY-RETRY-FAILED", script)
        self.assertLess(script.index('if "%UR_BALDOSA_RECOVERY_ATTEMPTED%"=="1"'),
                        script.index("choice.exe /c RTSQ"))
        self.assertLess(script.index('set "UR_BALDOSA_RECOVERY_ATTEMPTED=1"'),
                        script.rindex("goto UR-BALDOSA-NATIVE-START"))
        self.assertIn('type "%UR_RECOMP_USER_DATA_ROOT%\\profiles-v1.txt"', script)
        self.assertIn('Only the named target is validated', script)
        self.assertIn('if not "%~1"=="" (call :UR-BALDOSA-HOLD & exit /b 7)', script)
        self.assertIn('if defined UR_BALDOSA_NO_HOLD exit /b 7', script)
        self.assertIn('if not "%ERRORLEVEL%"=="89"', script)
        # R may fail before any archive, but T can write raw before journal
        # removal fails. A refusal cannot promise that no bytes changed.
        self.assertIn("Recovery did not complete; no safe relaunch was authorized", script)
        self.assertIn("Some files may already have been archived or restored", script)
        self.assertNotIn("No automatic replacement was made", script)
        self.assertLess(script.index('set "UR_BALDOSA_RECOVERY_ACTION="'),
                        script.index(':UR-BALDOSA-NATIVE-START'))
        self.assertLess(script.index(':UR-BALDOSA-RECOVERY-MENU'),
                        script.index('choice.exe /c RTSQ'))
        self.assertIn('CRASHED NAMED RACER RECOVERY', candidate.readme("test").decode("utf-8"))
        self.assertLess(script.index(':UR-BALDOSA-NATIVE-START'),
                        script.index(':UR-BALDOSA-REBOOT-FIRST-RACER'))
        self.assertNotIn("powershell.exe -ExecutionPolicy Bypass", script)
        self.assertNotIn("certutil -addstore", script)


    def test_launcher_user_data_root_requires_fully_qualified_path(self):
        script = candidate.launcher().decode("utf-8")
        self.assertEqual(script.count("[IO.Path]::IsPathRooted($d)"), 1)
        self.assertIn("[char]::IsLetter($d[0])", script)

        def ok(d):  # Python model of the launcher predicate
            sep = "\\/"
            drive = len(d) >= 3 and d[0].isalpha() and d[1] == ":" and d[2] in sep
            unc = len(d) >= 3 and d[0] == "\\" and d[1] == "\\" and d[2] not in sep
            return drive or unc

        for good in ("C:\\x", "C:/x", "\\\\server\\share", "\\\\?\\C:\\x"):
            self.assertTrue(ok(good), good)
        for bad in ("C:x", "\\x", "x", "\\\\\\x", "", "C:"):
            self.assertFalse(ok(bad), bad)

    def test_actual_no_args_launcher_autorestart_log_contract(self):
        from verify_baldosa_windows_extracted_launcher import (
            verify_first_user_cmd_relaunch_log,
        )
        valid = (
            "UR_BALDOSA_NATIVE_PROFILE DEFAULT no_host_state=1\n"
            "UR_BALDOSA_MODERN_ROOT opened=1\n"
            "UR_BALDOSA_MODERN_ROOT first_racer_opened=1 activation=next_process\n"
            "UR_BALDOSA_MODERN_ROOT noargs_launcher_gamepad "
            "profile=anonymous button=X\n"
            "UR_BALDOSA_NATIVE_FIRST_RACER status=0 preset=0 id=mike "
            "activation=next_process\n"
            "UR_BALDOSA_MODERN_ROOT first_racer_created=1 "
            "activation=next_process\n"
            "UR_BALDOSA_MODERN_ROOT noargs_launcher_gamepad "
            "profile=anonymous button=A\n"
            "UR_BALDOSA_MODERN_ROOT noargs_launcher_gamepad "
            "profile=anonymous button=B\n"
            "UR_BALDOSA_MODERN_ROOT noargs_launcher_gamepad "
            "profile=anonymous button=B\n"
            "UR_BALDOSA_MODERN_ROOT noargs_launcher_gamepad "
            "profile=anonymous button=A\n"
            "UR-BALDOSA-FIRST-RACER: Restarting with newly created racer.\n"
            "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike "
            "root=saves/profile-mike\n"
            "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=mike "
            "bytes=8192 fnv=12345678\n"
            "UR_BALDOSA_MODERN_ROOT opened=1\n"
            "UR_BALDOSA_MODERN_ROOT noargs_launcher_gamepad "
            "profile=mike button=B\n"
            "UR_BALDOSA_MODERN_ROOT noargs_launcher_gamepad "
            "profile=mike button=A\n"
        )
        verify_first_user_cmd_relaunch_log(valid)
        # subprocess supplies stdout then stderr, not their interleaved
        # chronology. Native event ordering is still strict; the .cmd echo
        # may appear first in the combined diagnostic without being a
        # premature game launch.
        cmd_echo = ("UR-BALDOSA-FIRST-RACER: Restarting with newly "
                    "created racer.\n")
        verify_first_user_cmd_relaunch_log(
            cmd_echo + valid.replace(cmd_echo, ""))
        for invalid in (
            valid.replace("status=0", "status=2"),
            valid.replace("profile=mike", "profile=other", 1),
            valid.replace("Restarting with newly created racer.",
                          "Skipped launcher restart."),
            valid.replace("first_racer_created=1",
                          "first_racer_created=0"),
            valid + valid,
            valid.replace("BOOT_SRAM profile=mike ", "BOOT_SRAM profile=other "),
            valid.replace("UR_BALDOSA_MODERN_ROOT opened=1\n", "", 1),
            valid.replace("UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike "
                          "root=saves/profile-mike\n",
                          ""),
        ):
            with self.subTest(invalid=invalid[-130:]):
                with self.assertRaises(ValueError):
                    verify_first_user_cmd_relaunch_log(invalid)


if __name__ == "__main__":
    unittest.main()
