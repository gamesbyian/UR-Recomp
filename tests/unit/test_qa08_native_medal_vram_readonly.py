"""QA-08 native source: authentic overlapping 2P gold and adjacent 4bpp.

No unverified assumptions about actual guest/render VRAM; all eight slot
lines are checked against the already source-qualified exact Win32 OBJ color.
"""
import unittest
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import baldosa_qa08_native_medal_vram_pixels_patch as patcher
import baldosa_qa08_native_effective_pixel_owner_patch as prior
import qa08_windows_effective_pixel_owner as witness


def records(override=0):
    out=[]
    for frame,gold,tile,wa in ((4032,"1e6","0f6","7f60"),
                               (4176,"1e2","0f2","7f20")):
        for y,adj,under in ((96,97,99),(120,96,98)):
            for slot,name,source_tile,source_wa,w0,w8,val in (
                (adj,"1ce","0de","7de0","0201","0203",14),
                (under,gold,tile,wa,"3f1f","7f0f",15)):
                out.append(
                  "UR_QA08_WIN_MEDAL_VRAM "
                  f"frame={frame} x=225 raster_y={y} ppu_line={y+1} "
                  f"slot={slot} xoff=6 yoff=8 usedcol=6 usedrow=8 "
                  f"name={name} obsel=63 obsel_bank=7000 tile={source_tile} "
                  f"wordaddr={source_wa} guest_w0={w0} guest_w8={w8} "
                  f"render_w0={w0} render_w8={w8} guest_idx={val} "
                  f"render_idx={val} actual_obj=06de actual_cgram=de "
                  f"overlay={override} vram_writes=101\n")
    return "".join(out)


class NativeOverlappingGoldVRAMTest(unittest.TestCase):
    def test_patch_stays_readonly_and_unique_after_source_PPU_observer(self):
        # unittest invocations run from repo root, but Windows executes this
        # file directly and may not see tests as a Python package. Do not
        # depend on imports of other test files for critical source fixtures.
        self.assertIn("PpuRenderVram(ppu)",patcher.ADDED)
        self.assertIn("ppu->vram[wa]",patcher.ADDED)
        self.assertIn("slots[2]",patcher.ADDED)
        self.assertIn("UR_QA08_WIN_MEDAL_VRAM",patcher.ADDED)
        self.assertIn("PPU_objTileAdr2(ppu)",patcher.ADDED)
        self.assertIn("for (unsigned qi = 0; qi < 2; ++qi)",patcher.ADDED)
        for forbidden in ("ppu->vram[wa] =","ppu->oam[slot * 2u] =",
                          "ppu->objBuffer.data[x+kPpuExtraLeftRight] ="):
            self.assertNotIn(forbidden,patcher.ADDED)
        with self.assertRaises(ValueError):
            patcher.patch_source("unrelated original native renderer")

    def test_live_gold_and_adjacent_indices_are_independent(self):
        r=witness.inspect_medal_live_vram(records())
        self.assertEqual(r["source_samples"],8)
        self.assertEqual(r["actual_Windows_pixel_pairs"],4)
        self.assertTrue(r["native_all_pair_source_overlap_hypothesis_observed"])
        for p in r["corresponding_overlapping_sprite_pairs"]:
            self.assertEqual((p["native_actual_earlier_slot_index"],
                              p["native_actual_gold_slot_index"],
                              p["actual_Windows_OBJ_color_index"]),(14,15,14))
            self.assertTrue(p["native_gold_tile_was_covered_by_lower_OAM_slot"])

    def test_reject_missing_duplicate_invalid_source_rows_and_overlay_forgery(self):
        good=records()
        for bad in (
            good.splitlines()[0]+"\n",
            good+good.splitlines()[0]+"\n",
            good.replace("slot=97","slot=99"),
            good.replace("wordaddr=7de0","wordaddr=7de1"),
            good.replace("obsel_bank=7000","obsel_bank=6000"),
            good.replace("actual_cgram=de","actual_cgram=df"),
            good.replace("render_idx=15","render_idx=14"),
            good.replace("guest_w0=3f1f","guest_w0=3f1d"),
            good+"UR_QA08_WIN_MEDAL_VRAM_REJECT frame=4176 slot=99\n",
        ):
            with self.subTest(case=bad[:80]),self.assertRaises(ValueError):
                witness.inspect_medal_live_vram(bad)

    def test_overlay_present_distinguishes_host_VRAM(self):
        s=records(override=1)
        out=witness.inspect_medal_live_vram(s)
        self.assertTrue(all(p["native_renderVram_override_active"]
                            for p in out["corresponding_overlapping_sprite_pairs"]))


if __name__=="__main__":
    unittest.main()
