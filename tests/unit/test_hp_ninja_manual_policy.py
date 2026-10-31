"""Contract tests for the HP opt-in Ninja generator and pinned owner-tool receipt."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERIFY = ROOT / "tools/devnode_benchmark/verify_hp_ninja.py"
SMOKE = ROOT / ".github/workflows/windows-native-smoke.yml"
HP = ROOT / ".github/workflows/owner-hp-main-windows-smoke.yml"
HOSTED = ROOT / ".github/workflows/qa05-qa09-windows-candidate.yml"
CMD = ROOT / "tools/ci/ninja_package_canary.cmd"
loader = importlib.util.spec_from_file_location("verify_hp_ninja", VERIFY)
mod = importlib.util.module_from_spec(loader)
loader.loader.exec_module(mod)


class HpNinjaManualPolicyTests(unittest.TestCase):
    def test_guarded_main_dispatch_not_pr_or_push(self):
        hp = HP.read_text(encoding="utf-8")
        smoke = SMOKE.read_text(encoding="utf-8")
        hosted = HOSTED.read_text(encoding="utf-8")
        self.assertIn("ninja_trial:", hp)
        self.assertIn("default: false", hp)
        self.assertIn("github.event_name == 'workflow_dispatch' && inputs.ninja_trial", hp)
        self.assertIn("run_on_hp: true", hp)
        self.assertIn("(!inputs.hp_ninja_canary ||", smoke)
        self.assertIn("github.event_name == 'workflow_dispatch'))", smoke)
        self.assertIn("github.ref == 'refs/heads/main'", smoke)
        self.assertIn("(!inputs.run_on_hp ||", smoke)
        self.assertNotIn("hp_ninja_canary: true", hosted)

    def test_automatic_vs_and_hosted_fidelity_retained(self):
        s = SMOKE.read_text(encoding="utf-8")
        self.assertIn('if [[ "${{ inputs.hp_ninja_canary }}" == "true" ]]; then', s)
        self.assertIn('cmake -S "$ROOT" -B "$ROOT/build" -G "Visual Studio 17 2022"', s)
        self.assertIn('cmake --build "$ROOT/build" --config Release --parallel "$HP_BUILD_JOBS"', s)
        self.assertIn("HP_NINJA_COMPILE_WINDOW=configure_plus_build", s)
        for token in ("Assemble and verify portable Windows package",
                      "QA-09 packaged Windows controller-only root",
                      "QA-05 packaged Windows default-Return Restart audio",
                      "Extracted-package race-result acceptance",
                      "Representative package startup diagnostics"):
            self.assertIn(token, s)
        self.assertIn("test_hp_compiler_profile: true", HOSTED.read_text(encoding="utf-8"))

    def test_automatic_hp_ninja_is_only_trusted_main_push(self):
        hp = HP.read_text(encoding="utf-8")
        smoke = SMOKE.read_text(encoding="utf-8")
        hosted = HOSTED.read_text(encoding="utf-8")
        self.assertIn("hp_ninja_auto: ${{ github.event_name == 'push' }}", hp)
        self.assertIn("(!inputs.hp_ninja_auto ||", smoke)
        self.assertIn("github.event_name == 'push'))", smoke)
        self.assertIn("!(inputs.hp_ninja_auto && inputs.hp_ninja_canary)", smoke)
        self.assertIn('elif [[ "${{ inputs.hp_ninja_auto }}" == "true" ]]; then', smoke)
        self.assertIn("HP_NINJA_AUTO=verified_source_bound", smoke)
        self.assertIn("HP_NINJA_AUTO=vs_fallback reason=owner_ninja_preflight_unavailable", smoke)
        self.assertIn("HP_NINJA_AUTO=vs_fallback reason=missing_verified_sdl3", smoke)
        self.assertIn("--allow-trusted-main-push", smoke)
        self.assertIn('if [[ "$HP_NINJA_SELECTED" == "1" ]]; then', smoke)
        self.assertIn('cmake --build "$ROOT/build" --config Release --parallel "$HP_BUILD_JOBS"', smoke)
        self.assertNotIn("hp_ninja_auto: true", hosted)
        self.assertNotIn("hp_ninja_canary: true", hosted)
        # A compiler error in selected Ninja must still fail the authoritative
        # Windows job; do not silently fall back to a different candidate.
        self.assertIn('MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL=', smoke)
        self.assertNotIn("|| cmake --build", smoke)

    def test_automatic_push_preflight_needs_explicit_opt_in(self):
        from unittest.mock import patch
        base = {"RUNNER_NAME": "hpmini-ur-recomp",
                "GITHUB_REPOSITORY": "gamesbyian/UR-Recomp",
                "GITHUB_REF": "refs/heads/main", "GITHUB_EVENT_NAME": "push"}
        with patch.dict(mod.os.environ, base, clear=True):
            with patch("sys.argv", ["verify_hp_ninja.py"]):
                with self.assertRaises(SystemExit):
                    mod.main()
            with patch("sys.argv", ["verify_hp_ninja.py", "--allow-trusted-main-push"]):
                with patch.object(mod, "verify", return_value="pinned/ninja.exe"):
                    with patch.object(mod, "file_hash", return_value="a" * 64):
                        self.assertEqual(mod.main(), 0)
            base["GITHUB_EVENT_NAME"] = "pull_request"
            with patch.dict(mod.os.environ, base, clear=True):
                with patch("sys.argv", ["verify_hp_ninja.py", "--allow-trusted-main-push"]):
                    with self.assertRaises(SystemExit):
                        mod.main()

    def test_owner_ninja_ten_compiler_jobs_are_bounded_and_logged(self):
        s = CMD.read_text(encoding="utf-8")
        self.assertIn('set "UR_HP_NINJA_BUILD_JOBS=10"', s)
        self.assertIn('echo HP_NINJA_BUILD_JOBS=%UR_HP_NINJA_BUILD_JOBS%', s)
        self.assertIn('cmake --build "%UR_NINJA_ROOT%/build" --config Release --parallel %UR_HP_NINJA_BUILD_JOBS%', s)
        self.assertNotIn('cmake --build "%UR_NINJA_ROOT%/build" --config Release --parallel 6', s)
        self.assertIn('if errorlevel 1 exit /b 32', s)
        self.assertIn("Ninja Multi-Config", s)
        self.assertIn("-DSNESRECOMP_SDL3_FETCH=OFF", s)
        source = SMOKE.read_text(encoding="utf-8")
        self.assertIn("HP_NINJA_AUTO=verified_source_bound", source)
        self.assertIn("HP_NINJA_COMPILE_WINDOW=configure_plus_build", source)
        self.assertIn("QA-05 packaged Windows default-Return Restart audio", source)
        self.assertIn("QA-09 packaged Windows controller-only root", source)

    def test_only_preverified_static_sdl_and_compiler_in_ninja(self):
        s = CMD.read_text(encoding="utf-8")
        for part in ("VsDevCmd.bat", "where ninja.exe", "Ninja Multi-Config",
                     "-DSNESRECOMP_SDL3_FETCH=OFF",
                     "-DSDL3_DIR=", "-DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded",
                     "if errorlevel 1 exit /b 32"):
            with self.subTest(part=part):
                self.assertIn(part, s)
        self.assertNotIn("-DSNESRECOMP_SDL3_FETCH=ON", s)

    def test_cmake_selects_exact_receipt_verified_owner_ninja(self):
        source = CMD.read_text(encoding="utf-8")
        self.assertIn('set "OWNER_NINJA_ARG="', source)
        self.assertIn('set "OWNER_NINJA_ARG=-DCMAKE_MAKE_PROGRAM=%UR_HP_NINJA_DIR%/ninja.exe"',
                      source)
        self.assertIn('"%UR_HP_NINJA_CANARY%"=="1"', source)
        self.assertIn('%OWNER_NINJA_ARG%', source)
        self.assertEqual(source.count("set \"OWNER_NINJA_ARG=-DCMAKE_MAKE_PROGRAM="), 1)
        self.assertIn('if not exist "%UR_HP_NINJA_DIR%\\ninja.exe" exit /b 34', source)

    def test_installed_binary_receipt_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            exe = d / "ninja.exe"
            exe.write_bytes(b"owned fixture")
            receipt = {"installer_id": mod.INSTALLER_ID, "version": mod.VERSION,
                       "archive_sha256": mod.ARCHIVE_SHA256,
                       "binary_sha256": mod.file_hash(exe)}
            (d / "ur-recomp-ninja-install.json").write_text(json.dumps(receipt))
            self.assertEqual(mod.verify(d, run_version=False), str(exe))
            exe.write_bytes(b"tampered")
            with self.assertRaises(ValueError):
                mod.verify(d, run_version=False)
            exe.write_bytes(b"owned fixture")
            (d / "stranger.txt").write_text("untouched")
            with self.assertRaises(ValueError):
                mod.verify(d, run_version=False)

    def test_wrong_provenance_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            exe = d / "ninja.exe"
            exe.write_bytes(b"owned fixture")
            marker = d / "ur-recomp-ninja-install.json"
            base = {"installer_id": mod.INSTALLER_ID, "version": mod.VERSION,
                    "archive_sha256": mod.ARCHIVE_SHA256,
                    "binary_sha256": mod.file_hash(exe)}
            for field in ("installer_id", "version", "archive_sha256", "binary_sha256"):
                with self.subTest(field=field):
                    wrong = dict(base)
                    wrong[field] = "forged"
                    marker.write_text(json.dumps(wrong))
                    with self.assertRaises(ValueError):
                        mod.verify(d, run_version=False)

    def test_reparse_point_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            actual = d / "actual"
            actual.mkdir()
            link = d / "linked"
            try:
                link.symlink_to(actual, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("Windows runner cannot create symlinks")
            with self.assertRaises(ValueError):
                mod.verify(link, run_version=False)

    def test_redirected_parent_with_valid_receipt_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            real_root = base / "real" / "Ninja" / "v1.13.2"
            real_root.mkdir(parents=True)
            binary = real_root / "ninja.exe"
            binary.write_bytes(b"owned real binary")
            receipt = {"installer_id": mod.INSTALLER_ID, "version": mod.VERSION,
                       "archive_sha256": mod.ARCHIVE_SHA256,
                       "binary_sha256": mod.file_hash(binary)}
            (real_root / "ur-recomp-ninja-install.json").write_text(json.dumps(receipt))
            self.assertEqual(mod.verify(real_root, run_version=False), str(binary))
            redirect = base / "runner-tools"
            try:
                redirect.symlink_to(base / "real", target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("runner cannot create directory symlink")
            with self.assertRaisesRegex(ValueError, "redirected owner Ninja"):
                mod.verify(redirect / "Ninja" / "v1.13.2", run_version=False)
            self.assertEqual(binary.read_bytes(), b"owned real binary")

    def test_exact_helper_trigger_paths(self):
        for file in (SMOKE, HP):
            source = file.read_text(encoding="utf-8")
            for path in ("tools/devnode_benchmark/verify_hp_ninja.py",
                         "tools/ci/ninja_package_canary.cmd",
                         "tests/unit/test_hp_ninja_manual_policy.py"):
                with self.subTest(file=file.name, path=path):
                    self.assertIn('      - "' + path + '"', source)


if __name__ == "__main__":
    unittest.main()
