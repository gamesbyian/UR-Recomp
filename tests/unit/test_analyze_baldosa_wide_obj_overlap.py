"""Native 342-wide PPU source overlaps and final-color visibility diagnostics."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools.analyze_baldosa_wide_obj_overlap import (
    HEADER, HEIGHT, SLOTS, WIDTH, analyze, assess,
    analyze_removal_counterfactual, attach_verified_removal,
)


def set_pixel(buf, x, y, rgb):
    offset = (y * WIDTH + x) * 4
    buf[offset:offset + 4] = bytes((*rgb, 255))


def scene():
    bg = bytes((9, 9, 9, 255))
    original = bytearray(bg * (WIDTH * HEIGHT))
    layers = {slot: bytearray(WIDTH * HEIGHT * 4) for slot in SLOTS}
    # Top winning slot98 (red); slot99 (green) emitted source but the
    # winner blocks its physically overlapping part.
    set_pixel(layers[98], 100, 40, (200, 0, 0))
    set_pixel(layers[98], 101, 40, (200, 0, 0))
    set_pixel(layers[99], 100, 40, (0, 200, 0))
    set_pixel(layers[99], 102, 40, (0, 200, 0))
    set_pixel(original, 100, 40, (200, 0, 0))
    set_pixel(original, 101, 40, (200, 0, 0))
    set_pixel(original, 102, 40, (0, 200, 0))

    # Independent split band: slot96 wins over 97.
    set_pixel(layers[96], 130, 150, (0, 0, 200))
    set_pixel(layers[96], 131, 150, (0, 0, 200))
    set_pixel(layers[97], 130, 150, (200, 0, 200))
    set_pixel(layers[97], 132, 150, (200, 0, 200))
    set_pixel(original, 130, 150, (0, 0, 200))
    set_pixel(original, 131, 150, (0, 0, 200))
    set_pixel(original, 132, 150, (200, 0, 200))
    return bytes(original), {k: bytes(v) for k, v in layers.items()}


class SourceOverlapTests(unittest.TestCase):
    def test_actual_split_slot_order_and_source_color_witness(self):
        original, layers = scene()
        result = analyze(original, layers, 1856)
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["source_alpha_total_across_slots"], 8)
        self.assertEqual(result["source_alpha_union_pixels"], 6)
        self.assertEqual(result["source_alpha_multi_slot_pixels"], 2)
        self.assertEqual(result["source_overlap_pairs"]["96-97"], 1)
        self.assertEqual(result["source_overlap_pairs"]["98-99"], 1)
        self.assertEqual(result["per_slot"]["98"]["main_rgb_differs_source"], 0)
        self.assertEqual(result["per_slot"]["96"]["main_rgb_differs_source"], 0)
        self.assertEqual(result["per_slot"]["99"]["overlap_main_rgb_differs"], 1)
        self.assertEqual(result["per_slot"]["97"]["overlap_main_rgb_differs"], 1)
        self.assertEqual(result["per_slot"]["99"]["unique_source_pixels"], 1)
        # A foreground interference in one otherwise unique OBJ pixel
        # remains visible in diagnostics but never counts as safe painting.
        hidden = bytearray(original)
        set_pixel(hidden, 102, 40, (255, 255, 0))
        finding = analyze(bytes(hidden), layers, 1856)
        self.assertEqual(finding["status"], "passed")
        self.assertEqual(finding["per_slot"]["99"]["unique_main_rgb_differs"], 1)

        # Change a source-front pixel in the final PPU frame. The strict
        # known native witness must fail even if all source planes still look fine.
        set_pixel(hidden, 100, 40, (255, 255, 255))
        self.assertEqual(analyze(bytes(hidden), layers, 1856)["status"], "unproven")
        with self.assertRaisesRegex(ValueError, "precisely four"):
            analyze(original, {98: layers[98]}, 1856)
        with self.assertRaisesRegex(ValueError, "342x224"):
            analyze(original[:20], layers, 1856)

    def test_second_moving_frame_is_independent_read_only_evidence(self):
        original, layers = scene()
        # On a later moving frame a previously overlapping rider can leave
        # the bottom OBJ source plane entirely. That is valid observation,
        # not a license to fabricate or replace a second rider.
        layers = dict(layers)
        layers[96] = bytes(WIDTH * HEIGHT * 4)
        layers[97] = bytes(WIDTH * HEIGHT * 4)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            slots = root / "slots"
            reports = root / "reports"
            slots.mkdir()
            reports.mkdir()
            main = root / "source.pam"
            main.write_bytes(HEADER + original)
            for slot, pixels in layers.items():
                (slots / (
                    f"ur-baldosa-ws342-obj-slot{slot}-frame001872.pam"
                )).write_bytes(HEADER + pixels)
                report = {
                    "status": "passed",
                    "source": {
                        "slot": slot,
                        "guest_frame": 1872,
                        "source_sha256": hashlib.sha256(pixels).hexdigest(),
                    },
                    "source_frame_main_raster_sha256":
                        hashlib.sha256(original).hexdigest(),
                }
                (reports / f"ws342_obj_slot_{slot}_frame1872.json").write_text(
                    json.dumps(report))
            witness = assess(main, slots, reports, 1872)
            self.assertEqual(witness["status"], "unproven")
            self.assertEqual(witness["per_slot"]["96"]["source_opaque"], 0)
            self.assertEqual(witness["per_slot"]["97"]["source_opaque"], 0)
            self.assertEqual(witness["guest_frame"], 1872)
            # The comparison still rejects incoherent independent native
            # processes even when a later frame lacks both overlapping pairs.
            mismatch = json.loads(
                (reports / "ws342_obj_slot_98_frame1872.json").read_text())
            mismatch["source_frame_main_raster_sha256"] = "0" * 64
            (reports / "ws342_obj_slot_98_frame1872.json").write_text(
                json.dumps(mismatch))
            with self.assertRaisesRegex(ValueError, "Different guest main"):
                assess(main, slots, reports, 1872)

    def test_shared_source_winner_color_budget_never_implies_ownership(self):
        original, layers = scene()
        result = analyze(original, layers, 1856)
        for band, front, rear in (("top", 98, 99), ("bottom", 96, 97)):
            witness = result["split_pair_final_color_witness"][band]
            self.assertEqual((witness["front_slot"], witness["rear_slot"]),
                             (front, rear))
            self.assertEqual(witness["shared_source_pixels"], 1)
            self.assertEqual(witness["front_only_matches_original"], 1)
            self.assertEqual(witness["rear_only_matches_original"], 0)
            self.assertEqual(witness["both_match_original"], 0)
            self.assertEqual(witness["neither_matches_original"], 0)
            self.assertEqual(witness["additional_obj_source_present"], 0)

        # The final upper pixel equals the rear isolated PPU RGB while the
        # front source remains red. That is a candidate, not a proved
        # source-order violation; another PPU effect can give that RGB.
        # In the lower viewport a third, non-OBJ RGB value wins.
        changed = bytearray(original)
        set_pixel(changed, 100, 40, (0, 200, 0))
        set_pixel(changed, 130, 150, (99, 100, 101))
        alternative = analyze(bytes(changed), layers, 1872)
        self.assertEqual(alternative["status"], "unproven")
        top = alternative["split_pair_final_color_witness"]["top"]
        bottom = alternative["split_pair_final_color_witness"]["bottom"]
        self.assertEqual(top["rear_only_matches_original"], 1)
        self.assertEqual(bottom["neither_matches_original"], 1)
        self.assertEqual(top["front_only_matches_original"], 0)
        self.assertEqual(bottom["front_only_matches_original"], 0)
        self.assertEqual(top["example_xy"]["rear_only"], [[100, 40]])
        self.assertEqual(bottom["example_xy"]["neither"], [[130, 150]])
        self.assertEqual(
            result["split_pair_final_color_witness"]["top"]["example_xy"]["front_only"],
            [[100, 40]],
        )

        # Identical front and rear source RGB cannot determine which OAM
        # source the final same-colour pixel came from.
        similar = dict(layers)
        rear = bytearray(layers[99])
        set_pixel(rear, 100, 40, (200, 0, 0))
        similar[99] = bytes(rear)
        same = analyze(original, similar, 1856)
        self.assertEqual(
            same["split_pair_final_color_witness"]["top"]["both_match_original"],
            1,
        )
        self.assertEqual(
            same["split_pair_final_color_witness"]["top"]["example_xy"]["both"],
            [[100, 40]],
        )

    def test_full_native_slot_provenance_and_changed_frame(self):
        original, layers = scene()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            directory = root / "slots"
            directory.mkdir()
            reports = root / "reports"
            reports.mkdir()
            main_file = root / "original.pam"
            main_file.write_bytes(HEADER + original)
            for slot, pixels in layers.items():
                (directory / (
                    f"ur-baldosa-ws342-obj-slot{slot}-frame001856.pam"
                )).write_bytes(HEADER + pixels)
                report = {
                    "status": "passed",
                    "source": {
                        "slot": slot,
                        "guest_frame": 1856,
                        "source_sha256": hashlib.sha256(pixels).hexdigest(),
                    },
                    "source_frame_main_raster_sha256":
                        hashlib.sha256(original).hexdigest(),
                }
                (reports / f"ws342_obj_slot_{slot}.json").write_text(
                    json.dumps(report))
            proof = assess(main_file, directory, reports, 1856)
            self.assertEqual(proof["status"], "passed")
            self.assertEqual(proof["guest_frame"], 1856)
            corrupted = json.loads((reports / "ws342_obj_slot_99.json").read_text())
            corrupted["source"]["guest_frame"] = 1888
            (reports / "ws342_obj_slot_99.json").write_text(json.dumps(corrupted))
            with self.assertRaisesRegex(ValueError, "provenance"):
                assess(main_file, directory, reports, 1856)
            corrupted["source"]["guest_frame"] = 1856
            (reports / "ws342_obj_slot_99.json").write_text(json.dumps(corrupted))
            main_file.write_bytes(HEADER + original[:-1])
            with self.assertRaisesRegex(ValueError, "P7"):
                assess(main_file, directory, reports, 1856)


    def test_real_ppu_removal_separates_rear_reveal_from_colour_collision(self):
        stock = bytearray(bytes((9, 9, 9, 255)) * (WIDTH * HEIGHT))
        removed = bytearray(stock)
        front = bytearray(WIDTH * HEIGHT * 4)
        rear = bytearray(WIDTH * HEIGHT * 4)
        for x in (11, 12, 13, 14):
            set_pixel(stock, x, 40, (100, 10, 10))
            set_pixel(front, x, 40, (100, 10, 10))
        set_pixel(rear, 11, 40, (20, 200, 20))
        set_pixel(removed, 11, 40, (20, 200, 20))
        set_pixel(removed, 12, 40, (9, 9, 9))
        # The source at 13 is still emitted, but the lower rear source has
        # *exactly the same colour*. Native stock-vs-removal sees no change.
        set_pixel(rear, 13, 40, (100, 10, 10))
        set_pixel(removed, 14, 40, (9, 9, 9))
        finding = analyze_removal_counterfactual(
            bytes(stock), bytes(removed), bytes(front), bytes(rear),
            1856, 98)
        self.assertEqual(finding["status"], "consistent-observation")
        self.assertEqual(finding["front_source_alpha_pixels"], 4)
        self.assertEqual(finding["counterfactual_changed_pixels"], 3)
        self.assertEqual(finding["changed_pixels_revealing_rear_rgb"], 1)
        self.assertEqual(finding["changed_pixels_revealing_other_rgb"], 2)
        self.assertEqual(finding["unchanged_pixels_matching_identical_rear_rgb"], 1)
        self.assertEqual(finding["counterfactual_changed_outside_front_alpha"], 0)
        self.assertFalse(finding["release_hd_admission"])
        self.assertEqual(finding["bounded_xy_examples"]["identical_rear_colour"],
                         [[13, 40]])

        original = {
            "guest_frame": 1856,
            "source_obj_sha256": {"98": hashlib.sha256(front).hexdigest()},
        }
        report = {
            "status": "passed", "guest_frame": 1856,
            "source_oam_slot": 98,
            "guest_crc_equal_in_all_three_processes": True,
            "single_slot_original_ppu_removal_armed": True,
            "stock_sha256": hashlib.sha256(stock).hexdigest(),
            "counterfactual_sha256": hashlib.sha256(removed).hexdigest(),
            "source_sha256": hashlib.sha256(front).hexdigest(),
            "native_ppu_final_contributed_pixels": 3,
            "native_ppu_changed_outside_emitted_source_alpha": 0,
            "source_emitted_alpha_pixels": 4,
        }
        authenticated = attach_verified_removal(
            original, bytes(stock), bytes(removed),
            {98: bytes(front), 99: bytes(rear)},
            report, frame=1856, front_slot=98)
        self.assertEqual(authenticated, finding)
        stale = {**report, "guest_frame": 1872}
        with self.assertRaisesRegex(ValueError, "provenance"):
            attach_verified_removal(original, bytes(stock), bytes(removed),
                                    {98: bytes(front), 99: bytes(rear)},
                                    stale, frame=1856, front_slot=98)
        changed_report = {**report, "native_ppu_final_contributed_pixels": 4}
        with self.assertRaisesRegex(ValueError, "disagrees"):
            attach_verified_removal(original, bytes(stock), bytes(removed),
                                    {98: bytes(front), 99: bytes(rear)},
                                    changed_report, frame=1856, front_slot=98)

        # Changing even one pixel OUTSIDE this OAM source is not an
        # attributable one-slot PPU counterfactual.
        set_pixel(removed, 50, 40, (1, 2, 3))
        outside = analyze_removal_counterfactual(
            bytes(stock), bytes(removed), bytes(front), bytes(rear),
            1856, 98)
        self.assertEqual(outside["status"], "unproven")
        self.assertEqual(outside["counterfactual_changed_outside_front_alpha"], 1)
        with self.assertRaisesRegex(ValueError, "known split front"):
            analyze_removal_counterfactual(
                bytes(stock), bytes(removed), bytes(front), bytes(rear),
                1856, 99)
        with self.assertRaisesRegex(ValueError, "342x224"):
            analyze_removal_counterfactual(
                bytes(stock[:-4]), bytes(removed), bytes(front), bytes(rear),
                1856, 98)


if __name__ == "__main__":
    unittest.main()
