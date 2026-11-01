"""ROM-free synthetic and retained-original temporal cadence/source-pose tests."""
import hashlib
import tempfile
import unittest
from pathlib import Path

from tools.art.audit_original_racer_cadence import (
    audit_rows, raw_mask_comparison, run, CANONICAL_ROM_SHA,
)


def sprite_mask(x=30, variant=0):
    mask = bytearray(4096)
    mask[38*64+x] = 1
    mask[38*64+x+1] = 1  # bottom-alpha x2=2*x+1, y2=76
    if variant:
        mask[36*64+x+variant] = 1
    return bytes(mask)


def record(player, frame, mask, color_number):
    lowest = [i % 64 for i, bit in enumerate(mask) if bit and i//64 == 38]
    return {
        "player": player, "guest_frame": frame,
        "representation_id": f"{player}-{frame}",
        "mask": mask,
        "binary_mask_sha256": hashlib.sha256(mask).hexdigest(),
        "source_rgba_sha256": f"{color_number:064x}",
        "source_png_sha256": f"{color_number+1000:064x}",
        "registered_contact_x2_y2": (min(lowest)+max(lowest), 76),
    }


def synthetic_rows():
    rows = []
    for frame in range(1205, 1221):
        # P1: true frame hold 1205..1211, novel shape 1212..1215,
        # then returns to the initial shape 1216..1220.
        p1mask = sprite_mask(30, 1 if 1212 <= frame <= 1215 else 0)
        p2mask = sprite_mask(40, 0)
        rows.append(record("p1", frame, p1mask, frame))
        rows.append(record("p2", frame, p2mask, frame+100))
    return rows


class OriginalRacerCadenceTests(unittest.TestCase):
    def report(self):
        return audit_rows(
            synthetic_rows(),
            registry_sha256="a"*64,
            rom_sha256=CANONICAL_ROM_SHA,
        )

    def test_true_original_shape_holds_and_return_are_temporally_distinct(self):
        result = self.report()
        self.assertEqual(result["original_frame_observations"], 32)
        self.assertEqual(result["distinct_original_binary_silhouettes"], 3)
        p1 = result["players"]["p1"]
        p2 = result["players"]["p2"]
        self.assertEqual(p1["distinct_original_binary_masks"], 2)
        self.assertEqual(p1["original_shape_change_edges"], 2)
        self.assertEqual(p1["unchanged_original_shape_edges"], 13)
        self.assertEqual([v["frame_count"] for v in p1["source_shape_holds"]], [7, 4, 5])
        self.assertEqual(p2["original_shape_change_edges"], 0)
        self.assertEqual(p2["longest_contiguous_source_shape_hold_frames"], 16)
        self.assertEqual(sum(x["both_players_held"]
                             for x in result["paired_player_frame_transition_observations"]), 13)
        self.assertFalse(result["source_1994_3d_pose_mapping_verified"])
        self.assertFalse(result["original_p1_p2_temporal_coupling_or_shared_3d_phase_verified"])
        self.assertFalse(result["shipping_art_approved"])

    def test_source_pixel_translation_does_not_create_spurious_shape_edit(self):
        rows = synthetic_rows()
        # Simulate P2 alpha changing only by its original object-local 2D
        # frame placement. The normalized shape must be invariant.
        for row in rows:
            if row["player"] == "p2" and row["guest_frame"] >= 1210:
                replacement = sprite_mask(42)
                row.update(record("p2", row["guest_frame"], replacement,
                                  row["guest_frame"] + 100))
        report = audit_rows(rows, registry_sha256="b"*64,
                            rom_sha256=CANONICAL_ROM_SHA)
        transition = next(x for x in report["players"]["p2"]["source_frame_transitions"]
                          if x["to_guest_frame"] == 1210)
        self.assertGreater(transition["raw_original_binary_mask_xor_pixels"], 0)
        self.assertEqual(transition["contact_aligned_binary_mask_xor_pixels"], 0)
        self.assertEqual(transition["contact_aligned_binary_mask_iou"], 1.0)
        self.assertEqual(transition["source_registered_anchor_delta_x2_y2"], [4,0])
        self.assertTrue(transition["exact_source_shape_changed"])

    def test_source_palette_change_alone_does_not_count_as_motion(self):
        rows = synthetic_rows()
        target = next(x for x in rows if x["player"] == "p2" and x["guest_frame"] == 1206)
        target["source_rgba_sha256"] = "f"*64
        result = audit_rows(rows, registry_sha256="b"*64,
                            rom_sha256=CANONICAL_ROM_SHA)
        self.assertEqual(result["players"]["p2"]["original_shape_change_edges"], 0)

    def test_duplicate_frame_absent_frame_and_wrong_player_rejected(self):
        for replacement in (
            lambda rows: rows.append(dict(rows[0])),
            lambda rows: rows.pop(),
            lambda rows: rows[0].update({"player": "p3"}),
        ):
            with self.subTest(replacement=replacement):
                rows = synthetic_rows()
                replacement(rows)
                with self.assertRaisesRegex(ValueError, "original"):
                    audit_rows(rows, registry_sha256="a"*64,
                               rom_sha256=CANONICAL_ROM_SHA)

    def test_tampered_source_mask_hash_and_wrong_registered_anchor_fail(self):
        rows = synthetic_rows()
        rows[0]["binary_mask_sha256"] = "0"*64
        with self.assertRaisesRegex(ValueError, "provenance"):
            audit_rows(rows, registry_sha256="a"*64, rom_sha256=CANONICAL_ROM_SHA)
        rows = synthetic_rows()
        rows[0]["registered_contact_x2_y2"] = (67, 76)
        with self.assertRaisesRegex(ValueError, "contact"):
            audit_rows(rows, registry_sha256="a"*64, rom_sha256=CANONICAL_ROM_SHA)

    def test_wrong_rom_and_registry_identity_are_rejected(self):
        rows = synthetic_rows()
        for rom, registry in (("0"*64, "a"*64), (CANONICAL_ROM_SHA, "invalid")):
            with self.assertRaisesRegex(ValueError, "identity"):
                audit_rows(rows, registry_sha256=registry, rom_sha256=rom)

    def test_comparison_rejects_nonbinary_pixels_and_wrong_shape(self):
        left = sprite_mask()
        with self.assertRaisesRegex(ValueError, "64x64"):
            raw_mask_comparison(left, b"\0"*4095)
        with self.assertRaisesRegex(ValueError, "64x64"):
            raw_mask_comparison(left, bytes([2]) + left[1:])

    def test_actual_retained_original_p1_p2_strip_is_witnessed(self):
        # Positive connection to real 1994 ROM-composed PNGs already in repo.
        # No original ROM, unsupported new view or private source export used.
        report = run()
        self.assertEqual(report["original_frame_observations"], 32)
        self.assertEqual(report["distinct_original_binary_silhouettes"], 10)
        self.assertEqual(len(report["paired_player_frame_transition_observations"]), 15)
        for player in ("p1","p2"):
            self.assertEqual(report["players"][player]["guest_frame_count"], 16)
            self.assertEqual(report["players"][player]["consecutive_frame_transition_count"], 15)
            self.assertEqual(sum(v["frame_count"]
                                 for v in report["players"][player]["source_shape_holds"]), 16)
        self.assertFalse(report["owner_likeness_approved"])
        self.assertFalse(report["source_1994_camera_recovered"])


if __name__ == "__main__":
    unittest.main()
