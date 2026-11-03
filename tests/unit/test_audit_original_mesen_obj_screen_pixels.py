"""ROM-free source SNES OBJ tile/colour and deterministic screen-match controls."""
import unittest
from tools.art.audit_original_mesen_obj_screen_pixels import (
    bgr555_to_rgb, colour_5_to_8, decode_source_obj, tile_from_vram,
    best_opaque_matches, p6_screen, FRAME_SIZE,
)


def fixture(*,flipped=False,large=False,second=False):
    vram=bytearray(65536)
    cgram=bytearray(512)
    # The first source tile in the selected OBJ page contains an opaque
    # red index-1 pixel at local (0,0) and no other painted pixels.
    word=0x6000+(0x1000 if second else 0)
    vram[2*word]=0x80
    cgram[2*129]=31
    row={
       "oam_slot":96,
       "source_oam_tile_word9":0x100 if second else 0,
       "source_obj_palette_id0_to7":0,
       "source_obj_size_select_large":large,
       "source_obj_hflip":flipped,
       "source_obj_vflip":False,
    }
    return row,bytes(vram),bytes(cgram)


class SourceOriginalObjMatchTests(unittest.TestCase):
    def test_exact_mesen_five_bit_colour(self):
        self.assertEqual([colour_5_to_8(v) for v in (0,1,16,31)],
                         [0,8,132,255])
        self.assertEqual(bgr555_to_rgb(31),(255,0,0))
        self.assertEqual(bgr555_to_rgb(31<<10),(0,0,255))
        for bad in (-1,32,True,2.5):
            with self.subTest(value=bad),self.assertRaisesRegex(ValueError,"five-bit"):
                colour_5_to_8(bad)

    def test_raw_VRAM_is_byte_addressed_but_upstream_obj_is_word_addressed(self):
        row,vram,cgram=fixture()
        tile=tile_from_vram(vram,0x6000)
        self.assertEqual(tile[0],1)
        self.assertTrue(all(x==0 for x in tile[1:]))
        with self.assertRaisesRegex(ValueError,"65536"):
            tile_from_vram(vram[:-1],0x6000)

    def test_mode4_small_sprite_palette_alpha_and_horizontal_flip(self):
        row,vram,cgram=fixture()
        obj=decode_source_obj(row,vram,cgram,oam_mode=4,obj_base=0x6000,
                              second_table_offset=0x1000)
        self.assertEqual(obj["size"],16)
        self.assertEqual(obj["opaque_count"],1)
        self.assertEqual(obj["plane"][0],1)
        self.assertEqual(obj["rgba"][:4],bytes([255,0,0,255]))
        self.assertEqual(obj["rgba"][4:8],bytes(4))
        row["source_obj_hflip"]=True
        flipped=decode_source_obj(row,vram,cgram,oam_mode=4,obj_base=0x6000,
                                  second_table_offset=0x1000)
        self.assertEqual(flipped["plane"][15],1)
        self.assertEqual(flipped["plane"][0],0)
        self.assertEqual(flipped["opaque_count"],1)

    def test_second_obj_tile_table_bit_and_large_sprite(self):
        row,vram,cgram=fixture(second=True,large=True)
        obj=decode_source_obj(row,vram,cgram,oam_mode=4,obj_base=0x6000,
                              second_table_offset=0x1000)
        self.assertEqual(obj["size"],64)
        self.assertEqual(obj["opaque_count"],1)
        self.assertEqual(obj["plane"][0],1)

    def test_unverified_original_mode_or_base_must_fail(self):
        row,vram,cgram=fixture()
        for args in ({'oam_mode':0,'obj_base':0x6000,'second_table_offset':0x1000},
                     {'oam_mode':4,'obj_base':0x3000,'second_table_offset':0x1000},
                     {'oam_mode':4,'obj_base':0x6000,'second_table_offset':0}):
            with self.subTest(args=args),self.assertRaisesRegex(ValueError,"OBSEL"):
                decode_source_obj(row,vram,cgram,**args)

    def test_synthetic_opaque_pixel_colour_registration_and_decoy(self):
        row,vram,cgram=fixture()
        obj=decode_source_obj(row,vram,cgram,oam_mode=4,obj_base=0x6000,
                              second_table_offset=0x1000)
        rgb=bytearray(FRAME_SIZE[0]*FRAME_SIZE[1]*3)
        pos=3*(47*256+104)
        rgb[pos:pos+3]=bytes([255,0,0])
        result=best_opaque_matches(obj,bytes(rgb),upper=True)
        self.assertTrue(result["complete_pixel_match"])
        self.assertEqual((result["source_screen_x"],result["source_screen_y"]),(104,47))
        rival=best_opaque_matches(obj,bytes(rgb),upper=False)
        self.assertFalse(rival["complete_pixel_match"])
        with self.assertRaisesRegex(ValueError,"screen RGB"):
            best_opaque_matches(obj,b"",upper=True)

    def test_strict_source_ppm_header(self):
        valid=b"P6\n256 239\n255\n"+bytes(FRAME_SIZE[0]*FRAME_SIZE[1]*3)
        self.assertEqual(len(p6_screen(valid)),256*239*3)
        for bad in (valid[:-1],b"P3"+valid[2:],valid+b"x"):
            with self.assertRaisesRegex(ValueError,"256x239"):
                p6_screen(bad)


if __name__=="__main__":
    unittest.main()
