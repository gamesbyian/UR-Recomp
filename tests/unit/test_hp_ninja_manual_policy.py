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

    def test_only_preverified_static_sdl_and_compiler_in_ninja(self):
        s = CMD.read_text(encoding="utf-8")
        for part in ("VsDevCmd.bat", "where ninja.exe", "Ninja Multi-Config",
                     "-DSNESRECOMP_SDL3_FETCH=OFF",
                     "-DSDL3_DIR=", "-DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded",
                     "if errorlevel 1 exit /b 32"):
            with self.subTest(part=part):
                self.assertIn(part, s)
        self.assertNotIn("-DSNESRECOMP_SDL3_FETCH=ON", s)

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
