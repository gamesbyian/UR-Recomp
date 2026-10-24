"""ROM-free controls for the original-attract cross-aspect SDL audit.

A synthetic 256x224 source is rendered into the 4:3 and 16:9 host geometries
with the audit's nearest-neighbour mapping, so the whole recover/compare path
is exercised without any retail pixels. A genuine Actions artifact may be
replayed by setting UR_ATTRACT_CROSS_ASPECT_ARTIFACT; it is never in the repo.
This is presentation-geometry consistency, not guest parity, art approval or
release evidence.
"""
import hashlib
import os
import random
import sys
import tempfile
import unittest
from pathlib import Path

try:
    import PIL  # noqa: F401
except ImportError:
    PIL = None

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
if PIL is not None:
    import verify_original_attract_cross_aspect as audit


def synthetic_source():
    rng = random.Random(0x256224)
    return bytes(rng.randrange(256) for _ in range(256 * 224 * 3))


def render(mode, source):
    (width, height), (left, top, vw, vh) = audit.MODES[mode]
    raw = bytearray(width * height * 4)
    for i in range(3, len(raw), 4):
        raw[i] = 255
    for y in range(top, top + vh):
        sy = ((2 * (y - top) + 1) * 224) // (2 * vh)
        for x in range(left, left + vw):
            sx = ((2 * (x - left) + 1) * 256) // (2 * vw)
            j = (sy * 256 + sx) * 3
            k = (y * width + x) * 4
            raw[k:k + 3] = source[j:j + 3]
    return bytes(raw)


@unittest.skipUnless(PIL is not None, "optional Pillow graphics dependency")
class AttractCrossAspectTests(unittest.TestCase):
    def test_clean_render_recovers_source_and_has_no_mismatch(self):
        source = synthetic_source()
        for mode in audit.MODES:
            with self.subTest(mode=mode):
                raw = render(mode, source)
                self.assertEqual(audit.recover_source(raw, mode), source)
                self.assertEqual(audit.compare_pixels(raw, mode, source), (0, 0))

    def test_corrupt_viewport_pixel_is_counted(self):
        source = synthetic_source()
        raw = bytearray(render("wide", source))
        k = (200 * 1280 + 300) * 4
        raw[k] ^= 1
        self.assertEqual(audit.compare_pixels(bytes(raw), "wide", source), (1, 0))

    def test_nonblack_matte_pixel_is_counted(self):
        source = synthetic_source()
        raw = bytearray(render("wide", source))
        raw[(200 * 1280 + 10) * 4] = 1  # inside the left pillarbox
        self.assertEqual(audit.compare_pixels(bytes(raw), "wide", source), (0, 1))

    def test_one_source_pixel_shift_changes_recovered_source(self):
        # Equal population of non-black pixels must not hide a moved pixel.
        source = bytearray(synthetic_source())
        a = bytearray(source)
        b = bytearray(source)
        a[0:3], a[3:6] = b"\xff\x00\x00", b"\x00\x00\x00"
        b[0:3], b[3:6] = b"\x00\x00\x00", b"\xff\x00\x00"
        self.assertNotEqual(audit.recover_source(render("4by3", bytes(a)), "4by3"),
                            audit.recover_source(render("4by3", bytes(b)), "4by3"))

    def test_unknown_mode_and_bad_p7_are_refused(self):
        with self.assertRaises(KeyError):
            audit.compare_pixels(b"", "wrong", b"")
        with self.assertRaisesRegex(ValueError, "bad P7"):
            audit.decode_pam(b"P7\nnot a header", (1280, 720))
        header = (b"P7\nWIDTH 2\nHEIGHT 1\nDEPTH 4\nMAXVAL 255\n"
                  b"TUPLTYPE RGB_ALPHA\nENDHDR\n")
        self.assertEqual(audit.decode_pam(header + bytes(8), (2, 1)), bytes(8))
        with self.assertRaisesRegex(ValueError, "bad P7"):
            audit.decode_pam(header + bytes(7), (2, 1))

    def test_wrong_archive_is_refused_before_any_member_is_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "artifact.zip"
            path.write_bytes(b"not the pinned artifact")
            self.assertNotEqual(hashlib.sha256(path.read_bytes()).hexdigest(),
                                audit.EXPECTED_SHA)
            with self.assertRaisesRegex(ValueError, "ZIP hash mismatch"):
                audit.audit(path)

    def test_original_artifact_if_supplied(self):
        artifact = os.environ.get("UR_ATTRACT_CROSS_ASPECT_ARTIFACT")
        if not artifact:
            self.skipTest("original Actions artifact not supplied; no evidence inferred")
        result = audit.audit(artifact)
        self.assertEqual(result["eight_P7_PNG_pairs_verified"], 8)
        self.assertEqual(
            result["stage_results"]["original-demo"]["source_rgb_cross_geometry_different_pixels"], 0)


if __name__ == "__main__":
    unittest.main()
