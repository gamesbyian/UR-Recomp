"""ROM-free adversarial tests of the read-only Win32 ON/OFF QA08 campaign."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools import qa08_late_effective_windows_pair as pair


class Win32PairedWitnessTests(unittest.TestCase):
    def test_filters_logs_without_copying_game_stdout(self):
        log = "private/log.txt\nUR_QA08_LATE_PPU_SOURCE frame=5184\n" \
              "noise\nUR_QA08_LATE_SPAN_FINAL frame=5184\n"
        self.assertEqual(pair.source_lines(log),
                         "UR_QA08_LATE_PPU_SOURCE frame=5184\n"
                         "UR_QA08_LATE_SPAN_FINAL frame=5184\n")
        self.assertEqual(pair.source_lines("just unrelated host messages"), "\n")
        with self.assertRaisesRegex(ValueError, "exceeded bounded"):
            pair.source_lines("UR_QA08_LATE_SPAN_FINAL a\n" * 1001)
        with self.assertRaisesRegex(ValueError, "bytes exceeded"):
            pair.source_lines("UR_QA08_LATE_SPAN_SOURCE " + "x" * 510000)

    def test_immutable_rom_controller_and_crc_contract(self):
        self.assertEqual(pair.ROM_SHA,
                         "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478")
        self.assertEqual(pair.EXPECTED_ROUTE,
                         "ef74ec51fa585aa76652f4a14d2727f0074434b3925522ab2607e3bd29aa0194")
        self.assertEqual(pair.EXPECTED_CRC,
                         "b735b0183b296ce32db009b282fab18bc9f9cf26668c02231373e9740184c568")
        self.assertEqual(pair.ENV, "UR_QA08_LATE_EFFECTIVE_PIXEL_TRACE")

    def test_wrong_rom_or_script_or_duplicate_pe_fails_before_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args = []
            for name in ("off", "on", "rom", "route", "original", "native"):
                path = root / name
                path.write_bytes(name.encode())
                args.append(path)
            with patch.object(pair, "run_route", side_effect=AssertionError("guest ran")):
                with self.assertRaisesRegex(ValueError,"ROM or actual controller"):
                    pair.run_pair(*args, root/"output", 360)
            self.assertFalse((root/"output").exists())

    def test_missing_source_and_output_collision_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args = []
            for name in ("off", "on", "rom", "route", "original", "native"):
                path = root/name
                path.write_bytes(name.encode())
                args.append(path)
            for timeout in (0, 721):
                with self.assertRaisesRegex(ValueError, "missing qualified"):
                    pair.run_pair(*args, root/"output", timeout)
            out = root/"output"
            out.mkdir()
            with self.assertRaisesRegex(ValueError, "output collision"):
                pair.run_pair(*args, out, 360)

    def test_real_cli_rejects_unprovided_source_paths(self):
        result = subprocess.run(
            [sys.executable, str(ROOT/"tools/qa08_late_effective_windows_pair.py"),
             "--off-exe", "missing-off.exe", "--on-exe", "missing-on.exe",
             "--rom", "missing.sfc", "--script", "missing-route.txt",
             "--original-inner", "missing-original.zip",
             "--native-outer", "missing-native.zip",
             "--out", "missing-run"],
            cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn("QA08_WIN32_EFFECTIVE_SOURCE_REFUSED:", result.stderr)


if __name__ == "__main__":
    unittest.main()
