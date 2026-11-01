"""ROM-free adversarial tests for ART-4K source-bound projected proportions."""
import hashlib
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[2] / "tools/art/audit_original_racer_projected_masses.py"
spec = importlib.util.spec_from_file_location("original_projected_masses", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def make_frame(upper=21, lower=24):
    data = bytearray(64 * 64 * 4)
    for y in range(2, 10):
        for x in range(upper, upper + 16):
            data[4*(y*64+x):4*(y*64+x)+4] = bytes((31, 31, 31, 255))
    for y in range(22, 39):
        for x in range(lower, lower + 18):
            data[4*(y*64+x):4*(y*64+x)+4] = bytes((31, 31, 31, 255))
    return bytes(data)


def corpus_fixture():
    originals, rows = {}, []
    for player, distinct in (("p1", 6), ("p2", 4)):
        for frame in mod.FRAMES:
            i = min(distinct-1, (frame-1205)*distinct//16)
            source = f"stock/{player}-{i:02}.png"
            pixels = make_frame(20+i+(player=="p2"), 24+(player=="p2"))
            png_sha = hashlib.sha256(source.encode()).hexdigest()
            originals[source] = (pixels, png_sha)
            rows.append({
                "player": player, "guest_frame": frame, "source_image": source,
                "png_file_sha256": png_sha,
                "source_rgba_sha256": hashlib.sha256(pixels).hexdigest(),
                "binary_mask_sha256": hashlib.sha256(
                    bytes(int(a != 0) for a in pixels[3::4])).hexdigest(),
            })
    return ({
        "schema": "UR-RACER-SOURCE-PIXEL-CORPUS/1",
        "historical_manifest_declared_rom_sha256": mod.ROM_SHA,
        "frame_observation_count": 32,
        "distinct_binary_silhouette_groups": 10,
        "decoded_png_rgba_sha_verified_against_review_manifest": True,
        "source_registry_current_sha256": "a"*64,
        "showcase_manifest_sha256": {"p1": "b"*64, "p2": "c"*64},
        "observations": rows,
    }, lambda obs: originals[obs["source_image"]])


class ProjectedMassTests(unittest.TestCase):
    def test_pixel_aspect_and_integer_bounds(self):
        m = mod.raster_masses(make_frame())
        self.assertEqual(m["upper_source_bbox_xyxy_inclusive"], [21, 2, 36, 9])
        self.assertEqual(m["lower_source_bbox_xyxy_inclusive"], [24, 22, 41, 38])
        r = m["physical_7_6_projected_ratios"]
        self.assertEqual(r["lower_width_over_lower_height"], round(18 * 7 / 6 / 17, 6))
        self.assertEqual(r["upper_width_over_lower_height"], round(16 * 7 / 6 / 17, 6))

    def test_temporal_duplicates_count_once_and_claims_stay_false(self):
        corpus, reader = corpus_fixture()
        r = mod.reduce_authenticated_observations(corpus, reader)
        self.assertEqual(r["original_observations"], 32)
        self.assertEqual(r["independent_source_binary_shapes"], 10)
        self.assertEqual(r["summary"]["p1"]["independent_silhouettes"], 6)
        self.assertEqual(r["summary"]["p2"]["independent_silhouettes"], 4)
        self.assertTrue(r["equal_weight_per_independent_mask"])
        self.assertFalse(r["original_3d_camera_or_geometry_identified"])
        self.assertFalse(r["original_pose_to_2026_glb_pose_mapping_verified"])
        self.assertFalse(r["heldout_different_source_family_verified"])
        self.assertFalse(r["original_character_likeness_approved"])

    def test_nonbinary_cropped_and_truncated_inputs_fail(self):
        pixels = bytearray(make_frame())
        pixels[3] = 120
        with self.assertRaisesRegex(ValueError, "nonbinary"):
            mod.raster_masses(bytes(pixels))
        pixels = bytearray(make_frame())
        for x in range(64):
            pixels[4*(38*64+x)+3] = 0
        with self.assertRaisesRegex(ValueError, "ordinary-racer"):
            mod.raster_masses(bytes(pixels))
        with self.assertRaisesRegex(ValueError, "64x64"):
            mod.raster_masses(b"invalid")

    def test_forged_file_rgba_mask_and_rom_hash_fail(self):
        for key, value, error in (
            ("png_file_sha256", "0"*64, "SHA mismatch"),
            ("source_rgba_sha256", "0"*64, "SHA mismatch"),
            ("binary_mask_sha256", "0"*64, "binary-mask"),
        ):
            corpus, reader = corpus_fixture()
            corpus["observations"][0][key] = value
            with self.subTest(field=key), self.assertRaisesRegex(ValueError, error):
                mod.reduce_authenticated_observations(corpus, reader)
        corpus, reader = corpus_fixture()
        corpus["historical_manifest_declared_rom_sha256"] = "f"*64
        with self.assertRaises(ValueError):
            mod.reduce_authenticated_observations(corpus, reader)

    def test_duplicate_frame_wrong_player_and_fake_shape_census_fail(self):
        corpus, reader = corpus_fixture()
        corpus["observations"][0]["guest_frame"] = 1206
        with self.assertRaisesRegex(ValueError, "duplicate"):
            mod.reduce_authenticated_observations(corpus, reader)
        corpus, reader = corpus_fixture()
        corpus["observations"][0]["player"] = "p3"
        with self.assertRaises(ValueError):
            mod.reduce_authenticated_observations(corpus, reader)
        corpus, reader = corpus_fixture()
        corpus["distinct_binary_silhouette_groups"] = 11
        with self.assertRaises(ValueError):
            mod.reduce_authenticated_observations(corpus, reader)

    def test_real_retained_original_pngs_and_corpus_when_present(self):
        strip = mod.STRIP
        if not (strip / "inputs-p1.json").is_file():
            self.skipTest("requires repository's retained original first-family PNGs")
        r = mod.audit()
        self.assertEqual(r["independent_source_binary_shapes"], 10)
        for p, n in (("p1", 6), ("p2", 4)):
            self.assertEqual(r["summary"][p]["independent_silhouettes"], n)
            self.assertEqual(
                r["summary"][p]["one_vote_per_binary_mask_means"]["lower_width_over_lower_height"],
                1.235294)


if __name__ == "__main__":
    unittest.main()
