import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class LocalTournamentReceiptRestoreCppTests(unittest.TestCase):
    def test_batch_restores_only_explicitly_bound_receipts(self):
        with tempfile.TemporaryDirectory() as work:
            exe = pathlib.Path(work) / "tournament-receipt-restore"
            subprocess.run(
                [
                    "g++", "-std=c++17", "-Wall", "-Wextra",
                    "-Werror", "-pedantic",
                    "-I", str(ROOT / "native/product"),
                    "-I", str(ROOT / "native/title"),
                    str(ROOT / "tests/native/local_tournament_receipt_restore_test.cpp"),
                    "-o", str(exe),
                ],
                check=True, cwd=ROOT,
            )
            subprocess.run([str(exe)], check=True, cwd=ROOT)


if __name__ == "__main__":
    unittest.main()
