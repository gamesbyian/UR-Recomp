"""ROM-free original pixel revalidation and anti-leakage family split tests."""
from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.art.export_registered_original_racer_corpus import collect
from tools.art.freeze_racer_source_family_splits import (
    freeze, validate_corpus, CANONICAL_ROM_SHA, REQUEST_SCHEMA,
)


class SourceFamilySplitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.manifest = self.root / "source-corpus.json"
        self.roles = self.root / "roles.json"
        entries = [
            {"representation_id": "p1-a", "player": "p1"},
            {"representation_id": "p1-alias", "player": "p1"},
            {"representation_id": "p2-b", "player": "p2"},
            {"representation_id": "p1-c", "player": "p1"},
        ]
        def window(frame, player, identity):
            return {"window_start": frame, "window_end": frame,
                    "frames": [{"frame": frame, player+"_representation_id": identity}]}
        registry = {
            "schema_version": 1, "entries": entries,
            "motion_review_sequence": window(100, "p1", "p1-a"),
            "motion_review_sequences": {
                "alias": window(110, "p1", "p1-alias"),
                "distinct": window(200, "p2", "p2-b"),
                "other": window(300, "p1", "p1-c"),
            },
        }
        def render(entry):
            # Same alpha for first/alias, but different palette colour.
            rid = entry["representation_id"]
            pixels = {"p1-a":(3,6), "p1-alias":(3,6),
                      "p2-b":(11,8), "p1-c":(25,14)}
            xy = pixels[rid]
            data = bytearray(64*64*4)
            pos = (xy[1]*64+xy[0])*4
            data[pos:pos+4] = bytes((20 if rid=="p1-a" else 50,80,120,255))
            return bytes(data)
        self.corpus, pngs = collect(registry, render)
        self.corpus["source_rom_verified_and_used_for_composition"] = True
        (self.root/"stock").mkdir()
        for rgba_sha, png in pngs.items():
            (self.root/"stock"/("source-"+rgba_sha+".png")).write_bytes(png)
        self.write()

    def write(self):
        self.manifest.write_text(json.dumps(self.corpus), encoding="utf-8")
        self.roles.write_text(json.dumps({
            "schema": REQUEST_SCHEMA, "roles": {
                "first-1205-1220": "fit",
                "alias": "fit",
                "distinct": "withheld_candidate",
                "other": "diagnostic",
            }
        }), encoding="utf-8")

    def test_distinct_original_source_groups_can_be_frozen(self):
        report = freeze(self.manifest, self.roles)
        self.assertEqual(report["total_source_windows"], 4)
        self.assertEqual(report["verified_distinct_original_binary_silhouettes"], 3)
        self.assertEqual(report["role_summary"]["fit"]["window_count"], 2)
        self.assertEqual(report["role_summary"]["fit"]["independent_binary_silhouette_group_count"], 1)
        self.assertEqual(report["independently_revalidated_source_png_count"], 4)
        self.assertTrue(report["no_original_binary_silhouette_across_roles"])
        self.assertFalse(report["withheld_candidate_is_an_independent_3d_camera"])
        self.assertFalse(report["shipping_art_approved"])

    def test_cross_window_alias_in_separate_roles_is_detected(self):
        r = json.loads(self.roles.read_text())
        r["roles"]["alias"] = "withheld_candidate"
        self.roles.write_text(json.dumps(r))
        with self.assertRaisesRegex(ValueError, "leaks across"):
            freeze(self.manifest, self.roles)

    def test_changed_corpus_png_and_self_updated_file_hash_fail(self):
        original = next(iter(self.corpus["source_representations"].values()))
        local = self.root/original["local_file"]
        local.write_bytes(local.read_bytes()[:-1] + b"\0")
        original["local_png_sha256"] = hashlib.sha256(local.read_bytes()).hexdigest()
        self.write()
        with self.assertRaises((ValueError, OSError)):
            freeze(self.manifest, self.roles)

    def test_original_image_sha_cannot_be_swapped_with_another_64px_png(self):
        source = self.corpus["source_representations"]["p1-a"]
        other = self.corpus["source_representations"]["p1-c"]
        source["local_file"] = other["local_file"]
        self.write()
        with self.assertRaisesRegex(ValueError, "swapped"):
            validate_corpus(self.manifest)

    def test_declared_rom_verified_false_and_wrong_rom_fail(self):
        self.corpus["source_rom_verified_and_used_for_composition"] = False
        self.write()
        with self.assertRaisesRegex(ValueError, "canonical-ROM"):
            freeze(self.manifest, self.roles)
        self.corpus["source_rom_verified_and_used_for_composition"] = True
        self.corpus["source_rom_sha256"] = "0"*64
        self.write()
        with self.assertRaisesRegex(ValueError, "canonical-ROM"):
            freeze(self.manifest, self.roles)

    def test_extra_or_unknown_window_roles_rejected(self):
        r=json.loads(self.roles.read_text())
        r["roles"]["phantom"] = "diagnostic"
        self.roles.write_text(json.dumps(r))
        with self.assertRaisesRegex(ValueError, "every source window"):
            freeze(self.manifest, self.roles)

    def test_missing_source_frame_and_duplicate_frame_rejected(self):
        self.corpus["source_temporal_frame_observations"] = []
        self.write()
        with self.assertRaisesRegex(ValueError, "malformed"):
            validate_corpus(self.manifest)
        self.corpus["source_temporal_frame_observations"] = [
            {"window": "first-1205-1220", "guest_frame": 100,
             "representations": {"p1": "p1-a"}}] * 2
        self.write()
        with self.assertRaisesRegex(ValueError, "duplicate"):
            validate_corpus(self.manifest)

    def test_source_mask_mismatch_is_rejected(self):
        self.corpus["source_representations"]["p1-a"]["source_binary_mask_sha256"] = "0"*64
        self.write()
        with self.assertRaisesRegex(ValueError, "mask hash"):
            freeze(self.manifest, self.roles)


if __name__ == "__main__":
    unittest.main()
