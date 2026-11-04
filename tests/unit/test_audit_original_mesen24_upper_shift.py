"""Lightweight source-only 2D translation and preserved-receipt assertions."""
import hashlib
import json
from pathlib import Path
import unittest
from tools.art.audit_original_mesen24_upper_shift import (
    SOURCE_ZIP_SHA,SHIFTS,SCHEMA,translated,score,analyze,audit,
)

REPORT=(Path(__file__).resolve().parents[2]/
        "analysis/data/racer-original-mesen24-source-upper-shifts-20261103.json")
REPORT_SHA="b892a372cc8365e21848da3eb1fa0fa7d67c8fba94327f553064a70dc7ee15e7"


def sprite(positions:dict[tuple[int,int],int])->dict:
    plane=bytearray(4096)
    for (x,y),value in positions.items():
        plane[y*64+x]=value
    return {"plane":bytes(plane),
            "alpha_mask":bytes(1 if x else 0 for x in plane)}


class OriginalShiftTests(unittest.TestCase):
    def test_shift_is_zero_filled_and_no_wrap(self):
        src=bytearray(4096)
        src[0]=5
        src[63]=6
        src[63*64]=7
        self.assertEqual(translated(bytes(src),1,0)[1],5)
        self.assertEqual(translated(bytes(src),1,0)[0],0)
        self.assertEqual(translated(bytes(src),-1,0)[62],6)
        self.assertEqual(translated(bytes(src),-1,0)[63],0)
        self.assertEqual(translated(bytes(src),0,-1)[62*64],7)
        for dx,dy in ((3,0),(0,-3),(0,2.0)):
            with self.assertRaises(ValueError):
                translated(bytes(src),dx,dy)
        with self.assertRaises(ValueError):
            translated(b"",0,0)

    def test_exact_one_pixel_shift_recovery_and_colour_counts(self):
        before=sprite({(3,4):5,(4,4):6,(5,4):7})
        after=sprite({(2,4):5,(3,4):6,(4,4):7})
        base=score(before,after,4,4,0,0)
        moved=score(before,after,4,4,-1,0)
        self.assertEqual(base["upper_alpha_xor"],2)
        self.assertEqual(moved["upper_alpha_xor"],0)
        self.assertEqual(moved["upper_index_mismatch"],0)
        best=analyze(before,after,4,4)
        self.assertEqual((best["preferred_by_index_and_magnitude"]["dx"],
                          best["preferred_by_index_and_magnitude"]["dy"]),(-1,0))
        self.assertEqual(len(SHIFTS),25)

    def test_pinned_source_receipt_and_all_23_edges(self):
        raw=REPORT.read_bytes()
        self.assertNotIn(b"\r",raw)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),REPORT_SHA)
        r=json.loads(raw)
        self.assertEqual(r["schema"],SCHEMA)
        self.assertEqual(r["source_actual_original_mesen_zip_sha256"],SOURCE_ZIP_SHA)
        self.assertEqual(r["source_actual_original_ticks"],list(range(1601,1625)))
        self.assertTrue(r["source_shift_zero_fill_no_wrap"])
        self.assertFalse(r["source_original_1994_rig_camera_or_pose_recovered"])
        self.assertFalse(r["original_PPU_final_screen_pixel_ownership_proven_by_this_audit"])
        self.assertFalse(r["source_frames_prospective_blind_holdout"])
        for who,v in r["per_source_player"].items():
            edges=v["original_23_consecutive_source_edge_comparisons"]
            self.assertEqual([(x["from_tick"],x["to_tick"]) for x in edges],
                             [(x,x+1) for x in range(1601,1624)])
            self.assertEqual(v["baseline_unchanged_upper_edges"],22)
            self.assertEqual(v["upper_edges_improved_by_bounded_2d_shift"],1)
            actual=next(x for x in edges if x["baseline"]["upper_alpha_xor"])
            self.assertEqual([actual["from_tick"],actual["to_tick"]],
                             v["actual_upper_source_event"])
            expected={"blue":(27,15,-1,0,72,61),"red":(20,14,1,0,55,43)}[who]
            got=(actual["baseline"]["upper_alpha_xor"],
                 actual["lowest_upper_alpha_xor"],
                 actual["preferred_by_index_and_magnitude"]["dx"],
                 actual["preferred_by_index_and_magnitude"]["dy"],
                 actual["baseline"]["upper_index_mismatch"],
                 actual["preferred_by_index_and_magnitude"]["upper_index_mismatch"])
            self.assertEqual(got,expected)

    def test_tampered_or_missing_archive_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"authenticated"):
            audit(b"PK\x03\x04"+bytes(100))


if __name__=="__main__":
    unittest.main()
