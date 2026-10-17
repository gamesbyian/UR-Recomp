"""Adversarial archived full-source medal mask, never crop, recolour, or conflate timing."""
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import qa08_medal_mask_temporal_source as m


class MedalMaskTest(unittest.TestCase):
    def test_source_geometry_guest_frames_and_non_gray_sample(self):
        self.assertEqual(m.SOURCE_SIZE,(256,224))
        self.assertEqual(len(m.NON_GRAY),21)
        self.assertEqual(len(m.GRAY),4)
        self.assertEqual(m.NON_GRAY[0],4032)
        self.assertEqual(m.NON_GRAY[-1],5136)
        self.assertEqual(m.GRAY,(4176,4512,4848,5184))
    def test_full_unmasked_rgb5_and_disconnected_components(self):
        raw=bytearray(m.COORD_COUNT*4)
        for p,(b,g,r) in ((5,(8,9,10)),(15,(24,31,49))):
            raw[4*p:4*p+4]=bytes((b,g,r,255))
        output=m.bgrx_to_rgb5_expanded(raw)
        self.assertEqual(tuple(output[15:18]),(10,8,8))
        self.assertEqual(tuple(output[45:48]),(49,24,24))
        with self.assertRaises(ValueError):
            m.bgrx_to_rgb5_expanded(b"partial")
        with self.assertRaises(ValueError):
            m.differing_pixels(output,bytes(m.COORD_COUNT*3-1))
        pair={(91*256+202),(91*256+203),(120*256+225)}
        self.assertEqual([x["pixels"] for x in m.components_of_mask(pair)],[2,1])
    def test_incorrect_zip_rejected_without_extracting_untrusted_content(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as folder:
            fake=Path(folder)/"not-an-authentic-archive.zip"
            fake.write_bytes(b"not pinned 2014 original or Windows")
            with self.assertRaisesRegex(ValueError,"genuine native"):
                m.analyze(fake,fake)
if __name__=="__main__":
    unittest.main()
