"""One frozen source palette-index relabel null for missing 2026 3D material evidence."""
import hashlib
import json
from pathlib import Path
import unittest
from tools.art.analyze_original_rom_palette_rotation_null import (
    SCHEMA, ROM_SHA, SOURCE_SHA, MODELS, EVEN_TRAIN, ODD_ANGLES,
    overlap_counts, majority_map, bijection_map, metric, audit,
)

ROOT=Path(__file__).resolve().parents[2]


class OriginalROMPaletteMappingNullTests(unittest.TestCase):
    def test_no_alpha_relabelling_and_exact_bijection(self):
        c=[[0]*16 for _ in range(16)]
        c[1][2]=8;c[1][1]=3
        c[2][1]=7;c[2][2]=2
        for n in range(3,16):c[n][n]=9
        maj=majority_map(c)
        bij=bijection_map(c)
        self.assertEqual(maj[0],0)
        self.assertEqual(bij[0],0)
        self.assertEqual(maj[1:3],(2,1))
        self.assertEqual(bij[1:3],(2,1))
        self.assertEqual(sorted(bij),list(range(16)))
        self.assertEqual(sum(c[i][bij[i]] for i in range(1,16)),8+7+13*9)

    def test_source_4bpp_overlap_changes_only_index_labels(self):
        actual=bytearray(4096)
        predicted=bytearray(4096)
        actual[800]=2;predicted[800]=1
        actual[801]=3;predicted[801]=3
        actual[802]=5
        predicted[803]=4
        c=[[0]*16 for _ in range(16)]
        self.assertEqual(overlap_counts(bytes(actual),bytes(predicted),c),2)
        self.assertEqual(c[1][2],1)
        self.assertEqual(c[3][3],1)
        identity=metric(bytes(actual),bytes(predicted),tuple(range(16)))
        remap=list(range(16));remap[1]=2
        improved=metric(bytes(actual),bytes(predicted),tuple(remap))
        self.assertEqual(identity["exact_original_index_matches"],1)
        self.assertEqual(improved["exact_original_index_matches"],2)
        self.assertEqual(identity["source_opaque_pixels"],3)
        self.assertEqual(improved["overlap_opaque_pixels"],2)
        self.assertAlmostEqual(improved["source_opaque_exact_index_recall"],2/3,places=8)
        with self.assertRaisesRegex(ValueError,"transparency"):
            metric(bytes(actual),bytes(predicted),tuple([1]+list(range(1,16))))

    def test_actual_source_rom_even_train_odd_score_and_baseline(self):
        rom=(ROOT/"reference/roms/retail/Uniracers_USA.sfc").read_bytes()
        source=(ROOT/"analysis/data/racer-original-ROM-24phase-64angle-source-axis-20261103.json").read_bytes()
        self.assertEqual(hashlib.sha256(rom).hexdigest(),ROM_SHA)
        self.assertEqual(hashlib.sha256(source).hexdigest(),SOURCE_SHA)
        record=audit(rom,source)
        self.assertEqual(record["schema"],SCHEMA)
        self.assertEqual(record["training_original_orientation_indices"],list(EVEN_TRAIN))
        self.assertEqual(record["scored_original_orientation_indices"],list(ODD_ANGLES))
        self.assertEqual(set(record["candidate_index_mappings"]),set(MODELS))
        self.assertFalse(record["physical_source_3D_mesh_camera_lights_or_materials_recovered"])
        self.assertFalse(record["source_owner_art_approval"])
        self.assertTrue(record["global_mapping_shared_across_all_phases_and_angles"])
        stats=record["pooled_original_odd_orientation_results"]
        self.assertEqual(stats["index_identity"]["source_opaque_pixels"],41141)
        self.assertEqual(stats["index_identity"]["exact_original_index_matches"],9806)
        self.assertGreater(record["training_pixel_pairs_in_opaque_overlap"],0)
        for model in MODELS:
            self.assertEqual(stats[model]["source_opaque_pixels"],41141)
            self.assertTrue(0<=stats[model]["pooled_source_exact_index_recall"]<=1)
        print("OK ART4K_SOURCE_ROTATED_2D_INDEX_RELABEL_NULL",
              json.dumps(stats,sort_keys=True))

    def test_invalid_original_rom_or_axis_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"SHA"):
            audit(b"",b"{}")


if __name__=="__main__":
    unittest.main()
