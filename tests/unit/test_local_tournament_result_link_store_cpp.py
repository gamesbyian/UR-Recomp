import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class LocalTournamentResultLinkStoreCppTests(unittest.TestCase):
    def test_fresh_process_fixture_links_to_exact_persisted_2p_pairs(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "tournament-result-links"
            sources = [
                "modern_racer_identity.cpp",
                "host_profile_runtime.cpp",
                "host_product_state.cpp",
                "output_resolution_policy.cpp",
                "completed_run_record.cpp",
                "completed_run_store.cpp",
                "local_multiplayer_match_binding.cpp",
                "multiplayer_match_record.cpp",
                "local_tournament_result_link_store.cpp",
            ]
            subprocess.run(
                [
                    "g++", "-std=c++17", "-Wall", "-Wextra",
                    "-Werror", "-pedantic", "-pthread",
                    "-I", str(ROOT / "native/product"),
                    "-I", str(ROOT / "native/title"),
                    *[str(ROOT / "native/product" / source) for source in sources],
                    str(ROOT / "tests/native/local_tournament_result_link_store_test.cpp"),
                    "-o", str(exe),
                ],
                check=True, cwd=ROOT,
            )
            subprocess.run([str(exe)], check=True, cwd=ROOT)


if __name__ == "__main__":
    unittest.main()
