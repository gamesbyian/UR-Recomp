import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class MultiplayerMatchBrowserCppTests(unittest.TestCase):
    def test_cpp_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "multiplayer-match-browser-test"
            subprocess.run(
                [
                    "g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-pedantic",
                    "-I", str(ROOT / "native" / "product"),
                    "-I", str(ROOT / "native" / "title"),
                    str(ROOT / "native" / "product" / "run_artifact_date.cpp"),
                    str(ROOT / "native" / "product" / "multiplayer_match_presentation.cpp"),
                    str(ROOT / "native" / "product" / "multiplayer_match_browser.cpp"),
                    str(ROOT / "tests" / "native" / "multiplayer_match_browser_test.cpp"),
                    "-o", str(exe),
                ],
                cwd=ROOT,
                check=True,
            )
            subprocess.run([str(exe)], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
