"""QA08 actual native 2P gold-medal guest VRAM versus render-VRAM source.

Four fixed live Win32 samples, 11 older PPU owners, 70 OAM slots and original
source 263 images belong to the same guest run; no archive/source mutation.
"""
import unittest
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import baldosa_qa08_native_medal_vram_pixels_patch as patcher
import baldosa_qa08_native_effective_pixel_owner_patch as previous
import qa08_windows_effective_pixel_owner as live


def records(override=0,idxword="0200",guest_word="0200"):
    text=[]
    for guest,name,tile,word in ((4032,"1e6","0f6","6f60"),
                                  (4176,"1e2","0f2","6f20")):
        for y,slot in ((96,99),(120,98)):
            text.append(
                "UR_QA08_WIN_MEDAL_VRAM "
                f"frame={guest} x=225 raster_y={y} ppu_line={y+1} "
                f"slot={slot} xoff=6 yoff=8 usedcol=6 usedrow=8 "
                f"name={name} obsel=63 obsel_bank=6000 tile={tile} "
                f"wordaddr={word} guest_w0={guest_word} guest_w8=0202 "
                f"render_w0={idxword} render_w8=0202 guest_idx=14 "
                f"render_idx=14 actual_obj=06de actual_cgram=de "
                f"overlay={override} vram_writes=101\n")
    return "".join(text)


class NativeMedalVRAMProbe(unittest.TestCase):
    def test_readonly_probe_is_idempotent_and_has_one_source_reader(self):
        from tests.unit.test_qa08_native_effective_pixel_owner_patch import ExactNativePixelOwnerSourceTest
        fixture=ExactNativePixelOwnerSourceTest()
        fixture.setUp()
        base=previous.patch_source(fixture.source)
        patched=patcher.patch_source(base)
        self.assertEqual(patched,patcher.patch_source(patched))
        for term in ("UR_QA08_WINDOWS_MEDAL_VRAM_TRACE",
                     "PPU_objTileAdr1(ppu)", "PPU_objTileAdr2(ppu)",
                     "PpuRenderVram(ppu)", "ppu->vram[wa]",
                     "UR_QA08_WIN_MEDAL_VRAM frame=",
                     "snes_frame_counter == 4032 || snes_frame_counter == 4176",
                     "y == 97 || y == 121"):
            self.assertIn(term,patched)
        self.assertEqual(patched.count(patcher.MARK),1)
        self.assertEqual(patched.count(previous.MARK),1)
        for bad in ("ppu->vram[wa] =", "ppu->oam[slot * 2u] =",
                    "ppu->objBuffer.data[x+kPpuExtraLeftRight] ="):
            self.assertNotIn(bad,patched)
        self.assertEqual(patched.count(previous.TRACE),1)
        with self.assertRaises(ValueError):
            patcher.patch_source("unknown unrelated PPU")

    def test_exact_four_lines_honor_scanline_and_render_VRAM_flags(self):
        result=live.inspect_medal_live_vram(records())
        self.assertEqual(result["observed_actual_Windows_pixel_count"],4)
        self.assertEqual([v["source_slot"] for v in result["source_registered_exact_four_pixel_records"]],
                         [99,98,99,98])
        self.assertTrue(all(v["native_render_vram_4bpp_index"]==14
                            for v in result["source_registered_exact_four_pixel_records"]))
        self.assertTrue(all(v["native_objBuffer_and_decoded_render_VRAM_agree"]
                            for v in result["source_registered_exact_four_pixel_records"]))

    def test_real_host_override_must_be_explicit_if_render_words_differ(self):
        with self.assertRaisesRegex(ValueError,"host override"):
            live.inspect_medal_live_vram(records().replace("render_w0=0200","render_w0=0204"))
        # Different guest/render plane bits outside this pixel may appear,
        # but only if the source actually reports a host-owned VRAM override.
        altered=records(override=1).replace("render_w0=0200","render_w0=0204")
        self.assertTrue(all(v["host_render_VRAM_override_live"] for v in
                     live.inspect_medal_live_vram(altered)["source_registered_exact_four_pixel_records"]))

    def test_missing_extra_duplicate_and_broken_VRAM_words_fail_closed(self):
        good=records()
        for text in (
            good.splitlines()[0]+"\n",
            good+good.splitlines()[0]+"\n",
            good.replace("frame=4176","frame=4177"),
            good.replace("actual_cgram=de","actual_cgram=df"),
            good.replace("render_idx=14","render_idx=15"),
            good.replace("wordaddr=6f60","wordaddr=6f61"),
            good+"UR_QA08_WIN_MEDAL_VRAM_REJECT frame=4176 slot=99\n",
        ):
            with self.subTest(text=text[:90]),self.assertRaises(ValueError):
                live.inspect_medal_live_vram(text)


if __name__=="__main__":
    unittest.main()
