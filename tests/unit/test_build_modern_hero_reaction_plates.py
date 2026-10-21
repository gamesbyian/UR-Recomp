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
            path = builder.write_private_review(report, frames, Path(tmp))
            self.assertTrue(path.is_file())
            receipt = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(len(list(Path(tmp).glob("*.png"))), 10)
            for frame in receipt["frames"]:
                image_path = Path(tmp) / (
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
