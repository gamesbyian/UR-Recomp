import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class LocalTournamentSessionCoordinatorCppTests(unittest.TestCase):
    def test_durable_fixture_lifecycle_over_real_saved_two_player_pairs(self):
        with tempfile.TemporaryDirectory() as work:
            exe = pathlib.Path(work) / "tournament-coordinator"
            sources = [
                "modern_racer_identity.cpp",
                "host_profile_runtime.cpp",
                "host_product_state.cpp",
                "output_resolution_policy.cpp",
                "completed_run_record.cpp",
                "completed_run_store.cpp",
                "local_multiplayer_match_binding.cpp",
                "multiplayer_match_record.cpp",
                "local_tournament_session_store.cpp",
                "local_tournament_fixture_launch_store.cpp",
                "local_tournament_result_link_store.cpp",
                "local_tournament_session_coordinator.cpp",
            ]
            subprocess.run(
                [
                    "g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
                    "-pedantic",
                    "-I", str(ROOT / "native/product"),
                    "-I", str(ROOT / "native/title"),
                    *[str(ROOT / "native/product" / source) for source in sources],
                    str(ROOT / "tests/native/local_tournament_session_coordinator_test.cpp"),
                    "-o", str(exe),
                ],
                check=True, cwd=ROOT,
            )
            subprocess.run([str(exe)], check=True, cwd=ROOT)


if __name__ == "__main__":
    unittest.main()
