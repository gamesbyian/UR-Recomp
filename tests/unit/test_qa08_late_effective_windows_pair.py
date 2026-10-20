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

    def test_same_epoch_controls_run_both_before_historical_refusal(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            paths = [root / x for x in ("off.exe", "on.exe", "rom.sfc",
                                       "route.txt", "orig.zip", "native.zip")]
            for path, data in zip(paths, (b"off", b"on", b"ROM", b"input",
                                          b"historical", b"native")):
                path.write_bytes(data)
            crc = [f"0x{i:08x}" for i in range(5484)]
            fake = {"anchors": [{
                "xy": [70, 58], "actual_renderer": "span", "main_layer": 0,
                "main_directcolor": False, "main_selected_palette_index": 108,
                "main_actual_resolved_rgb555": "4a52",
                "main_current_index_CGRAM_word": "4a52",
                "current_main_CGRAM_6c_6f": ["4a52", "4631", "4210", "56b5"],
                "new_native_final_RGB5": [17, 17, 17],
            }]}
            out = root / "campaign"
            with (patch.object(pair, "ROM_SHA", pair.sha(b"ROM")),
                  patch.object(pair, "EXPECTED_ROUTE", pair.sha(b"input")),
                  patch.object(pair, "run_route", side_effect=[
                      (crc, "unrelated control stdout"), (crc, "unrelated observer stdout")]) as native,
                  patch.object(pair, "summarize_trace", return_value=fake),
                  patch.object(pair, "verify", side_effect=AssertionError("historical promoted"))):
                with self.assertRaisesRegex(ValueError,
                                            "historic RF017 CRC did not"):
                    pair.run_pair(*paths, out, 360)
            self.assertEqual(native.call_count, 2)
            receipt = json.loads((out/"status.json").read_text())
            self.assertEqual(receipt["actual_source_process_runs"], 2)
            self.assertEqual(receipt["off_CRC_sha256"],receipt["on_CRC_sha256"])
            self.assertTrue(receipt["same_epoch_ON_OFF_guest_CRC_equal"])
            self.assertFalse(receipt["historical_RF017_guest_CRC_qualified"])
            self.assertTrue(receipt["unadmitted_PPU_observation_only"])
            self.assertFalse(receipt["QA08_QA10_release_accepted"])
            self.assertEqual(receipt["unadmitted_live_PPU_sample"][0]["main_selected_palette_index"],108)
            self.assertIs(receipt["unadmitted_live_PPU_sample"][0]["same_historical_original_native_source_epoch_proven"],False)
            self.assertEqual(receipt["final_diagnostic_outcome"],"REFUSED")
            self.assertNotIn("effective_source",receipt)

    def test_on_off_crc_divergence_is_refusal_without_palette_promotion(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            paths=[root/x for x in ("off","on","rom","route","original","native")]
            for p,data in zip(paths,(b"a",b"b",b"r",b"s",b"o",b"n")):
                p.write_bytes(data)
            off=["0x00000000"]*5484
            on=off[:]
            on[-1]="0x00000001"
            with (patch.object(pair,"ROM_SHA",pair.sha(b"r")),
                  patch.object(pair,"EXPECTED_ROUTE",pair.sha(b"s")),
                  patch.object(pair,"run_route",side_effect=[(off,""),(on,"")]) as native,
                  patch.object(pair,"summarize_trace",side_effect=AssertionError("promoted"))):
                with self.assertRaisesRegex(ValueError,"changed real guest CRC"):
                    pair.run_pair(*paths,root/"out",360)
            receipt=json.loads((root/"out/status.json").read_text())
            self.assertEqual(native.call_count,2)
            self.assertFalse(receipt["same_epoch_ON_OFF_guest_CRC_equal"])
            self.assertFalse(receipt["unadmitted_PPU_observation_only"])
            self.assertFalse(receipt["complete_guest_replay_equivalence_proven"])
            self.assertFalse(receipt["QA08_QA10_release_accepted"])

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
