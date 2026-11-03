"""ROM-free source OAM semantics and fail-closed original artifact tests."""
import unittest
from tools.art.audit_original_mesen_oam_descriptors import decode_oam, summarize, descriptor, analyze_archived_source


def sample():
    """Original SNES OAM high-table packing with 4 intentionally distinct slots."""
    o=bytearray(544)
    # All remaining 128 slots default x=-32, y=224.
    for i in range(128):
        o[i*4:i*4+4]=bytes([224,224,0,0])
        o[512+i//4]|=1<<(2*(i%4))
    # Big size bit plus X-low/right, multiple OBJ palette and priority choices.
    for i,t,a in ((96,136,0x68),(97,0,0x66)):
        o[i*4:i*4+4]=bytes([104,153,t,a])
        o[512+i//4]&=~(3<<(2*(i%4)))
        o[512+i//4]|=2<<(2*(i%4))
    # X bit set gives signed x=-152, not +360 pixels.
    for i,t,a in ((98,0,0x66),(99,136,0x68)):
        o[i*4:i*4+4]=bytes([104,40,t,a])
        o[512+i//4]&=~(3<<(2*(i%4)))
        o[512+i//4]|=1<<(2*(i%4))
    return bytes(o)


class OriginalOamWordTests(unittest.TestCase):
    def test_high_table_2bit_packing_signed_x_and_palette_attributes(self):
        rows=decode_oam(sample())
        self.assertEqual(len(rows),128)
        self.assertEqual(rows[0]["source_oam_x_signed9"],-32)
        self.assertEqual([rows[i]["source_oam_x_signed9"] for i in range(96,100)],
                         [104,104,-152,-152])
        self.assertEqual([rows[i]["source_obj_size_select_large"] for i in range(96,100)],
                         [True,True,False,False])
        self.assertEqual([rows[i]["source_oam_tile_word9"] for i in range(96,100)],
                         [136,0,0,136])
        self.assertEqual([rows[i]["source_obj_palette_id0_to7"] for i in range(96,100)],
                         [4,3,3,4])
        self.assertEqual([rows[i]["source_obj_priority_id0_to3"] for i in range(96,100)],
                         [2]*4)
        self.assertTrue(all(rows[i]["source_obj_hflip"] for i in range(96,100)))
        self.assertTrue(all(not rows[i]["source_obj_vflip"] for i in range(96,100)))
        self.assertFalse(rows[96]["source_oam_y_raw8"]==rows[98]["source_oam_y_raw8"])

    def test_modal_source_structure_is_statistical_not_visibility(self):
        data=summarize(sample())
        self.assertEqual(data["modal_original_descriptor_slots"],124)
        self.assertEqual(data["different_from_modal_original_oam_slots"],[96,97,98,99])
        self.assertEqual(data["distinct_original_oam_descriptors"],5)
        self.assertFalse(data["original_displayed_sprite_pixels_verified"])
        self.assertFalse(data["source_OBSEL_sprite_pixel_sizes_verified"])

    def test_high_tile_number9_and_y_raw_unwrapped(self):
        data=bytearray(sample())
        data[4*5+2]=255
        data[4*5+3]=0xFF
        row=decode_oam(bytes(data))[5]
        self.assertEqual(row["source_oam_tile_word9"],511)
        self.assertEqual(row["source_obj_palette_id0_to7"],7)
        self.assertEqual(row["source_obj_priority_id0_to3"],3)
        self.assertTrue(row["source_obj_vflip"])
        self.assertTrue(row["source_obj_hflip"])

    def test_malformed_oam_and_unauthenticated_archive_rejected(self):
        for data in (bytearray(544), bytes(543), bytes(545), None):
            with self.subTest(type=str(type(data))),self.assertRaisesRegex(ValueError,"exact 544"):
                decode_oam(data)
        with self.assertRaisesRegex(ValueError,"frozen original"):
            analyze_archived_source(b"PK\\x03\\x04not-a-proven-original-replay")

    def test_slots_are_not_anatomical_and_compare_does_not_infer_draw_order(self):
        data=summarize(sample())
        self.assertEqual([row["oam_slot"] for row in data["nonmodal_original_oam_entries"]],
                         [96,97,98,99])
        self.assertFalse(data["source_original_3d_anatomy_verified"])
        a=decode_oam(sample())
        self.assertEqual(descriptor(a[96])[0],104)
        self.assertEqual(descriptor(a[98])[0],-152)


if __name__=="__main__":
    unittest.main()
