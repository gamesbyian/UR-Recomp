"""ROM-free tests for registered 2014/native medal review writer."""
import hashlib
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools import qa08_medal_capture_scrubber as scrub


def field_pair(x=207, y=91, red=130, green=45, blue=22):
    original = bytearray(256 * 224 * 4)
    native = bytearray(256 * 224 * 4)
    p = (y * 256 + x) * 4
    original[p:p+4] = bytes((blue, green, red, 0))
    native[p:p+4] = bytes((red, green, blue, 0))
    return original, bytearray(scrub.P7_HEADER + native)


class MedalRegisteredScrubber(unittest.TestCase):
    def test_immutable_source_registration_and_crop(self):
        self.assertEqual(scrub.GUEST_FRAMES,tuple(range(4032,5185,48)))
        self.assertEqual(len(scrub.GUEST_FRAMES),25)
        self.assertEqual(scrub.ORIGINAL_SHA,
            "72b7b152d08d8abb3636053bfd132db64926a5bf188f4dbba7e30b20d9583e9e")
        self.assertEqual(scrub.INTEGRATED_SHA,
            "832c08263e2d3013d5b15df82b2b0574fabfd3114194b7cbef9f6bb1b2959727")
        self.assertEqual(scrub.CROP,(184,78,246,169))
        self.assertIn("Original callback is always guest-1",scrub.__doc__)
        self.assertIn("original",scrub.HTML.lower())
        self.assertNotIn("https://",scrub.HTML)  # fully offline

    def test_real_rgb5_threshold_distinguishes_large_and_small(self):
        a, b = field_pair()
        orig, native, heat, large, difference = scrub.read_crop(bytes(a), bytes(b))
        self.assertEqual((large,difference),(0,0))
        self.assertEqual(orig,native)
        self.assertEqual(len(heat),(246-184)*(169-78)*3)
        p=(91*256+207)*4
        # In green, +7 RGB8 changes no 5-bit channel; +8 changes exactly one,
        # which is still outside the >1 RGB5 heatmap.
        b[len(scrub.P7_HEADER)+p+1] = 54
        _,_,_,large,difference = scrub.read_crop(bytes(a),bytes(b))
        self.assertEqual((large,difference),(0,1))
        b[len(scrub.P7_HEADER)+p+1] = 69
        _,_,heat,large,difference = scrub.read_crop(bytes(a),bytes(b))
        self.assertEqual((large,difference),(1,1))
        offset=((91-78)*(246-184)+(207-184))*3
        self.assertEqual(heat[offset:offset+3],bytes((255,56,60)))

    def test_context_and_actual_medal_region_counts_remain_distinct(self):
        self.assertEqual(scrub.MEDAL_BOX,(202,91,228,154))
        width=(scrub.CROP[2]-scrub.CROP[0])
        height=(scrub.CROP[3]-scrub.CROP[1])
        heat=bytearray(bytes((25,29,34)) * (width*height))
        def mark(x,y):
            start=((y-scrub.CROP[1])*width+x-scrub.CROP[0])*3
            heat[start:start+3]=bytes((255,56,60))
        mark(207,91)  # in true medal region
        mark(184,78)  # outside medal region but in wider scene
        self.assertEqual(scrub.count_large_errors_in_box(bytes(heat)),1)
        with self.assertRaisesRegex(ValueError,"within true source crop"):
            scrub.count_large_errors_in_box(bytes(heat),(0,0,1,1))

    def test_decode_rejects_cropped_and_forged_channel(self):
        a,b=field_pair()
        with self.assertRaisesRegex(ValueError,"shape"):
            scrub.read_crop(bytes(a[:-1]),bytes(b))
        with self.assertRaisesRegex(ValueError,"shape"):
            scrub.read_crop(bytes(a),bytes(b[:-1]))
        b[0]=0
        with self.assertRaisesRegex(ValueError,"channel"):
            scrub.read_crop(bytes(a),bytes(b))
        a,b=field_pair()
        b[len(scrub.P7_HEADER)+(91*256+207)*4+3]=255
        with self.assertRaisesRegex(ValueError,"fourth-channel"):
            scrub.read_crop(bytes(a),bytes(b))
        a,b=field_pair()
        with self.assertRaisesRegex(ValueError,"outside"):
            scrub.read_crop(bytes(a),bytes(b),(-1,78,246,169))

    def test_stdlib_png_byte_identity_without_image_deps(self):
        rgb=bytes([255,0,255, 0,255,0, 10,20,30, 40,50,60])
        png=scrub.rgb_png(2,2,rgb)
        self.assertTrue(png.startswith(b"\x89PNG\r\n\x1a\n"))
        position=8; parts={}
        while position<len(png):
            count=struct.unpack(">I",png[position:position+4])[0]
            kind=png[position+4:position+8]
            payload=png[position+8:position+8+count]
            expected=struct.unpack(">I",png[position+8+count:position+12+count])[0]
            self.assertEqual(zlib.crc32(kind+payload)&0xFFFFFFFF,expected)
            parts[kind]=payload
            position+=12+count
        self.assertEqual(struct.unpack(">II",parts[b"IHDR"][:8]),(2,2))
        self.assertEqual(zlib.decompress(parts[b"IDAT"]),
                         b"\x00"+rgb[:6]+b"\x00"+rgb[6:])
        with self.assertRaisesRegex(ValueError,"crop"):
            scrub.rgb_png(2,2,b"short")

    def test_no_false_source_if_archives_or_output_change(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/"fake-original.zip"
            p.write_bytes(b"not an original archive")
            with self.assertRaisesRegex(ValueError,"identities"):
                scrub.build(p,p)
        src=(ROOT/"tools/qa08_medal_capture_scrubber.py").read_text()
        for invariant in (
            "guest - 1",
            'native_info["original_callback"] != original_frame',
            'sha(source) != original_info["original_unchanged_BGRX_sha256"]',
            'sha(native) != native_info["experimental_P7_sha256"]',
            "source_shift=0 release_accepted=0",
            "refusing to overwrite another local review file",
        ):
            self.assertIn(invariant,src)
        self.assertNotIn("PpuSetOverlayOamRange",src)


if __name__=="__main__":
    unittest.main()
