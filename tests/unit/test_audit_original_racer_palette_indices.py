"""ROM-free original 4bpp source palette-index / wheel-disc contracts."""
import unittest
from unittest.mock import patch
from tools.art.audit_original_racer_palette_indices import (
    rasterize_composed_palette_indices, rgba_from_original_index_plane,
    palette_disk_census, parse_id)
from tools.extract_racer_presentation_family import encode_4bpp_tile


def tile(colour=3):
    rows=[[0]*8 for _ in range(8)]
    rows[0][0]=colour
    rows[1][1]=7
    return encode_4bpp_tile(rows)


def composition(n):
    return {"cells":[{"player":"p1","word_hex":f"0x{i+1:04X}",
                      "minor_slot":0,"major_slot":0} for i in range(n)]}


def palette():
    cols=[(10,10,10,255) for _ in range(16)]
    cols[0]=(0,0,0,0)
    cols[3]=(240,30,30,255)
    cols[7]=(40,70,220,255)
    return cols


class OriginalIndexTests(unittest.TestCase):
    def test_exact_source_4bpp_tile_positions_and_reflections(self):
        with patch("tools.art.audit_original_racer_palette_indices.piece_source_tile",
                   return_value=(tile(),{})):
            plane=rasterize_composed_palette_indices(b"",composition(1),"p1")
            flipped=rasterize_composed_palette_indices(
                b"",composition(1),"p1",hflip=True,vflip=True)
        self.assertEqual(len(plane),4096)
        self.assertEqual(plane[8],3)
        self.assertEqual(plane[64+9],7)
        self.assertEqual(plane[9],0)
        self.assertEqual(flipped[63*64+55],3)
        self.assertEqual(flipped[62*64+54],7)
        self.assertEqual(sum(bool(v) for v in plane),2)

    def test_transparent_second_source_tile_replaces_opaque_prior(self):
        blank=encode_4bpp_tile([[0]*8 for _ in range(8)])
        with patch("tools.art.audit_original_racer_palette_indices.piece_source_tile",
                   side_effect=[(tile(),{}),(blank,{})]):
            plane=rasterize_composed_palette_indices(b"",composition(2),"p1")
        self.assertEqual(sum(plane),0)
        self.assertEqual(plane[8],0)

    def test_nonblack_transparent_palette_zero_matches_existing_rom_rgba_composer(self):
        from tools.extract_racer_presentation_family import rasterize_composed_player_rgba
        pal=palette()
        pal[0]=(47,28,62,0)
        with patch("tools.art.audit_original_racer_palette_indices.piece_source_tile",
                   return_value=(tile(),{})):
            index,touched=rasterize_composed_palette_indices(
                b"",composition(1),"p1",return_touched=True)
        actual=rgba_from_original_index_plane(index,touched,pal)
        with patch("tools.extract_racer_presentation_family.piece_source_tile",
                   return_value=(tile(),{})), patch(
                   "tools.extract_racer_presentation_family.rgba_palette",return_value=pal):
            source=rasterize_composed_player_rgba(b"",composition(1),"p1",6)
        self.assertEqual(actual,source)
        # The authored cell covers one 8x8 tile at original x8..15, y0..7.
        self.assertEqual(sum(touched),64)
        self.assertEqual(actual[:4],bytes([0,0,0,0]))
        self.assertEqual(actual[4*9:4*10],bytes([47,28,62,0]))
        self.assertEqual(actual[4*8:4*9],bytes([240,30,30,255]))
        with self.assertRaisesRegex(ValueError,"unwritten"):
            rgba_from_original_index_plane(bytes([3])+bytes(4095),bytes(4096),pal)
        with self.assertRaises(ValueError):
            rgba_from_original_index_plane(index,bytes(4095),pal)

    def test_index_level_disk_census_retains_tied_original_wheel_centre(self):
        plane=bytearray(4096)
        for x,y,v in ((20,20,3),(22,22,3),(20,15,7)):
            plane[y*64+x]=v
        r=palette_disk_census(bytes(plane),[[20,20,7],[21,20,7]],palette())
        self.assertEqual(r["opaque_source_pixels"],3)
        self.assertEqual(r["all_source_wheel_centre_candidates"],2)
        self.assertEqual(r["opaque_palette_indices"]["3"]["source_wheel_disc_pixels_min"],2)
        self.assertEqual(r["opaque_palette_indices"]["3"]["source_high_chroma_heuristic"],"red")
        self.assertEqual(r["opaque_palette_indices"]["7"]["source_high_chroma_heuristic"],"blue")
        self.assertFalse(r["source_3d_part_identity_verified"])

    def test_invalid_index_plane_and_hex_ids_fail_closed(self):
        self.assertEqual(parse_id("0x0001"),1)
        for bad in (1,"0001","0x10000","-1"):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                parse_id(bad)
        with self.assertRaises(ValueError):
            rasterize_composed_palette_indices(b"",composition(0),"p3")
        plane=bytearray(4096)
        plane[20*64+20]=3
        good=bytes(plane)
        for plane,centres,colours in (
            (b"x"*4096,[[20,20,7]],palette()),
            (bytes(4096),[[20,20,7]],palette()),
            (good,[],palette()),
            (good,[[20,20,6]],palette()),
            (good,[[64,20,7]],palette()),
            (good,[[20,20,7]],palette()[:8]),
        ):
            with self.assertRaises(ValueError):
                palette_disk_census(plane,centres,colours)


if __name__=="__main__":
    unittest.main()
