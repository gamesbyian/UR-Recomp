"""Synthetic source-free nearest-block consistency and invalid receipt guards."""
import sys
import unittest
from pathlib import Path
from fractions import Fraction
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
from qa06_original_block_consistency import verify_blocks
from qa06_raster_roi_reference import (raster_roi,source_pixel_at_host_coordinate,
    validated_policy_source_pixel_at_host_coordinate, source_pixel_host_span)


class BlockConsistencyTest(unittest.TestCase):
    def test_consistent_original_matte_and_opaque_surface(self):
        pixel=bytes((19,27,35,255));w,h=640,448
        receipt=verify_blocks('original',w,h,pixel*(w*h),matte=pixel,
                              require_opaque=True)
        self.assertEqual(receipt['distinct_source_pixels'],256*224)
        self.assertEqual(receipt['release_gate_credit'],0)
        self.assertFalse(receipt['source_frame_verified'])
        self.assertFalse(receipt['art_approved'])

    def test_one_changed_pixel_within_a_source_block_rejected(self):
        w,h=640,448;pixel=bytes((19,27,35,255));src=bytearray(pixel*(w*h))
        roi=raster_roi(256,224,w,h)
        source_xy=source_pixel_at_host_coordinate(roi,99,90)
        self.assertEqual(source_xy,source_pixel_at_host_coordinate(roi,100,90))
        src[(90*w+100)*4]^=1
        with self.assertRaisesRegex(ValueError,'inconsistent nearest-neighbour'):
            verify_blocks('original',w,h,bytes(src),matte=pixel,
                          require_opaque=True)

    def test_whole_source_frame_shift_can_pass_block_consistency(self):
        # Recovered H26 source-free negative control: a uniformly incorrect
        # source-frame mapping remains internally nearest-neighbour correct.
        # This test prevents us from treating a consistency pass as parity.
        w, h = 512, 448
        roi = raster_roi(256, 224, w, h)
        normal, shifted = bytearray(w*h*4), bytearray(w*h*4)
        matte = bytes((0, 0, 0, 255))
        for y in range(h):
            for x in range(w):
                location = source_pixel_at_host_coordinate(roi, x, y)
                if location is None:
                    a = b = matte
                else:
                    sx, sy = location
                    a = bytes((sx % 256, sy % 256, (sx ^ sy) % 256, 255))
                    wrong_x = (sx + 1) % 256
                    b = bytes((wrong_x, sy % 256, (wrong_x ^ sy) % 256, 255))
                start = (y*w + x)*4
                normal[start:start+4] = a
                shifted[start:start+4] = b
        self.assertNotEqual(normal, shifted)
        correct = verify_blocks('original', w, h, bytes(normal),
                                matte=matte, require_opaque=True)
        incorrect = verify_blocks('original', w, h, bytes(shifted),
                                  matte=matte, require_opaque=True)
        self.assertEqual(correct['distinct_source_pixels'], 256*224)
        self.assertEqual(incorrect['distinct_source_pixels'], 256*224)
        self.assertEqual(correct['source_host_samples'],
                         incorrect['source_host_samples'])
        for receipt in (correct, incorrect):
            self.assertFalse(receipt['source_frame_verified'])
            self.assertFalse(receipt['art_approved'])
            self.assertEqual(receipt['release_gate_credit'], 0)

    def test_opaque_and_matte_must_match_explicit_policy(self):
        w,h=640,448
        with self.assertRaisesRegex(ValueError,'transparent'):
            verify_blocks('original',w,h,bytes(4)*(w*h),matte=bytes(4),
                          require_opaque=True)
        with self.assertRaisesRegex(ValueError,'matte'):
            verify_blocks('original',w,h,bytes((0,0,0,255))*(w*h),
                          matte=bytes((1,1,1,255)))

    def test_reference_receipt_refuses_forged_origin_and_source_mode(self):
        roi=raster_roi(256,224,1920,1080)
        x,y,w,h=roi['roi_xywh']
        self.assertIsNotNone(validated_policy_source_pixel_at_host_coordinate(
            roi,x,y,mode='original'))
        forgery=dict(roi)
        forgery['roi_xywh']=[x+1,y,w,h]
        with self.assertRaises(ValueError):
            validated_policy_source_pixel_at_host_coordinate(
                forgery,x,y,mode='original')
        with self.assertRaises(ValueError):
            validated_policy_source_pixel_at_host_coordinate(
                roi,x,y,mode='world342')

    def test_span_and_output_coordinate_validation(self):
        self.assertEqual(source_pixel_host_span(256,512,20),[40,42])
        with self.assertRaises(ValueError):
            source_pixel_host_span(256,512,256)
        with self.assertRaises(ValueError):
            verify_blocks('invented',3,3,bytes(36))

if __name__ == '__main__':
    unittest.main()
