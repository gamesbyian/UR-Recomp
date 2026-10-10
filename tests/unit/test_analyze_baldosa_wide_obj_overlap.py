"""Native 342-wide PPU source overlaps and final-color visibility diagnostics."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools.analyze_baldosa_wide_obj_overlap import (
    HEADER, HEIGHT, SLOTS, WIDTH, analyze, assess,
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


if __name__ == "__main__":
    unittest.main()
