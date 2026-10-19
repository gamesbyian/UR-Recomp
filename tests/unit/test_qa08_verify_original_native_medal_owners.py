"""QA08 source identity and original/native winner crosswalk adversarial checks."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools import qa08_verify_original_native_medal_owners as q

class MedalWinnerSourceIdentity(unittest.TestCase):
    def test_pinned_actual_source_population(self):
        self.assertEqual(q.FRAMES,(4032,4176))
        self.assertEqual(len(q.POINTS),5)
        self.assertEqual(q.OWNERS[(207,91)],None)
        self.assertEqual([q.OWNERS[pt] for pt in q.POINTS[1:]],
                         [113,114,97,96])
        self.assertEqual(q.ORIGINAL_SHA,
            "8387c413d42cf8d2da2a61ba3ec67e8375394f938171dc4d73a3e4ba567920e4")
        self.assertEqual(q.NATIVE_SHA,
            "725ef03df3d43ff5d30b4bea944e32555974fb0b0e01af025da76ef88959b408")

    def test_observed_source_record_guard(self):
        d=q.decode("UR_QA08_WIN_OBJ_FETCH frame=4032 slot=97 used_tile=0de",
                   "UR_QA08_WIN_OBJ_FETCH")
        self.assertEqual(d["slot"],"97")
        self.assertEqual(q.inthex(d["used_tile"]) & 255,0xde)
        with self.assertRaisesRegex(ValueError,"duplicate source field"):
            q.decode("UR_QA08_WIN_OBJ_FETCH slot=97 slot=99",
                     "UR_QA08_WIN_OBJ_FETCH")
        with self.assertRaisesRegex(ValueError,"wrong source event"):
            q.decode("fake slot=97","UR_QA08_WIN_OBJ_FETCH")
        with self.assertRaisesRegex(ValueError,"malformed"):
            q.decode("UR_QA08_WIN_OBJ_FETCH slot=97 unexpected",
                     "UR_QA08_WIN_OBJ_FETCH")

    def test_forged_archive_rejected_without_reading_source(self):
        with tempfile.TemporaryDirectory() as temp:
            candidate=Path(temp)/"wrong.zip"
            candidate.write_bytes(b"fabricated source")
            with self.assertRaisesRegex(ValueError,"SHA mismatch"):
                q.member(candidate,q.NATIVE_SHA,q.NATIVE_LOG)

    def test_winner_crosswalk_does_not_approve_display_fidelity(self):
        code=(ROOT/"tools/qa08_verify_original_native_medal_owners.py").read_text()
        for token in (
            '"correct_original_to_native_video_frame_registration_proven":False',
            '"same_original_native_guest_consumed_input_and_beam_proven":False',
            '"original_native_color_math_or_CGRAM_parity_proven":False',
            '"release_or_QA08_gate_accepted":False',
            '"native_misaligned_2014_callback_pixels_corrected":0',
        ):
            self.assertIn(token,code)
        self.assertNotIn("PpuSetOverlayOamRange",code)
        self.assertNotIn("recolor",code.lower())

if __name__=="__main__":
    unittest.main()
