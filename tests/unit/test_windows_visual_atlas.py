"""ROM-free contract tests for the inventory, build and capture admission boundary."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import struct
import tempfile
import unittest

from tools import windows_visual_atlas as atlas


class WindowsAtlasTests(unittest.TestCase):
    def test_catalog_is_unique_and_routes_are_real(self):
        catalog = atlas.load_catalog()
        entries = atlas.validate(catalog)
        self.assertGreaterEqual(len(entries), 50)
        self.assertGreaterEqual(len([e for e in entries if e.get("capture")]), 10)
        self.assertEqual(len({e["id"] for e in entries}), len(entries))

    def test_original_ui_and_visual_qa_coverage_cannot_go_stale(self):
        catalog = atlas.load_catalog()
        self.assertEqual(
            sum(e.get("source_inventory", {}).get("path") == "analysis/ui-capture-manifest.json"
                for e in catalog["entries"]), 120)
        self.assertEqual(
            sum(e.get("source_inventory", {}).get("path") == "analysis/modern-visual-acceptance-matrix.json"
                for e in catalog["entries"]), 25)
        missing = copy.deepcopy(catalog)
        missing["entries"] = [e for e in missing["entries"] if e["id"] != "URV-OG-001"]
        with self.assertRaisesRegex(ValueError, "original UI coverage drift"):
            atlas.validate(missing)
        changed = copy.deepcopy(catalog)
        qa = next(e for e in changed["entries"] if e["id"] == "URV-QA-001")
        qa["source_inventory"]["acceptance_case_id"] = "imaginary"
        with self.assertRaisesRegex(ValueError, "visual QA case"):
            atlas.validate(changed)

    def test_duplicate_and_forged_route_fail_closed(self):
        catalog = atlas.load_catalog()
        duplicate = copy.deepcopy(catalog)
        duplicate["entries"].append(copy.deepcopy(duplicate["entries"][0]))
        with self.assertRaisesRegex(ValueError, "repeated"):
            atlas.validate(duplicate)
        bad = copy.deepcopy(catalog)
        bad["entries"][0]["capture"]["route"] = "not-a-real-native-route"
        with self.assertRaisesRegex(ValueError, "not supported"):
            atlas.validate(bad)

    def test_missing_artwork_is_an_error_not_an_invented_reference(self):
        catalog = atlas.load_catalog()
        catalog["entries"][0]["art"] = "no-such-original-drawing"
        with self.assertRaisesRegex(ValueError, "missing"):
            atlas.validate(catalog)

    def test_preview_site_keeps_every_expected_id_and_marks_all_uncaptured(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "site"
            data = atlas.build(atlas.load_catalog(), out, None, None)
            self.assertEqual(data["counts"]["captured"], 0)
            self.assertEqual(len(data["entries"]), len(atlas.validate(atlas.load_catalog())))
            self.assertTrue((out / "atlas.js").is_file())
            self.assertTrue((out / "assets/modern-frame.png").is_file())
            self.assertTrue(all(entry["status"] in ("planned", "capture_pending")
                                for entry in data["entries"]))
            with self.assertRaisesRegex(ValueError, "overwrite"):
                atlas.build(atlas.load_catalog(), out, None, None)

    def test_missing_failure_marker_has_stable_id_check(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            place = root / "captures" / "URV-MD-001"
            place.mkdir(parents=True)
            (place / "capture-failure.json").write_text(json.dumps({"id":"OTHER","status":"failed"}))
            with self.assertRaisesRegex(ValueError, "unrelated"):
                atlas.build(atlas.load_catalog(), root / "out", root, None)

    def test_fake_png_or_receipt_is_rejected(self):
        entry = next(e for e in atlas.load_catalog()["entries"] if e["id"] == "URV-MD-001")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "readback-receipt.json").write_text(json.dumps({
                "source_sha":"a" * 40, "native_semantic_route":"root-quit",
                "requested_window_size":[1280,720],"actual_sdl_renderer_output":[1280,720],
                "SDL_driver":"windows","release_gate_credit":0,
                "visual_approved":False,"hardware_approved":False,
                "exe_sha256":"b"*64,"png_sha256":"c"*64,
            }))
            (root / "actual-sdl-drawable.png").write_bytes(b"not a screenshot")
            with self.assertRaisesRegex(ValueError, "PNG hash"):
                atlas.valid_receipt(entry, root, "a"*40, None)

    def test_capture_source_and_window_mismatch_rejected_before_images(self):
        entry = next(e for e in atlas.load_catalog()["entries"] if e["id"] == "URV-MD-001")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "readback-receipt.json").write_text(json.dumps({
                "source_sha":"a"*40,"native_semantic_route":"root-quit",
                "requested_window_size":[1024,768],"actual_sdl_renderer_output":[1024,768],
                "SDL_driver":"windows","release_gate_credit":0,
                "visual_approved":False,"hardware_approved":False,
                "exe_sha256":"b"*64,"png_sha256":"c"*64,
            }))
            (root / "actual-sdl-drawable.png").write_bytes(b"imposter")
            with self.assertRaisesRegex(ValueError, "source_sha"):
                atlas.valid_receipt(entry, root, "f"*40, None)


if __name__ == "__main__":
    unittest.main()
