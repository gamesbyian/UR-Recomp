"""Synthetic ROM-free controls for source-registered multi-family extraction."""
import copy
import tempfile
import unittest
from pathlib import Path

from tools.art.export_registered_original_racer_corpus import (
    collect, export, windows_from_registry, FIRST,
)
from tools.art.racer_source_pixels import alpha_metrics


class OriginalRacerCorpusExporterTests(unittest.TestCase):
    def setUp(self):
        self.registry = {
            "schema_version": 1,
            "entries": [
                {"representation_id": "p1-a", "player": "p1", "palette_asset_id": "0x06"},
                {"representation_id": "p2-b", "player": "p2", "palette_asset_id": "0x07"},
                {"representation_id": "p1-c", "player": "p1", "palette_asset_id": "0x06"},
            ],
            "motion_review_sequence": {
                "window_start": 100, "window_end": 101,
                "frames": [
                    {"frame": 100, "p1_representation_id": "p1-a", "p2_representation_id": "p2-b"},
                    {"frame": 101, "p1_representation_id": "p1-a", "p2_representation_id": "p2-b"},
                ],
            },
            "motion_review_sequences": {
                "separate": {
                    "window_start": 200, "window_end": 200,
                    "frames": [{"frame": 200, "p1_representation_id": "p1-c"}],
                },
            },
        }

    @staticmethod
    def render(item):
        # An intentional synthetic same-mask cross-player palette variant.
        rgba = (255, 0, 0, 255) if item["player"] == "p1" else (0, 255, 0, 255)
        return bytes(rgba) * (64*64)

    def test_real_registry_structure_and_all_windows_without_rom(self):
        from tools.art.build_racer_source_pixel_corpus import REGISTRY
        import json
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        summary, images = collect(registry, lambda item: self.render(item))
        self.assertGreater(summary["unique_representations"], 30)
        self.assertGreater(summary["unique_rgba_images"], 0)
        self.assertEqual(summary["unique_binary_silhouettes"], 1)
        self.assertEqual(summary["unique_rgba_images"], 2)
        self.assertFalse(summary["source_rom_verified_and_used_for_composition"])
        self.assertFalse(summary["shipping_art_approved"])

    def test_color_variants_share_binary_silhouette_but_not_rgba(self):
        summary, files = collect(self.registry, self.render)
        self.assertEqual(summary["unique_representations"], 3)
        self.assertEqual(summary["unique_rgba_images"], 2)
        self.assertEqual(summary["unique_binary_silhouettes"], 1)
        self.assertEqual(len(files), 2)
        self.assertEqual(len(summary["source_temporal_frame_observations"]), 3)
        self.assertFalse(summary["owner_likeness_approved"])
        self.assertFalse(summary["source_3d_geometry_recovered"])

    def test_selecting_only_one_window_cannot_export_other_window(self):
        summary, _ = collect(self.registry, self.render, ["separate"])
        self.assertEqual(summary["unique_representations"], 1)
        self.assertEqual(summary["registered_source_windows"], ["separate"])
        self.assertEqual(summary["source_temporal_frame_observations"][0]["guest_frame"], 200)

    def test_duplicate_unknown_malformed_windows_fail_closed(self):
        for selected in ([], ["missing"], [FIRST, FIRST]):
            with self.subTest(selected=selected), self.assertRaises(ValueError):
                collect(self.registry, self.render, selected)
        corrupted = copy.deepcopy(self.registry)
        corrupted["motion_review_sequences"][FIRST] = corrupted["motion_review_sequence"]
        with self.assertRaisesRegex(ValueError, "duplicated"):
            windows_from_registry(corrupted)

    def test_bad_player_identity_duplicate_and_bad_time_rejected(self):
        bad = copy.deepcopy(self.registry)
        bad["motion_review_sequence"]["frames"][0]["p2_representation_id"] = "p1-a"
        with self.assertRaisesRegex(ValueError, "player"):
            collect(bad, self.render)
        bad = copy.deepcopy(self.registry)
        bad["entries"].append(copy.deepcopy(bad["entries"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            collect(bad, self.render)
        bad = copy.deepcopy(self.registry)
        bad["motion_review_sequence"]["frames"][1]["frame"] = 100
        with self.assertRaisesRegex(ValueError, "strictly"):
            collect(bad, self.render)

    def test_empty_and_malformed_original_rgba_rejected(self):
        with self.assertRaisesRegex(ValueError, "64x64 RGBA"):
            collect(self.registry, lambda _: bytes(10))
        with self.assertRaisesRegex(ValueError, "no visible"):
            collect(self.registry, lambda _: bytes(64*64*4))

    def test_source_pixels_cannot_be_exported_inside_public_checkout(self):
        from tools.art.export_registered_original_racer_corpus import ROOT
        destination = ROOT / "analysis" / "unsafe-source-corpus-fixture"
        with self.assertRaisesRegex(ValueError, "outside repository"):
            export(Path("/missing-ROM.sfc"), Path("/missing-registry.json"), destination)
        self.assertFalse(destination.exists())

    def test_rom_sha_is_required_before_writing_any_source_pixels(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            rom = root/"fake.sfc"
            rom.write_bytes(bytes(2097152))
            from json import dumps
            registry = root/"registry.json"
            registry.write_text(dumps(self.registry))
            dest = root/"private-corpus"
            with self.assertRaisesRegex(ValueError, "canonical USA ROM"):
                export(rom, registry, dest)
            self.assertFalse(dest.exists())


if __name__ == "__main__":
    unittest.main()
