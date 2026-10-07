import json
import hashlib
import pathlib
import subprocess
import sys
import tempfile
import zipfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "assemble_windows_package.py"
WORKFLOW = ROOT / ".github" / "workflows" / "windows-native-smoke.yml"
STARTUP_PATCH = ROOT / "tools" / "patches" / "snesrecomp-startup-failure-presentation.patch"


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

    def test_controller_startup_failure_has_specific_release_code(self):
        patch = STARTUP_PATCH.read_text()
        controller_anchor = "if (!snesrecomp_sdl_init(SDL_INIT_GAMECONTROLLER))"
        controller_return = 'return StartupFail(\n+        "UR-STARTUP-CONTROLLER", "controller", NULL,'
        self.assertEqual(patch.count(controller_anchor), 1)
        self.assertEqual(patch.count(controller_return), 1)
        controller_pos = patch.index(controller_anchor)
        code_pos = patch.index(controller_return)
        self.assertGreater(code_pos, controller_pos)
        self.assertLess(code_pos - controller_pos, 300)
        self.assertNotIn('"UR-STARTUP-UNKNOWN", "controller"', patch)
        self.assertNotIn('"UR-STARTUP-CONTROLLER", "video"', patch)
        self.assertNotIn('"UR-STARTUP-CONTROLLER", "audio"', patch)
        self.assertNotIn('"UR-STARTUP-CONTROLLER", "rom"', patch)
        self.assertNotIn('"UR-STARTUP-CONTROLLER", "save-root"', patch)

    def test_assemble_verify_and_clean_stale_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            build, rom = self.make_inputs(root)
            package = root / "package"
            package.mkdir()
            (package / "stale.txt").write_text("stale")

            # A dirty build tree may contain mutable runtime leftovers from a
            # developer launch. The consumer assembler must never absorb them.
            (build / "config.ini").write_text("build-local-config\n")
            (build / "keybinds.ini").write_text("build-local-keybinds\n")
            (build / "host-state-v1.txt").write_text("build-local-host-state\n")
            (build / "saves").mkdir()
            (build / "saves" / "dirty.srm").write_bytes(b"dirty-save")

            result = self.run_tool(
                "assemble",
                "--build-dir", build,
                "--rom", rom,
                "--output", package,
                "--source-revision", "abc123",
            )
            self.assertIn("WINDOWS_PACKAGE_ASSEMBLED", result.stdout)
            self.assertFalse((package / "stale.txt").exists())
            self.assertFalse((package / "config.ini").exists())
            self.assertFalse((package / "keybinds.ini").exists())
            self.assertFalse((package / "host-state-v1.txt").exists())
            self.assertFalse((package / "saves").exists())
            self.assertTrue((package / "run-uniracers.cmd").is_file())
            self.assertIn(
                "Source revision: abc123",
                (package / "README.txt").read_text(),
            )
            launcher = (package / "run-uniracers.cmd").read_text()
            readme = (package / "README.txt").read_text()
            self.assertIn("Do not overlay a new ZIP onto an old package tree.", readme)
            self.assertIn("Source revision: abc123", readme)
            self.assertIn("UR-STARTUP-*", readme)
            self.assertIn("Startup code guide:", readme)
            for startup_code in (
                "UR-STARTUP-ROM-MISSING",
                "UR-STARTUP-ROM-INVALID",
                "UR-STARTUP-RUNTIME-DATA",
                "UR-STARTUP-SAVE-ROOT",
                "UR-STARTUP-VIDEO",
                "UR-STARTUP-AUDIO",
                "UR-STARTUP-CONTROLLER",
            ):
                self.assertEqual(readme.count(startup_code), 1)
            self.assertNotIn("UR-STARTUP-UNKNOWN", readme)
            self.assertIn("diagnostics\\startup.log", readme)
            self.assertIn("no ROM bytes", readme)
            self.assertIn("save contents", readme)
            self.assertIn("profile names", readme)
            self.assertIn("controller input", readme)
            self.assertIn("setlocal DisableDelayedExpansion", launcher)
            self.assertIn(
                '"%~dp0UniracersSNESRecomp.exe" "%~dp0Uniracers_USA.sfc" %*',
                launcher,
            )
            self.assertIn(
                "UR-STARTUP-ROM-MISSING",
                launcher,
            )
            self.assertIn("UR-STARTUP-RUNTIME-DATA", launcher)
            self.assertIn(
                "Required package directory is empty: mods",
                launcher,
            )
            self.assertIn("UR-STARTUP-SAVE-ROOT", launcher)
            self.assertIn("diagnostics\\startup.log", launcher)
            self.assertIn("schema=ur-startup-log-v1", launcher)
            self.assertIn("build_revision=abc123", launcher)
            self.assertIn("architecture=x64", launcher)
            self.assertIn("SNESRECOMP_STARTUP_LOG", launcher)
            self.assertIn(":startup_fail", launcher)
            self.assertIn("process_exit=%UR_GAME_RC%", launcher)
            self.assertEqual(
                launcher.count(
                    '> "%UR_RECOMP_USER_DATA_ROOT%\\diagnostics\\startup.log" echo schema=ur-startup-log-v1'
                ),
                1,
            )
            self.assertEqual(
                launcher.count(
                    'set "SNESRECOMP_STARTUP_LOG=%UR_RECOMP_USER_DATA_ROOT%\\diagnostics\\startup.log"'
                ),
                1,
            )
            self.assertEqual(
                launcher.count(
                    'if defined UR_RECOMP_STARTUP_LOG >> "%UR_RECOMP_STARTUP_LOG%" echo process_exit=%UR_GAME_RC%'
                ),
                1,
            )
            startup_log_writes = [
                line
                for line in launcher.splitlines()
                if "startup.log" in line or "UR_RECOMP_STARTUP_LOG" in line
                if " echo " in line
            ]
            startup_log_text = "\n".join(startup_log_writes).lower()
            for forbidden in (
                "profile",
                "sram",
                "controller_input",
                "rom_bytes",
                "save_contents",
            ):
                self.assertNotIn(forbidden, startup_log_text)
            expected_log_keys = {
                "schema",
                "build_revision",
                "architecture",
                "subsystem",
                "package_root",
                "user_data_root",
                "result",
                "process_exit",
                "code",
            }
            observed_log_keys = set()
            for line in startup_log_writes:
                payload = line.split(" echo ", 1)[1]
                key = payload.split("=", 1)[0].strip().lower()
                observed_log_keys.add(key)
            self.assertEqual(observed_log_keys, expected_log_keys)
            self.assertIn(
                "set \"UR_RECOMP_USER_DATA_ROOT=%APPDATA%\\gamesbyian\\UR-Recomp\"",
                launcher,
            )
            self.assertIn(
                "set \"SNESRECOMP_USER_DATA_DIR=%UR_RECOMP_USER_DATA_ROOT%\"",
                launcher,
            )
            self.assertIn(
                'if "%UR_RECOMP_USER_DATA_ROOT:~1,2%"==":\\" goto user_root_ready',
                launcher,
            )
            self.assertIn(
                'if "%UR_RECOMP_USER_DATA_ROOT:~0,2%"=="\\\\" goto user_root_ready',
                launcher,
            )
            self.assertIn(
                "resolved user data root must be an absolute Windows path",
                launcher,
            )
            self.assertIn(
                "User data config.ini is a directory",
                launcher,
            )
            self.assertIn(
                "User data saves path is not a directory",
                launcher,
            )
            self.assertIn(
                "user data directory must be outside the extracted package",
                launcher,
            )
            self.assertIn(
                ":check_user_root_location",
                launcher,
            )
            self.assertIn(
                "cannot create the configured user data directory",
                launcher,
            )
            self.assertNotIn(
                "cannot create user data directory: %UR_RECOMP_USER_DATA_ROOT%",
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
            self.assertIn(
                'set "UR_MIGRATE_TOKEN=%RANDOM%-%RANDOM%"',
                launcher,
            )
            self.assertIn(
                'set "UR_MIGRATE_CONFIG=%UR_RECOMP_USER_DATA_ROOT%\\.ur-recomp-config.ini.%UR_MIGRATE_TOKEN%.migrate.tmp"',
                launcher,
            )
            self.assertIn(
                'set "UR_MIGRATE_SAVES=%UR_RECOMP_USER_DATA_ROOT%\\.ur-recomp-saves.%UR_MIGRATE_TOKEN%.migrate.tmp"',
                launcher,
            )
            self.assertIn(
                'mkdir "%UR_MIGRATE_SAVES%"',
                launcher,
            )
            self.assertIn(
                'ren "%UR_MIGRATE_SAVES%" "saves"',
                launcher,
            )
            self.assertIn(
                'ren "%UR_MIGRATE_CONFIG%" "config.ini"',
                launcher,
            )
            self.assertIn(
                '.ur-recomp-config.ini.migrate.tmp',
                launcher,
            )
            self.assertIn(
                '.ur-recomp-saves.migrate.tmp',
                launcher,
            )
            self.assertNotIn(
                '.ur-recomp-config.ini*.migrate.tmp',
                launcher,
            )
            self.assertNotIn(
                '.ur-recomp-saves*.migrate.tmp',
                launcher,
            )
            self.assertNotIn("move /y", launcher)
            self.assertNotIn("/h /k /y", launcher)
            self.assertIn('attrib -R "%UR_RECOMP_USER_DATA_ROOT%\\config.ini"', launcher)
            self.assertIn('attrib -R "%UR_RECOMP_USER_DATA_ROOT%\\keybinds.ini"', launcher)
            self.assertIn('attrib -R "%UR_RECOMP_USER_DATA_ROOT%\\mod-state.toml"', launcher)
            self.assertIn('attrib -R "%UR_RECOMP_USER_DATA_ROOT%\\saves\\*" /s /d', launcher)
            self.assertNotIn("UR_MIGRATE_FILE", launcher)
            self.assertNotIn("UR_MIGRATE_DIR", launcher)
            self.assertIn("exit /b %UR_GAME_RC%", launcher)

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

            manifest_path = package / "PACKAGE-MANIFEST.json"
            provenance_manifest = json.loads(manifest_path.read_text())
            provenance_manifest["source_revision"] = ""
            manifest_path.write_text(
                json.dumps(provenance_manifest, indent=2, sort_keys=True) + "\n"
            )
            provenance_failed = self.run_tool(
                "verify", "--package", package, check=False
            )
            self.assertNotEqual(provenance_failed.returncode, 0)
            self.assertIn(
                "unsupported or malformed package manifest",
                provenance_failed.stderr,
            )
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n"
            )

            mismatch_manifest = json.loads(json.dumps(manifest))
            mismatch_manifest["source_revision"] = "different-revision"
            manifest_path.write_text(
                json.dumps(mismatch_manifest, indent=2, sort_keys=True) + "\n"
            )
            mismatch_failed = self.run_tool(
                "verify", "--package", package, check=False
            )
            self.assertNotEqual(mismatch_failed.returncode, 0)
            self.assertIn(
                "README source revision does not match manifest",
                mismatch_failed.stderr,
            )
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n"
            )

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

            mismatch_archive = root / "package-mismatch-revision.zip"
            with zipfile.ZipFile(archive1, "r") as source, zipfile.ZipFile(
                mismatch_archive, "w", compression=zipfile.ZIP_DEFLATED
            ) as target:
                for info in source.infolist():
                    if info.filename.endswith("/PACKAGE-MANIFEST.json"):
                        archive_manifest = json.loads(
                            source.read(info.filename).decode("utf-8")
                        )
                        archive_manifest["source_revision"] = "different-revision"
                        target.writestr(
                            info,
                            json.dumps(
                                archive_manifest,
                                indent=2,
                                sort_keys=True,
                            ) + "\n",
                        )
                    else:
                        target.writestr(info, source.read(info.filename))
            mismatch_archive_result = self.run_tool(
                "verify-archive",
                "--archive", mismatch_archive,
                check=False,
            )
            self.assertNotEqual(mismatch_archive_result.returncode, 0)
            self.assertIn(
                "README source revision does not match manifest",
                mismatch_archive_result.stderr,
            )

            metadata_archive = root / "package-metadata-drift.zip"
            with zipfile.ZipFile(archive1, "r") as source, zipfile.ZipFile(
                metadata_archive, "w", compression=zipfile.ZIP_DEFLATED
            ) as target:
                for info in source.infolist():
                    payload = source.read(info.filename)
                    if info.filename.endswith("/README.txt"):
                        info.date_time = (2026, 1, 1, 0, 0, 0)
                    target.writestr(info, payload)
            metadata_result = self.run_tool(
                "verify-archive",
                "--archive", metadata_archive,
                check=False,
            )
            self.assertNotEqual(metadata_result.returncode, 0)
            self.assertIn(
                "package archive metadata is not normalized",
                metadata_result.stderr,
            )

            with zipfile.ZipFile(archive1) as package_zip:
                names = package_zip.namelist()
            self.assertIn(
                "UR-Recomp-Windows-x64/PACKAGE-MANIFEST.json", names
            )
            self.assertIn(
                "UR-Recomp-Windows-x64/UniracersSNESRecomp.exe", names
            )

            missing_exe_archive = root / "package-missing-exe.zip"
            missing_exe_manifest = json.loads(json.dumps(manifest))
            missing_exe_manifest["files"] = [
                entry for entry in missing_exe_manifest["files"]
                if entry["path"] != "UniracersSNESRecomp.exe"
            ]
            with zipfile.ZipFile(archive1, "r") as source, zipfile.ZipFile(
                missing_exe_archive, "w", compression=zipfile.ZIP_DEFLATED
            ) as target:
                for info in source.infolist():
                    if info.filename.endswith("/UniracersSNESRecomp.exe"):
                        continue
                    if info.filename.endswith("/PACKAGE-MANIFEST.json"):
                        target.writestr(
                            info,
                            json.dumps(
                                missing_exe_manifest,
                                indent=2,
                                sort_keys=True,
                            ) + "\n",
                        )
                    else:
                        target.writestr(info, source.read(info.filename))
            missing_exe = self.run_tool(
                "verify-archive",
                "--archive", missing_exe_archive,
                check=False,
            )
            self.assertNotEqual(missing_exe.returncode, 0)
            self.assertIn(
                "required archive package files missing: "
                "UniracersSNESRecomp.exe",
                missing_exe.stderr,
            )

            empty_mods_archive = root / "package-empty-mods.zip"
            empty_mods_manifest = json.loads(json.dumps(manifest))
            empty_mods_manifest["files"] = [
                entry for entry in empty_mods_manifest["files"]
                if not entry["path"].startswith("mods/")
            ]
            with zipfile.ZipFile(archive1, "r") as source, zipfile.ZipFile(
                empty_mods_archive, "w", compression=zipfile.ZIP_DEFLATED
            ) as target:
                for info in source.infolist():
                    if "/mods/" in info.filename:
                        continue
                    if info.filename.endswith("/PACKAGE-MANIFEST.json"):
                        target.writestr(
                            info,
                            json.dumps(
                                empty_mods_manifest,
                                indent=2,
                                sort_keys=True,
                            ) + "\n",
                        )
                    else:
                        target.writestr(info, source.read(info.filename))
            empty_mods = self.run_tool(
                "verify-archive",
                "--archive", empty_mods_archive,
                check=False,
            )
            self.assertNotEqual(empty_mods.returncode, 0)
            self.assertIn(
                "archive package mods directory is empty",
                empty_mods.stderr,
            )

            duplicate_manifest_archive = root / "package-duplicate-manifest.zip"
            duplicate_manifest = json.loads(json.dumps(manifest))
            duplicate_entry = next(
                entry for entry in duplicate_manifest["files"]
                if entry["path"] == "UniracersSNESRecomp.exe"
            )
            duplicate_manifest["files"].append(dict(duplicate_entry))
            with zipfile.ZipFile(archive1, "r") as source, zipfile.ZipFile(
                duplicate_manifest_archive,
                "w",
                compression=zipfile.ZIP_DEFLATED,
            ) as target:
                for info in source.infolist():
                    if info.filename.endswith("/PACKAGE-MANIFEST.json"):
                        target.writestr(
                            info,
                            json.dumps(
                                duplicate_manifest,
                                indent=2,
                                sort_keys=True,
                            ) + "\n",
                        )
                    else:
                        target.writestr(info, source.read(info.filename))
            duplicate_manifest_result = self.run_tool(
                "verify-archive",
                "--archive", duplicate_manifest_archive,
                check=False,
            )
            self.assertNotEqual(duplicate_manifest_result.returncode, 0)
            self.assertIn(
                "duplicate package archive manifest path: "
                "UniracersSNESRecomp.exe",
                duplicate_manifest_result.stderr,
            )

            unsafe_manifest_archive = root / "package-unsafe-manifest.zip"
            unsafe_manifest = json.loads(json.dumps(manifest))
            unsafe_manifest["files"][0]["path"] = "../escape.bin"
            with zipfile.ZipFile(archive1, "r") as source, zipfile.ZipFile(
                unsafe_manifest_archive,
                "w",
                compression=zipfile.ZIP_DEFLATED,
            ) as target:
                for info in source.infolist():
                    if info.filename.endswith("/PACKAGE-MANIFEST.json"):
                        target.writestr(
                            info,
                            json.dumps(
                                unsafe_manifest,
                                indent=2,
                                sort_keys=True,
                            ) + "\n",
                        )
                    else:
                        target.writestr(info, source.read(info.filename))
            unsafe_manifest_result = self.run_tool(
                "verify-archive",
                "--archive", unsafe_manifest_archive,
                check=False,
            )
            self.assertNotEqual(unsafe_manifest_result.returncode, 0)
            self.assertIn(
                "unsafe package archive manifest path: ../escape.bin",
                unsafe_manifest_result.stderr,
            )

            (package / "Uniracers_USA.sfc").write_bytes(b"tampered")
            failed = self.run_tool(
                "verify", "--package", package, check=False
            )
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn(
                "package contents do not match", failed.stderr
            )

    def test_archive_checksum_sidecar_is_canonical(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            build, rom = self.make_inputs(root)
            package = root / "package"
            self.run_tool(
                "assemble",
                "--build-dir", build,
                "--rom", rom,
                "--output", package,
                "--source-revision", "test-revision",
            )

            archive = root / "UR-Recomp-Windows-x64.zip"
            self.run_tool("archive", "--package", package, "--output", archive)

            sidecar = root / "UR-Recomp-Windows-x64.zip.sha256"
            result = self.run_tool(
                "checksum-archive",
                "--archive", archive,
                "--output", sidecar,
            )
            expected = hashlib.sha256(archive.read_bytes()).hexdigest()
            self.assertEqual(
                sidecar.read_text(encoding="ascii"),
                f"{expected}  {archive.name}\n",
            )
            self.assertIn(
                f"WINDOWS_PACKAGE_ARCHIVE_SHA256 sha256={expected}",
                result.stdout,
            )

    def test_archive_checksum_sidecar_verifies_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            build, rom = self.make_inputs(root)
            package = root / "package"
            self.run_tool(
                "assemble",
                "--build-dir", build,
                "--rom", rom,
                "--output", package,
                "--source-revision", "test-revision",
            )
            archive = root / "UR-Recomp-Windows-x64.zip"
            sidecar = root / "UR-Recomp-Windows-x64.zip.sha256"
            self.run_tool("archive", "--package", package, "--output", archive)
            self.run_tool(
                "checksum-archive",
                "--archive", archive,
                "--output", sidecar,
            )

            verified = self.run_tool(
                "verify-archive-checksum",
                "--archive", archive,
                "--checksum", sidecar,
            )
            self.assertIn(
                "WINDOWS_PACKAGE_ARCHIVE_SHA256_VERIFIED",
                verified.stdout,
            )

            original = sidecar.read_text(encoding="ascii")

            wrong_archive_name = "XR-Recomp-Windows-x64.zip"
            self.assertEqual(len(wrong_archive_name), len(archive.name))
            sidecar.write_text(
                original.replace(archive.name, wrong_archive_name),
                encoding="ascii",
                newline="\n",
            )
            wrong_name = self.run_tool(
                "verify-archive-checksum",
                "--archive", archive,
                "--checksum", sidecar,
                check=False,
            )
            self.assertNotEqual(wrong_name.returncode, 0)
            self.assertIn(
                "archive checksum does not identify this archive",
                wrong_name.stderr,
            )

            sidecar.write_text(
                "A" + original[1:],
                encoding="ascii",
                newline="\n",
            )
            uppercase = self.run_tool(
                "verify-archive-checksum",
                "--archive", archive,
                "--checksum", sidecar,
                check=False,
            )
            self.assertNotEqual(uppercase.returncode, 0)
            self.assertIn(
                "archive checksum does not identify this archive",
                uppercase.stderr,
            )

            sidecar.write_text(
                "0" * 64 + "  " + archive.name + "\n",
                encoding="ascii",
                newline="\n",
            )
            mismatch = self.run_tool(
                "verify-archive-checksum",
                "--archive", archive,
                "--checksum", sidecar,
                check=False,
            )
            self.assertNotEqual(mismatch.returncode, 0)
            self.assertIn(
                "archive checksum does not match package archive",
                mismatch.stderr,
            )

            sidecar.write_text(
                original.replace("\n", "\r\n"),
                encoding="ascii",
                newline="",
            )
            crlf = self.run_tool(
                "verify-archive-checksum",
                "--archive", archive,
                "--checksum", sidecar,
                check=False,
            )
            self.assertNotEqual(crlf.returncode, 0)
            self.assertIn(
                "archive checksum must be one canonical LF-terminated line",
                crlf.stderr,
            )

            sidecar.write_text(
                original + "extra\n",
                encoding="ascii",
                newline="\n",
            )
            extra_line = self.run_tool(
                "verify-archive-checksum",
                "--archive", archive,
                "--checksum", sidecar,
                check=False,
            )
            self.assertNotEqual(extra_line.returncode, 0)
            self.assertIn(
                "archive checksum must be one canonical LF-terminated line",
                extra_line.stderr,
            )

    def test_archive_checksum_verifier_fails_closed_for_missing_sidecar(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            archive = root / "UR-Recomp-Windows-x64.zip"
            archive.write_bytes(b"archive")
            result = self.run_tool(
                "verify-archive-checksum",
                "--archive", archive,
                "--checksum", root / "missing.sha256",
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("archive checksum missing", result.stderr)

    def test_archive_checksum_fails_closed_for_missing_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            result = self.run_tool(
                "checksum-archive",
                "--archive", root / "missing.zip",
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("package archive missing", result.stderr)


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
                "--source-revision", "test-revision",
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("required package input missing", result.stderr)


    def test_empty_mod_payload_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            build, rom = self.make_inputs(root)
            for path in (build / "mods").rglob("*"):
                if path.is_file():
                    path.unlink()
            result = self.run_tool(
                "assemble",
                "--build-dir", build,
                "--rom", rom,
                "--output", root / "package",
                "--source-revision", "test-revision",
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("required package input empty", result.stderr)


    def test_destructive_output_paths_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            build, rom = self.make_inputs(root)

            result = self.run_tool(
                "assemble",
                "--build-dir", build,
                "--rom", rom,
                "--output", root,
                "--source-revision", "test-revision",
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "package output must be outside",
                result.stderr,
            )
            self.assertTrue((build / "UniracersSNESRecomp.exe").is_file())
            self.assertTrue(rom.is_file())

            output_file = root / "package-as-file"
            output_file.write_text("not a directory")
            output_file_result = self.run_tool(
                "assemble",
                "--build-dir", build,
                "--rom", rom,
                "--output", output_file,
                "--source-revision", "test-revision",
                check=False,
            )
            self.assertNotEqual(output_file_result.returncode, 0)
            self.assertIn(
                "package output exists and is not a directory",
                output_file_result.stderr,
            )
            self.assertEqual(output_file.read_text(), "not a directory")

            package = root / "safe-package"
            self.run_tool(
                "assemble",
                "--build-dir", build,
                "--rom", rom,
                "--output", package,
                "--source-revision", "test-revision",
            )
            inside_archive = package / "inside.zip"
            archived = self.run_tool(
                "archive",
                "--package", package,
                "--output", inside_archive,
                check=False,
            )
            self.assertNotEqual(archived.returncode, 0)
            self.assertIn(
                "package archive must be written outside the package tree",
                archived.stderr,
            )
            self.assertFalse(inside_archive.exists())

            archive_dir = root / "archive-as-directory.zip"
            archive_dir.mkdir()
            archive_dir_result = self.run_tool(
                "archive",
                "--package", package,
                "--output", archive_dir,
                check=False,
            )
            self.assertNotEqual(archive_dir_result.returncode, 0)
            self.assertIn(
                "package archive output exists and is not a file",
                archive_dir_result.stderr,
            )
            self.assertTrue(archive_dir.is_dir())

            verified = self.run_tool("verify", "--package", package)
            self.assertIn("WINDOWS_PACKAGE_VERIFIED", verified.stdout)


    def test_windows_workflow_verifies_canonical_rom_before_assembly(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        verify = workflow.index(
            'python tools/verify_rom.py "reference/roms/retail/Uniracers_USA.sfc"'
        )
        assemble = workflow.index(
            "python tools/assemble_windows_package.py assemble"
        )
        self.assertLess(verify, assemble)


    def test_windows_workflow_proves_archive_identity_before_upload(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        archive = workflow.index(
            "python tools/assemble_windows_package.py archive"
        )
        verify = workflow.index(
            "python tools/assemble_windows_package.py verify-archive",
            archive,
        )
        repro = workflow.index(
            'REPRO_ARCHIVE="$RUNNER_TEMP/UR-Recomp-Windows-x64-repro.zip"',
            verify,
        )
        compare = workflow.index('cmp "$ARCHIVE" "$REPRO_ARCHIVE"', repro)
        checksum = workflow.index(
            "python tools/assemble_windows_package.py checksum-archive",
            compare,
        )
        checksum_verify = workflow.index(
            "python tools/assemble_windows_package.py verify-archive-checksum",
            checksum,
        )
        upload = workflow.index("name: Upload Windows evidence", checksum_verify)
        self.assertLess(archive, verify)
        self.assertLess(verify, repro)
        self.assertLess(repro, compare)
        self.assertLess(compare, checksum)
        self.assertLess(checksum, checksum_verify)
        self.assertLess(checksum_verify, upload)
        self.assertIn("UR-Recomp-Windows-x64.zip.sha256", workflow)


    def test_missing_source_revision_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            build, rom = self.make_inputs(root)
            result = self.run_tool(
                "assemble",
                "--build-dir", build,
                "--rom", rom,
                "--output", root / "package",
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "source revision is required for a shippable package",
                result.stderr,
            )

            multiline = self.run_tool(
                "assemble",
                "--build-dir", build,
                "--rom", rom,
                "--output", root / "package-multiline",
                "--source-revision", "abc123\nspoofed",
                check=False,
            )
            self.assertNotEqual(multiline.returncode, 0)
            self.assertIn(
                "source revision is required for a shippable package",
                multiline.stderr,
            )

            tabbed = self.run_tool(
                "assemble",
                "--build-dir", build,
                "--rom", rom,
                "--output", root / "package-tabbed",
                "--source-revision", "abc123\tspoofed",
                check=False,
            )
            self.assertNotEqual(tabbed.returncode, 0)
            self.assertIn(
                "source revision is required for a shippable package",
                tabbed.stderr,
            )



if __name__ == "__main__":
    unittest.main()
