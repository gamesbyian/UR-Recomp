#!/usr/bin/env python3
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/analyze_unused_audio_path.py"
SPEC = importlib.util.spec_from_file_location("analyze_unused_audio_path", TOOL)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class UnusedAudioPathTests(unittest.TestCase):
    def load_inputs(self):
        return (
            json.loads((ROOT / "analysis/generated/audio-setup-selector-map.json").read_text()),
            json.loads((ROOT / "analysis/generated/audio-package-map.json").read_text()),
            json.loads((ROOT / "analysis/generated/audio-extended-block-correlation.json").read_text()),
            json.loads((ROOT / "analysis/generated/apu-upload-path-summary.json").read_text()),
            json.loads((ROOT / "analysis/generated/audio-block-spc-correlation.json").read_text()),
        )

    def test_generated_analysis_is_fresh(self):
        report = MODULE.build_analysis(*self.load_inputs())
        expected = json.loads((ROOT / "analysis/generated/audio-unused-path-analysis.json").read_text())
        self.assertEqual(report, expected)
        expected_md = (ROOT / "analysis/generated/audio-unused-path-analysis.md").read_text()
        self.assertEqual(MODULE.render_markdown(report), expected_md)

    def test_unused_selector_and_orphan_table_structure(self):
        report = MODULE.build_analysis(*self.load_inputs())
        self.assertEqual(report["missing_setup_selectors"], ["0x3B", "0x3D"])
        relation = report["uncalled_table"]["relation_to_celebration_table_03FAD5"]
        self.assertTrue(relation["is_strict_subset"])
        self.assertTrue(relation["same_shared_slot_positions"])
        self.assertEqual(relation["removed_block_ids_hex"], ["0x07", "0x15", "0x29"])
        self.assertEqual(report["package_marker_analysis"]["Unused Song 1"]["zero_mismatch_tables"], ["0x03FB15"])
        self.assertEqual(report["package_marker_analysis"]["Unused Song 2"]["zero_mismatch_tables"], ["0x03FB55", "0x03FBD5"])
        self.assertTrue(report["interpretation"]["unused_song_2_race_package_corroboration"]["unused_song_2_same_offset"])


if __name__ == "__main__":
    unittest.main()
