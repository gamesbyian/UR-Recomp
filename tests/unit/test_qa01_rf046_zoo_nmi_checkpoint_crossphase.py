"""RF046 source-NMI pre/post and independent full-WRAM checkpoint correlation."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_rf046_zoo_nmi_checkpoint_crossphase as rf046
from test_qa01_rf043_zoo_first_stack_window import FirstStack

class NMICrossPhase(unittest.TestCase):
    def fixture(self):
        producer = FirstStack().fixture()
        samplemap = {s["race_relative_frame"]: s for s in producer["zoo_race_mesh"]["samples"]}
        sequence = [
            (1017,"82D4F0","8197005526","26F0D48226"),
            (1018,"82D4EE","8197FF2726","26EED48226"),
            (1019,"82D4F0","8197FF5526","26F0D48226"),
            (1020,"82D4EE","8197FF2726","26EED48226"),
            (1021,"82D4F0","8197FF5526","26F0D48226"),
            (1022,"82D4EE","8197FF2726","26EED48226"),
            (1023,"82D4F0","8197FF5526","26F0D48226"),
            (1024,"82D4EE","8197FF2726","26EED48226"),
            (1025,"82D4EE","8197FF5526","26EED48226"),
        ]
        original_log = "\n".join(
            f"QA01RF044ORIGNMI f={f} f1={f} pc={pc} S0=01F0 S1=01EC old={old} new={new}"
            for f,pc,old,new in sequence
        ) + "\n"
        shapes = {
            1:"26F0D482", 2:"26EED482", 4:"26EED482",
            32:"26EED482", 219:"26EED482",
            604:"27F0D482",840:"27F0D482",841:"27F0D482",
            1080:"27F0D482",1531:"27F0D482",1532:"27EED482",
            1720:"27F0D482",1721:"27EED482",1800:"27F0D482",
            2160:"27F0D482",2520:"27F0D482",2880:"27EED482",
            3120:"27EED482",3600:"27EED482",4920:"27F0D482"
        }
        for rel,pattern in shapes.items():
            entries = samplemap[rel]["original_native_full_wram_byte_difference"][
                "first_24_differences"]
            for i,entry in enumerate(entries):
                entry["original_byte"] = int(pattern[i*2:i*2+2],16)
        for rel in rf046.EARLY:
            host = 1017 + rel
            _, _, pre, post = sequence[host-1-1017]
            entries=samplemap[rel]["original_native_full_wram_byte_difference"]["first_24_differences"]
            for i,entry in enumerate(entries):
                entry["original_byte"]=int(post[i*2:i*2+2],16)
                entry["native_byte"]=int(pre[i*2:i*2+2],16)
        return producer,{"disposition":"strict_candidate","release_credit":0},original_log

    def test_all_three_correspondences_without_claiming_native_NMI_phase(self):
        r=rf046.compare(*self.fixture())
        self.assertEqual([x["relative_frame"] for x in r["exact_early_checkpoint_NMI_matches"]],[1,2,4])
        self.assertTrue(all(x["native_checkpoint_equals_preceding_source_NMI_pre"]
                            and x["original_checkpoint_equals_preceding_source_NMI_post"]
                            for x in r["exact_early_checkpoint_NMI_matches"]))
        self.assertEqual(r["original_NMI_nine_frame_census_count"],9)
        self.assertEqual(r["source_original_twenty_four_byte_image_histogram"],
                         rf046.EXPECTED_ORIGINAL_NMI_SHAPE_COUNTS)
        self.assertFalse(r["later_frames_have_executed_source_NMI_proven"])
        self.assertFalse(r["native_actual_NMI_instruction_phase_from_correspondence_proven"])
        self.assertFalse(r["differing_stack_bytes_never_consumed_proven"])
        self.assertEqual(r["complete_USA_events_admitted"],0)

    def test_reject_changed_byte_or_wrong_host_offset(self):
        p,c,log=self.fixture()
        p["zoo_race_mesh"]["samples"][1]["original_native_full_wram_byte_difference"][
            "first_24_differences"][0]["native_byte"]=0
        with self.assertRaisesRegex(ValueError,"correspondence"):
            rf046.compare(p,c,log)
        p,c,log=self.fixture()
        p["zoo_race_mesh"]["samples"][1]["original_absolute_host_frame"]=1019
        with self.assertRaisesRegex(ValueError,"host clocks changed"):
            rf046.compare(p,c,log)

    def test_reject_missing_NMI_or_truncated_unmasked_controls(self):
        p,c,log=self.fixture()
        with self.assertRaisesRegex(ValueError,"incomplete"):
            rf046.compare(p,c,log.replace("QA01RF044ORIGNMI f=1023 f1=1023","wrong f=1023 f1=1023"))
        p,c,log=self.fixture()
        p["zoo_race_mesh"]["masked_or_excluded_wram_bytes"]=1
        with self.assertRaisesRegex(ValueError,"unmasked"):
            rf046.compare(p,c,log)
        p,c,log=self.fixture()
        with self.assertRaisesRegex(ValueError,"truncated"):
            rf046.compare(p,c,log+"QA01RF044ORIGNMI_TRUNCATED\n")

if __name__=="__main__":
    unittest.main()
