"""Hosted-only real Ninja package canary: guard the personal HP runner and existing QA."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SMOKE = ROOT / ".github/workflows/windows-native-smoke.yml"
CALLER = ROOT / ".github/workflows/qa05-qa09-windows-candidate.yml"
HP = ROOT / ".github/workflows/owner-hp-main-windows-smoke.yml"
NINJA = ROOT / "tools/ci/ninja_package_canary.cmd"


class NinjaPackagePolicyTests(unittest.TestCase):
    def test_generator_is_hosted_pr_only_and_never_changes_hp_default(self):
        smoke = SMOKE.read_text(encoding="utf-8")
        hp = HP.read_text(encoding="utf-8")
        caller = CALLER.read_text(encoding="utf-8")
        self.assertIn("(!inputs.test_ninja_generator_profile ||", smoke)
        self.assertIn("(!inputs.run_on_hp && inputs.test_hp_compiler_profile &&", smoke)
        self.assertIn("github.event_name == 'pull_request'))", smoke)
        self.assertIn("run_on_hp: true", hp)
        self.assertNotIn("test_ninja_generator_profile: true", hp)
        self.assertIn("test_ninja_generator_profile: true", caller)
        self.assertIn("test_hp_compiler_profile: true", caller)
        self.assertIn("(!inputs.run_on_hp ||", smoke)

    def test_ninja_build_uses_exact_prebuilt_static_sdl_and_vs_sdk(self):
        source = NINJA.read_text(encoding="utf-8")
        for part in ("VsDevCmd.bat", "where ninja.exe", "Ninja Multi-Config",
                     "-DSNESRECOMP_SDL3_FETCH=OFF",
                     "-DSDL3_DIR=", "-DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded",
                     "VC\\Tools\\Llvm\\x64\\bin\\clang-cl.exe",
                     "if errorlevel 1 exit /b 32"):
            with self.subTest(token=part):
                self.assertIn(part, source)
        self.assertNotIn("-DSNESRECOMP_SDL3_FETCH=ON", source)
        self.assertNotIn("curl", source.lower())
        self.assertNotIn("Invoke-WebRequest", source)

    def test_actual_ninja_executable_used_by_unchanged_full_qa(self):
        smoke = SMOKE.read_text(encoding="utf-8")
        self.assertIn('cmd.exe /d /c "$(cygpath -w "$GITHUB_WORKSPACE/tools/ci/ninja_package_canary.cmd")"', smoke)
        self.assertIn('[[ -n "${UR_SDL3_PREBUILT_DIR:-}" ]]', smoke)
        self.assertIn('if [[ "${{ inputs.test_ninja_generator_profile }}" != "true" ]]; then', smoke)
        self.assertIn('EXE="$(find "$ROOT/build" -name \'UniracersSNESRecomp.exe\'', smoke)
        for required in ("Assemble and verify portable Windows package",
                         "Independently verify portable ZIP",
                         "Extracted-package race-result acceptance",
                         "QA-09 packaged Windows controller-only root",
                         "QA-05 packaged Windows default-Return Restart audio",
                         "Package refresh preserves user data",
                         "Representative package startup diagnostics"):
            self.assertIn(required, smoke)

    def test_ninja_inputs_invalidate_hosted_pr_validation(self):
        caller = CALLER.read_text(encoding="utf-8")
        for path in ("tools/ci/ninja_package_canary.cmd",
                     "tests/unit/test_hp_ninja_package_policy.py"):
            self.assertIn('      - "'+path+'"', caller)


if __name__ == "__main__":
    unittest.main()
