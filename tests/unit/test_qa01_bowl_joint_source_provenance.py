"""ROM-free same-source Bowl historical-movie/input/guest archive binding tests."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests/unit"))
import qa01_bowl_joint_source_provenance as joint
import qa01_bowl_source_movie_memory as movie
from test_qa01_bowl_movie_sram_crosswalk import fixture as three_guest_fixture


class BowlJointSourceProvenanceTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        source_zip, _, _ = three_guest_fixture(self.root)
        with ZipFile(source_zip) as z:
            z.extractall(self.root)
        self.primary = self.root / "bowl-report.json"
        record = json.loads(self.primary.read_text())
        record["original_movie_window_sha256"] = "c" * 64
        record["native_frame_shift"] = 1
        for sample in record["bowl_source_movie_three_guest_memory"]["samples"]:
            offset = sample["offset_from_source_movie_bowl_result"]
            for guest, folder in (("original", "ref"), ("native", "native")):
                receipt = sample["fresh_guests"][guest]
                for kind in ("wram", "sram"):
                    original = (self.root / "bowl" / "source" /
                                f"source-bowl-switcher-{offset:03d}.{kind}.bin").read_bytes()
                    actual = (self.root / "bowl" / "replay" / folder /
                              f"bowl-next-switcher-{offset}.{kind}.bin").read_bytes()
                    receipt[kind + "_source_vs_guest"] = movie.diff(original, actual)
        self.primary.write_text(json.dumps(record), encoding="utf-8")
        sha = hashlib.sha256(self.primary.read_bytes()).hexdigest()
        self.raw = self.root / "bowl-independent-raw-audit.json"
        self.raw.write_text(json.dumps({
            "case": "bowl", "producer_sha256": sha,
            "observed_raw_wram_sram_pairs": 12,
            "accepted_event_credit": 0,
            "independent_complete_usa_event_adjudication": "HOLD",
        }), encoding="utf-8")
        self.route = self.root / "bowl-source-input-identity.json"
        self.route.write_text(json.dumps({
            "original_case": "bowl", "original_producer_sha256": sha,
            "usa_event_admissions": 0,
            "route": {
                "original_2014_movie_controller_window_recomputed": True,
                "original_native_supplied_masks_and_durations_equal": True,
                "guest_controller_consumption_proven": False,
                "release_credit": 0,
                "source_original_movie_window_sha256": "c" * 64,
                "native_supplied_input_shift_exact": 1,
                "input_event_rows_per_guest": 593,
            },
        }), encoding="utf-8")

    def test_joint_original_producer_same_run_without_acceptance(self):
        evidence = joint.audit(self.root)
        self.assertTrue(evidence["same_producer_input_and_memory_evidence_proven"])
        self.assertEqual(evidence["actual_2014_movie_source_images_independently_rehashed"], 16)
        self.assertEqual(evidence["actual_fresh_guest_memory_images_independently_rehashed"], 32)
        self.assertEqual(len(evidence["source_movie_guest_full_byte_differences"]), 16)
        self.assertFalse(evidence["guest_consumed_input_proven"])
        self.assertEqual(evidence["accepted_complete_usa_events"], 0)

    def test_wrong_producer_hash_in_source_input_fails_closed(self):
        row = json.loads(self.route.read_text())
        row["original_producer_sha256"] = "1" * 64
        self.route.write_text(json.dumps(row))
        with self.assertRaisesRegex(ValueError, "different producer"):
            joint.audit(self.root)

    def test_raw_movie_memory_change_detected_without_reconstructing_zip(self):
        image = (self.root / "bowl/source/source-bowl-switcher-334.wram.bin")
        raw = bytearray(image.read_bytes())
        raw[0x69] ^= 2
        image.write_bytes(raw)
        with self.assertRaisesRegex(ValueError, "memory SHA256"):
            joint.audit(self.root)

    def test_missing_source_movie_or_native_image_blocks_joint_receipt(self):
        image = (self.root / "bowl/replay/native/bowl-next-switcher-354.sram.bin")
        image.unlink()
        with self.assertRaisesRegex(ValueError, "missing or symlinked"):
            joint.audit(self.root)

    def test_tampered_raw_comparison_fails_despite_image_sha_match(self):
        row = json.loads(self.primary.read_text())
        row["bowl_source_movie_three_guest_memory"]["samples"][0][
            "fresh_guests"]["original"]["wram_source_vs_guest"][
                "different_byte_count"] = 0
        self.primary.write_text(json.dumps(row))
        digest = hashlib.sha256(self.primary.read_bytes()).hexdigest()
        for path in (self.route, self.raw):
            item = json.loads(path.read_text())
            item["original_producer_sha256" if path == self.route
                 else "producer_sha256"] = digest
            path.write_text(json.dumps(item))
        with self.assertRaisesRegex(ValueError, "difference receipt contradicted"):
            joint.audit(self.root)

    def test_source_movie_input_window_mismatch_blocks_joint_receipt(self):
        row = json.loads(self.route.read_text())
        row["route"]["source_original_movie_window_sha256"] = "2" * 64
        self.route.write_text(json.dumps(row))
        with self.assertRaisesRegex(ValueError, "2014 source movie controller input proof"):
            joint.audit(self.root)


if __name__ == "__main__":
    unittest.main()
