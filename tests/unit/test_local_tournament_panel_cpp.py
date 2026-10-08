import pathlib
import shutil
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class LocalTournamentPanelCppTests(unittest.TestCase):
    def test_setup_overview_and_fixture_selection_model(self):
        compilers = [c for c in ("g++", "clang++") if shutil.which(c)]
        self.assertTrue(compilers)
        for compiler in compilers:
            with self.subTest(compiler=compiler), \
                    tempfile.TemporaryDirectory() as work:
                exe = pathlib.Path(work) / "tournament-panel"
                subprocess.run(
                    [
                        compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror",
                        "-pedantic",
                        "-I", str(ROOT / "native/product"),
                        "-I", str(ROOT / "native/title"),
                        str(ROOT / "tests/native/local_tournament_panel_test.cpp"),
                        "-o", str(exe),
                    ],
                    check=True, cwd=ROOT,
                )
                subprocess.run([str(exe)], check=True, cwd=ROOT)


if __name__ == "__main__":
    unittest.main()
