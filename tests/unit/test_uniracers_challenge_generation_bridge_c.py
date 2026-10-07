import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


STRICT_C_FLAGS = [
    "-std=c11",
    "-Wall",
    "-Wextra",
    "-Wpedantic",
    "-Werror",
    "-Wconversion",
    "-Wsign-conversion",
    "-Wshadow",
    "-Wstrict-prototypes",
    "-Wmissing-prototypes",
]


class ChallengeGenerationBridgeCTests(unittest.TestCase):
    def test_default_pass_through_and_typed_filter(self):
        for compiler in ("gcc", "clang"):
            with self.subTest(compiler=compiler), tempfile.TemporaryDirectory() as tmp:
                exe = pathlib.Path(tmp) / "challenge-generation-bridge-test"
                subprocess.run(
                [
                    compiler,
                    *STRICT_C_FLAGS,
                    "-fsanitize=address,undefined",
                    "-fno-omit-frame-pointer",
                    "-I",
                    str(ROOT / "native" / "title"),
                    str(ROOT / "native" / "title" /
                        "uniracers_challenge_generation_bridge.c"),
                    str(ROOT / "tests" / "native" /
                        "uniracers_challenge_generation_bridge_test.c"),
                    "-o",
                    str(exe),
                ],
                    cwd=ROOT,
                    check=True,
                )
                subprocess.run([str(exe)], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
