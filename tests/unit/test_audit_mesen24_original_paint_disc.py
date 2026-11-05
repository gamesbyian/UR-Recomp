"""Source-only controls for the authentic 48-tick paint/disc cross-check."""
import copy
import unittest

from tools.art.audit_mesen24_original_paint_disc import (
    ROLES, SCHEMA, SOURCE_PPU_SHA, SOURCE_POSE_SHA, SOURCE_SCHEMA,
    ORIGINAL_ROM_SHA256, summarize_variants, verified_manifest,
)


def packet():
    records = []
    for role, (_, slot, _) in ROLES.items():
        for tick in range(1601, 1625):
            records.append({
                "role": role,
                "tick": tick,
                "png": f"{role}-{tick}.png",
                "png_sha256": "a" * 64,
                "source_RGBA_sha256": "b" * 64,
                "source_4bpp_plane_sha256": "c" * 64,
                "original_OAM_slot": slot,
                "original_ROM_frame_ID": 64 * 3 + 17,
                "source_phase_index": 3,
                "source_orientation_index": 17,
            })
    return {
        "schema": SOURCE_SCHEMA,
        "source_USA_ROM_sha256": ORIGINAL_ROM_SHA256,
        "original_Mesen24_source_sha256": SOURCE_PPU_SHA,
        "exact_original_ROM_pose_receipt_sha256": SOURCE_POSE_SHA,
        "source_pixel_size": [64, 64],
        "display_pixel_aspect": [7, 6],
        "source_sprite_index_zero_transparent": True,
        "original_1994_3D_mesh_camera_pose_recovered": False,
        "original_source_to_2026_GLB_joint_pose_verified": False,
        "frames": records,
    }


def observation(role, tick, mask, rgba, disc, top):
    return {
        "role": role, "tick": tick,
        "binary_mask_sha256": mask,
        "rgba_sha256": rgba,
        "all_tied_source_wheel_disc_fractions": disc,
        "all_tied_source_at_or_below_ring_top_fractions": top,
    }


class OriginalMesen24PaintDiscTests(unittest.TestCase):
    def test_exact_source_pins_and_all_48_unique_chronological_records(self):
        records = verified_manifest(packet())
        self.assertEqual(len(records), 48)
        self.assertEqual(records["blue", 1601]["original_OAM_slot"], 96)
        self.assertEqual(records["red", 1624]["original_OAM_slot"], 97)

    def test_invalid_source_is_not_reinterpreted_as_new_art_or_anatomy(self):
        for mutation in ("rom", "ppu", "pose", "wrong_3d", "art",
                         "one_missing", "duplicate", "png_traversal",
                         "wrong_orientation", "wrong_slot", "bad_hash",
                         "wrong_pixel_aspect"):
            data = packet()
            if mutation == "rom":
                data["source_USA_ROM_sha256"] = "0" * 64
            elif mutation == "ppu":
                data["original_Mesen24_source_sha256"] = "0" * 64
            elif mutation == "pose":
                data["exact_original_ROM_pose_receipt_sha256"] = "0" * 64
            elif mutation == "wrong_3d":
                data["original_1994_3D_mesh_camera_pose_recovered"] = True
            elif mutation == "art":
                data["original_source_to_2026_GLB_joint_pose_verified"] = True
            elif mutation == "one_missing":
                data["frames"].pop()
            elif mutation == "duplicate":
                data["frames"][1] = dict(data["frames"][0])
            elif mutation == "png_traversal":
                data["frames"][0]["png"] = "../blue-1601.png"
            elif mutation == "wrong_orientation":
                data["frames"][0]["source_orientation_index"] = 2
            elif mutation == "wrong_slot":
                data["frames"][0]["original_OAM_slot"] = 97
            elif mutation == "bad_hash":
                data["frames"][0]["source_RGBA_sha256"] = "broken"
            elif mutation == "wrong_pixel_aspect":
                data["display_pixel_aspect"] = [1, 1]
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                verified_manifest(data)

    def test_one_vote_per_alpha_not_24_repeated_frames(self):
        # The A mask appears on two ticks, with two genuine RGB variants.
        # It is weighted ONCE, after equal weighting its two variants and
        # conservatively retaining the multiple true wheel-centre ties.
        rows = [
            observation("blue", 1601, "a"*64, "1"*64, [.5, .7], [.6, .9]),
            observation("blue", 1602, "a"*64, "1"*64, [.5, .7], [.6, .9]),
            observation("blue", 1603, "a"*64, "2"*64, [.3, .9], [.4, .8]),
            observation("blue", 1604, "b"*64, "3"*64, [.1], [.5]),
            observation("red", 1601, "c"*64, "4"*64, [.2, .6], [.7, .8]),
        ]
        report = summarize_variants(rows, expected_shapes={"blue": 2, "red": 1})
        blue = report["blue"]
        self.assertEqual(blue["unique_original_binary_shapes_equal_vote"], 2)
        self.assertEqual(blue["original_rgba_variant_count"], 3)
        # Alpha-A low = (.5+.3)/2=.4; alpha-B low=.1; equal-shape .25.
        self.assertEqual(blue["mean_source_chroma_inside_wheel_disc_low"], .25)
        self.assertEqual(blue["mean_source_chroma_inside_wheel_disc_high"], .45)
        self.assertEqual(report["red"]["mean_source_chroma_inside_wheel_disc_low"], .2)
        self.assertEqual(report["red"]["mean_source_chroma_inside_wheel_disc_high"], .6)

    def test_ambiguous_source_rgb_cannot_silently_shift_between_ticks(self):
        rows = [
            observation("blue", 1601, "a"*64, "b"*64, [.4], [.6]),
            observation("blue", 1602, "a"*64, "b"*64, [.6], [.7]),
            observation("red", 1601, "c"*64, "d"*64, [.5], [.7]),
        ]
        with self.assertRaisesRegex(ValueError, "identical original RGBA"):
            summarize_variants(rows, expected_shapes={"blue": 1, "red": 1})
        rows[1] = observation("blue", 1602, "a"*64, "b"*64, [.4], [.6])
        result = summarize_variants(rows, expected_shapes={"blue": 1, "red": 1})
        self.assertEqual(result["blue"]["original_rgba_variant_count"], 1)
        rows[2]["all_tied_source_wheel_disc_fractions"] = [float("nan")]
        with self.assertRaisesRegex(ValueError, "invalid tied"):
            summarize_variants(rows, expected_shapes={"blue": 1, "red": 1})


if __name__ == "__main__":
    unittest.main()
