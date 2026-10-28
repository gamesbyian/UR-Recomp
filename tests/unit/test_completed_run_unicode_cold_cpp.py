"""ROM-free production Records -> replay Unicode cold-process regression.

Tests exactly two separate compiled native processes. Unicode subpaths are
constructed inside C++, so narrow Windows argv cannot accidentally substitute
an ACP pathname. The complete GUI, physical controller and DATA-05 criterion
remain separate acceptance requirements.
"""
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


def compile_native_runner(exe: pathlib.Path) -> None:
    compiler = shutil.which("g++") or shutil.which("clang++")
    if not compiler:
        raise RuntimeError("a C++17 compiler is required for the native replay witness")
    cmd = [
        compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror",
        "-pedantic", "-pthread", "-I",
        str(ROOT / "native" / "product"),
        *[str(ROOT / "native" / "product" / name) for name in (
            "completed_run_record.cpp",
            "completed_run_capture.cpp",
            "completed_run_store.cpp",
            "completed_run_replay.cpp",
            "output_resolution_policy.cpp",
            "host_product_state.cpp",
            "host_product_store.cpp",
            # Cold-read the actual same-PE source-earned two-player pair through
            # the same shipping catalog and Records summary as Modern mode.
            "multiplayer_match_record.cpp",
            "multiplayer_match_catalog.cpp",
            "multiplayer_match_summary.cpp",
            "baldosa_native_multiplayer_records_summary.cpp",
            "local_multiplayer_match_binding.cpp",
            "host_profile_runtime.cpp",
            "modern_racer_identity.cpp",
        )],
        str(ROOT / "tests" / "native" /
            "completed_run_unicode_cold_test.cpp"),
        "-o", str(exe),
    ]
    subprocess.run(cmd, cwd=ROOT, check=True, timeout=120)


class CompletedRunUnicodeColdCppTests(unittest.TestCase):

    def test_windows_bridge_invalidates_on_unicode_fixture_changes(self):
        workflow = (ROOT / ".github" / "workflows" /
                    "baldosa-windows-native-bridge.yml").read_text(
                        encoding="utf-8")
        trigger = workflow[:workflow.index("  workflow_dispatch:")]
        for path in ("tests/native/completed_run_unicode_cold_test.cpp",
                     "tests/unit/test_completed_run_unicode_cold_cpp.py"):
            self.assertIn(f'      - "{path}"', trigger)
        self.assertIn(
            "python -m unittest -v tests.unit.test_completed_run_unicode_cold_cpp",
            workflow)

    def test_source_earned_unicode_replay_runs_after_real_windows_journey(self):
        workflow = (ROOT / ".github" / "workflows" /
                    "baldosa-windows-native-bridge.yml").read_text(
                        encoding="utf-8")
        self.assertIn(
            "tests/unit/test_completed_run_unicode_cold_cpp.py --source-earned-base",
            workflow)
        self.assertLess(
            workflow.index("Exercise the keyboard plus one pad 2P join on Win32"),
            workflow.index("Test source-earned Win32 Unicode replay after cold Records"))
        self.assertIn(
            "ur-keyboard-pad-join/earned_return_cold_records/earned_run/source.urrun",
            workflow)
        source = (ROOT / "tests" / "native" /
                  "completed_run_unicode_cold_test.cpp").read_text(
                      encoding="utf-8")
        self.assertIn("source-earned-cold-read", source)
        self.assertIn("reload_matching_completed_run_replay_record(", source)
        self.assertIn("stage_completed_run_replay_input_file(", source)
        self.assertIn("DATA05_UNICODE_SOURCE_EARNED_REPLAY_COLD=passed", source)
        self.assertIn(
            'fs::u8path(u8"user_2p_漢字-🚲")', source)
        self.assertIn("inspect_multiplayer_match_artifacts(", source)
        self.assertIn("inspect_baldosa_native_two_player_records_archive(", source)
        self.assertIn("DATA05_UNICODE_SOURCE_EARNED_2P_RECORDS_COLD=passed", source)
        self.assertIn("cold_read_source_earned_two_player_pair(acceptance_base);",
                      source)

    def test_unicode_archive_to_replay_across_cold_process(self):
        compiler = shutil.which("g++") or shutil.which("clang++")
        if not compiler:
            self.skipTest("C++17 compiler unavailable")
        with tempfile.TemporaryDirectory(prefix="ur-data05-cold-") as temporary:
            base = pathlib.Path(temporary)
            exe = base / ("unicode-run-replay.exe" if sys.platform == "win32"
                          else "unicode-run-replay")
            compile_native_runner(exe)
            root = base / "cold-root"
            for mode, marker in (
                ("write", "DATA05_UNICODE_COLD_WRITE=passed"),
                ("cold-read", "DATA05_UNICODE_COLD_READ=passed"),
            ):
                with self.subTest(mode=mode):
                    completed = subprocess.run(
                        [str(exe), str(root), mode], cwd=ROOT, check=True,
                        capture_output=True, text=True, timeout=30)
                    self.assertIn(marker, completed.stdout)
                    options_marker = ("DATA05_UNICODE_OPTIONS_WRITE=passed"
                                      if mode == "write" else
                                      "DATA05_UNICODE_OPTIONS_COLD_READ=passed")
                    self.assertIn(options_marker, completed.stdout)
            # One immutable .urrun must survive replay staging/cleanup.
            runs = list((root / "player-漢字-資料-🚲" /
                         "runs" / "mike").glob("*.urrun"))
            self.assertEqual(len(runs), 1)
            self.assertGreater(runs[0].stat().st_size, 100)
            options = root / "player-漢字-資料-🚲" / "options-v1.txt"
            self.assertTrue(options.is_file())
            self.assertGreater(options.stat().st_size, 20)



if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--source-earned-base":
        base = pathlib.Path(sys.argv[2]).resolve()
        if not base.is_dir():
            raise SystemExit("actual native source-earned acceptance directory missing")
        with tempfile.TemporaryDirectory(prefix="ur-data05-earned-") as temporary:
            exe = pathlib.Path(temporary) / (
                "unicode-earned-replay.exe" if sys.platform == "win32"
                else "unicode-earned-replay")
            compile_native_runner(exe)
            outcome = subprocess.run(
                [str(exe), str(base), "source-earned-cold-read"],
                cwd=ROOT, check=True, capture_output=True,
                text=True, timeout=30,
            )
            marker = "DATA05_UNICODE_SOURCE_EARNED_REPLAY_COLD=passed"
            if marker not in outcome.stdout:
                raise SystemExit("actual source-earned replay witness absent")
            pair_marker = "DATA05_UNICODE_SOURCE_EARNED_2P_RECORDS_COLD=passed"
            if pair_marker not in outcome.stdout:
                raise SystemExit("actual source-earned Unicode 2P Records cold witness absent")
            print(outcome.stdout.strip())
    else:
        unittest.main()
