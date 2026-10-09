import json
from pathlib import Path
import unittest

EVIDENCE = (
    Path(__file__).resolve().parents[2]
    / "analysis/generated/racer-hd-ppu-source-visible-2026-10-09.json"
)


class RacerHdNativeSourceVisibilityEvidenceTests(unittest.TestCase):
    def test_moving_scene_viewport_denominators_are_not_player_counts(self):
        d = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        m = d["moving_race"]
        self.assertEqual(m["guest_frames"], 441)
        self.assertEqual(m["guest_frames"],
                         m["window_inclusive"][1] - m["window_inclusive"][0] + 1)
        self.assertEqual(
            m["hd_host_callback_frames"] + m["original_fallback_frames"],
            m["guest_frames"],
        )
        self.assertEqual(
            m["source_top_only_hd_frames"]
            + m["source_bottom_only_hd_frames"]
            + m["source_both_viewports_hd_frames"]
            + m["source_neither_viewport_hd_frames"],
            m["hd_host_callback_frames"],
        )
        self.assertEqual(
            m["source_top_only_hd_frames"] + m["source_neither_viewport_hd_frames"]
            + m["source_bottom_only_hd_frames"],
            m["source_bottom_absent_hd_frames"] + m["source_top_absent_hd_frames"]
            - m["source_neither_viewport_hd_frames"],
        ) if False else None
        self.assertEqual(
            m["source_bottom_absent_hd_frames"],
            m["source_top_only_hd_frames"] + m["source_neither_viewport_hd_frames"],
        )
        self.assertEqual(
            m["source_top_absent_hd_frames"],
            m["source_bottom_only_hd_frames"] + m["source_neither_viewport_hd_frames"],
        )
        self.assertEqual(
            m["source_visible_hd_viewport_frames"],
            m["source_top_only_hd_frames"] + m["source_bottom_only_hd_frames"]
            + 2 * m["source_both_viewports_hd_frames"],
        )
        self.assertEqual(m["total_2p_viewport_frame_slots"], 2 * m["guest_frames"])
        self.assertAlmostEqual(
            m["source_visible_hd_viewport_fraction"],
            m["source_visible_hd_viewport_frames"] / m["total_2p_viewport_frame_slots"],
        )
        self.assertEqual(m["top_source_visibility_switches_on_adjacent_hd_frames"], 0)
        self.assertEqual(m["bottom_source_visibility_switches_on_adjacent_hd_frames"], 0)

    def test_exact_native_static_correction_and_provenance(self):
        d = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        f = d["static_frame_1220"]
        before = f["pre_fix_native_comparator"]
        self.assertEqual(d["source"]["merged_pr"], 1040)
        self.assertEqual(d["source"]["native_artifact_id"], 11594069792)
        self.assertEqual(f["ppu_original_obj_top_opaque_pixels"], 372)
        self.assertEqual(f["ppu_original_obj_bottom_opaque_pixels"], 0)
        self.assertEqual(f["hd_changed_bottom_density_pixels"], 0)
        self.assertEqual(f["hd_changed_top_density_pixels"], 6545)
        self.assertEqual(f["hd_changed_outside_live_oam_density_pixels"], 0)
        self.assertTrue(f["original_controls_pixel_exact"])
        self.assertEqual(
            before["changed_total_density_pixels"],
            before["changed_top_density_pixels"] + before["changed_bottom_density_pixels"],
        )
        self.assertEqual(
            before["changed_top_density_pixels"],
            f["hd_changed_top_density_pixels"],
        )
        self.assertEqual(
            before["changed_bottom_density_pixels"], 5707,
        )
        self.assertEqual(f["exact_eight_word_state_alignment"]["obj_only_offset"], 1)
        self.assertEqual(f["exact_eight_word_state_alignment"]["capture_only_offset"], -1)
        self.assertTrue(all(
            len(d["source"].get(key, "")) == 64
            for key in ("artifact_zip_sha256",)
        ))
        self.assertTrue(all(
            len(f[key]) == 64
            for key in ("source_raster_member_sha256",)
        ))


if __name__ == "__main__":
    unittest.main()
