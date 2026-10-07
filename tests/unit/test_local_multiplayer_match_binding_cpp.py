import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class LocalMultiplayerMatchBindingCppTests(unittest.TestCase):
    def test_explicit_profiles_bind_only_when_guest_riders_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "local-multiplayer-match-binding-test"
            subprocess.run(
                [
                    "g++",
                    "-std=c++17",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    "-pedantic",
                    "-I",
                    str(ROOT / "native/product"),
                    "-I",
                    str(ROOT / "native/title"),
                    str(ROOT / "tests/native/local_multiplayer_match_binding_test.cpp"),
                    str(ROOT / "native/product/local_multiplayer_match_binding.cpp"),
                    str(ROOT / "native/product/modern_racer_identity.cpp"),
                    str(ROOT / "native/title/uniracers_course_identity.cpp"),
                    "-o",
                    str(exe),
                ],
                cwd=ROOT,
                check=True,
            )
            subprocess.run([str(exe)], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
