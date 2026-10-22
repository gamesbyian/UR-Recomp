"""Source-only image checks must never self-award monitor/art acceptance."""
import unittest
from tools import qa_modern_visual_native_contrast as c


def p7(width, height, pixels):
    h = (f"P7\nWIDTH {width}\nHEIGHT {height}\nDEPTH 4\nMAXVAL 255\n"
         "TUPLTYPE RGB_ALPHA\nENDHDR\n").encode()
    return h + bytes(channel for p in pixels for channel in p)


class SourceContrastTests(unittest.TestCase):
    def test_known_real_source_palette_reference_gap(self):
        self.assertAlmostEqual(c.contrast_ratio((152,)*3, (80,)*3), 2.7952, places=3)
        self.assertAlmostEqual(c.contrast_ratio((200,)*3, (80,)*3), 4.8194, places=3)

    def test_raw_p7_checker_pixel_adjacency_and_zero_approval(self):
        rgb = [(47,47,47,224),(80,80,80,224),(152,152,152,255),
               (80,80,80,224),(47,47,47,224),(80,80,80,224)]
        result=c.audit_frame(p7(3,2,rgb),(0,0,3,2),(152,)*3,((47,)*3,(80,)*3))
        self.assertEqual(result['foreground_pixels'],1)
        self.assertEqual([x['pixels'] for x in result['backgrounds']],[2,3])
        self.assertEqual([x['text_pixels_within_two_pixels'] for x in result['backgrounds']],[1,1])
        self.assertFalse(result['passes_source_rgb_reference'])
        self.assertEqual(result['alpha_values_observed'],[224,255])
        self.assertFalse(result['physical_monitor_approved'])
        self.assertFalse(result['human_visual_approved'])
        self.assertEqual(result['release_gate_credit'],0)

    def test_rejects_missing_palette_and_forged_geometry(self):
        image=p7(2,1,[(152,152,152,255),(80,80,80,224)])
        with self.assertRaisesRegex(ValueError,'text and all backgrounds'):
            c.audit_frame(image,(0,0,2,1),(152,)*3,((47,)*3,(80,)*3))
        with self.assertRaisesRegex(ValueError,'ROI'):
            c.audit_frame(image,(0,0,3,1),(152,)*3,((80,)*3,))
        with self.assertRaisesRegex(ValueError,'truncated'):
            c.unpack_p7(image[:-1])
        with self.assertRaisesRegex(ValueError,'original RGB_ALPHA'):
            c.unpack_p7(image.replace(b'RGB_ALPHA',b'RGB',1))

    def test_rejects_bad_parameters(self):
        image=p7(3,1,[(152,152,152,255),(80,80,80,224),(47,47,47,224)])
        for backgrounds in [(),((80,)*3,(80,)*3),((152,)*3,)]:
            with self.subTest(backgrounds=backgrounds), self.assertRaises(ValueError):
                c.audit_frame(image,(0,0,3,1),(152,)*3,backgrounds)
        with self.assertRaisesRegex(ValueError,'reference'):
            c.audit_frame(image,(0,0,3,1),(152,)*3,((80,)*3,),0)


    def test_h27_minimum_neutral_foreground_for_observed_checker(self):
        # H27 archived P7 sampling: 152 on 80 is 2.795:1, and neutral
        # RGB194 is the first candidate meeting 4.5:1 over RGB80.
        self.assertAlmostEqual(c.contrast_ratio((152,)*3, (80,)*3), 2.7951867, places=5)
        self.assertEqual(c.minimum_neutral_foreground(80), 194)
        self.assertLess(c.contrast_ratio((193,)*3, (80,)*3), 4.5)
        self.assertGreaterEqual(c.contrast_ratio((194,)*3, (80,)*3), 4.5)
        self.assertGreaterEqual(c.contrast_ratio((194,)*3, (47,)*3), 4.5)
        self.assertIsNone(c.minimum_neutral_foreground(255))
        self.assertIsNone(c.minimum_neutral_foreground(128))

    def test_contrast_helper_rejects_non_rgb8_and_bad_reference(self):
        for background in (-1, 256, True, 80.0, '80'):
            with self.subTest(background=background), self.assertRaises(ValueError):
                c.minimum_neutral_foreground(background)
        for reference in (0, True, 22, float('nan'), float('inf'), '4.5'):
            with self.subTest(reference=reference), self.assertRaises(ValueError):
                c.minimum_neutral_foreground(80, reference)
        for rgb in ((True,80,80), (80.0,80,80), (80,80,False)):
            with self.subTest(rgb=rgb), self.assertRaises(ValueError):
                c.relative_luminance(rgb)

    def test_neutral_foreground_option_does_not_award_art_approval(self):
        image = p7(3,1,[(152,152,152,255),(80,80,80,224),(47,47,47,224)])
        result = c.audit_frame(image,(0,0,3,1),(152,)*3,((80,)*3,(47,)*3))
        self.assertEqual(c.minimum_neutral_foreground(80), 194)
        self.assertFalse(result['passes_source_rgb_reference'])
        self.assertFalse(result['human_visual_approved'])
        self.assertFalse(result['physical_monitor_approved'])
        self.assertEqual(result['release_gate_credit'],0)


if __name__=='__main__':
    unittest.main()
