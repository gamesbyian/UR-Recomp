"""Adversarial full-route source geometry census, never automatically authorize HD."""
import json
from pathlib import Path
import tempfile
import unittest

from tools.check_baldosa_1p_oam_art_visibility import assess, bounds, parse_oam


def trace(frame, semantic, registered, art, selected, fallback,
          tx=-80, ty=200, top=0, bx=96, by=96, bottom=1,
          obsel="83", bank=1, safe=1):
    gate = ("UR_RACER_HD_CENSUS frame={f} phase=gate "
            "status=original reason=unsupported-geometry\n").format(f=frame)
    state = (
        f"UR_RACER_HD_1P_STATE frame={frame} semantic={semantic} "
        f"primary={semantic} companion=0000 selector=0000 gate=0000 "
        f"registered={registered} art={art} selected={selected} fallback={fallback}\n"
    )
    oam = (
        f"UR_RACER_HD_1P_OAM frame={frame} source_ready=1 "
        f"top_x={tx} top_y={ty} top_tile=00 top_large=1 top_geom={top} "
        f"bottom_x={bx} bottom_y={by} bottom_tile=00 bottom_large=1 bottom_geom={bottom} "
        f"obsel={obsel} rotation=0 source_bank={bank} front_safe={safe}\n"
    )
    return gate + state + oam


class NativeOamArtWorklistTests(unittest.TestCase):
    def test_hardware_256line_wrap_and_original_split_geometry(self):
        self.assertTrue(bounds(96, 96, False))
        self.assertFalse(bounds(-80, 200, True))
        self.assertTrue(bounds(40, 250, True))  # OBJ wraps from Y250 to 0.
        self.assertFalse(bounds(40, 250, False))
        self.assertFalse(bounds(-64, 120, False))
        self.assertTrue(bounds(-63, 120, False))
        self.assertFalse(bounds(256, 120, False))

    def test_actual_guest_state_rank_excludes_offscreen_art_and_unsafe_p2(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            baseline, trial = root / "base.crc", root / "trial.crc"
            log = root / "native.log"
            baseline.write_bytes(b"DEADBEEF\n" * 5447)
            trial.write_bytes(baseline.read_bytes())
            start = "script f=1720 until 00E1F ok after 351 frames\n"
            end = "script f=5447 dump end ok\n"
            witness = (
                trace(1728, "0A4B", 0, 0, 0, 2)
                + trace(1744, "08D5", 0, 0, 0, 2,
                        bx=-80, by=200, bottom=0, safe=0)
                + trace(3000, "01B9", 1, 1, 1, 0, safe=0)
            )
            log.write_text(start + witness + end)
            report = assess(baseline, trial, log)
            self.assertEqual(report["native_guest_crc_equal"], 5447)
            self.assertEqual(report["native_post_race_milestone_guest_observations"], 3)
            self.assertEqual(report["classification"]["missing_art_total"], 2)
            self.assertEqual(report["classification"]["missing_art_onscreen_geometry_possible"], 1)
            self.assertEqual(report["classification"]["missing_art_conservative_p1_only_geometry_safe"], 1)
            self.assertEqual(report["classification"]["missing_art_original_stock_screen_empty_geometry"], 1)
            self.assertFalse(report["source_obj_alpha_visibility_proven"])
            self.assertFalse(report["new_art_approved"])
            self.assertFalse(report["wide_hd_admitted"])
            first = report["top_30_original_source_geometry_caller_states"][0]
            self.assertTrue(first["state"].startswith("0A4B:"))
            self.assertEqual(first["onscreen_geometry_possible"], 1)

            # Impossible geometry cannot gain provisional green source credit.
            log.write_text(start + witness.replace(
                "top_x=-80 top_y=200 top_tile=00 top_large=1 top_geom=0",
                "top_x=-80 top_y=200 top_tile=00 top_large=1 top_geom=1", 1) + end)
            with self.assertRaisesRegex(ValueError, "impossible"):
                assess(baseline, trial, log)

            # Changed source geometry must never borrow the same frame ID twice.
            log.write_text(start + witness + witness.splitlines(True)[2] + end)
            with self.assertRaisesRegex(ValueError, "duplicate"):
                assess(baseline, trial, log)

            log.write_text(start + witness + end)
            trial.write_bytes(b"DEADBEEF\n" * 5446)
            with self.assertRaisesRegex(ValueError, "CRC"):
                assess(baseline, trial, log)

    def test_native_reader_uses_exact_old_ppu_slots_before_geometry_gate(self):
        base = Path(__file__).resolve().parents[2]
        native = (base / "native/presentation/racer_hd_presenter.cpp").read_text()
        i = native.index('UR_RACER_HD_1P_OAM frame=%u')
        gate = native.index('racer_hd_can_capture_frame_geometry(')
        self.assertLess(i, gate)
        self.assertIn("racer_p1_only_no_stock_p2_occlusion(", native[:gate])
        self.assertIn("decode_racer_split_ppu_placement(", native[:gate])
        self.assertIn('trace[1] == \\'\\0\\' && number >= 1700', native)

    def test_inconsistent_oam_bank_and_front_safety_rejected(self):
        text = trace(1728, "0A4B", 0, 0, 0, 2)
        line = next(x for x in text.splitlines() if x.startswith("UR_RACER_HD_1P_OAM"))
        with self.assertRaisesRegex(ValueError, "source P1 OBJ"):
            parse_oam([line.replace("obsel=83", "obsel=00")])
        with self.assertRaisesRegex(ValueError, "priority bypass"):
            parse_oam([line.replace("source_bank=1", "source_bank=0")])


if __name__ == "__main__":
    unittest.main()
