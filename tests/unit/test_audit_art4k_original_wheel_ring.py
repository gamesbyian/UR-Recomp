"""Original 64x64 ROM source wheel-ring pixels, no ROM or Pillow dependency."""
import unittest
from tools.art.audit_art4k_original_wheel_ring import ring_candidates,OFFSETS,MIN_GREY_RING_HITS


def colored_rgba(cx=None,cy=28,radius=7,red=False):
    arr=bytearray(64*64*4)
    if cx is not None:
        for dx,dy in OFFSETS[radius]:
            index=(cy+dy)*64+cx+dx
            arr[4*index:4*index+4]=bytes((65,65,65,255))
    if red:
        arr[4*(15*64+28):4*(15*64+28)+4]=bytes((210,15,17,255))
    return bytes(arr)


class OriginalRingTests(unittest.TestCase):
    def test_exact_synthetic_neutral_ring_yields_source_raster_anchor(self):
        r=ring_candidates(colored_rgba(cx=29))
        self.assertEqual(r["max_neutral_ring_hits"],48)
        self.assertIn([29,28,7],r["best_candidate_centres_xy_radius_logical_px"])
        self.assertTrue(r["not_an_original_3d_axle"])
        self.assertGreaterEqual(r["max_neutral_ring_hits"],MIN_GREY_RING_HITS)

    def test_source_circle_sampling_has_explicit_half_pixel_rounding(self):
        self.assertEqual(OFFSETS[7][4],(6,4))
        self.assertEqual(OFFSETS[7][16],(-4,6))
        self.assertEqual(OFFSETS[7][20],(-6,4))
        self.assertEqual(OFFSETS[7][40],(4,-6))

    def test_non_grey_frame_pixel_does_not_move_source_ring(self):
        a=ring_candidates(colored_rgba(cx=29))
        b=ring_candidates(colored_rgba(cx=29,red=True))
        self.assertEqual(a,b)

    def test_ambiguous_or_missing_ring_does_not_invent_3d_axle(self):
        with self.assertRaisesRegex(ValueError,"insufficient"):
            ring_candidates(colored_rgba())
        with self.assertRaisesRegex(ValueError,"64x64"):
            ring_candidates(b"not an image")
        self.assertEqual(len(OFFSETS),5)

    def test_nonbinary_alpha_is_rejected(self):
        raw=bytearray(colored_rgba(cx=29))
        raw[3]=127
        with self.assertRaisesRegex(ValueError,"binary alpha"):
            ring_candidates(bytes(raw))


if __name__=="__main__":
    unittest.main()
