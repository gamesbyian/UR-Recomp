"""ROM-free native SDL original-title/demo/wake evidence negative contracts.

Synthetic images NEVER represent actual Uniracers artwork or guest state.
"""
import unittest
from pathlib import Path

from tools.capture_modern_title_attract_sdl_win32 import (
    STAGES, verify_actual_attract_frames, USA)


def pixels(rgb, width=320, height=224):
    return bytes((*rgb, 255)) * (width * height)


class ActualOriginalTitleAttractSDLTest(unittest.TestCase):
    def test_source_order_and_rom_id_are_exact(self):
        self.assertEqual([v[0] for v in STAGES],
                         ["original-title", "original-demo", "woken-modern", "confirmed-root"])
        self.assertEqual([v[1] for v in STAGES], [1000, 1584, 1616, 1696])
        self.assertEqual([v[2] for v in STAGES], ["original", "original", "modern", "root"])
        self.assertEqual(len(USA), 64)

    def test_reject_static_or_blank_guest_or_root(self):
        good={name:pixels((20+i*37,30+i*31,40+i*17))
              for i,(name,_,_) in enumerate(STAGES)}
        changes=verify_actual_attract_frames(good,(320,224))
        self.assertEqual(len(changes),3)
        # A duplicate of a directly adjacent rendered stage must fail.
        # A nonadjacent but different frame is not necessarily a duplicate:
        # replacing stage 3 with stage 1 could still differ from both
        # neighbors, so it cannot be claimed a valid static rejection.
        names = [item[0] for item in STAGES]
        for index,name in enumerate(names):
            adjacent = names[index-1] if index else names[1]
            for candidate in (good[adjacent], b"\x00"*len(good[name]),
                              good[name][:-1]):
                bad=dict(good)
                bad[name]=candidate
                with self.subTest(name=name),self.assertRaises(ValueError):
                    verify_actual_attract_frames(bad,(320,224))
        bad=dict(good);bad.pop("original-demo")
        with self.assertRaises(ValueError):verify_actual_attract_frames(bad,(320,224))
        bad=dict(good);bad["woken-modern"]=good["original-demo"]
        with self.assertRaises(ValueError):verify_actual_attract_frames(bad,(320,224))

    def test_source_only_ci_and_archive_allowlist(self):
        root=Path(__file__).resolve().parents[2]
        source=(root/".github/workflows/modern-visual-native-win32-capture.yml").read_text()
        self.assertIn("qa_modern_visual_sdl_capture.py --framework baldosa/snesrecomp",source)
        self.assertIn("Prove actual original stock attract/demo and safe Modern wake SDL",source)
        self.assertIn("modern-title-original-attract-final-sdl-pr2043",source)
        allow=source.split("name: modern-title-original-attract-final-sdl-pr2043",1)[1].split("if-no-files-found:",1)[0]
        self.assertIn("*/native-sdl.pam",allow)
        self.assertIn("*/native-sdl.png",allow)
        self.assertIn("*/native-process.log",allow)
        for forbidden in ("throwaway-test-user","save.srm",".sfc",".exe"):
            self.assertNotIn(forbidden,allow)


if __name__=="__main__":
    unittest.main()
