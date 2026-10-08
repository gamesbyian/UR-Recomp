import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class LocalTournamentSystemTokensCppTests(unittest.TestCase):
    def test_os_entropy_tokens_arm_existing_fixture(self):
        with tempfile.TemporaryDirectory() as work:
            executable = pathlib.Path(work) / "tournament-tokens"
            subprocess.run(
                [
                    "g++", "-std=c++17", "-Wall", "-Wextra",
                    "-Werror", "-pedantic",
                    "-I", str(ROOT / "native/product"),
                    "-I", str(ROOT / "native/title"),
                    str(ROOT / "tests/native/local_tournament_tokens_test.cpp"),
                    "-o", str(executable),
                ],
                check=True, cwd=ROOT,
            )
            subprocess.run([str(executable)], check=True, cwd=ROOT)


if __name__ == "__main__":
    unittest.main()
