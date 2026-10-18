"""Fail closed on fabricated medal 4bpp source, writer priority, and guest drift."""
import unittest
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"tools")]
from tools import qa08_current_medal_obj_fetch_patch as p
from tools import qa08_join_current_medal_obj_fetch as j

NATIVE={
    "real_2p_guest_frames":5484,
    "real_guest_CRC_SHA256":
       "b735b0183b296ce32db009b282fab18bc9f9cf26668c02231373e9740184c568",
    "source_original_same_field_ownership_proven":False,
}
CORE_SOURCE="""#include <stdio.h>
#include <stdlib.h>
static bool ppu_evaluateSprites(Ppu *ppu, int line);
PpuRenderVram(ppu); PpuComposeExtraObjects();
"""+p.ANCHOR

def full_owner():
    owner=dict(NATIVE)
    owner["pixels"]=[
        {"frame":f,"xy":[x,y],"main":"4" if (f==4032 and (x,y) in
         ((205,115),(205,139),(225,96),(225,120))) else "0",
         "obj_zbuffer":"0281","obj_word":"7c12"} for f in j.FRAMES for x,y in j.COORDS
    ]
    return owner

def writer(frame,x,y,slot=112,plane=0x80,pixel=1,z=0x281):
    return (f"UR_QA08_WIN_OBJ_FETCH frame={frame} x={x} raster_y={y} "
            f"slot={slot} oam=607d attrs=0000 "
            f"oam_tile=00 used_tile=000 objadr=0000 "
            f"row=0 src_col=0 px=0 palette=80 priority=2 "
            f"pixel={pixel:x} plane={plane:08x} writer_obj={z:04x}")

def four_rows():
    return "\n".join(writer(4032,x,y) for x,y in
                     ((205,115),(205,139),(225,96),(225,120)))

class Medal4BppSource(unittest.TestCase):
    def test_bounded_actual_source_injection_is_reversible(self):
        patched=p.patch_source(CORE_SOURCE)
        self.assertEqual(p.patch_source(patched),patched)
        self.assertEqual(patched.replace(p.TRACE,p.ANCHOR),CORE_SOURCE)
        self.assertIn("const uint16 *addr",patched) if "const uint16 *addr" in CORE_SOURCE else None
        for bad in (
            "",
            CORE_SOURCE.replace("PpuRenderVram(ppu)", "otherVRAM(ppu)"),
            CORE_SOURCE+p.ANCHOR,
            patched.replace(p.MARK,"FOREIGN_TILE_CHANGE"),
            patched.replace('writer_obj=%04x', 'writer_obj=%08x'),
        ):
            with self.subTest(raw=bad[:60]),self.assertRaises(ValueError):
                p.patch_source(bad)
        self.assertNotIn("dst[0] = 0",patched)
        self.assertIn("dst[0] = z + pixel;",patched)

    def test_exact_four_native_current_raster_winners(self):
        report=j.joined(four_rows(),full_owner())
        self.assertEqual(report["current_native_exact_sprite_winners"],4)
        self.assertEqual(report["actual_source_sprite_port_writes"],4)
        self.assertEqual(report["current_native_non_OBJ_main_cases"],21)
        self.assertTrue(all(q["actual_current_native_winning_oam_slot"]==112
                            for q in report["actual_current_OBJ_source_tile_pixels"]))
        self.assertFalse(report["source_2014_Snes9x_pixel_winner_tile_identical_proven"])
        self.assertFalse(report["global_output_shift_or_tile_reindex_authorized"])
        self.assertFalse(report["renderer_mutation_or_art_release_accepted"])

    def test_encoded_obj_pixel_is_not_cgram_palette_word(self):
        owner=full_owner()
        owner["pixels"][3]["obj_word"]="cafe" # colour must not enter priority check
        self.assertEqual(j.joined(four_rows(),owner)["current_native_exact_sprite_winners"],4)
        owner["pixels"][3]["obj_zbuffer"]="0282"
        with self.assertRaisesRegex(ValueError,"OBJ buffer winner"):
            j.joined(four_rows(),owner)

    def test_true_overlapping_OAM_writer_wins_last_without_repainting(self):
        rows=four_rows().splitlines()
        rows[0]=writer(4032,205,115,slot=114,pixel=1,z=0x281)
        rows.insert(1,writer(4032,205,115,slot=112,pixel=1,z=0x281))
        report=j.joined("\n".join(rows),full_owner())
        item=next(x for x in report["actual_current_OBJ_source_tile_pixels"]
                  if x["xy"]==[205,115])
        self.assertEqual(item["direct_sprite_contenders_in_real_writer_order"],2)
        self.assertEqual(item["actual_current_native_winning_oam_slot"],112)

    def test_missing_wrong_vram_4bpp_or_priority_fails(self):
        source=four_rows()
        invalid=[
            source.replace("pixel=1","pixel=2",1),
            source.replace("plane=00000080","plane=00000000",1),
            source.replace("priority=2","priority=256",1),
            source.replace("frame=4032","frame=4031",1),
            source.replace("writer_obj=0281","writer_obj=0282",1),
            source.replace("slot=112","slot=128",1),
            source.splitlines()[0],
            "",
        ]
        for s in invalid:
            with self.subTest(raw=s[:100]),self.assertRaises(ValueError):
                j.joined(s,full_owner())
        wrong=full_owner()
        wrong["real_guest_CRC_SHA256"]="0"*64
        with self.assertRaisesRegex(ValueError,"gate missing"):
            j.joined(source,wrong)

if __name__=="__main__":
    unittest.main()
