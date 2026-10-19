"""ROM-free fail-closed 2014/Win32 source grayscale budget guards."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools import qa08_verify_112field_grey_pixel_budget as q

def fake_frame(pairs):
    original=bytearray(q.FRAME_PIXELS*4)
    native=bytearray(len(q.P7_HEADER)+q.FRAME_PIXELS*4)
    native[:len(q.P7_HEADER)]=q.P7_HEADER
    for i,((r,g,b),(nr,ng,nb)) in enumerate(pairs):
        j=i*4
        original[j:j+4]=bytes((b*8,g*8,r*8,0))
        native[len(q.P7_HEADER)+j:len(q.P7_HEADER)+j+4]=bytes((nr*8,ng*8,nb*8,0))
    return bytes(original),bytes(native)

class SourceGreyPhase(unittest.TestCase):
    def test_exact_source_phase_schedule_and_negative_release_authority(self):
        self.assertEqual(q.SPIKES,tuple(range(4064,5409,112)))
        self.assertEqual(len(q.SPIKES),13)
        self.assertEqual(q.SPIKES[-1],5408)
        self.assertEqual(q.CYCLE,((15,20),(16,15),(17,16),(20,17)))
        self.assertEqual(q.NATIVE_OUTER_SHA,
            "832c08263e2d3013d5b15df82b2b0574fabfd3114194b7cbef9f6bb1b2959727")
        source=(ROOT/"tools/qa08_verify_112field_grey_pixel_budget.py").read_text()
        for claim in ('"same_original_native_consumed_input_beam_proven":False',
                      '"CGRAM_ingestion_root_cause_proven":False',
                      '"global_palette_remap_or_video_frame_shift_authorized":False',
                      '"independent_graphics_or_release_acceptance":False'):
            self.assertIn(claim,source)
        self.assertNotIn("PpuSetOverlayOamRange",source)

    def test_genuine_rgb5_four_state_counter_and_exact_other_gray(self):
        original,native=fake_frame([
            ((15,15,15),(20,20,20)),
            ((16,16,16),(15,15,15)),
            ((17,17,17),(16,16,16)),
            ((20,20,20),(17,17,17)),
            ((6,6,6),(5,5,5)),
            ((14,7,9),(14,7,8)),
            ((2,3,4),(2,3,4))
        ])
        wrong,gray,cycle,counts=q.measure_frame(original,native)
        self.assertEqual((wrong,gray,cycle),(6,5,4))
        self.assertEqual({k:counts[k] for k in q.CYCLE},
            {(15,20):1,(16,15):1,(17,16):1,(20,17):1})
        self.assertEqual(counts[(6,5)],1)

    def test_change_only_one_rgb5_level_is_not_silent(self):
        orig,nat=fake_frame([((0,0,0),(0,0,1))])
        self.assertEqual(q.measure_frame(orig,nat)[:3],(1,0,0))
        orig,nat=fake_frame([((15,15,15),(15,15,15))])
        self.assertEqual(q.measure_frame(orig,nat)[:3],(0,0,0))

    def test_bad_original_native_shapes_and_channel_flags_are_rejected(self):
        orig,nat=fake_frame([])
        with self.assertRaisesRegex(ValueError,"shape"):
            q.measure_frame(orig[:-4],nat)
        with self.assertRaisesRegex(ValueError,"shape"):
            q.measure_frame(orig,nat[:-4])
        bad=bytearray(nat)
        bad[0]=0
        with self.assertRaisesRegex(ValueError,"P7 channel"):
            q.measure_frame(orig,bytes(bad))
        bad=bytearray(nat)
        bad[len(q.P7_HEADER)+3]=255
        with self.assertRaisesRegex(ValueError,"fourth channel"):
            q.measure_frame(orig,bytes(bad))
        bad=bytearray(orig)
        bad[3]=255
        with self.assertRaisesRegex(ValueError,"fourth channel"):
            q.measure_frame(bytes(bad),nat)

    def test_committed_numeric_receipt_is_consistent_and_releaseless(self):
        import json
        path=ROOT/"analysis/data/qa08-real-112field-13frame-grayscale-error-budget-20261019.json"
        report=json.loads(path.read_text(encoding="utf-8"))
        rows=report["frames_summary"]
        self.assertEqual([x["native_guest"] for x in rows],list(q.SPIKES))
        self.assertTrue(all(x["original_callback"]==x["native_guest"]-1
                            for x in rows))
        sums=report["totals"]
        self.assertEqual(sum(x["wrong_rgb5"] for x in rows),359013)
        self.assertEqual(sum(x["both_grayscale_wrong_rgb5"] for x in rows),342086)
        self.assertEqual(sum(x["four_cycle_wrong_rgb5"] for x in rows),318775)
        self.assertEqual(sum(sums["four_cycle_wrong_rgb5_pair_counts"].values()),318775)
        self.assertEqual(sums["fraction_of_all_263_wrong_pixels_from_four_cycle_ppm"],
                         318775*1000000//890205)
        self.assertTrue(all(x["four_cycle_wrong_rgb5"]>20000 for x in rows))
        self.assertTrue(all(report["negative_gates"].values()))

    def test_unmatched_archive_sha_refused_prior_to_any_pixel_claim(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"forged-original.zip"
            p.write_bytes(b"not the genuine original source")
            with self.assertRaisesRegex(ValueError,"2014 original"):
                q.verify(p,p)

if __name__=="__main__":
    unittest.main()
