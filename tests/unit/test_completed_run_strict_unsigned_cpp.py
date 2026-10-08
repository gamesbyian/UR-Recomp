import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
PRODUCT = ROOT / "native" / "product"


class StrictUnsignedCodecTests(unittest.TestCase):
    def test_checksum_valid_signed_integer_regressions(self):
        with tempfile.TemporaryDirectory() as work:
            exe = pathlib.Path(work) / "strict-unsigned-codec"
            subprocess.run(
                [
                    "g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
                    "-pedantic", "-I", str(PRODUCT),
                    str(PRODUCT / "completed_run_record.cpp"),
                    str(PRODUCT / "completed_run_ghost.cpp"),
                    str(PRODUCT / "completed_run_ghost_trace.cpp"),
                    str(ROOT / "tests/native/completed_run_strict_unsigned_test.cpp"),
                    "-o", str(exe),
                ],
                cwd=ROOT, check=True,
            )
            subprocess.run([str(exe)], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
