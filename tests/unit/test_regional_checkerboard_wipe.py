"""ROM-free contract checks for the isolated regional checkerboard presenter."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "tools" / "showcase" / "regional_checkerboard_wipe.py"
spec = importlib.util.spec_from_file_location("regional_checkerboard_wipe", SCRIPT)
wipe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wipe)


class GeometryTests(unittest.TestCase):
    def test_diagonal_rank_reversal(self):
        cells, cols, rows = wipe.grid(24, 18, 8, 6, 0, 0)
        self.assertEqual((cols, rows), (3, 3))
        for c, r, _, _ in cells:
            a = wipe.tile_rank(c, r, cols, rows, "to-unirally")
            b = wipe.tile_rank(c, r, cols, rows, "to-uniracers")
            self.assertEqual(a + b, cols + rows - 2)
        self.assertEqual(wipe.tile_rank(0, 0, cols, rows, "to-unirally"), 0)
        self.assertEqual(wipe.tile_rank(2, 2, cols, rows, "to-uniracers"), 0)

    def test_cropped_edge_cells_keep_original_grid_phase(self):
        cells, cols, rows = wipe.grid(17, 14, 8, 6, 3, 2)
        self.assertEqual((cols, rows), (3, 3))
        self.assertEqual((cells[0][2], cells[0][3]), (-3, -2))
        self.assertEqual(wipe.total_frames(cols, rows, 8, 2), 16)

    def test_invalid_geometry_or_timing_rejected(self):
        with self.assertRaises(ValueError):
            wipe.grid(16, 16, 0, 8, 0, 0)
        with self.assertRaises(ValueError):
            wipe.grid(16, 16, 8, 8, 8, 0)
        with self.assertRaises(ValueError):
            wipe.total_frames(2, 2, 1, 1)
        with self.assertRaises(ValueError):
            wipe.tile_rank(0, 0, 2, 2, "sideways")


@unittest.skipIf(wipe.Image is None, "Pillow optional for image-based preview tests")
class RenderingTests(unittest.TestCase):
    def setUp(self):
        self.source = wipe.Image.new("RGB", (24, 16), (17, 43, 91))
        self.target = wipe.Image.new("RGB", (24, 16), (198, 83, 19))
        self.options = dict(tile_w=8, tile_h=8, offset_x=0, offset_y=0,
                            grey=(120, 121, 122), flip_frames=8, stagger_frames=2)
        self.total = wipe.total_frames(3, 2, 8, 2)

    def test_immutable_endpoints(self):
        for direction in wipe.DIRECTIONS:
            old, new = (self.source, self.target) if direction == "to-unirally" else (self.target, self.source)
            self.assertEqual(wipe.render(old, new, direction=direction, frame=0, **self.options).tobytes(), old.tobytes())
            self.assertEqual(wipe.render(old, new, direction=direction, frame=self.total, **self.options).tobytes(), new.tobytes())

    def test_no_blended_pixels_and_grey_midturn(self):
        result = wipe.render(self.source, self.target, direction="to-unirally", frame=4, **self.options)
        self.assertEqual(result.getpixel((3, 3)), (120, 121, 122))
        self.assertTrue(set(result.getdata()) <= {(17, 43, 91), (198, 83, 19), (120, 121, 122)})

    def test_signed_projection_and_repeatability(self):
        a = wipe.render(self.source, self.target, direction="to-unirally", frame=6, **self.options)
        b = wipe.render(self.source, self.target, direction="to-unirally", frame=6, **self.options)
        self.assertEqual(a.tobytes(), b.tobytes())
        rev = wipe.render(self.target, self.source, direction="to-uniracers", frame=6, **self.options)
        self.assertNotEqual(a.tobytes(), rev.tobytes())

    def test_provenance_hash_binding(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            menu = wipe.Image.new("RGB", (24, 16), (91, 95, 99))
            menu.putpixel((3, 4), (101, 102, 103))
            filename = root / "menu.png"
            menu.save(filename)
            data = {"schema": wipe.CALIBRATION_SCHEMA, "status": "measured-original-main-menu",
                    "menu_sha256": wipe.sha256(filename), "source_description": "unit fixture",
                    "capture_tag": "unit-only", "logical_size": [24, 16],
                    "tile_width": 8, "tile_height": 8, "offset_x": 0, "offset_y": 0,
                    "grey_sample_xy": [3, 4]}
            calib = root / "calibration.json"
            calib.write_text(json.dumps(data))
            self.assertEqual(wipe.calibration(calib, filename)[1], (101, 102, 103))
            data["menu_sha256"] = "0" * 64
            calib.write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                wipe.calibration(calib, filename)

    def test_cli_creates_labeled_synthetic_review_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "preview"
            subprocess.run([sys.executable, str(SCRIPT), "--synthetic-demo",
                            "--outdir", str(out)], check=True, capture_output=True)
            m = json.loads((out / "manifest.json").read_text())
            self.assertEqual(m["schema"], wipe.OUTPUT_SCHEMA)
            self.assertIn("SYNTHETIC", m["source"]["status"])
            self.assertEqual(len(m["frames"]), 10)
            for record in m["frames"]:
                self.assertEqual(record["sha256"], wipe.sha256(out / record["file"]))


if __name__ == "__main__":
    unittest.main()
