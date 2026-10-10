"""No invented Remastered coverage: rank real native guest semantic composition states."""
from pathlib import Path
import tempfile
import unittest

from tools.check_baldosa_1p_art_state_worklist import assess


class OnePlayerSemanticWorklistTests(unittest.TestCase):
    def test_native_registered_missing_asset_and_composition_gaps_separate(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            original, candidate, log = root / "stock.crc", root / "native.crc", root / "native.log"
            original.write_bytes(b"12345678\n" * 5447)
            candidate.write_bytes(original.read_bytes())
            intro = "script f=1720 until 00E1F ok after 351 frames\n"
            trace = (
                "UR_RACER_HD_CENSUS frame=1728 phase=gate status=armed reason=p1-only\n"
                "UR_RACER_HD_1P_STATE frame=1728 semantic=0439 primary=0439 "
                "companion=0000 selector=0011 gate=0022 registered=1 art=1 "
                "selected=1 fallback=0\n"
                "UR_RACER_HD_CENSUS frame=1744 phase=gate status=original "
                "reason=p1-selection-or-art\n"
                "UR_RACER_HD_1P_STATE frame=1744 semantic=01B9 primary=01B9 "
                "companion=0000 selector=0033 gate=0044 registered=0 art=1 "
                "selected=0 fallback=3\n"
                "UR_RACER_HD_CENSUS frame=3000 phase=gate status=original "
                "reason=p1-selection-or-art\n"
                "UR_RACER_HD_1P_STATE frame=3000 semantic=F999 primary=F999 "
                "companion=0000 selector=0000 gate=0000 registered=0 art=0 "
                "selected=0 fallback=2\n"
            )
            log.write_text(intro + trace + "script f=5447 dump end ok\n")
            report = assess(original, candidate, log)
            self.assertEqual(report["post_milestone_trace_guest_frames"], 3)
            self.assertEqual(report["missing_authored_asset_samples"], 1)
            self.assertEqual(report["registered_art_state_mismatch_samples"], 1)
            self.assertEqual(report["registered_state_samples"], 1)
            self.assertEqual(report["top_missing_art_exact_states"][0]["guest_frames"], 1)
            self.assertFalse(report["release_art_approval"])
            self.assertFalse(report["widescreen_hd_admission"])

            log.write_text(intro + trace + trace +
                           "script f=5447 dump end ok\n")
            with self.assertRaisesRegex(ValueError, "duplicate"):
                assess(original, candidate, log)
            log.write_text(intro + trace.replace(
                "registered=0 art=0 selected=0 fallback=2",
                "registered=0 art=0 selected=9 fallback=2") +
                "script f=5447 dump end ok\n")
            with self.assertRaisesRegex(ValueError, "malformed"):
                assess(original, candidate, log)
            log.write_text(intro + trace + "script f=5447 dump end ok\n")
            candidate.write_bytes(original.read_bytes().replace(b"12345678", b"33333333", 1))
            with self.assertRaisesRegex(ValueError, "CRC"):
                assess(original, candidate, log)

    def test_diagnostic_is_guest_read_only_and_opt_in(self):
        source = (Path(__file__).resolve().parents[2] /
                  "native/presentation/racer_hd_presenter.cpp").read_text()
        self.assertIn('std::getenv("UR_RACER_HD_1P_STATE_TRACE")', source)
        self.assertIn("read_racer_guest_snapshot(g_ram, 0x20000)", source)
        self.assertIn("number >= 1700 && number <= 5150", source)
        self.assertIn('g_ram[0x009F] == 0x3Cu', source)
        self.assertEqual(source.count("UR_RACER_HD_1P_STATE frame=%u"), 1)


if __name__ == "__main__":
    unittest.main()
