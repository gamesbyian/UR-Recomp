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


class UniracersWsMarginsCTests(unittest.TestCase):
    def test_c_core(self):
        for compiler in ("gcc", "clang"):
            with self.subTest(compiler=compiler), tempfile.TemporaryDirectory() as tmp:
                exe = pathlib.Path(tmp) / "uniracers-ws-margins-test"
                subprocess.run(
                [
                    compiler,
                    *STRICT_C_FLAGS,
                    "-fsanitize=address,undefined",
                    "-fno-omit-frame-pointer",
                    "-DUR_WS_MARGINS_NO_RUNTIME",
                    "-I",
                    str(ROOT / "native" / "title"),
                    str(ROOT / "native" / "title" / "uniracers_ws_margins.c"),
                    str(ROOT / "tests" / "native" / "uniracers_ws_margins_test.c"),
                    "-o",
                    str(exe),
                ],
                    cwd=ROOT,
                    check=True,
                )
                subprocess.run([str(exe)], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
