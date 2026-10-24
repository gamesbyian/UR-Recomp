"""ROM-free negative controls for the final SDL racer identity P7 auditor."""
import unittest

from tools import qa_modern_identity_strip_p7 as audit


class FakeFrame:
    def __init__(self, logical_width, foreign=None, foreground=True, clipped=False):
        self.width, self.height = (1280, 720) if logical_width == 342 else (1024, 768)
        self.logical_width = logical_width
        self.foreign = foreign
        self.foreground = foreground
        self.clipped = clipped
        self.mapping = audit.visual.mapping(logical_width, 224, self.width, self.height)

    def rgb(self, x, y):
        m = self.mapping
        lx = int(m.logical_x(x))
        ly = int(m.logical_y(y))
        panel = 320 if self.logical_width == 342 else 240
        root_x = (self.logical_width - panel) // 2
        if self.foreign and lx == root_x + 15 and ly == 42:
            return self.foreign
        if self.foreground and 46 <= ly < 54 and (
                root_x + (panel - 8 if self.clipped else 8) <= lx <
                root_x + (panel - 4 if self.clipped else 20)):
            return audit.FG
        return audit.BG


class IdentityStripP7Test(unittest.TestCase):
    def test_wide_and_compact(self):
        for width in (342, 256):
            with self.subTest(width=width):
                report = audit.audit_frame(FakeFrame(width), width)
                self.assertTrue(report["pass"], report)
                self.assertGreater(report["source_rgb_contrast"], 10)

    def test_old_checker_leak_fails(self):
        for width in (342, 256):
            report = audit.audit_frame(FakeFrame(width, foreign=(80, 80, 80)), width)
            self.assertFalse(report["pass"])
            self.assertFalse(report["checks"]["opaque_strip_no_checker_bleed"])

    def test_missing_glyphs_fail(self):
        report = audit.audit_frame(FakeFrame(342, foreground=False), 342)
        self.assertFalse(report["pass"])
        self.assertFalse(report["checks"]["visible_identity_glyphs"])

    def test_right_clipped_glyphs_fail(self):
        report = audit.audit_frame(FakeFrame(256, clipped=True), 256)
        self.assertFalse(report["pass"])
        self.assertFalse(report["checks"]["identity_not_clipped"])

    def test_invalid_width_refused(self):
        with self.assertRaises(ValueError):
            audit.audit_frame(FakeFrame(342), 320)


if __name__ == "__main__":
    unittest.main()
