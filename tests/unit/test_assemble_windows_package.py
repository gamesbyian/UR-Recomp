import json
import hashlib
import os
import shutil
import pathlib
import subprocess
import sys
import tempfile
import zipfile
import unittest

from tools import assemble_windows_package as package_tool


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

    def write_manifest(self, path, manifest):
        path.write_bytes(
            (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode(
                "utf-8"
            )
        )

    def run_tool(self, *args, check=True):
        return subprocess.run(
            [sys.executable, str(TOOL), *map(str, args)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=check,
        )

    def test_launcher_unc_pushd_has_one_cleanup_for_every_exit(self):
        launcher = package_tool.launcher_text("unc-cleanup-contract")
        self.assertIn('pushd "%~dp0" 2>nul', launcher)
        self.assertNotIn('cd /d "%~dp0"', launcher)
        # 31 guarded refusals plus the normal native-process exit.
        self.assertEqual(launcher.count("goto launcher_cleanup"), 35)
        self.assertEqual(launcher.count("exit /b "), 3)
        self.assertIn(
            ":launcher_cleanup\r\npopd\r\nexit /b %UR_GAME_RC%\r\n",
            launcher,
        )
        self.assertIn(
            "if errorlevel 1 (echo UR-STARTUP-RUNTIME-DATA: "
            "cannot enter the extracted package directory.",
            launcher,
        )

    def test_write_probe_uses_exclusive_directory_and_nonrecursive_cleanup(self):
        launcher = package_tool.launcher_text("exclusive-write-probe")
        self.assertIn('mkdir "%UR_WRITE_PROBE_DIR%" >nul 2>&1', launcher)
        self.assertIn('> "%UR_WRITE_PROBE_DIR%\\probe.tmp" echo writable', launcher)
        self.assertIn('rmdir "%UR_WRITE_PROBE_DIR%" >nul 2>&1', launcher)
        self.assertNotIn('> "%UR_WRITE_PROBE%" echo writable', launcher)
        self.assertNotIn('rmdir /s /q "%UR_WRITE_PROBE_DIR%"', launcher)


    def test_legacy_migration_refuses_occupied_staging_paths(self):
        launcher = package_tool.launcher_text("migration-stage-collision")
        for stage, source in (
            ("UR_MIGRATE_CONFIG", "config.ini"),
            ("UR_MIGRATE_KEYS", "keybinds.ini"),
            ("UR_MIGRATE_MOD", "mods\\preloaded\\state.toml"),
        ):
            with self.subTest(stage=stage):
                guard = f'if exist "%{stage}%" (call :startup_fail'
                copy = f'copy /b /y "{source}" "%{stage}%"'
                self.assertIn(guard, launcher)
                self.assertIn(copy, launcher)
                self.assertLess(launcher.index(guard), launcher.index(copy))
        self.assertIn(
            'mkdir "%UR_MIGRATE_SAVES%" >nul 2>&1\r\n'
            '  if errorlevel 1 (call :startup_fail',
            launcher,
        )

    def test_failed_legacy_migration_commit_cleans_exact_staging_path(self):
        launcher = package_tool.launcher_text("migration-cleanup")
        for stage, command, description in (
            ("UR_MIGRATE_CONFIG", "del /q", "config.ini"),
            ("UR_MIGRATE_KEYS", "del /q", "keybinds.ini"),
            ("UR_MIGRATE_SAVES", "rmdir /s /q", "saves"),
            ("UR_MIGRATE_MOD", "del /q", "mod-state"),
        ):
            with self.subTest(stage=stage):
                self.assertIn(
                    f'else ({command} "%{stage}%" >nul 2>&1 & '
                    f'call :startup_fail "UR-STARTUP-SAVE-ROOT" "save-root" '
                    f'"Could not commit legacy {description} migration."',
                    launcher,
                )

                self.assertIn(
                    f'  if errorlevel 1 ({command} "%{stage}%" >nul 2>&1 & '
                    f'call :startup_fail "UR-STARTUP-SAVE-ROOT" "save-root" '
                    f'"Could not commit legacy {description} migration."',
                    launcher,
                )

    def test_windows_launcher_restores_caller_cwd_on_success_and_refusal(self):
        # Real CMD process: a mapped UNC drive must be POPD-ed just as a
        # local PUSHD must restore the caller's original working directory.
        # This exercises both exit classes without requiring an SMB share.
        if os.name != "nt":
            self.skipTest("requires Windows cmd.exe")
        with tempfile.TemporaryDirectory() as tmp:
            base = pathlib.Path(tmp)
            payload = base / "portable & game! (source)"
            payload.mkdir()
            caller = base / "caller & shell!"
            caller.mkdir()
            user_data = base / "user & save!"
            attrib = pathlib.Path(os.environ["SystemRoot"]) / "System32" / "attrib.exe"
            shutil.copyfile(attrib, payload / package_tool.EXE_NAME)
            (payload / package_tool.ROM_NAME).write_bytes(b"synthetic-rom")
            (payload / "rom.cfg").write_bytes(package_tool.ROM_CONFIG_BYTES)
            catalog = payload / "mods" / "preloaded" / "packages"
            catalog.mkdir(parents=True)
            (catalog / ".gitkeep").touch()
            launcher = payload / package_tool.LAUNCHER_NAME
            package_tool.write_launcher(launcher, "cwd-restore-test")
            env = os.environ.copy()
            for case in ("success", "missing-rom", "root-inside-package"):
                with self.subTest(case=case):
                    env["UR_RECOMP_USER_DATA_ROOT"] = str(
                        payload / "forbidden" if case == "root-inside-package"
                        else user_data
                    )
                    if case == "missing-rom":
                        (payload / package_tool.ROM_NAME).unlink()
                    # Separate tokens avoid cmd.exe /C outer-quote removal
                    # for batch paths containing spaces and metacharacters.
                    proc = subprocess.run(
                        ["cmd.exe", "/d", "/c", "call", str(launcher), "&", "cd"],
                        cwd=caller, env=env, capture_output=True, text=True,
                        errors="replace", timeout=30, check=False,
                    )
                    self.assertTrue(proc.stdout.splitlines(), proc.stderr)
                    self.assertEqual(
                        proc.stdout.splitlines()[-1].casefold(),
                        str(caller).casefold(),
                        proc.stdout + proc.stderr,
                    )
                    if case == "missing-rom":
                        self.assertIn("UR-STARTUP-ROM-MISSING", proc.stderr)
                    elif case == "root-inside-package":
                        self.assertIn("UR-STARTUP-SAVE-ROOT", proc.stderr)
                    else:
                        self.assertIn(
                            "process_exit=0",
                            (user_data / "diagnostics" / "startup.log").read_text(
                                encoding="utf-8"
                            ),
                        )

    def test_windows_legacy_migration_rename_failure_removes_current_stage(self):
        # Exercise the real generated CMD control flow, injecting a failed
        # rename after successful staging. This is not an ACL integration test.
        if os.name != "nt":
            self.skipTest("requires Windows cmd.exe")
        cases = (
            ("UR_MIGRATE_CONFIG", "config.ini", "config.ini"),
            ("UR_MIGRATE_KEYS", "keybinds.ini", "keybinds.ini"),
            ("UR_MIGRATE_SAVES", "saves", "saves"),
            ("UR_MIGRATE_MOD", "mod-state.toml", "mods/preloaded/state.toml"),
        )
        with tempfile.TemporaryDirectory() as tmp:
            base = pathlib.Path(tmp)
            attrib = pathlib.Path(os.environ["SystemRoot"]) / "System32" / "attrib.exe"
            for stage, destination, legacy in cases:
                with self.subTest(stage=stage):
                    payload = base / stage / "portable"
                    payload.mkdir(parents=True)
                    user_data = base / stage / "persistent"
                    shutil.copyfile(attrib, payload / package_tool.EXE_NAME)
                    (payload / package_tool.ROM_NAME).write_bytes(b"synthetic-rom")
                    (payload / "rom.cfg").write_bytes(package_tool.ROM_CONFIG_BYTES)
                    catalog = payload / "mods" / "preloaded" / "packages"
                    catalog.mkdir(parents=True)
                    (catalog / ".gitkeep").touch()
                    legacy_path = payload.joinpath(*legacy.split("/"))
                    if legacy == "saves":
                        legacy_path.mkdir()
                        (legacy_path / "original.srm").write_bytes(b"original")
                    else:
                        legacy_path.parent.mkdir(parents=True, exist_ok=True)
                        legacy_path.write_bytes(b"original")
                    generated = package_tool.launcher_text("rename-failure-fixture")
                    needle = f'  ren "%{stage}%" "{destination}" >nul 2>&1\r\n'
                    self.assertEqual(generated.count(needle), 1)
                    generated = generated.replace(
                        needle, "  rem injected rename failure after staging\r\n"
                    )
                    launcher = payload / package_tool.LAUNCHER_NAME
                    launcher.write_bytes(generated.encode("utf-8"))
                    env = os.environ.copy()
                    env["UR_RECOMP_USER_DATA_ROOT"] = str(user_data)
                    proc = subprocess.run(
                        ["cmd.exe", "/d", "/c", "call", str(launcher)],
                        cwd=payload, env=env, capture_output=True, text=True,
                        errors="replace", timeout=30, check=False,
                    )
                    self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
                    self.assertIn("Could not commit legacy", proc.stderr)
                    self.assertFalse((user_data / destination).exists())
                    self.assertEqual(list(user_data.glob(".ur-recomp-*.migrate.tmp")), [])
                    self.assertTrue(legacy_path.exists())

        # The hosted Windows consumer selects this existing test explicitly.
        # Exercise the competing-destination race on the same real CMD path.
        self._assert_windows_legacy_migration_collision_rejects_other_writer()
        self._assert_windows_probe_collision_never_clobbers_user_file()
        self._assert_windows_preexisting_legacy_stage_survives()


    def _assert_windows_preexisting_legacy_stage_survives(self):
        if os.name != "nt":
            self.skipTest("requires Windows cmd.exe")
        cases = (
            ("config.ini", "config.ini", "config.ini", False),
            ("keybinds.ini", "keybinds.ini", "keybinds.ini", False),
            ("saves", "saves", "saves", True),
            ("mod-state.toml", "mods/preloaded/state.toml", "mod-state.toml", False),
        )
        with tempfile.TemporaryDirectory() as tmp:
            base = pathlib.Path(tmp)
            attrib = pathlib.Path(os.environ["SystemRoot"]) / "System32" / "attrib.exe"
            for stage, legacy, destination, is_directory in cases:
                with self.subTest(stage=stage):
                    payload = base / stage / "portable"
                    payload.mkdir(parents=True)
                    user_data = base / stage / "persistent"
                    user_data.mkdir()
                    shutil.copyfile(attrib, payload / package_tool.EXE_NAME)
                    (payload / package_tool.ROM_NAME).write_bytes(b"synthetic-rom")
                    (payload / "rom.cfg").write_bytes(package_tool.ROM_CONFIG_BYTES)
                    catalog = payload / "mods" / "preloaded" / "packages"
                    catalog.mkdir(parents=True)
                    (catalog / ".gitkeep").touch()
                    legacy_path = payload.joinpath(*legacy.split("/"))
                    legacy_path.parent.mkdir(parents=True, exist_ok=True)
                    if legacy == "saves":
                        legacy_path.mkdir()
                        (legacy_path / "original.srm").write_bytes(b"original")
                    else:
                        legacy_path.write_bytes(b"original")
                    token = "27182"
                    foreign = user_data / f".ur-recomp-{stage}.{token}-{token}.migrate.tmp"
                    sentinel = b"foreign stage must survive"
                    if is_directory:
                        foreign.mkdir()
                        (foreign / "sentinel.bin").write_bytes(sentinel)
                    else:
                        foreign.write_bytes(sentinel)
                    launcher = payload / package_tool.LAUNCHER_NAME
                    package_tool.write_launcher(launcher, "stage-collision-fixture")
                    env = os.environ.copy()
                    env["UR_RECOMP_USER_DATA_ROOT"] = str(user_data)
                    env["RANDOM"] = token
                    proc = subprocess.run(
                        ["cmd.exe", "/d", "/c", "call", str(launcher)],
                        cwd=payload, env=env, capture_output=True, text=True,
                        errors="replace", timeout=30, check=False,
                    )
                    self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
                    self.assertIn("UR-STARTUP-SAVE-ROOT", proc.stderr)
                    if is_directory:
                        self.assertEqual((foreign / "sentinel.bin").read_bytes(), sentinel)
                        self.assertEqual((legacy_path / "original.srm").read_bytes(), b"original")
                    else:
                        self.assertEqual(foreign.read_bytes(), sentinel)
                        self.assertEqual(legacy_path.read_bytes(), b"original")
                    self.assertFalse((user_data / destination).exists())

    def _assert_windows_probe_collision_never_clobbers_user_file(self):
        # The real CMD regression uses an explicit RANDOM environment value.
        # An existing user file with the same probe name must not be truncated.
        if os.name != "nt":
            self.skipTest("requires Windows cmd.exe")
        with tempfile.TemporaryDirectory() as tmp:
            base = pathlib.Path(tmp)
            payload = base / "portable"
            payload.mkdir()
            user_data = base / "persistent"
            user_data.mkdir()
            attrib = pathlib.Path(os.environ["SystemRoot"]) / "System32" / "attrib.exe"
            shutil.copyfile(attrib, payload / package_tool.EXE_NAME)
            (payload / package_tool.ROM_NAME).write_bytes(b"synthetic-rom")
            (payload / "rom.cfg").write_bytes(package_tool.ROM_CONFIG_BYTES)
            catalog = payload / "mods" / "preloaded" / "packages"
            catalog.mkdir(parents=True)
            (catalog / ".gitkeep").touch()
            launcher = payload / package_tool.LAUNCHER_NAME
            package_tool.write_launcher(launcher, "write-probe-collision-fixture")
            token = "27182"
            preexisting = user_data / f".ur-recomp-write-probe-{token}-{token}.tmp"
            sentinel = b"PREEXISTING USER DATA MUST SURVIVE\\r\\n"
            preexisting.write_bytes(sentinel)
            env = os.environ.copy()
            env["UR_RECOMP_USER_DATA_ROOT"] = str(user_data)
            env["RANDOM"] = token
            proc = subprocess.run(
                ["cmd.exe", "/d", "/c", "call", str(launcher)],
                cwd=payload, env=env, capture_output=True, text=True,
                errors="replace", timeout=30, check=False,
            )
            self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
            self.assertIn("UR-STARTUP-SAVE-ROOT", proc.stderr)
            self.assertEqual(preexisting.read_bytes(), sentinel)
            self.assertFalse((user_data / "diagnostics").exists())

    def _assert_windows_legacy_migration_collision_rejects_other_writer(self):
        # A second launcher creates the final name after our initial absent
        # check but before the staged rename. A failed rename must not be
        # mistaken for this process having committed its own migration.
        if os.name != "nt":
            self.skipTest("requires Windows cmd.exe")
        cases = (
            ("UR_MIGRATE_CONFIG", "config.ini", "config.ini"),
            ("UR_MIGRATE_KEYS", "keybinds.ini", "keybinds.ini"),
            ("UR_MIGRATE_SAVES", "saves", "saves"),
            ("UR_MIGRATE_MOD", "mod-state.toml", "mods/preloaded/state.toml"),
        )
        with tempfile.TemporaryDirectory() as tmp:
            base = pathlib.Path(tmp)
            attrib = pathlib.Path(os.environ["SystemRoot"]) / "System32" / "attrib.exe"
            for stage, destination, legacy in cases:
                with self.subTest(stage=stage):
                    payload = base / stage / "portable"
                    payload.mkdir(parents=True)
                    user_data = base / stage / "persistent"
                    shutil.copyfile(attrib, payload / package_tool.EXE_NAME)
                    (payload / package_tool.ROM_NAME).write_bytes(b"synthetic-rom")
                    (payload / "rom.cfg").write_bytes(package_tool.ROM_CONFIG_BYTES)
                    catalog = payload / "mods" / "preloaded" / "packages"
                    catalog.mkdir(parents=True)
                    (catalog / ".gitkeep").touch()
                    legacy_path = payload.joinpath(*legacy.split("/"))
                    if legacy == "saves":
                        legacy_path.mkdir()
                        (legacy_path / "original.srm").write_bytes(b"original")
                    else:
                        legacy_path.parent.mkdir(parents=True, exist_ok=True)
                        legacy_path.write_bytes(b"original")
                    generated = package_tool.launcher_text("rename-collision-fixture")
                    needle = f'  ren "%{stage}%" "{destination}" >nul 2>&1\r\n'
                    self.assertEqual(generated.count(needle), 1)
                    if destination == "saves":
                        injection = (
                            '  mkdir "%UR_RECOMP_USER_DATA_ROOT%\\saves" >nul 2>&1\r\n'
                            '  > "%UR_RECOMP_USER_DATA_ROOT%\\saves\\concurrent.srm" echo other-writer\r\n'
                        )
                    else:
                        injection = (
                            f'  > "%UR_RECOMP_USER_DATA_ROOT%\\{destination}" echo other-writer\r\n'
                        )
                    injection += '  cmd.exe /d /c exit /b 1\r\n'
                    generated = generated.replace(needle, injection)
                    launcher = payload / package_tool.LAUNCHER_NAME
                    launcher.write_bytes(generated.encode("utf-8"))
                    env = os.environ.copy()
                    env["UR_RECOMP_USER_DATA_ROOT"] = str(user_data)
                    proc = subprocess.run(
                        ["cmd.exe", "/d", "/c", "call", str(launcher)],
                        cwd=payload, env=env, capture_output=True, text=True,
                        errors="replace", timeout=30, check=False,
                    )
                    self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
                    self.assertIn("Could not commit legacy", proc.stderr)
                    target = user_data / destination
                    self.assertTrue(target.exists())
                    competing = target / "concurrent.srm" if destination == "saves" else target
                    self.assertEqual(competing.read_text().strip(), "other-writer")
                    self.assertEqual(list(user_data.glob(".ur-recomp-*.migrate.tmp")), [])
                    self.assertTrue(legacy_path.exists())

    def test_windows_launcher_retains_metacharacter_paths_in_startup_log(self):
        # Real CMD parsing, not a string-only policy assertion. Only the
        # hosted Windows package gate runs this; Linux tooling skips it.
        if os.name != "nt":
            self.skipTest("requires Windows cmd.exe")
        from tools import assemble_windows_package as package_tool

        with tempfile.TemporaryDirectory() as tmp:
            base = pathlib.Path(tmp)
            payload = base / "package & game! (portable)"
            payload.mkdir()
            user_data = base / "player & user! (data)"
            # A stock system command serves as a harmless native EXE that
            # reads the single ROM path argument and exits successfully.
            attrib = pathlib.Path(os.environ["SystemRoot"]) / "System32" / "attrib.exe"
            shutil.copyfile(attrib, payload / package_tool.EXE_NAME)
            (payload / package_tool.ROM_NAME).write_bytes(b"synthetic-rom")
            (payload / "rom.cfg").write_bytes(package_tool.ROM_CONFIG_BYTES)
            catalog = payload / "mods" / "preloaded" / "packages"
            catalog.mkdir(parents=True)
            (catalog / ".gitkeep").touch()
            package_tool.write_launcher(payload / package_tool.LAUNCHER_NAME, "cmd-path-test")

            env = os.environ.copy()
            env["UR_RECOMP_USER_DATA_ROOT"] = str(user_data)
            process = subprocess.run(
                ["cmd.exe", "/d", "/c", package_tool.LAUNCHER_NAME],
                cwd=payload, env=env, capture_output=True, text=True,
                timeout=30, check=False,
            )
            self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
            startup = (user_data / "diagnostics" / "startup.log").read_text(
                encoding="utf-8"
            ).splitlines()
            self.assertEqual(
                [line for line in startup if line.startswith("package_root=")],
                ["package_root=" + str(payload)],
            )
            self.assertEqual(
                [line for line in startup if line.startswith("user_data_root=")],
                ["user_data_root=" + str(user_data)],
            )
            self.assertIn("process_exit=0", startup)
            self.assertEqual(startup.count("result=startup-begin"), 1)
            self.assertFalse((payload / "diagnostics").exists())

    def test_windows_manifest_names_reject_case_aliased_parent_components(self):
        for paths in (
            {"mods/preloaded/Case/file-a.bin", "mods/preloaded/case/file-b.bin"},
            {"mods/preloaded/packages/X.dat", "mods/preloaded/packages/x.dat"},
        ):
            with self.subTest(paths=paths):
                with self.assertRaisesRegex(
                    ValueError, "case-colliding Windows paths"
                ):
                    package_tool.validate_windows_portable_paths(
                        paths, context="test manifest"
                    )

    def test_source_mod_case_alias_fails_before_removing_completed_output(self):
        if os.name == "nt":
            self.skipTest("cannot create case-distinct directory entries on NTFS")
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            build, rom = self.make_inputs(root)
            mods = build / "mods" / "preloaded" / "packages"
            (mods / "CaseData.txt").write_text("first")
            (mods / "casedata.txt").write_text("second")
            output = root / "existing-package"
            output.mkdir()
            keep = output / "preserve-on-source-failure"
            keep.write_text("good completed package")
            with self.assertRaisesRegex(
                ValueError, "package source mods contains case-colliding"
            ):
                package_tool.assemble(build, rom, output, "source-case-test")
            self.assertEqual(keep.read_text(), "good completed package")

    def test_archive_rejects_manifest_consistent_ntfs_name_aliases(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            build, rom = self.make_inputs(root)
            output = root / "package"
            package_tool.assemble(build, rom, output, "case-collision-test")
            original = root / "original.zip"
            package_tool.create_archive(output, original)
            forged = root / "alias.zip"
            alias = "mods/preloaded/packages/CATALOG.json"
            payload = b'{"alias": true}\\n'
            with zipfile.ZipFile(original) as source, zipfile.ZipFile(
                forged, "w", compression=zipfile.ZIP_DEFLATED
            ) as target:
                manifest = json.loads(
                    source.read(
                        f"{package_tool.ARCHIVE_ROOT}/{package_tool.MANIFEST_NAME}"
                    )
                )
                manifest["files"].append({
                    "path": alias,
                    "size": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                })
                for info in source.infolist():
                    data = source.read(info.filename)
                    if info.filename.endswith("/PACKAGE-MANIFEST.json"):
                        data = package_tool.canonical_manifest_bytes(manifest)
                    target.writestr(info, data)
                # Alias is self-consistent with both ZIP and manifest.
                info = zipfile.ZipInfo(
                    f"{package_tool.ARCHIVE_ROOT}/{alias}",
                    date_time=package_tool.ARCHIVE_TIMESTAMP,
                )
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                target.writestr(info, payload)
            with self.assertRaisesRegex(
                ValueError, "package archive contains case-colliding Windows paths"
            ):
                package_tool.verify_archive(forged)

    def test_ntfs_reserved_and_invalid_package_path_components(self):
        for relative, diagnostic in (
            ("mods/preloaded/packages/CON.txt", "Windows-reserved device name"),
            ("mods/preloaded/packages/lpt9.cfg", "Windows-reserved device name"),
            ("mods/preloaded/packages/COM².dll", "Windows-reserved device name"),
            ("mods/preloaded/packages/trailing.", "Windows-incompatible path"),
            ("mods/preloaded/packages/trailing ", "Windows-incompatible path"),
            ("mods/preloaded/packages/stream:alt.bin", "Windows-incompatible path"),
            ("mods/preloaded/packages/bad?.dat", "Windows-incompatible path"),
            ("mods//preloaded/file", "Windows-incompatible path"),
        ):
            with self.subTest(relative=relative):
                with self.assertRaisesRegex(ValueError, diagnostic):
                    package_tool.validate_windows_portable_paths(
                        {relative}, context="test manifest"
                    )
        package_tool.validate_windows_portable_paths(
            {"mods/preloaded/packages/.gitkeep", "README.txt", "rom.cfg"},
            context="test valid package",
        )

    def test_invalid_windows_mod_source_preserves_prior_output(self):
        if os.name == "nt":
            self.skipTest("reserved NTFS names cannot be created on Windows")
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            build, rom = self.make_inputs(root)
            output = root / "completed-package"
            output.mkdir()
            marker = output / "preserve-if-input-invalid"
            marker.write_text("existing release")
            bad_mod = build / "mods" / "preloaded" / "packages" / "CON.txt"
            bad_mod.write_text("invalid for the consumer OS")
            with self.assertRaisesRegex(
                ValueError, "package source mods contains Windows-reserved device name"
            ):
                package_tool.assemble(build, rom, output, "bad-path-preflight")
            self.assertEqual(marker.read_text(), "existing release")

    def test_archive_rejects_signed_windows_reserved_device_filename(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            build, rom = self.make_inputs(root)
            package_dir = root / "package"
            package_tool.assemble(build, rom, package_dir, "reserved-zip-test")
            original = root / "original.zip"
            package_tool.create_archive(package_dir, original)
            forged = root / "reserved.zip"
            name = "mods/preloaded/packages/CON.txt"
            payload = b"unsafe Windows device path"
            with zipfile.ZipFile(original) as source, zipfile.ZipFile(
                forged, "w", compression=zipfile.ZIP_DEFLATED
            ) as target:
                manifest = json.loads(source.read(
                    f"{package_tool.ARCHIVE_ROOT}/{package_tool.MANIFEST_NAME}"
                ))
                manifest["files"].append({
                    "path": name,
                    "size": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                })
                for info in source.infolist():
                    data = source.read(info.filename)
                    if info.filename.endswith("/PACKAGE-MANIFEST.json"):
                        data = package_tool.canonical_manifest_bytes(manifest)
                    target.writestr(info, data)
                info = zipfile.ZipInfo(
                    f"{package_tool.ARCHIVE_ROOT}/{name}",
                    date_time=package_tool.ARCHIVE_TIMESTAMP,
                )
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                target.writestr(info, payload)
            with self.assertRaisesRegex(
                ValueError, "package archive contains Windows-reserved device name"
            ):
                package_tool.verify_archive(forged)

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
            (build / "mods" / "preloaded" / "state.toml").write_text(
                "build-local-mod-state\n"
            )

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
            self.assertFalse(
                (package / "mods" / "preloaded" / "state.toml").exists()
            )
            self.assertTrue((package / "run-uniracers.cmd").is_file())
            self.assertIn(
                "Source revision: abc123",
                (package / "README.txt").read_text(),
            )
            launcher = (package / "run-uniracers.cmd").read_text()
            readme = (package / "README.txt").read_text()
            self.assertNotIn(b"\r", (package / "README.txt").read_bytes())
            self.assertNotIn(
                b"\r", (package / "PACKAGE-MANIFEST.json").read_bytes()
            )
            self.assertIn("Do not overlay a new ZIP onto an old package tree.", readme)
            self.assertIn("static MSVC runtime", readme)
            self.assertIn("Visual C++ Redistributable", readme)
            self.assertIn("On a normal Windows desktop", readme)
            self.assertIn("PowerShell Expand-Archive", readme)
            self.assertIn("paths contain spaces", readme)
            self.assertIn("you do not need to set", readme)
            self.assertIn("the launcher uses APPDATA automatically", readme)
            self.assertIn("Do not start the .exe directly", readme)
            self.assertIn(
                r"%APPDATA%\gamesbyian\UR-Recomp by default.",
                readme,
            )
            self.assertNotIn(
                r"%APPDATA%\\gamesbyian\\UR-Recomp",
                readme,
            )
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
            self.assertIn("setlocal EnableDelayedExpansion", launcher)
            self.assertIn("echo package_root=!UR_PACKAGE_ROOT!", launcher)
            self.assertIn("echo user_data_root=!UR_RECOMP_USER_DATA_ROOT!", launcher)
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
            self.assertEqual(
                (package / "rom.cfg").read_bytes(),
                b"Uniracers_USA.sfc\n",
            )

            verify = self.run_tool("verify", "--package", package)
            self.assertIn("WINDOWS_PACKAGE_VERIFIED", verify.stdout)

            unexpected_file = package / "surprise.dll"
            unexpected_file.write_bytes(b"unexpected")
            unexpected_manifest = json.loads(
                (package / "PACKAGE-MANIFEST.json").read_text()
            )
            unexpected_manifest["files"] = [
                {
                    "path": p.relative_to(package).as_posix(),
                    "size": p.stat().st_size,
                    "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                }
                for p in sorted(package.rglob("*"))
                if p.is_file() and p.name != "PACKAGE-MANIFEST.json"
            ]
            self.write_manifest(
                package / "PACKAGE-MANIFEST.json",
                unexpected_manifest,
            )
            unexpected_failed = self.run_tool(
                "verify", "--package", package, check=False
            )
            self.assertNotEqual(unexpected_failed.returncode, 0)
            self.assertIn(
                "unexpected packaged files: surprise.dll",
                unexpected_failed.stderr,
            )
            unexpected_file.unlink()
            self.write_manifest(
                package / "PACKAGE-MANIFEST.json",
                manifest,
            )

            mutable_state = package / "mods" / "preloaded" / "state.toml"
            mutable_state.write_text("leaked-mod-state\n")
            mutable_manifest = json.loads(
                (package / "PACKAGE-MANIFEST.json").read_text()
            )
            mutable_manifest["files"] = [
                {
                    "path": p.relative_to(package).as_posix(),
                    "size": p.stat().st_size,
                    "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                }
                for p in sorted(package.rglob("*"))
                if p.is_file() and p.name != "PACKAGE-MANIFEST.json"
            ]
            self.write_manifest(
                package / "PACKAGE-MANIFEST.json",
                mutable_manifest,
            )
            mutable_failed = self.run_tool(
                "verify", "--package", package, check=False
            )
            self.assertNotEqual(mutable_failed.returncode, 0)
            self.assertIn(
                "contains mutable user state: mods/preloaded/state.toml",
                mutable_failed.stderr,
            )
            mutable_state.unlink()
            self.write_manifest(
                package / "PACKAGE-MANIFEST.json",
                manifest,
            )

            absolute_rom_cfg = b"C:\\build\\checkout\\Uniracers_USA.sfc\n"
            (package / "rom.cfg").write_bytes(absolute_rom_cfg)
            blessed_absolute_manifest = json.loads(
                (package / "PACKAGE-MANIFEST.json").read_text()
            )
            for entry in blessed_absolute_manifest["files"]:
                if entry["path"] == "rom.cfg":
                    entry["size"] = len(absolute_rom_cfg)
                    entry["sha256"] = hashlib.sha256(
                        absolute_rom_cfg
                    ).hexdigest()
                    break
            self.write_manifest(
                package / "PACKAGE-MANIFEST.json",
                blessed_absolute_manifest,
            )
            absolute_cfg = self.run_tool(
                "verify", "--package", package, check=False
            )
            self.assertNotEqual(absolute_cfg.returncode, 0)
            self.assertIn(
                "rom.cfg must contain canonical package-relative ROM path",
                absolute_cfg.stderr,
            )
            (package / "rom.cfg").write_bytes(b"Uniracers_USA.sfc\n")
            self.write_manifest(
                package / "PACKAGE-MANIFEST.json",
                manifest,
            )


            manifest_path = package / "PACKAGE-MANIFEST.json"
            canonical_manifest_bytes = manifest_path.read_bytes()
            manifest_path.write_bytes(
                canonical_manifest_bytes.replace(b"\n", b"\r\n")
            )
            crlf_manifest = self.run_tool(
                "verify", "--package", package, check=False
            )
            self.assertNotEqual(crlf_manifest.returncode, 0)
            self.assertIn(
                "manifest is not canonical UTF-8/LF JSON",
                crlf_manifest.stderr,
            )
            manifest_path.write_bytes(canonical_manifest_bytes)
            provenance_manifest = json.loads(manifest_path.read_text())
            provenance_manifest["source_revision"] = ""
            self.write_manifest(manifest_path, provenance_manifest)
            provenance_failed = self.run_tool(
                "verify", "--package", package, check=False
            )
            self.assertNotEqual(provenance_failed.returncode, 0)
            self.assertIn(
                "unsupported or malformed package manifest",
                provenance_failed.stderr,
            )
            self.write_manifest(manifest_path, manifest)

            mismatch_manifest = json.loads(json.dumps(manifest))
            mismatch_manifest["source_revision"] = "different-revision"
            self.write_manifest(manifest_path, mismatch_manifest)
            mismatch_failed = self.run_tool(
                "verify", "--package", package, check=False
            )
            self.assertNotEqual(mismatch_failed.returncode, 0)
            self.assertIn(
                "README source revision does not match manifest",
                mismatch_failed.stderr,
            )
            self.write_manifest(manifest_path, manifest)

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

            crlf_manifest_archive = root / "package-crlf-manifest.zip"
            with zipfile.ZipFile(archive1, "r") as source, zipfile.ZipFile(
                crlf_manifest_archive,
                "w",
                compression=zipfile.ZIP_DEFLATED,
            ) as target:
                for info in source.infolist():
                    payload = source.read(info.filename)
                    if info.filename.endswith("/PACKAGE-MANIFEST.json"):
                        payload = payload.replace(b"\n", b"\r\n")
                    target.writestr(info, payload)
            crlf_manifest_result = self.run_tool(
                "verify-archive",
                "--archive", crlf_manifest_archive,
                check=False,
            )
            self.assertNotEqual(crlf_manifest_result.returncode, 0)
            self.assertIn(
                "archive manifest is not canonical UTF-8/LF JSON",
                crlf_manifest_result.stderr,
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

            absolute_rom_archive = root / "package-absolute-rom-config.zip"
            absolute_rom_manifest = json.loads(json.dumps(manifest))
            absolute_rom_payload = b"C:\\runner\\checkout\\Uniracers_USA.sfc\n"
            for entry in absolute_rom_manifest["files"]:
                if entry["path"] == "rom.cfg":
                    entry["size"] = len(absolute_rom_payload)
                    entry["sha256"] = hashlib.sha256(
                        absolute_rom_payload
                    ).hexdigest()
                    break
            with zipfile.ZipFile(archive1, "r") as source, zipfile.ZipFile(
                absolute_rom_archive,
                "w",
                compression=zipfile.ZIP_DEFLATED,
            ) as target:
                for info in source.infolist():
                    if info.filename.endswith("/PACKAGE-MANIFEST.json"):
                        payload = (
                            json.dumps(
                                absolute_rom_manifest,
                                indent=2,
                                sort_keys=True,
                            ) + "\n"
                        ).encode("utf-8")
                    elif info.filename.endswith("/rom.cfg"):
                        payload = absolute_rom_payload
                    else:
                        payload = source.read(info.filename)
                    target.writestr(info, payload)
            absolute_archive_result = self.run_tool(
                "verify-archive",
                "--archive", absolute_rom_archive,
                check=False,
            )
            self.assertNotEqual(absolute_archive_result.returncode, 0)
            self.assertIn(
                "rom.cfg must contain canonical package-relative ROM path",
                absolute_archive_result.stderr,
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


    def test_source_revision_cannot_inject_windows_launcher_commands(self):
        # The value appears in an unquoted CMD echo and a diagnostic line.
        # Source provenance must be a single inert token, even for offline
        # assembly where --source-revision is supplied by the caller.
        for revision in ("abc123", "test-revision", "release_2026.10.23", "a" * 40):
            with self.subTest(allowed=revision):
                self.assertEqual(package_tool.normalize_source_revision(revision), revision)
        for revision in (
            "rev&whoami", "rev|more", "rev>file", "rev<file",
            "rev%COMSPEC%", "rev!EXPAND!", "rev^caret", 'rev"quote',
            "rev (parentheses)", "rev/branch", "rev\\branch",
            "rev\u00e9", "rev\nspoof", "x" * 129,
        ):
            with self.subTest(rejected=revision):
                with self.assertRaises(ValueError):
                    package_tool.normalize_source_revision(revision)

        # Fail before touching a previously completed package tree.
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            build, rom = self.make_inputs(root)
            output = root / "package"
            output.mkdir()
            sentinel = output / "completed-build.txt"
            sentinel.write_text("preserve existing bytes", encoding="utf-8")
            result = self.run_tool(
                "assemble", "--build-dir", build, "--rom", rom,
                "--output", output, "--source-revision", "rev&whoami",
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("source revision is required for a shippable package", result.stderr)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "preserve existing bytes")

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
