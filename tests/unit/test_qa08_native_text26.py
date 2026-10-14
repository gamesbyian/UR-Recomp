"""Fail-closed synthetic tests; no unit fixture is a native PPU pass."""
from pathlib import Path
import tempfile
import unittest

from tools import qa08_patch_ppu_pixel_compose_probe as two
from tools import qa08_patch_ppu_text26_source as patch
from tools import check_qa08_native_text26 as check


COORDS = [
    (133,47), (132,48), (133,48), (135,48), (136,48),
    (132,49), (133,49), (135,49), (132,50), (133,50),
    (132,51), (133,51), (132,52),
]

def fake_points():
    def record(slot, dy):
        return {
            "native_guest_frame": 2208,
            "authentic_native_arm_marker_one": True,
            "all_four_guest_crc_streams_equal_at_exact_frame_count": 2473,
            "bounded_original_red_text_over_front_samples": [
                {"xy":[x, y+dy], "native_final_changed":True,
                 "source_rgb":[49,49,49], "stock_original_rgb":[156,49,49],
                 "native_original_after_front_removal_rgb":
                     [107,156,0] if dy else [231,0,0]}
                for x,y in COORDS
            ],
        }
    return {
        "guest_frame": 2208,
        "native_each_front_removed_in_independent_full_guest_process": True,
        "per_original_front_slot": {"98": record(98,0), "96":record(96,112)},
    }

def rgb_frame(kind):
    image=bytearray(342*224*4)
    for x, y in (*COORDS, *((x,y+112) for x,y in COORDS)):
        is_lower=y>=112
        removed = kind == ("removed96" if is_lower else "removed98")
        rgb=([107,156,0] if is_lower else [231,0,0]) if removed else [156,49,49]
        at=4*(342*y+x)
        image[at:at+4]=bytes([*rgb,255])
    return bytes(image)

def native_log(kind, *, mutate=None):
    rows=[]
    for x,y in (*COORDS, *((x,y+112) for x,y in COORDS)):
        low=y>=112
        gone=kind==("removed96" if low else "removed98")
        sub = "0500" if gone else ("A4C3" if low else "A6B3")
        sub15 = "0000" if gone else "18C6"
        final = ("6B9C00" if low else "E70000") if gone else "9C3131"
        text=(f"UR_QA08_NATIVE_PPU_TEXT26 frame=2208 x={x} y={y} "
              f"main=F21B sub={sub} main15=000D sub15={sub15} "
              f"final={final} cgadsub=04 cgwsel=02 "
              f"fixed15={'0260' if low else '000F'} "
              "math=1 rendered_sub=1 "
              f"sub_present={0 if gone else 1} clip_main=1")
        rows.append(text)
    if mutate is not None:
        rows[9]=rows[9].replace("main=F21B",mutate)
    return "\n".join(rows)+"\n"

class OriginalNativeText26Tests(unittest.TestCase):
    def test_pinned_read_only_extension_never_replaces_two_point_probe(self):
        anchor = ("static NOINLINE void PpuDrawWholeLine(Ppu *ppu, uint y) {\n"
                  + two.ANCHOR + "}\n")
        first=two.patch_source(anchor)
        second=patch.patch_source(first)
        self.assertEqual(second.count("UR_QA08_NATIVE_PPU_TEXT26 frame="),1)
        self.assertEqual(second.count("UR_QA08_NATIVE_PPU_PIXEL frame="),1)
        self.assertEqual(second.count(two.ANCHOR),1)
        self.assertIn("{2,27,11,3,3,1}",second)
        self.assertIn("UR_QA08_PPU_TEXT26_FRAME",second)
        with self.assertRaisesRegex(ValueError,"already present"):
            patch.patch_source(second)
        with self.assertRaisesRegex(ValueError,"two-pixel"):
            patch.patch_source(anchor)

    def test_authentic_geometry_paired_and_exact_26(self):
        d=check.expected_points(fake_points())
        self.assertEqual(len(d),26)
        self.assertEqual(sum(y>=112 for x,y in d),13)
        self.assertEqual(d[(133,50)]["source_front"],98)
        self.assertEqual(d[(133,162)]["source_front"],96)
        bad=fake_points()
        bad["per_original_front_slot"]["96"]["bounded_original_red_text_over_front_samples"][0]["source_rgb"]=[0,0,0]
        with self.assertRaisesRegex(ValueError,"pairing differs"):
            check.expected_points(bad)

    def test_exact_78_synthetic_compositor_records(self):
        points=check.expected_points(fake_points())
        with tempfile.TemporaryDirectory() as directory:
            for kind in ("stock","removed98","removed96"):
                log=Path(directory)/f"{kind}.log"
                log.write_text(native_log(kind))
                result=check.read_records(log, rgb_frame(kind), points, kind)
                self.assertEqual(set(result),set(points))
                self.assertEqual(sum(not x["subscreen_present"] for x in result.values()),
                                 0 if kind=="stock" else 13)
            log=Path(directory)/"corrupted.log"
            log.write_text(native_log("stock",mutate="main=F41B"))
            with self.assertRaisesRegex(ValueError,"BG3"):
                check.read_records(log,rgb_frame("stock"),points,"stock")
            log.write_text(native_log("stock").splitlines()[0]+"\n")
            with self.assertRaisesRegex(ValueError,"not all 26"):
                check.read_records(log,rgb_frame("stock"),points,"stock")

    def test_non_5bit_source_and_screen_RGB_rejected(self):
        with self.assertRaisesRegex(ValueError,"5-bit"):
            check.rgb5_from_rgb8([1,2,3])
        self.assertEqual(check.rgb5_from_rgb15(0x18C6),[6,6,6])
        with self.assertRaisesRegex(ValueError,"source RGB"):
            check.rgb5_from_rgb8([49,49])


if __name__=="__main__":
    unittest.main()
