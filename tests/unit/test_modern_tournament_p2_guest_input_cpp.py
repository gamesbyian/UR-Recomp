import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]

class TournamentP2GuestWordTests(unittest.TestCase):
    def test_mapped_word_release_latch_in_cpp(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "p2-guest"
            subprocess.run(
                ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-pedantic",
                 "-I", str(ROOT / "native/product"),
                 str(ROOT / "tests/native/modern_tournament_p2_guest_input_test.cpp"),
                 "-o", str(exe)], cwd=ROOT, check=True)
            subprocess.run([str(exe)], cwd=ROOT, check=True)

if __name__ == "__main__":
    unittest.main()
