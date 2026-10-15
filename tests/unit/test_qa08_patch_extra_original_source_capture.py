"""Adversarial pinned native 2P original-source observer-only extension."""
import unittest
from pathlib import Path

from tools.qa08_patch_extra_original_source_capture import (
    patch_source, ANCHOR_ENV, ANCHOR_IF, MARK,
)

ROOT = Path(__file__).resolve().parents[2]


class MovingSourceCapturePatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = (ROOT / "tools/baldosa_native_racer_presentation.cpp").read_text()

    def test_real_native_host_patch_is_additive_and_nonshipping(self):
        after = patch_source(self.src)
        self.assertEqual(after.count(MARK), 1)
        self.assertIn('g_frame == 2192 && matches(qa08_a, g_frame)', after)
        self.assertIn('g_frame == 2224 && matches(qa08_b, g_frame)', after)
        self.assertIn("if (!field || width != 256 || height != 224", after)
        self.assertEqual(after.count("save_presented_pam("), self.src.count("save_presented_pam("))
        self.assertEqual(after.count("ur_baldosa_hd_draw_frame("), self.src.count("ur_baldosa_hd_draw_frame("))
        self.assertEqual(after.count("g_original_source_saved_frame = g_frame"), 1)
        self.assertEqual(after.replace(
            ANCHOR_ENV + after.split(ANCHOR_ENV, 1)[1].split(
                '    const auto matches =',1)[0], ANCHOR_ENV, 1
        ).replace(
            "    if (!matches(primary, g_frame) &&\n"
            "        !matches(extra, g_frame) &&\n"
            "        !matches(live, g_frame) &&\n"
            "        !(g_frame == 2192 && matches(qa08_a, g_frame)) &&\n"
            "        !(g_frame == 2224 && matches(qa08_b, g_frame)))\n"
            "        return;\n", ANCHOR_IF, 1), self.src)

    def test_unpinned_or_double_patch_fails(self):
        once = patch_source(self.src)
        for candidate in (
            once,
            self.src.replace(ANCHOR_ENV, ""),
            self.src.replace(ANCHOR_IF, "return;"),
            self.src.replace("width != 256", "width != 512"),
        ):
            with self.subTest(before=candidate[:60]):
                with self.assertRaises(ValueError):
                    patch_source(candidate)


if __name__ == "__main__":
    unittest.main()
