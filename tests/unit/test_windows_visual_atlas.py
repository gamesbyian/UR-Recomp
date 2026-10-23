"""ROM-free contract tests for the inventory, build and capture admission boundary."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest import mock

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

    def test_assembled_capture_requires_independent_native_witness(self):
        # A PNG with a matching JSON receipt must not earn captured status
        # without the original P7 pixels and native-process log. The witness
        # validator itself is exercised separately by the intake tests.
        source = "a" * 40
        receipt = {
            "source_sha": source, "exe_sha256": "b" * 64,
            "png_sha256": "c" * 64, "SDL_driver": "windows",
            "native_semantic_route": "root-quit",
            "actual_sdl_renderer_output": [1280, 720],
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case = root / "captures" / "URV-MD-001"
            case.mkdir(parents=True)
            (case / "readback-receipt.json").write_text("{}", encoding="utf-8")
            (case / "actual-sdl-drawable.png").write_bytes(b"fixture")
            with (mock.patch.object(atlas, "valid_receipt", return_value=(receipt, "b" * 64)),
                  mock.patch("tools.windows_visual_atlas_intake.witness", return_value=False) as check):
                with self.assertRaisesRegex(ValueError, "native P7/log witness"):
                    atlas.build(atlas.load_catalog(), root / "unverified", root, source)
                check.assert_called_once_with(receipt, case)
            with (mock.patch.object(atlas, "valid_receipt", return_value=(receipt, "b" * 64)),
                  mock.patch("tools.windows_visual_atlas_intake.witness", return_value=True) as check):
                data = atlas.build(atlas.load_catalog(), root / "verified", root, source)
                check.assert_called_once_with(receipt, case)
            self.assertEqual(data["counts"]["captured"], 1)
            self.assertEqual((root / "verified" / "images" / "URV-MD-001.png").read_bytes(),
                             b"fixture")


    def test_resume_keeps_native_witnesses_and_emits_parseable_jsonl(self):
        # ROM-free orchestration regression: a complete previous capture must
        # skip the driver, retain its P7/log provenance and journal two events.
        entry = {
            "id": "URV-MD-001",
            "capture": {"shard": "frontend", "route": "root-quit", "size": "1280x720"},
        }
        digest = "b" * 64
        receipt = {"p7_sha256": digest, "native_process_log_sha256": digest}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prior = root / "prior" / "captures" / entry["id"]
            stage = prior / "capture_observed"
            stage.mkdir(parents=True)
            (prior / "readback-receipt.json").write_text("{}", encoding="utf-8")
            (prior / "actual-sdl-drawable.png").write_bytes(b"test-png")
            (stage / "actual-sdl-drawable.pam").write_bytes(b"test-p7")
            (stage / "native-process.log").write_text("test-native-log", encoding="utf-8")
            output = root / "new"
            def mock_witness(_receipt, folder):
                witness_root = folder / "capture_observed"
                return ((witness_root / "actual-sdl-drawable.pam").is_file()
                        and (witness_root / "native-process.log").is_file())
            with (mock.patch.object(atlas, "validate", return_value=[entry]),
                  mock.patch.object(atlas, "sha256", return_value=digest),
                  mock.patch.object(atlas, "valid_receipt", return_value=(receipt, digest)),
                  mock.patch("tools.windows_visual_atlas_intake.witness",
                             side_effect=mock_witness),
                  mock.patch.object(atlas.subprocess, "run",
                                    side_effect=AssertionError("unexpected native recapture")) as driver):
                status = atlas.capture_shard(
                    {"entries": [entry]}, shard="frontend", exe=root / "game.exe",
                    rom=root / "retail.sfc", target=output, source="a" * 40,
                    timeout=5, workers=1, resume_from=root / "prior")
            self.assertEqual(status, 0)
            driver.assert_not_called()
            reused = output / "captures" / entry["id"]
            self.assertEqual((reused / "capture_observed" / "actual-sdl-drawable.pam").read_bytes(),
                             b"test-p7")
            self.assertEqual((reused / "capture_observed" / "native-process.log").read_text(),
                             "test-native-log")
            events = [json.loads(line) for line in
                      (output / "progress.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual([event["status"] for event in events], ["start", "end"])
            self.assertEqual(events[-1]["result"], "resumed")
            summary = json.loads((output / "shard-summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["reused"], 1)



    def test_assembled_artifact_root_matches_download_layout(self):
        # Each capture artifact retains its captures/<atlas-id>/... tree.
        # The assembler itself appends captures/<atlas-id> to --captures.
        # Downloading into an additional captures/ layer silently makes
        # every successfully captured case appear pending in the website.
        workflow = (atlas.ROOT / ".github/workflows/windows-visual-atlas.yml").read_text(
            encoding="utf-8")
        assemble = workflow.split("\n  assemble:\n", 1)[1].split(
            "\n  publish-pages:\n", 1)[0]
        self.assertIn("pattern: visual-atlas-*", assemble)
        self.assertIn("merge-multiple: true", assemble)
        self.assertIn("path: ${{ runner.temp }}/atlas-captures\n", assemble)
        self.assertIn('--captures "$RUNNER_TEMP/atlas-captures"', assemble)
        self.assertNotIn("path: ${{ runner.temp }}/atlas-captures/captures", assemble)


if __name__ == "__main__":
    unittest.main()
