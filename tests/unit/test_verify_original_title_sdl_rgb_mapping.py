"""ROM-free independent original-title SDL mapping contract tests."""
from __future__ import annotations
import importlib.util
import unittest
from pathlib import Path

P = Path(__file__).resolve().parents[2] / 'tools' / 'verify_original_title_sdl_rgb_mapping.py'
spec = importlib.util.spec_from_file_location('source_mapping', P)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def synthetic(mode):
    w, h = m.SOURCE_SIZE
    pixels = bytearray(w * h * 3)
    for y in range(h):
        for x in range(w):
            i = (y*w+x)*3
            pixels[i:i+3] = bytes((x & 255, y & 255, (x ^ y) & 255))
    src = b'P6\n256 224\n255\n' + bytes(pixels)
    (host_w, host_h), (left, top, vw, vh) = m.CASES[mode]
    host = bytearray(host_w*host_h*4)
    for y in range(vh):
        sy = ((2*y+1)*h)//(2*vh)
        for x in range(vw):
            sx = ((2*x+1)*w)//(2*vw)
            j = (sy*w+sx)*3
            i = ((y+top)*host_w+(x+left))*4
            host[i:i+3] = pixels[j:j+3]
    header = (f'P7\nWIDTH {host_w}\nHEIGHT {host_h}\nDEPTH 4\nMAXVAL 255\n'
              'TUPLTYPE RGB_ALPHA\nENDHDR\n').encode()
    return src, header + bytes(host), len(header)


class MappingTest(unittest.TestCase):
    def test_wide_exact(self):
        self.assertEqual(m.compare(*synthetic('wide')[:2], 'wide')['viewport_rgb_mismatches'], 0)

    def test_compact_exact(self):
        self.assertEqual(m.compare(*synthetic('4by3')[:2], '4by3')['host_rgb_pixels_checked'], 1024*768)

    def test_corrupted_viewport_refused(self):
        src, host, offset = synthetic('wide')
        changed = bytearray(host)
        changed[offset + (100*1280+500)*4] ^= 1
        with self.assertRaisesRegex(ValueError, 'RGB mismatch'):
            m.compare(src, bytes(changed), 'wide')

    def test_corrupted_matte_refused(self):
        src, host, offset = synthetic('wide')
        changed = bytearray(host)
        changed[offset + (100*1280+10)*4] = 255
        with self.assertRaisesRegex(ValueError, 'matte=1'):
            m.compare(src, bytes(changed), 'wide')

    def test_corrupted_source_refused(self):
        src, host, _ = synthetic('4by3')
        changed = bytearray(src)
        changed[len(b'P6\n256 224\n255\n')+3] ^= 1
        with self.assertRaisesRegex(ValueError, 'RGB mismatch'):
            m.compare(bytes(changed), host, '4by3')

    def test_blank_source_refused(self):
        src, host, _ = synthetic('wide')
        changed = src[:len(b'P6\n256 224\n255\n')] + bytes(256*224*3)
        with self.assertRaisesRegex(ValueError, 'blank'):
            m.compare(changed, host, 'wide')

    def test_wrong_pam_header_refused(self):
        src, host, _ = synthetic('wide')
        with self.assertRaisesRegex(ValueError, 'P7'):
            m.compare(src, host.replace(b'DEPTH 4', b'DEPTH 3', 1), 'wide')

    def test_source_png_not_accepted_as_p6(self):
        _, host, _ = synthetic('wide')
        with self.assertRaisesRegex(ValueError, 'P6'):
            m.compare(b'PNG', host, 'wide')

if __name__ == '__main__':
    unittest.main()
