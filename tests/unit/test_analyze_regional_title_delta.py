import importlib.util
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "analyze_regional_title_delta.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("regional_title_delta", TOOL)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RegionalTitleDeltaTests(unittest.TestCase):
    def test_contiguous_ranges_contract(self):
        tool = load_tool()
        self.assertEqual(
            tool.contiguous_ranges([1, 2, 3, 7, 9, 10]),
            [
                {"start": 1, "end_exclusive": 4, "length": 3},
                {"start": 7, "end_exclusive": 8, "length": 1},
                {"start": 9, "end_exclusive": 11, "length": 2},
            ],
        )

    def test_blob_grouping_reports_tiles_and_colors(self):
        tool = load_tool()
        a = bytes(64)
        b = bytearray(a)
        b[31] = 1
        b[32] = 2
        report = tool.compare_blob(bytes(a), bytes(b), grouping=32)
        self.assertEqual(report["changed_bytes"], 2)
        self.assertEqual(report["changed_groups"], [0, 1])

        cgram_a = bytes(8)
        cgram_b = bytearray(cgram_a)
        cgram_b[2] = 1
        cgram_b[3] = 2
        colors = tool.compare_blob(bytes(cgram_a), bytes(cgram_b), grouping=2)
        self.assertEqual(colors["changed_groups"], [1])

    def test_checkpoint_and_cross_frame_stability(self):
        tool = load_tool()
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            usa = root / "usa"
            eur = root / "europe"
            usa.mkdir()
            eur.mkdir()

            for index, checkpoint in enumerate(tool.DEFAULT_CHECKPOINTS):
                usa_fb = bytes([0, 0, 0, 0] * 4)
                eur_fb = bytearray(usa_fb)
                eur_fb[4:8] = bytes([1, 2, 3, 4])
                (usa / f"{checkpoint}.fb.bgrx").write_bytes(usa_fb)
                (eur / f"{checkpoint}.fb.bgrx").write_bytes(bytes(eur_fb))

                usa_vram = bytes(tool.VRAM_BYTES)
                eur_vram = bytearray(usa_vram)
                # Tile 5 changes at every checkpoint; tile 7 changes only once.
                eur_vram[5 * 32] = index + 1
                if index == 0:
                    eur_vram[7 * 32] = 9
                (usa / f"{checkpoint}.vram.bin").write_bytes(usa_vram)
                (eur / f"{checkpoint}.vram.bin").write_bytes(bytes(eur_vram))

                usa_cgram = bytes(tool.CGRAM_BYTES)
                eur_cgram = bytearray(usa_cgram)
                eur_cgram[3 * 2] = index + 1
                if index == 2:
                    eur_cgram[8 * 2] = 4
                (usa / f"{checkpoint}.cgram.bin").write_bytes(usa_cgram)
                (eur / f"{checkpoint}.cgram.bin").write_bytes(bytes(eur_cgram))

            report = tool.analyze(usa, eur)
            self.assertEqual(report["summary"]["matched_checkpoint_count"], 3)
            row = report["checkpoints"][0]
            self.assertEqual(row["framebuffer"]["changed_pixels"], 1)
            self.assertEqual(row["framebuffer"]["bbox"], [1, 0, 1, 0])
            self.assertEqual(row["vram"]["changed_tile_indices"], [5, 7])
            self.assertEqual(row["cgram"]["changed_color_indices"], [3])

            stable_tiles = report["summary"]["stable_vram_tiles"]
            self.assertEqual(stable_tiles["intersection"], [5])
            self.assertEqual(stable_tiles["union"], [5, 7])
            stable_colors = report["summary"]["stable_cgram_colors"]
            self.assertEqual(stable_colors["intersection"], [3])
            self.assertEqual(stable_colors["union"], [3, 8])


    def test_settled_asset_requires_repeated_exact_frame_pair(self):
        tool = load_tool()
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            usa = root / "usa"
            eur = root / "europe"
            usa.mkdir()
            eur.mkdir()

            checkpoints = ["a", "b", "c"]
            usa_frame = bytes([0, 0, 0, 0] * tool.FRAME_WIDTH)
            eur_frame = bytearray(usa_frame)
            eur_frame[4:8] = bytes([3, 2, 1, 0])
            for checkpoint in checkpoints[:2]:
                (usa / f"{checkpoint}.fb.bgrx").write_bytes(usa_frame)
                (eur / f"{checkpoint}.fb.bgrx").write_bytes(bytes(eur_frame))
                (usa / f"{checkpoint}.cgram.bin").write_bytes(bytes(tool.CGRAM_BYTES))
                (eur / f"{checkpoint}.cgram.bin").write_bytes(bytes(tool.CGRAM_BYTES))

            other = bytearray(usa_frame)
            other[8:12] = bytes([4, 5, 6, 0])
            (usa / "c.fb.bgrx").write_bytes(usa_frame)
            (eur / "c.fb.bgrx").write_bytes(bytes(other))
            (usa / "c.cgram.bin").write_bytes(bytes(tool.CGRAM_BYTES))
            (eur / "c.cgram.bin").write_bytes(bytes(tool.CGRAM_BYTES))

            rows = [tool.compare_checkpoint(usa, eur, cp) for cp in checkpoints]
            asset = tool.build_settled_asset(usa, eur, rows)
            self.assertEqual(asset["evidence_checkpoints"], ["a", "b"])
            self.assertEqual(asset["bbox_inclusive"], [1, 0, 1, 0])
            self.assertEqual(asset["width"], 1)
            self.assertEqual(asset["height"], 1)
            self.assertEqual(asset["indices_decoded_bytes"], 1)
            self.assertEqual(len(asset["palette_u32_le"]), 1)
            self.assertTrue(asset["cgram_identical_across_evidence"])
            self.assertIn("source_crop_sha256", asset)
            self.assertIn("target_crop_sha256", asset)

    def test_missing_checkpoint_is_retained_without_fake_evidence(self):
        tool = load_tool()
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            usa = root / "usa"
            eur = root / "europe"
            usa.mkdir()
            eur.mkdir()
            report = tool.analyze(usa, eur, ["missing"])
            self.assertEqual(report["summary"]["matched_checkpoint_count"], 0)
            self.assertIsNone(report["checkpoints"][0]["framebuffer"])
            self.assertEqual(
                report["summary"]["stable_vram_tiles"]["intersection"], []
            )


if __name__ == "__main__":
    unittest.main()
