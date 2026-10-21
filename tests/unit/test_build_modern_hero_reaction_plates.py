"""Original-ROM hero review plate producer; tests use synthetic raster, never art."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools import audit_modern_hero_source_clips as audit
from tools import build_modern_hero_reaction_plates as builder


def synthetic_rgba(colour):
    pixel = bytes((colour, 50, 60, 255))
    transparent = b"\x00\x00\x00\x00"
    data = bytearray(64 * 64 * 4)
    for y in range(10, 30):
        for x in range(10, 30):
            start = (y * 64 + x) * 4
            data[start:start + 4] = pixel
    return bytes(data)


class ModernHeroReactionPlatesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads(audit.REGISTRY.read_text(encoding="utf-8"))
        cls.source = json.loads(audit.SOURCE.read_text(encoding="utf-8"))

    def test_reject_noncanonical_or_absent_clip_without_pixels(self):
        with self.assertRaisesRegex(audit.ClipAdmissionError, "canonical USA"):
            builder.rasterize_original_clip(
                b"pretend rom", self.registry, self.source,
                "settle-and-recover")
        with self.assertRaisesRegex(audit.ClipAdmissionError, "only separately"):
            builder.rasterize_original_clip(
                b"pretend rom", self.registry, self.source,
                "root-entry-reaction")

    def _fixture(self):
        rom = b"R" * 2_097_152  # Synthetic, deliberately NOT a source ROM.
        digest = hashlib.sha256(rom).hexdigest()
        registry = copy.deepcopy(self.registry)
        source = {**self.source, "rom_sha256": digest}
        clip = audit.inspect_clip  # first validate real source before override
        ids = [x["p1_representation_id"] for x in registry[
            "motion_review_sequences"]["ordinary-race-1230-1239-entry-hold-exit"]["frames"]]
        colours = {rid: number + 1 for number, rid in enumerate(dict.fromkeys(ids))}
        for entry in registry["entries"]:
            if entry["representation_id"] in colours:
                entry["registration"]["semantic_anchors"]["wheel_contact_x2_y2"] = [39, 58]
        return rom, digest, registry, source, colours

    def test_synthetic_plate_output_keeps_provenance_and_no_loop(self):
        rom, digest, registry, source, colours = self._fixture()
        def fake_raster(_rom, entry):
            return synthetic_rgba(colours[entry["representation_id"]])
        with patch.object(builder, "CANONICAL_USA_SHA256", digest), patch.object(
            audit, "CANONICAL_USA_SHA256", digest
        ), patch.object(builder, "build_stock_rgba", side_effect=fake_raster):
            report, frames = builder.rasterize_original_clip(
                rom, registry, source, "settle-and-recover")
        self.assertEqual(len(frames), 10)
        self.assertEqual(len(report["frames"]), 10)
        self.assertEqual(len(set(x["original_rgba_sha256"] for x in report["frames"])), 3)
        self.assertFalse(report["may_reverse_or_loop"])
        self.assertFalse(report["native_hero_admitted"])
        self.assertEqual(report["canonical_rom_sha256"], digest)
        metrics = report["temporal_original_raster_metrics"]
        self.assertEqual(metrics["frame_count"], 10)
        self.assertEqual(metrics["distinct_rgba_frames"], 3)
        self.assertEqual(metrics["observed_static_edges"], 6)
        self.assertEqual(metrics["observed_dynamic_edges"], 3)
        self.assertEqual(metrics["max_observed_visible_change_pixels"], 400)
        self.assertEqual(metrics["counterfactual_last_to_first_edge"][
            "visible_changed_pixels"], 400)
        self.assertFalse(metrics["loop_certified"])
        self.assertFalse(metrics["source_guest_timing_independently_certified"])
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / "original-review"
            path = builder.write_private_review(report, frames, destination)
            self.assertTrue(path.is_file())
            receipt = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(len(list(destination.glob("original-guest-*.png"))), 10)
            self.assertEqual(len(list(destination.glob("*.png"))), 11)
            sheet = receipt["source_contact_sheet"]
            self.assertFalse(sheet["native_screenshot"])
            self.assertFalse(sheet["source_timing_certified"])
            self.assertFalse(sheet["human_visual_approval"])
            self.assertEqual([sheet["width"], sheet["height"]], [1280, 512])
            self.assertEqual(sheet["nearest_scale"], 4)
            self.assertEqual(sheet["source_registered_guest_frames"],
                             [f["registered_guest_frame"] for f in receipt["frames"]])
            self.assertEqual(hashlib.sha256(
                (destination / sheet["filename"]).read_bytes()).hexdigest(),
                sheet["review_png_sha256"])
            for frame in receipt["frames"]:
                image_path = destination / (
                    f"original-guest-{frame['registered_guest_frame']:04d}.png")
                self.assertEqual(hashlib.sha256(image_path.read_bytes()).hexdigest(),
                                 frame["review_png_sha256"])

    def test_direct_executable_help_imports_in_a_foreign_cwd(self):
        # Prior version worked as tools.* import but relied on PYTHONPATH
        # when invoked directly. Test the documented real CLI launch form.
        script = builder.ROOT / "tools" / "build_modern_hero_reaction_plates.py"
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, str(script), "--help"], cwd=tmp,
                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--clip", result.stdout)
        self.assertIn("--out-dir", result.stdout)

    def test_original_contact_sheet_replication_and_empty_final_slot(self):
        a = synthetic_rgba(17)
        b = synthetic_rgba(31)
        rgba, width, height = builder.nearest_original_contact_sheet([a, b])
        self.assertEqual((width, height), (1280, 256))
        self.assertEqual(len(rgba), 1280 * 256 * 4)
        def pixel(x, y):
            return rgba[(y * width + x) * 4:(y * width + x + 1) * 4]
        for x in (40, 41, 42, 43):
            for y in (40, 41, 42, 43):
                self.assertEqual(pixel(x, y), bytes((17, 50, 60, 255)))
        self.assertEqual(pixel(256 + 40, 40), bytes((31, 50, 60, 255)))
        self.assertEqual(pixel(1280 - 1, 255), b"\\x00\\x00\\x00\\x00")
        self.assertEqual(pixel(0, 0), b"\\x00\\x00\\x00\\x00")

    def test_refuse_existing_targets_symlinks_and_receipt_mismatch(self):
        frame = synthetic_rgba(17)
        report = {"frames": [{
            "registered_guest_frame": 5,
            "original_rgba_sha256": hashlib.sha256(frame).hexdigest(),
        }]}
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            target = tmp / "result"
            target.mkdir()
            with self.assertRaisesRegex(audit.ClipAdmissionError, "new and absent"):
                builder.write_private_review(report, [frame], target)
            target.rmdir()
            target.symlink_to(tmp, target_is_directory=True)
            with self.assertRaisesRegex(audit.ClipAdmissionError, "new and absent"):
                builder.write_private_review(report, [frame], target)
            target.unlink()
            bad = copy.deepcopy(report)
            bad["frames"][0]["original_rgba_sha256"] = "0" * 64
            with self.assertRaisesRegex(audit.ClipAdmissionError, "does not match"):
                builder.write_private_review(bad, [frame], target)
            self.assertFalse(target.exists())
            self.assertEqual(list(tmp.iterdir()), [])

    def test_atomic_publish_failure_cleans_staging_and_keeps_target_absent(self):
        frame = synthetic_rgba(17)
        report = {"frames": [{
            "registered_guest_frame": 5,
            "original_rgba_sha256": hashlib.sha256(frame).hexdigest(),
        }]}
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            target = folder / "receipt"
            with patch.object(builder.os, "rename", side_effect=OSError("disk full")):
                with self.assertRaisesRegex(OSError, "disk full"):
                    builder.write_private_review(report, [frame], target)
            self.assertFalse(target.exists())
            self.assertEqual(list(folder.iterdir()), [])
            result = builder.write_private_review(report, [frame], target)
            self.assertTrue(result.is_file())
            self.assertEqual(len(list(target.glob("*.png"))), 2)
            with self.assertRaisesRegex(audit.ClipAdmissionError, "new and absent"):
                builder.write_private_review(report, [frame], target)

    def test_duplicate_and_out_of_order_output_labels_fail_closed(self):
        frame = synthetic_rgba(17)
        digest = hashlib.sha256(frame).hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            for labels in ([5, 5], [5, 7], [7, 6], [True, 1]):
                report = {"frames": [
                    {"registered_guest_frame": n, "original_rgba_sha256": digest}
                    for n in labels]}
                with self.subTest(labels=labels), self.assertRaises(
                    audit.ClipAdmissionError):
                    builder.write_private_review(
                        report, [frame, frame], Path(tmp) / "receipt")
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_review_art_must_not_write_into_checkout(self):
        with self.assertRaisesRegex(audit.ClipAdmissionError, "outside repository"):
            builder.require_private_output_dir(audit.ROOT / "analysis" / "generated")
        with self.assertRaisesRegex(audit.ClipAdmissionError, "outside repository"):
            builder.require_private_output_dir(audit.ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(builder.require_private_output_dir(Path(tmp)),
                             Path(tmp).resolve())

    def test_identical_representation_must_have_identical_raster(self):
        rom, digest, registry, source, colours = self._fixture()
        counter = [0]
        def fake_raster(_rom, _entry):
            counter[0] += 1
            return synthetic_rgba(counter[0])
        with patch.object(builder, "CANONICAL_USA_SHA256", digest), patch.object(
            audit, "CANONICAL_USA_SHA256", digest
        ), patch.object(builder, "build_stock_rgba", side_effect=fake_raster):
            with self.assertRaisesRegex(audit.ClipAdmissionError,
                                        "same source representation"):
                builder.rasterize_original_clip(
                    rom, registry, source, "settle-and-recover")

    def test_changed_anchor_and_incomplete_raster_fail_closed(self):
        rom, digest, registry, source, colours = self._fixture()
        with patch.object(builder, "CANONICAL_USA_SHA256", digest), patch.object(
            audit, "CANONICAL_USA_SHA256", digest
        ), patch.object(builder, "build_stock_rgba", return_value=b""):
            with self.assertRaisesRegex(audit.ClipAdmissionError, "64x64"):
                builder.rasterize_original_clip(
                    rom, registry, source, "settle-and-recover")
        affected = next(e for e in registry["entries"] if
                        e["representation_id"] in colours)
        affected["registration"]["semantic_anchors"]["wheel_contact_x2_y2"] = [0, 0]
        with patch.object(builder, "CANONICAL_USA_SHA256", digest), patch.object(
            audit, "CANONICAL_USA_SHA256", digest
        ), patch.object(builder, "build_stock_rgba",
                        side_effect=lambda _rom, e:
                            synthetic_rgba(colours[e["representation_id"]])):
            with self.assertRaisesRegex(audit.ClipAdmissionError, "wheel contact"):
                builder.rasterize_original_clip(
                    rom, registry, source, "settle-and-recover")


if __name__ == "__main__":
    unittest.main()
