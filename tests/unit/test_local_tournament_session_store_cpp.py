import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class LocalTournamentSessionStoreCppTests(unittest.TestCase):
    def test_durable_profile_authorized_session_and_fresh_load(self):
        with tempfile.TemporaryDirectory() as work:
            exe = pathlib.Path(work) / "tournament-session-store"
            subprocess.run(
                [
                    "g++", "-std=c++17", "-Wall", "-Wextra",
                    "-Werror", "-pedantic",
                    "-I", str(ROOT / "native/product"),
                    "-I", str(ROOT / "native/title"),
                    str(ROOT / "tests/native/local_tournament_session_store_test.cpp"),
                    str(ROOT / "native/product/local_tournament_session_store.cpp"),
                    "-o", str(exe),
                ],
                check=True, cwd=ROOT,
            )
            subprocess.run([str(exe)], check=True, cwd=ROOT)


if __name__ == "__main__":
    unittest.main()
