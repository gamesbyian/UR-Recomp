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
        self.assertEqual([v[1] for v in STAGES], [1200, 1584, 1616, 1696])
        self.assertEqual([v[2] for v in STAGES], ["original", "original", "modern", "root"])
        self.assertNotEqual(STAGES[0][1], 1000)  # Source-confirmed blank transition
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

    def test_original_guest_p6_must_be_real_and_exact(self):
        import tempfile
        from tools.capture_modern_title_attract_sdl_win32 import read_original_source_p6
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "original-presdl.ppm"
            payload = b"P6\n256 224\n255\n" + (b"\x00\x42\x00" * (256*224))
            path.write_bytes(payload)
            self.assertEqual(
                read_original_source_p6(path)["nonblack_rgb_pixels"], 256*224)
            for corrupt in (payload[:-1], payload+b"\x00",
                            b"P6\n257 224\n255\n"+payload.split(b"\n",3)[3]):
                path.write_bytes(corrupt)
                with self.assertRaises(ValueError):
                    read_original_source_p6(path)
            path.unlink()
            with self.assertRaises(ValueError):
                read_original_source_p6(path)

    def test_source_only_ci_and_archive_allowlist(self):
        root=Path(__file__).resolve().parents[2]
        source=(root/".github/workflows/modern-visual-native-win32-capture.yml").read_text()
        self.assertIn("qa_modern_visual_sdl_capture.py --framework baldosa/snesrecomp",source)
        self.assertIn("Prove actual original stock attract/demo and safe Modern wake SDL",source)
        self.assertIn("Diagnose original guest full title P6 versus final SDL at frame1000", source)
        self.assertIn("modern-title-original-attract-final-sdl-pr2043",source)
        allow=source.split("name: modern-title-original-attract-final-sdl-pr2043",1)[1].split("if-no-files-found:",1)[0]
        self.assertIn("*/native-sdl.pam",allow)
        self.assertIn("*/native-sdl.png",allow)
        self.assertIn("*/native-process.log",allow)
        for forbidden in ("throwaway-test-user","save.srm",".sfc",".exe"):
            self.assertNotIn(forbidden,allow)


if __name__=="__main__":
    unittest.main()
