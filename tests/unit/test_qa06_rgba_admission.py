"""Recovered H25 synthetic full-frame RGBA witness tests (QA06).

Source: Evidence Library archive 142bXAi_4D-928Wz7FntyRbVzTYvt_sJZ
(h26.zip -> agent5-h25.zip -> agent4-h25.zip -> h25/tests/test_agent4_h25.py,
class Presentation, ported). Synthetic buffers only: no GPU readback,
original/native parity, art approval or release-gate credit.
"""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from qa06_rgba_admission import audit_rgba
from qa06_span_certificate import certify
from qa06_raster_roi_reference import source_pixel_at_output_centre


class OpaqueRgbaAdmission(unittest.TestCase):
    def fixture(self):
        w, h = 640, 360
        geo = certify('original', w, h)
        sw, sh = geo['source']
        source = bytes((30, 70, 110, 255)) * (sw * sh)
        matte = bytes((0, 0, 0, 255))
        host = bytearray(matte * (w * h))
        x0, y0, rw, rh = geo['roi_xywh']
        for y in range(y0, y0 + rh):
            sy = source_pixel_at_output_centre(sh, rh, y - y0)
            for x in range(x0, x0 + rw):
                sx = source_pixel_at_output_centre(sw, rw, x - x0)
                idx = 4 * (y * w + x)
                host[idx:idx + 4] = source[4 * (sy * sw + sx):4 * (sy * sw + sx) + 4]
        return w, h, source, bytes(host), matte

    def test_opaque_composed_synthetic_frame_passes(self):
        w, h, source, host, matte = self.fixture()
        result = audit_rgba('original', w, h, source, host, matte_rgba=matte)
        self.assertTrue(result['exact_rgba_match'])
        self.assertEqual(result['pixel_mismatches'], 0)
        self.assertFalse(result['physical_gpu_accepted'])
        self.assertEqual(result['release_gate_credit'], 0)

    def test_transparent_source_and_host_refused(self):
        w, h, source, host, matte = self.fixture()
        transparent_source = bytearray(source)
        transparent_source[3] = 0
        with self.assertRaisesRegex(ValueError, 'transparent source'):
            audit_rgba('original', w, h, bytes(transparent_source), host, matte_rgba=matte)
        with self.assertRaises(ValueError):
            audit_rgba('original', w, h, bytes((0, 0, 0, 0)) * (256 * 224),
                       bytes((0, 0, 0, 0)) * (w * h), matte_rgba=bytes((0, 0, 0, 0)))

    def test_one_matte_pixel_and_one_source_pixel_fail(self):
        w, h, source, host, matte = self.fixture()
        for index in (0, len(host) // 2):
            damaged = bytearray(host)
            damaged[index] ^= 1
            result = audit_rgba('original', w, h, source, bytes(damaged), matte_rgba=matte)
            self.assertFalse(result['exact_rgba_match'])
            self.assertEqual(result['pixel_mismatches'], 1)

    def test_incomplete_buffers_refused(self):
        w, h, source, host, matte = self.fixture()
        with self.assertRaises(ValueError):
            audit_rgba('original', w, h, source[:-4], host, matte_rgba=matte)
        with self.assertRaises(ValueError):
            audit_rgba('original', w, h, source, host[:-4], matte_rgba=matte)


if __name__ == '__main__':
    unittest.main()
