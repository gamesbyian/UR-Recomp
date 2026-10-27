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

    def test_missing_owner_approved_plate_fails_closed(self):
        catalog = atlas.load_catalog()
        required = {atlas.placeholder_art(entry) for entry in catalog["entries"]}
        self.assertEqual(required, set(atlas.ATLAS_ART.values()))
        with tempfile.TemporaryDirectory() as directory:
            art = Path(directory)
            # A legacy per-entry art label cannot supply a substitute image.
            catalog["entries"][0]["art"] = "no-such-original-drawing"
            for name in sorted(required):
                (art / (name + ".png")).write_bytes(b"test fixture")
            self.assertEqual(len(atlas.validate(catalog, art_directory=art)),
                             len(catalog["entries"]))
            for name in sorted(required):
                (art / (name + ".png")).unlink()
                with self.assertRaisesRegex(ValueError, "approved coming-soon plate missing"):
                    atlas.validate(catalog, art_directory=art)
                (art / (name + ".png")).write_bytes(b"test fixture")

    def test_preview_site_keeps_every_expected_id_and_marks_all_uncaptured(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "site"
            data = atlas.build(atlas.load_catalog(), out, None, None)
            self.assertEqual(data["counts"]["captured"], 0)
            self.assertEqual(len(data["entries"]), len(atlas.validate(atlas.load_catalog())))
            self.assertTrue((out / "atlas.js").is_file())
            required = {atlas.placeholder_art(entry) for entry in data["entries"]}
            self.assertEqual(required, set(atlas.ATLAS_ART.values()))
            for name in required:
                self.assertTrue((out / "assets" / (name + ".png")).is_file())
            self.assertFalse((out / "assets/modern-frame.png").exists())
            self.assertTrue(all(entry["art"] == atlas.placeholder_art(entry)
                                for entry in data["entries"]))
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

    def test_failed_capture_partial_receipt_does_not_break_partial_site(self):
        source = "a" * 40
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case = root / "captures" / "URV-MD-001"
            case.mkdir(parents=True)
            (case / "readback-receipt.json").write_text(
                '{"incomplete":true}', encoding="utf-8")
            (case / "capture-failure.json").write_text(json.dumps({
                "id": "URV-MD-001", "status": "failed", "reason": "driver exited"
            }), encoding="utf-8")
            with mock.patch.object(atlas, "valid_receipt",
                                   side_effect=AssertionError("partial receipt admitted")):
                data = atlas.build(atlas.load_catalog(), root / "site", root, source)
            self.assertEqual(data["counts"]["capture_failed"], 1)
            self.assertEqual(data["counts"]["captured"], 0)
            case_data = next(e for e in data["entries"] if e["id"] == "URV-MD-001")
            self.assertEqual(case_data["status"], "capture_failed")

    def test_failed_current_capture_cannot_be_masked_by_approved_incidental(self):
        # An older, reviewed capture can fill a pending atlas slot, but it
        # must not overwrite this campaign's explicit native driver failure.
        # No ROM, native process or real screenshot is needed for this guard.
        source = "a" * 40
        entry = next(e for e in atlas.load_catalog()["entries"]
                     if e["id"] == "URV-MD-001")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            failed = root / "captures" / entry["id"]
            failed.mkdir(parents=True)
            (failed / "capture-failure.json").write_text(json.dumps({
                "id": entry["id"], "status": "failed",
                "reason": "native capture driver exited",
            }), encoding="utf-8")
            approved = root / "media/windows-visual-atlas/approved" / entry["id"]
            approved.mkdir(parents=True)
            (approved / "intake-approval.json").write_text(json.dumps({
                "schema_version": 1, "atlas_id": entry["id"],
                "source_sha": source, "code_integrated_at_scan": True,
                "independent_visual_approval": False, "release_gate_credit": 0,
            }), encoding="utf-8")
            with (mock.patch.object(atlas, "ROOT", root),
                  mock.patch.object(atlas, "validate", return_value=[entry]),
                  mock.patch("tools.windows_visual_atlas_intake.code_state",
                             return_value="integrated-current-visual") as code,
                  mock.patch.object(atlas, "valid_receipt",
                                    side_effect=AssertionError(
                                        "failed capture fell through to incidental"))):
                data = atlas.build({"entries": [entry]}, root / "site",
                                   root, source)
            self.assertEqual(data["counts"]["capture_failed"], 1)
            self.assertEqual(data["counts"]["captured"], 0)
            self.assertEqual(data["entries"][0]["status"], "capture_failed")
            self.assertNotIn("image", data["entries"][0])
            code.assert_not_called()

    def test_capture_driver_without_native_witness_is_a_failed_case(self):
        entry = {"id": "URV-MD-001", "capture": {
            "shard": "frontend", "route": "root-quit", "size": "1280x720"}}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            exe = root / "game.exe"
            exe.write_bytes(b"synthetic executable")
            def driver(command, **_kwargs):
                output = Path(command[command.index("--out") + 1])
                output.mkdir(parents=True)
                (output / "readback-receipt.json").write_text(
                    '{"incomplete":true}', encoding="utf-8")
                return mock.Mock(returncode=0, stdout="", stderr="")
            with (mock.patch.object(atlas, "validate", return_value=[entry]),
                  mock.patch.object(atlas.subprocess, "run", side_effect=driver),
                  mock.patch.object(atlas, "valid_receipt", return_value=({}, "b" * 64)),
                  mock.patch("tools.windows_visual_atlas_intake.witness", return_value=False)):
                status = atlas.capture_shard(
                    {"entries": [entry]}, shard="frontend", exe=exe,
                    rom=root / "retail.sfc", target=root / "output",
                    source="a" * 40, timeout=5, workers=1)
            self.assertEqual(status, 1)
            failed = root / "output" / "captures" / "URV-MD-001" / "capture-failure.json"
            self.assertTrue(failed.is_file())
            self.assertIn("native P7/log witness", failed.read_text(encoding="utf-8"))

    def test_unexpected_case_error_survives_as_explicit_failed_capture(self):
        # A malformed driver receipt may raise an unexpected exception.
        # Preserve the failed case in the assembled atlas rather than showing
        # a pending slot, while allowing other shard cases to complete.
        entry = next(e for e in atlas.load_catalog()["entries"]
                     if e["id"] == "URV-MD-001")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            exe = root / "game.exe"
            exe.write_bytes(b"synthetic executable")
            capture = root / "capture"
            with (mock.patch.object(atlas, "validate", return_value=[entry]),
                  mock.patch.object(atlas.subprocess, "run", return_value=mock.Mock(
                      returncode=0, stdout="", stderr="")),
                  mock.patch.object(atlas, "valid_receipt",
                                    side_effect=TypeError("malformed receipt object"))):
                status = atlas.capture_shard(
                    {"entries": [entry]}, shard="frontend", exe=exe,
                    rom=root / "retail.sfc", target=capture,
                    source="a" * 40, timeout=5, workers=1)
            self.assertEqual(status, 1)
            failure = json.loads((capture / "captures" / entry["id"] /
                                  "capture-failure.json").read_text(encoding="utf-8"))
            self.assertEqual(failure["id"], entry["id"])
            self.assertEqual(failure["status"], "failed")
            self.assertIn("TypeError", failure["reason"])
            summary = json.loads((capture / "shard-summary.json").read_text(
                encoding="utf-8"))
            self.assertEqual(summary["failed"], 1)
            journal = [json.loads(line) for line in (capture / "progress.jsonl")
                       .read_text(encoding="utf-8").splitlines()]
            self.assertEqual([event["status"] for event in journal], ["start", "end"])
            with mock.patch.object(atlas, "validate", return_value=[entry]):
                site = atlas.build({"entries": [entry]}, root / "site", capture,
                                   "a" * 40)
            self.assertEqual(site["counts"]["capture_failed"], 1)
            self.assertEqual(site["entries"][0]["status"], "capture_failed")

    def test_capture_rejects_receipt_from_different_executable(self):
        # A driver returning zero is insufficient: the receipt must name the
        # executable whose bytes this shard actually launched.
        entry = {"id": "URV-MD-001", "capture": {
            "shard": "frontend", "route": "root-quit", "size": "1280x720"}}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            exe = root / "game.exe"
            exe.write_bytes(b"expected-executable")
            expected = atlas.sha256(exe)
            wrong = "f" * 64 if expected != "f" * 64 else "e" * 64
            seen = []
            def validate_receipt(_entry, _root, _source, exe_digest):
                seen.append(exe_digest)
                if exe_digest != wrong:
                    raise ValueError("Atlas captures used different Windows executables")
                return {"exe_sha256": wrong}, wrong
            with (mock.patch.object(atlas, "validate", return_value=[entry]),
                  mock.patch.object(atlas.subprocess, "run",
                                    return_value=mock.Mock(returncode=0, stdout="", stderr="")),
                  mock.patch.object(atlas, "valid_receipt",
                                    side_effect=validate_receipt)):
                status = atlas.capture_shard(
                    {"entries": [entry]}, shard="frontend", exe=exe,
                    rom=root / "retail.sfc", target=root / "output",
                    source="a" * 40, timeout=5, workers=1)
            self.assertEqual(status, 1)
            self.assertEqual(seen, [expected])
            failure = json.loads((root / "output" / "captures" / entry["id"] /
                                  "capture-failure.json").read_text(encoding="utf-8"))
            self.assertIn("different Windows executables", failure["reason"])
            summary = json.loads((root / "output" / "shard-summary.json").read_text(
                encoding="utf-8"))
            self.assertEqual(summary["failed"], 1)
            self.assertEqual(summary["captured"], 0)

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
