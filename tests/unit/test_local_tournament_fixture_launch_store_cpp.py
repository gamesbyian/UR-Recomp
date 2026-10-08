import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class LocalTournamentLaunchStoreCppTests(unittest.TestCase):
    def test_atomic_save_reload_and_containment(self):
        with tempfile.TemporaryDirectory() as tmp:
            executable = pathlib.Path(tmp) / "local-tournament-launch-store"
            subprocess.run(
                [
                    "g++", "-std=c++17", "-Wall", "-Wextra",
                    "-Werror", "-pedantic",
                    "-I", str(ROOT / "native/product"),
                    "-I", str(ROOT / "native/title"),
                    str(ROOT / "tests/native/local_tournament_fixture_launch_store_test.cpp"),
                    str(ROOT / "native/product/local_tournament_fixture_launch_store.cpp"),
                    "-o", str(executable),
                ],
                cwd=ROOT, check=True,
            )
            subprocess.run([str(executable)], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
