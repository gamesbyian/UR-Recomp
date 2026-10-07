import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]


class MultiplayerMatchRecordCppTests(unittest.TestCase):
    def test_cpp_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "multiplayer-match-record-test"
            subprocess.run(
                [
                    "g++",
                    "-std=c++17",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    "-pedantic",
                    "-I",
                    str(ROOT / "native" / "product"),
                    "-I",
                    str(ROOT / "native" / "title"),
                    str(ROOT / "native" / "product" / "modern_racer_identity.cpp"),
                    str(ROOT / "native" / "product" / "multiplayer_match_record.cpp"),
                    str(
                        ROOT
                        / "tests"
                        / "native"
                        / "multiplayer_match_record_test.cpp"
                    ),
                    "-o",
                    str(exe),
                ],
                cwd=ROOT,
                check=True,
            )
            subprocess.run([str(exe)], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
