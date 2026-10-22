"""Recovered Agent4 H25 opaque-RGBA audit against exact merged geometry helpers.

All RGBA buffers are deterministic, synthetic fixtures. This never attests
actual native SDL pixels, monitor output, art approval or release readiness.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from qa06_rgba_admission import audit_rgba
from qa06_span_certificate import certify
from qa06_raster_roi_reference import source_pixel_at_output_centre


class QA06OpaqueRGBAH25(unittest.TestCase):
    @staticmethod
    def fixture(mode='original', width=640, height=360):
        geometry = certify(mode, width, height)
        sw, sh = geometry['source']
        source = bytes((30, 70, 110, 255)) * (sw * sh)
        matte = bytes((0, 0, 0, 255))
        host = bytearray(matte * (width * height))
        x0, y0, rw, rh = geometry['roi_xywh']
        for y in range(y0, y0 + rh):
            sy = source_pixel_at_output_centre(sh, rh, y - y0)
            for x in range(x0, x0 + rw):
                sx = source_pixel_at_output_centre(sw, rw, x - x0)
                index = 4 * (y * width + x)
                offset = 4 * (sy * sw + sx)
                host[index:index + 4] = source[offset:offset + 4]
        return source, bytes(host), matte

    def test_full_opaque_composition_original_and_world342(self):
        for mode in ('original', 'world342'):
            with self.subTest(mode=mode):
                source, host, matte = self.fixture(mode)
                result = audit_rgba(mode, 640, 360, source, host,
                                    matte_rgba=matte)
                self.assertTrue(result['exact_rgba_match'])
                self.assertEqual(result['pixel_mismatches'], 0)
                self.assertEqual(result['pixels_examined'], 640 * 360)
                self.assertFalse(result['physical_gpu_accepted'])
                self.assertFalse(result['character_art_approved'])
                self.assertEqual(result['release_gate_credit'], 0)

    def test_transparent_source_and_nonopaque_matte_rejected(self):
        source, host, matte = self.fixture()
        source_changed = bytearray(source)
        source_changed[3] = 0
        with self.assertRaisesRegex(ValueError, 'transparent source'):
            audit_rgba('original', 640, 360, bytes(source_changed), host,
                       matte_rgba=matte)
        with self.assertRaisesRegex(ValueError, 'nonopaque matte'):
            audit_rgba('original', 640, 360, source, host,
                       matte_rgba=bytes((0, 0, 0, 0)))

    def test_bad_source_or_host_shape_fails_closed(self):
        source, host, matte = self.fixture()
        for new_source, new_host in ((source[:-4], host),
                                     (source, host[:-4]),
                                     (source, bytearray(host))):
            with self.subTest(src_len=len(new_source), host_len=len(new_host)), \
                    self.assertRaisesRegex(ValueError, 'incomplete RGBA'):
                audit_rgba('original', 640, 360, new_source, new_host,
                           matte_rgba=matte)

    def test_one_source_or_matte_pixel_corruption_detected(self):
        for mode in ('original', 'world342'):
            with self.subTest(mode=mode):
                source, host, matte = self.fixture(mode)
                for index in (0, len(host) // 2, len(host) - 4):
                    changed = bytearray(host)
                    changed[index] ^= 1
                    verdict = audit_rgba(mode, 640, 360, source,
                                         bytes(changed), matte_rgba=matte)
                    self.assertFalse(verdict['exact_rgba_match'])
                    self.assertGreater(verdict['pixel_mismatches'], 0)

    def test_host_alpha_corruption_detected(self):
        source, host, matte = self.fixture()
        changed = bytearray(host)
        changed[len(changed) // 2 + 3] = 0
        result = audit_rgba('original', 640, 360, source, bytes(changed),
                            matte_rgba=matte)
        self.assertFalse(result['exact_rgba_match'])
        self.assertEqual(result['pixel_mismatches'], 1)


if __name__ == '__main__':
    unittest.main()
