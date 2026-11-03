"""ROM-free source 8x8 tile byte lineage and pseudo-motion controls."""
import hashlib
import unittest
from tools.art.audit_original_racer_tile_lineage import (
    decode_tile, compose_tile_lineage, summarize_lineages)

FILLED=bytes([255,0]*8+[0]*16)  # 64 original index-one pixels
EMPTY=bytes(32)


def grid(filled=(0,0), player="p1"):
    cells=[]
    for row in range(5):
        for col in range(14):
            occupant=("p1" if col<6 else "p2" if col>=8 else None)
            slot=(col if occupant=="p1" else col-8 if occupant=="p2" else None)
            number=(1 if occupant==player and (row,slot)==filled else 2)
            cells.append({"player":occupant,"major_slot":row if occupant else None,
                          "minor_slot":slot,"word_hex":f"0x{number:04X}" if occupant==player else None,
                          "choice":f"{player}_primary" if occupant==player else "blank"})
    return {"cells":cells}


def loader(number):
    raw=FILLED if number==1 else EMPTY
    return raw,{"source_sha256":hashlib.sha256(raw).hexdigest(),
                "source_snes":f"27:{0x8000+number*32:04X}",
                "source_rom_offset":number*32}


def wrap(id,source):
    return {"representation_id":id,"lineage":source}


class OriginalTileLineageTests(unittest.TestCase):
    def test_decode_real_4bpp_bitplanes(self):
        self.assertEqual(decode_tile(FILLED),tuple([1]*64))
        self.assertEqual(decode_tile(EMPTY),tuple([0]*64))
        with self.assertRaises(ValueError):
            decode_tile(bytes(31))

    def test_exact_64px_grid_transparent_zero_and_source_slot(self):
        result=compose_tile_lineage(grid(), "p1", loader)
        self.assertEqual(result["tile_slots_written"],30)
        self.assertEqual(result["opaque_source_pixels"],64)
        self.assertEqual(result["explicit_transparent_source_pixels"],30*64-64)
        self.assertEqual(sum(result["_touched"]),30*64)
        self.assertEqual(sum(result["_indices"]),64)
        self.assertEqual(result["_indices"][8],1)
        self.assertEqual(result["_indices"][0],0)
        self.assertEqual(result["entries"][0]["source_tile_snes"],"27:8020")
        self.assertEqual(result["entries"][0]["source_stream_choice"],"p1_primary")

    def test_moved_identical_tile_is_shared_asset_not_recovered_bone(self):
        a=compose_tile_lineage(grid((0,0)),"p1",loader)
        b=compose_tile_lineage(grid((0,2)),"p1",loader)
        report=summarize_lineages([wrap("source-a",a),wrap("source-b",b)])
        self.assertEqual(report["unique_original_index_planes"],2)
        self.assertEqual(report["unique_exact_8x8_tile_payloads"],2)
        self.assertEqual(report["exact_nonblank_tile_payloads_reused_in_multiple_source_planes"],1)
        self.assertEqual(report["tile_payloads_observed_at_multiple_source_slots"],2)
        self.assertEqual(report["distinct_original_pose_pairs_with_shared_nonblank_8x8_tiles"],1)
        self.assertFalse(report["original_1994_anatomical_part_correspondence_verified"])

    def test_palette_recolour_does_not_claim_independent_pose(self):
        a=compose_tile_lineage(grid(),"p1",loader)
        report=summarize_lineages([wrap("palette-a",a),wrap("palette-b",a)])
        self.assertEqual(report["original_source_representations"],2)
        self.assertEqual(report["unique_original_index_planes"],1)
        self.assertEqual(report["distinct_original_pose_pairs_with_shared_nonblank_8x8_tiles"],0)

    def test_equal_index_plane_with_incompatible_tile_provenance_rejected(self):
        a=compose_tile_lineage(grid(),"p1",loader)
        b=compose_tile_lineage(grid(),"p1",loader)
        b["entries"][0]={**b["entries"][0],"source_tile_sha256":"f"*64}
        with self.assertRaisesRegex(ValueError,"conflicting"):
            summarize_lineages([wrap("a",a),wrap("b",b)])

    def test_reused_representation_id_is_rejected(self):
        a=compose_tile_lineage(grid(),"p1",loader)
        with self.assertRaisesRegex(ValueError,"identities"):
            summarize_lineages([wrap("a",a),wrap("a",a)])

    def test_wrong_sha_invalid_slot_and_missing_cells_rejected(self):
        def forged(number):
            raw,meta=loader(number)
            return raw,{**meta,"source_sha256":"0"*64}
        with self.assertRaisesRegex(ValueError,"unverified"):
            compose_tile_lineage(grid(),"p1",forged)
        wrong=grid();wrong["cells"][0]["minor_slot"]=100
        with self.assertRaisesRegex(ValueError,"slot"):
            compose_tile_lineage(wrong,"p1",loader)
        with self.assertRaisesRegex(ValueError,"grid"):
            compose_tile_lineage({"cells":grid()["cells"][:-1]},"p1",loader)

    def test_player_two_has_independent_canonical_slots(self):
        a=compose_tile_lineage(grid((1,3),player="p2"),"p2",loader)
        self.assertEqual(a["tile_slots_written"],30)
        self.assertEqual(a["opaque_source_pixels"],64)
        self.assertEqual(a["_indices"][(1*8)*64+(4*8)],1)


if __name__=="__main__":
    unittest.main()
