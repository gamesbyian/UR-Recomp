#!/usr/bin/env python3
"""Focus on source-derived Win32 guest CRC and pause-proof parser semantics."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import baldosa_windows_native_pause_route as probe


class NativeWindowsPauseProbeTests(unittest.TestCase):
    def test_reads_authoritative_framedump_crc_in_numeric_order(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for frame, value in ((10, "0xABCD"), (2, "0x00FF"), (1, "0x1234")):
                (root / f"frame_{frame:06}.json").write_text(
                    '{"crc32_wram": "' + value + '"}')
            self.assertEqual(probe.frame_crcs(root),
                             ["0x1234", "0x00ff", "0xabcd"])

    def test_missing_or_malformed_frame_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(ValueError, "No real"):
                probe.frame_crcs(root)
            (root / "frame_000001.json").write_text('{"bogus": "0xAA"}')
            with self.assertRaisesRegex(ValueError, "Missing real"):
                probe.frame_crcs(root)
            (root / "frame_000001.json").unlink()
            (root / "frame_invalid.json").write_text('{"crc32_wram": "0xAA"}')
            with self.assertRaisesRegex(ValueError, "Unexpected"):
                probe.frame_crcs(root)

    def test_pause_needs_all_three_real_witnesses(self):
        valid = ("UR_BALDOSA_NATIVE_PAUSE ARMED guest=1952 live_race=1 modern_session=1 physical_sdl=1\n"
                 "UR_BALDOSA_NATIVE_PAUSE RELEASED guest=1952 frozen_pumps=24 physical_sdl=1\n"
                 "UR_BALDOSA_NATIVE_PAUSE RESUMED previous_guest=1952 new_guest=1953 frozen_pumps=24\n")
        self.assertEqual(set(probe.check_pause_log(valid)),
                         {"ARMED", "RELEASED", "RESUMED"})
        with self.assertRaisesRegex(ValueError, "live gameplay"):
            probe.check_pause_log(valid.replace("live_race=1", "live_race=0"))
        with self.assertRaisesRegex(ValueError, "Modern session API"):
            probe.check_pause_log(valid.replace("modern_session=1", "modern_session=0"))
        with self.assertRaisesRegex(ValueError, "physical SDL key edges"):
            probe.check_pause_log(valid.replace("physical_sdl=1", "physical_sdl=0"))
        with self.assertRaisesRegex(ValueError, "Missing"):
            probe.check_pause_log(valid.replace(" RESUMED ", " MISSING "))
        with self.assertRaisesRegex(ValueError, "too short"):
            probe.check_pause_log(valid.replace("frozen_pumps=24", "frozen_pumps=2"))
        with self.assertRaisesRegex(ValueError, "violation"):
            probe.check_pause_log(valid + "UR_BALDOSA_NATIVE_PAUSE FAIL=wrong\n")


if __name__ == "__main__":
    unittest.main()
