import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class LocalTournamentRoundRobinCppTests(unittest.TestCase):
    def test_cpp_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "local-tournament-round-robin-test"
            subprocess.run(
                [
                    "g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
                    "-pedantic",
                    "-I", str(ROOT / "native/product"),
                    "-I", str(ROOT / "native/title"),
                    str(ROOT / "tests/native/local_tournament_round_robin_test.cpp"),
                    "-o", str(exe),
                ],
                cwd=ROOT, check=True,
            )
            subprocess.run([str(exe)], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
