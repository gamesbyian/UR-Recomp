import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class UniracersChallengeAwardCppTests(unittest.TestCase):
    def test_stock_award_previous_medal_adapter(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "challenge-award-test"
            subprocess.run(
                [
                    "g++",
                    "-std=c++17",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    "-pedantic",
                    "-I",
                    str(ROOT / "native" / "title"),
                    str(ROOT / "native" / "title" /
                        "uniracers_challenge_award.cpp"),
                    str(ROOT / "tests" / "native" /
                        "uniracers_challenge_award_test.cpp"),
                    "-o",
                    str(exe),
                ],
                cwd=ROOT,
                check=True,
            )
            subprocess.run([str(exe)], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
