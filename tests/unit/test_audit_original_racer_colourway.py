"""ROM-free accents, original colour grouping and exact retained source evidence."""
from __future__ import annotations

import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

from tools.art.audit_original_racer_colourway import (
    CANONICAL_ROM_SHA, SCHEMA, analyse_source_rgba,
    aggregate_source_colourways, audit, classify_source_chroma,
)


def make_rgba(n: int, player: str, variant: int = 0) -> bytes:
    data = bytearray(64 * 64 * 4)
    # One neutral wheel-like pixel and one palette accent (no component claim).
    col = (198, 33, 16) if player == "p1" else (16, 24, 198)
    if variant:
        col = (173, 33, 8) if player == "p1" else (16, 24, 173)
    for x, rgb in ((n+2, (74, 74, 74)), (n+3, col)):
        at = (38*64+x)*4
        data[at:at+4] = bytes((*rgb, 255))
    return bytes(data)


def make_rows():
    first = [0]*4 + [1]*6 + [2]*2 + [3]*2 + [4, 5]
    second = [6]*10 + [7]*3 + [8] + [9]*2
    result = []
    for player, groups in (("p1", first), ("p2", second)):
        for frame, shape in zip(range(1205, 1221), groups):
            rgba = make_rgba(shape, player)
            binary = bytes(1 if x else 0 for x in rgba[3::4])
            result.append({
                "player": player,
                "guest_frame": frame,
                "representation_id": f"{player}-source-{shape}",
                "source_png_sha256": f"{frame:064x}",
                "source_rgba_sha256": hashlib.sha256(rgba).hexdigest(),
                "source_binary_mask_sha256": hashlib.sha256(binary).hexdigest(),
                "source_decoded_rgba": rgba,
            })
    return result


class RacerColourwayTests(unittest.TestCase):
    def reduce(self, rows=None):
        return aggregate_source_colourways(
            make_rows() if rows is None else rows,
            source_rom_sha256=CANONICAL_ROM_SHA,
            source_registry_sha256="a"*64,
        )

    def test_palette_classifier_is_explicit_nonmaterial_descriptor(self):
        self.assertEqual(classify_source_chroma((198,33,16)), "red")
        self.assertEqual(classify_source_chroma((16,24,198)), "blue")
        self.assertEqual(classify_source_chroma((74,74,74)), "other")
        self.assertEqual(classify_source_chroma((180,170,100)), "other")
        with self.assertRaisesRegex(ValueError, "64x64"):
            analyse_source_rgba(b"tiny")

    def test_32_frames_count_as_ten_original_source_shapes(self):
        data = self.reduce()
        self.assertEqual(data["schema"], SCHEMA)
        self.assertEqual(data["original_64x64_observation_count"], 32)
        self.assertEqual(data["distinct_2d_binary_source_silhouettes"], 10)
        p1 = data["original_racer_source_colourways"]["p1"]
        p2 = data["original_racer_source_colourways"]["p2"]
        self.assertEqual(p1["distinct_original_binary_silhouette_weight"], 6)
        self.assertEqual(p2["distinct_original_binary_silhouette_weight"], 4)
        self.assertEqual(p1["mean_red_chroma_indicator_pixels_per_shape"], 1.0)
        self.assertEqual(p1["mean_blue_chroma_indicator_pixels_per_shape"], 0.0)
        self.assertEqual(p2["mean_red_chroma_indicator_pixels_per_shape"], 0.0)
        self.assertEqual(p2["mean_blue_chroma_indicator_pixels_per_shape"], 1.0)
        self.assertEqual(p1["distinct_original_source_opaque_rgb_colours"], 2)
        self.assertEqual(p2["distinct_original_source_opaque_rgb_colours"], 2)
        self.assertEqual(
            data["original_source_palette_overlap"]["shared_opaque_rgb_colours"],
            ["#4a4a4a"])
        self.assertFalse(
            data["original_source_palette_overlap"]["rgb_palette_union_is_a_recovered_1994_3d_material_map"])
        self.assertFalse(data["source_colour_is_an_authentic_3d_material_label"])
        self.assertFalse(data["shipping_art_approved"])
        self.assertFalse(data["1994_3d_camera_or_lighting_recovered"])

    def test_colour_variants_of_same_binary_mask_do_not_create_new_shape_vote(self):
        rows = make_rows()
        modified = next(x for x in rows
                        if x["player"] == "p1" and x["guest_frame"] == 1206)
        changed = make_rgba(0, "p1", variant=1)
        modified["source_decoded_rgba"] = changed
        modified["source_rgba_sha256"] = hashlib.sha256(changed).hexdigest()
        data = self.reduce(rows)
        p1 = data["original_racer_source_colourways"]["p1"]
        group = next(g for g in p1["source_shape_groups"]
                     if g["distinct_original_rgba_colour_variants"] == 2)
        self.assertEqual(len(group["original_source_frame_references"]), 4)
        self.assertEqual(p1["distinct_original_binary_silhouette_weight"], 6)
        self.assertEqual(p1["mean_red_chroma_indicator_pixels_per_shape"], 1.0)

    def test_missing_or_duplicate_guest_frame_and_spoofed_player_rejected(self):
        for edit in (
            lambda rows: rows.pop(),
            lambda rows: rows[0].update(guest_frame=1206),
            lambda rows: rows[0].update(player="p3"),
        ):
            with self.subTest(edit=edit):
                rows = make_rows()
                edit(rows)
                with self.assertRaisesRegex(ValueError, "frame"):
                    self.reduce(rows)

    def test_malicious_decoded_rgba_or_binary_sha_is_not_accepted(self):
        rows = make_rows()
        rows[0]["source_decoded_rgba"] += b"malicious trailing data"
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            self.reduce(rows)
        rows = make_rows()
        rows[0]["source_binary_mask_sha256"] = "0"*64
        with self.assertRaisesRegex(ValueError, "binary-mask digest mismatch"):
            self.reduce(rows)

    def test_malformed_or_partial_alpha_is_rejected(self):
        pixels = bytearray(make_rgba(0, "p1"))
        pixels[(38*64+2)*4+3] = 128
        with self.assertRaisesRegex(ValueError, "alpha is not binary"):
            analyse_source_rgba(bytes(pixels))

    def test_wrong_original_rom_or_registry_identity_is_rejected(self):
        for rom, registry in (("0"*64,"a"*64), (CANONICAL_ROM_SHA, "unknown")):
            with self.assertRaisesRegex(ValueError,"identity"):
                aggregate_source_colourways(make_rows(),
                                            source_rom_sha256=rom,
                                            source_registry_sha256=registry)

    def test_real_verified_rom_composed_source_has_distinct_p1_red_and_p2_blue(self):
        actual = audit()
        self.assertEqual(actual["original_64x64_observation_count"], 32)
        self.assertEqual(actual["distinct_2d_binary_source_silhouettes"], 10)
        p1 = actual["original_racer_source_colourways"]["p1"]
        p2 = actual["original_racer_source_colourways"]["p2"]
        self.assertEqual(p1["distinct_original_binary_silhouette_weight"], 6)
        self.assertEqual(p2["distinct_original_binary_silhouette_weight"], 4)
        self.assertEqual(p1["mean_red_chroma_indicator_pixels_per_shape"], 54)
        self.assertEqual(p1["mean_blue_chroma_indicator_pixels_per_shape"], 0)
        self.assertEqual(p2["mean_red_chroma_indicator_pixels_per_shape"], 0)
        self.assertEqual(p2["mean_blue_chroma_indicator_pixels_per_shape"], 67)
        self.assertEqual(p1["distinct_original_source_opaque_rgb_colours"], 15)
        self.assertEqual(p2["distinct_original_source_opaque_rgb_colours"], 15)
        self.assertEqual(
            actual["original_source_palette_overlap"]["shared_opaque_rgb_colours"],
            ["#181818", "#313131", "#4a4a4a", "#737373", "#a5a5a5"])
        self.assertEqual(len(
            actual["original_source_palette_overlap"]["p1_only_opaque_rgb_colours"]), 10)
        self.assertEqual(len(
            actual["original_source_palette_overlap"]["p2_only_opaque_rgb_colours"]), 10)
        self.assertFalse(actual["source_colour_is_an_authentic_3d_material_label"])
        self.assertFalse(actual["owner_character_likeness_approved"])


if __name__ == "__main__":
    unittest.main()
