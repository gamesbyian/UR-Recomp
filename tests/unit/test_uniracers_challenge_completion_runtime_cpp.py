import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class ChallengeCompletionRuntimeCppTests(unittest.TestCase):
    def test_selected_tour_stunt_and_award_lifecycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "challenge-completion-runtime-test"
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
                        "uniracers_challenge_qualification.cpp"),
                    str(ROOT / "native" / "title" /
                        "uniracers_challenge_award.cpp"),
                    str(ROOT / "native" / "title" /
                        "uniracers_challenge_completion_runtime.cpp"),
                    str(ROOT / "native" / "title" /
                        "uniracers_challenge_generation_bridge.c"),
                    str(ROOT / "tests" / "native" /
                        "uniracers_challenge_completion_runtime_test.cpp"),
                    "-o",
                    str(exe),
                ],
                cwd=ROOT,
                check=True,
            )
            subprocess.run([str(exe)], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
