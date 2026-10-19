"""QA08: phase attribution is evidence, not permission to re-time PPU frames."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools import qa08_verify_original_medal_next_internal_stage as q
from tools.qa08_verify_original_medal_callback_registration import rgb565_to_rgb8


class GenuineSourceOnlyMedalDiscriminator(unittest.TestCase):
    def test_source_identity_and_all_frames_are_immutable(self):
        self.assertEqual(q.ORIGINAL_NESTED,
            "72b7b152d08d8abb3636053bfd132db64926a5bf188f4dbba7e30b20d9583e9e")
        self.assertEqual(q.NATIVE_OUTER,
            "832c08263e2d3013d5b15df82b2b0574fabfd3114194b7cbef9f6bb1b2959727")
        self.assertEqual(q.FRAMES,(4032,4176))
        self.assertEqual(len(q.RECURRING_GUEST_FRAMES),25)
        self.assertEqual(q.RECURRING_GUEST_FRAMES[0],4032)
        self.assertEqual(q.RECURRING_GUEST_FRAMES[-1],5184)
        self.assertTrue(all((b-a)==48 for a,b in zip(q.RECURRING_GUEST_FRAMES,q.RECURRING_GUEST_FRAMES[1:])))
        self.assertEqual(len(q.POINTS),5)
        self.assertEqual(q.HEADER.count(b"WIDTH 256"),1)

    def test_source_green_six_bit_to_comparison_five_bit(self):
        # Snes9x painter uses RGB565, native final compare uses RGB5.
        self.assertEqual(q.rgb565_rgb5(0x8183),(16,6,3))
        self.assertEqual(q.rgb565_rgb5(0x738e),(14,14,14))
        self.assertEqual(q.rgb565_rgb5(0x83cd),(16,15,13))
        self.assertEqual(q.rgb5((130,45,22)),(16,5,2))
        self.assertEqual(q.rgb565_rgb5(0x8183),
                         q.rgb5(rgb565_to_rgb8(0x8183)))

    def test_real_registered_and_counterfactual_owners_separate(self):
        ref=(115,56,74)
        next_painter=(114,114,114)
        native=(114,114,114)
        observed=q.classify(ref,ref,next_painter,native)
        self.assertFalse(observed["correctly_registered_exact"])
        self.assertTrue(observed["counterfactual_next_internal_stage_equal"])
        self.assertEqual(observed["absolute_next_stage_difference"],[0,0,0])

    def test_weak_shade_match_cannot_be_called_exact(self):
        ref=(115,56,74)
        next_painter=rgb565_to_rgb8(0x8183)
        native=(130,45,22)
        result=q.classify(ref,ref,next_painter,native)
        self.assertFalse(result["correctly_registered_exact"])
        self.assertFalse(result["counterfactual_next_internal_stage_equal"])
        self.assertEqual(result["absolute_next_stage_difference"],[0,1,1])

    def test_forged_original_painter_callback_alignment_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"SAME original callback"):
            q.classify((115,56,74),(114,114,114),(130,123,107),(130,123,107))

    def test_cropped_or_forged_source_rejected(self):
        with self.assertRaisesRegex(ValueError,"cropped"):
            q.original_rgb(b"",207,91)
        with self.assertRaisesRegex(ValueError,"cropped"):
            q.native_rgb(b"",207,91)
        # The real native P7 source reserves channel 4 as zero; mutate only
        # the selected source pixel to validate the rejection guard.
        png=bytearray(q.HEADER + b"\x00"*(256*224*4))
        png[len(q.HEADER)+4*(91*256+207)+3]=255
        with self.assertRaisesRegex(ValueError,"alpha"):
            q.native_rgb(bytes(png),207,91)
        with self.assertRaisesRegex(ValueError,"original artifact SHA"):
            with patch.object(Path,"read_bytes",return_value=b"forged"):
                q.checked(Path("forged.zip"),q.ORIGINAL_OUTER)

    def test_diagnostic_cannot_claim_shipped_fidelity(self):
        source=(ROOT/"tools/qa08_verify_original_medal_next_internal_stage.py").read_text()
        for claim in ('"global_video_frame_shift_authorized":False',
                      '"shipping_original_result_parity_proven":False',
                      '"QA08_or_release_accepted":False',
                      '"native_guest_to_original_consumed_controller_identity_proven":False'):
            self.assertIn(claim,source)
        self.assertNotIn("PpuSetOverlayOamRange",source)


if __name__=="__main__":
    unittest.main()
