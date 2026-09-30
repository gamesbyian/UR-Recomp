import unittest

from tools.compare_framebuffers import compare_frames


class FramebufferCompareTests(unittest.TestCase):
    def test_identical_frames(self):
        a = bytes.fromhex("00 00 00 00 01 00 00 00 02 00 00 00 03 00 00 00")
        row = compare_frames(a, a, width=2, bytes_per_pixel=4)
        self.assertEqual(row["changed_pixels"], 0)
        self.assertIsNone(row["bbox"])

    def test_reports_changed_bbox(self):
        a = bytes(24)
        b = bytearray(a)
        b[4:8] = bytes.fromhex("01 00 00 00")
        b[16:20] = bytes.fromhex("02 00 00 00")
        row = compare_frames(a, bytes(b), width=3, bytes_per_pixel=4)
        self.assertEqual(row["changed_pixels"], 2)
        self.assertEqual(row["bbox"], [1, 0, 1, 1])


if __name__ == "__main__":
    unittest.main()
