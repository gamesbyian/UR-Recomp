import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "display_active_height",
    ROOT / "tools/analyze_display_active_height.py",
)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)


def rows(width, values):
    out = []
    for value in values:
        out.extend([value] * width)
    return out


class DisplayActiveHeightTests(unittest.TestCase):
    def test_detects_nonpadding_edge_bands(self):
        width = 8
        height = 20
        data = []
        for y in range(height):
            data.extend([
                ((x + y) % 3, (x * 2 + y) % 5, (x + y * 3) % 7)
                for x in range(width)
            ])
        row = MOD.analyze_pixels(width, height, data, crop_rows=2)
        self.assertTrue(row["top_edge"]["non_padding_authored_content"])
        self.assertTrue(row["bottom_edge"]["non_padding_authored_content"])
        self.assertTrue(row["fixed_center_crop_discards_authored_edge_pixels"])

    def test_rejects_repeated_flat_padding(self):
        width = 8
        height = 20
        black = (0, 0, 0)
        body = (1, 2, 3)
        data = rows(width, [black] * 4 + [body] * 12 + [black] * 4)
        row = MOD.analyze_pixels(width, height, data, crop_rows=2)
        self.assertFalse(row["top_edge"]["non_padding_authored_content"])
        self.assertFalse(row["bottom_edge"]["non_padding_authored_content"])
        self.assertFalse(row["fixed_center_crop_discards_authored_edge_pixels"])

    def test_report_requires_representative_matrix(self):
        original = MOD.analyze_capture
        try:
            MOD.analyze_capture = lambda path, crop_rows=4: {
                "capture": path.name,
                "dimensions": [256, 224],
                "fixed_center_crop_discards_authored_edge_pixels": True,
            }
            report = MOD.build_report(
                [Path("menu.bmp"), Path("pre-race.bmp"), Path("race.bmp")],
                crop_rows=4,
            )
        finally:
            MOD.analyze_capture = original
        self.assertTrue(report["accepted"])
        self.assertEqual(report["reference_active_height_policy"], "full-224")
        self.assertEqual(report["crt_overscan_treatment"], "optional-and-separate")


if __name__ == "__main__":
    unittest.main()
