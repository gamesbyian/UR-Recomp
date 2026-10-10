"""Exact guest-frame temporal analysis must not mistake held state for motion art."""
from pathlib import Path
import tempfile
import unittest

from tools.report_baldosa_1p_semantic_phases import assess


class OnePlayerTemporalPhasesTests(unittest.TestCase):
    def test_long_held_native_state_does_not_dominate_moving_pose_priority(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            stock, candidate, log = root / "base.crc", root / "native.crc", root / "native.log"
            stock.write_bytes(b"DEADBEEF\n" * 5447)
            candidate.write_bytes(stock.read_bytes())
            lines = ["script f=1720 until 00E1F ok after 351 frames\n"]
            for frame in range(1700, 5151):
                if frame <= 1720:
                    semantic, gate = "0542", "0000"
                elif frame <= 3399:
                    semantic = ("08D5", "0895", "0855")[(frame - 1721) % 3]
                    gate = "0000"
                elif frame <= 3638:
                    semantic, gate = f"{0x0A45 + ((frame - 3400) % 24):04X}", "0000"
                else:
                    semantic, gate = "0A4B", "0000" if frame < 3917 else "0100"
                lines.append(
                    f"UR_RACER_HD_CENSUS frame={frame} phase=gate "
                    f"status=original reason=unsupported-geometry\n"
                )
                lines.append(
                    f"UR_RACER_HD_1P_STATE frame={frame} semantic={semantic} "
                    f"primary={semantic} companion=0000 selector=0000 "
                    f"gate={gate} registered=0 art=0 selected=0 fallback=2\n"
                )
            lines.append("script f=5447 dump end ok\n")
            log.write_text("".join(lines))
            report = assess(stock, candidate, log)
            self.assertEqual(report["status"], "source-derived-1p-temporal-art-priorities")
            self.assertEqual(report["native_guest_crc_equal"], 5447)
            self.assertEqual(report["motion_rich_upper_bound_window"], [1721, 3399])
            self.assertEqual(report["motion_rich_source_frames"], 1679)
            self.assertEqual(report["transition_window"], [3400, 3638])
            self.assertEqual(report["transition_source_guest_frames"], 239)
            self.assertEqual(report["longest_held_semantic"]["semantic"], "0A4B")
            self.assertEqual(report["longest_held_semantic"]["start"], 3639)
            self.assertEqual(report["held_source_guest_frames"], 1512)
            self.assertEqual(report["held_source_gate_counts"], {"0000": 278, "0100": 1234})
            self.assertEqual({x["semantic_frame"] for x in report["motion_rich_semantic_top3"]},
                             {"08D5", "0895", "0855"})
            self.assertEqual(report["motion_rich_top3_fraction"], 1.0)
            self.assertFalse(report["new_art_approved"])
            self.assertFalse(report["source_alpha_and_final_ppu_priority_proven"])

            candidate.write_bytes(b"DEADBEEF\n" * 5446)
            with self.assertRaisesRegex(ValueError, "CRC"):
                assess(stock, candidate, log)
            candidate.write_bytes(stock.read_bytes())
            log.write_text("".join(lines[:-1]) + lines[-2] + lines[-1])
            with self.assertRaisesRegex(ValueError, "duplicate"):
                assess(stock, candidate, log)

    def test_held_state_threshold_is_bounded(self):
        with self.assertRaisesRegex(ValueError, "threshold"):
            assess(Path("/no/such/base"), Path("/no/such/candidate"),
                   Path("/no/such/log"), min_hold=30)


if __name__ == "__main__":
    unittest.main()
