"""Regression for archived real research evidence, not original/native acceptance."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REPORT=ROOT/"docs/QA-FRONTIER-15-FRAME-RESULTS-20261013.md"
SOURCE=ROOT/"tools/summarize_paired_player_slots.py"
CAMERA=ROOT/"docs/knowledge/rendering-camera-and-oam.md"


class FifteenFrameResearchHandoff(unittest.TestCase):
    def test_real_run_and_reproducer_identities_are_preserved(self):
        report=REPORT.read_text()
        for value in ("38446393623","20,579","50036056",
                      "50036005","50036002","2580","1980","2820",
                      "dd5632f0a612ee22cc46d9b1ce7a6005a5fa555f"):
            self.assertIn(value,report)
        self.assertIn("29",report)
        self.assertIn("5",report)
        self.assertIn("0/45",report)

    def test_culling_camera_and_air_offsets_stay_separate(self):
        from importlib.util import spec_from_file_location, module_from_spec
        spec=spec_from_file_location("paired_slot_source_contract",SOURCE)
        module=module_from_spec(spec)
        spec.loader.exec_module(module)
        mode=module.CAMERA_AND_VIEWPORT["mode"]
        screen=module.CAMERA_AND_VIEWPORT["screen_relative"]
        self.assertEqual(mode["split_screen_active_raw"],("u8",0x0DDB))
        self.assertEqual(mode["player1_offscreen_raw"],("u8",0x121B))
        self.assertEqual(mode["player2_offscreen_raw"],("u8",0x121D))
        self.assertEqual(screen["screen1_player1_visibility_raw"],("u8",0x1599))
        self.assertEqual(module.SLOTS["slot1"]["air_effective"],("u8",0x0545))
        self.assertEqual(module.SLOTS["slot2"]["air"],("u8",0x0547))
        text=CAMERA.read_text()
        self.assertIn("$0DDB != 0",text)
        self.assertIn("$1599",text)
        report=REPORT.read_text()
        self.assertIn("scanlines 0 and 112",report)
        self.assertIn("not",report.lower())


if __name__=="__main__":
    unittest.main()
