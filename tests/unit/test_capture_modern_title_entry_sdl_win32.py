"""Synthetic rejection tests only; source/native SDL is run on real Windows."""
import tempfile
import unittest
from pathlib import Path
from tools.capture_modern_title_entry_sdl_win32 import (
    STAGES, read_p7, rgb_differences, verify_frames)


def case(w=320, h=224):
    base = bytearray(b"\x20\x30\x40\xff" * (w*h))
    def color(region, rgb):
        b = base.copy()
        if region == "logo":
            xs, ys = range(w//16, w*15//16), range(h//8, h//2)
        elif region == "prompt":
            xs, ys = range(w), range(h*4//5, h)
        else:
            xs, ys = range(w), range(h)
        for y in ys:
            for x in xs:
                i = (y*w+x)*4
                b[i:i+4] = bytes((*rgb, 255))
        return bytes(b)
    return {
        "entry": color("logo",(200, 50, 30)),
        "settled": bytes(base),
        "leaving": color("prompt",(220, 100, 40)),
        "root": color("all",(80,90,100)),
        "reduced-early": bytes(base), "reduced-late": bytes(base)
    }


class NativeSDLTitleMotionTest(unittest.TestCase):
    def test_canonical_rom_hash_is_complete(self):
        from tools.capture_modern_title_entry_sdl_win32 import USA
        self.assertEqual(len(USA), 64)
        self.assertEqual(USA, "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478")

    def test_source_clock_phases(self):
        self.assertEqual([x[1] for x in STAGES], [16,40,64,100,16,40])
        self.assertEqual(len(set(x[0] for x in STAGES)), 6)

    def test_visible_movement_and_reduced_motion(self):
        for size in ((320,224),(342,224)):
            proof = verify_frames(case(*size),size)
            self.assertGreater(proof["enter_logo"], 0)
            self.assertEqual(proof["leave_logo"], 0)
            self.assertEqual(proof["reduced_still"], 0)

    def test_missing_or_forged_motion_refused(self):
        w,h=320,224
        base=case(w,h)
        trials=[]
        bad=dict(base);del bad["leaving"];trials.append(bad)
        for k,v in (("entry",base["settled"]),
                    ("leaving",base["settled"]),
                    ("root",base["leaving"]),
                    ("reduced-late",base["entry"]),
                    ("root",b"\x00"*len(base["root"])),
                    ("entry",b"")):
            bad=dict(base);bad[k]=v;trials.append(bad)
        bad=dict(base);l=bytearray(base["leaving"])
        l[4*((h//4)*w+w//3)]^=0xFF
        bad["leaving"]=bytes(l);trials.append(bad)
        for i,bad in enumerate(trials):
            with self.subTest(i=i),self.assertRaises(ValueError):
                verify_frames(bad,(w,h))

    def test_bad_comparison_and_p7_refused(self):
        w,h=320,224
        a=case(w,h)["entry"]
        with self.assertRaises(ValueError): rgb_differences(a[:-1],a,w,h)
        with self.assertRaises(ValueError): rgb_differences(a,a,w,h,"not-region")
        head=(f"P7\nWIDTH {w}\nHEIGHT {h}\nDEPTH 4\nMAXVAL 255\n"
              "TUPLTYPE RGB_ALPHA\nENDHDR\n").encode("ascii")
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"r.pam"
            path.write_bytes(head+a)
            self.assertEqual(read_p7(path,(w,h)),a)
            for corrupt in (head+a[:-1],head+a+b"X",b"BAD"+a):
                path.write_bytes(corrupt)
                with self.assertRaises(ValueError):read_p7(path,(w,h))
            path.write_bytes(head+a)
            with self.assertRaises(ValueError):read_p7(path,(342,h))


if __name__ == "__main__":
    unittest.main()
