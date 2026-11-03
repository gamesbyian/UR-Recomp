"""ROM-free source MesenCE serializer-map and exact SNES OBJ-size controls."""
import unittest

from tools.art.original_mesen_ppu_registers import (
    SCHEMA, REQUIRED_INTS, REQUIRED_BOOLEANS, W, H,
    obj_pixel_dimensions, extract_serialized_ppu_registers, add_oam_pixel_sizes,
)


def authentic_shape_synthetic_state(mode=2):
    data={k:low for k,(low,_) in REQUIRED_INTS.items()}
    data["ppu.oammode"]=mode
    data["ppu.oamaddressoffset"]=0x1000
    data["ppu.framecount"]=1218
    data["ppu.scanline"]=225
    data.update({k:False for k in REQUIRED_BOOLEANS})
    for ax in ("hscroll","vscroll"):
        for n in range(4):
            data[f"ppu.layers[{n}].{ax}"]=n*21
    data["cpu.accumulator"]=654321
    return data


class PinnedMesenObjConfigTests(unittest.TestCase):
    def test_all_eight_source_sizes_match_pinned_real_mesen_tables(self):
        self.assertEqual(len(W),16)
        self.assertEqual(len(H),16)
        for mode in range(8):
            self.assertEqual(obj_pixel_dimensions(mode,False),(W[mode],H[mode]))
            self.assertEqual(obj_pixel_dimensions(mode,True),(W[mode+8],H[mode+8]))
        self.assertEqual(obj_pixel_dimensions(2,True),(64,64))
        self.assertEqual(obj_pixel_dimensions(6,False),(16,32))
        self.assertEqual(obj_pixel_dimensions(6,True),(32,64))
        self.assertEqual(obj_pixel_dimensions(7,True),(32,32))

    def test_unexpected_high_table_bool_and_mode_rejected(self):
        for v in (-1,8,True,1.2,"2",None):
            with self.subTest(v=v),self.assertRaisesRegex(ValueError,"OBJ size"):
                obj_pixel_dimensions(v,False)
        with self.assertRaisesRegex(ValueError,"OBJ size"):
            obj_pixel_dimensions(2,1)

    def test_pinned_map_whitelists_source_registers_and_no_inferred_visibility(self):
        data=extract_serialized_ppu_registers(authentic_shape_synthetic_state())
        self.assertEqual(data["schema"],SCHEMA)
        self.assertEqual(data["original_16bit_OBJ_small_dimensions_pixels"],[8,8])
        self.assertEqual(data["original_16bit_OBJ_large_dimensions_pixels"],[64,64])
        self.assertNotIn("cpu.accumulator",data["source_registers"])
        self.assertEqual(data["source_registers"]["ppu.framecount"],1218)
        self.assertRegex(data["source_state_whitelist_sha256"],r"\A[0-9a-f]{64}\Z")
        self.assertFalse(data["original_PPUSCANOUT_phase_independently_verified"])
        self.assertFalse(data["owner_likeness_approved"])

    def test_missing_wrong_type_and_unaligned_source_registers_rejected(self):
        baseline=authentic_shape_synthetic_state()
        for key in ["ppu.oammode","ppu.oamaddressoffset","ppu.layers[0].hscroll",
                    "ppu.screenbrightness","ppu.forcedblank"]:
            with self.subTest(key=key):
                case=dict(baseline)
                del case[key]
                with self.assertRaisesRegex(ValueError,"missing"):
                    extract_serialized_ppu_registers(case)
        for key,value in [("ppu.oammode",True),("ppu.oammode",8),
                          ("ppu.oambaseaddress",8193),
                          ("ppu.oamaddressoffset",4097),
                          ("ppu.layers[2].vscroll",0x2000),
                          ("ppu.forcedblank",1)]:
            with self.subTest(key=key,value=value):
                case=dict(baseline)
                case[key]=value
                with self.assertRaises(ValueError):
                    extract_serialized_ppu_registers(case)

    def test_exact_raw_original_oam_high_bits_produce_128_unclaimed_obj_sizes(self):
        raw=bytearray(544)
        raw[512]=0b00001000  # slot 1 large, other 3 default small
        raw[4*1]=0x80
        state=extract_serialized_ppu_registers(authentic_shape_synthetic_state(mode=2))
        result=add_oam_pixel_sizes(bytes(raw),state)
        rows=result["original_size_config_for_each_source_OAM_slot"]
        self.assertEqual(result["original_source_OAM_slots"],128)
        self.assertEqual((rows[0]["source_OBJ_width"],rows[0]["source_OBJ_height"]),(8,8))
        self.assertEqual((rows[1]["source_OBJ_width"],rows[1]["source_OBJ_height"]),(64,64))
        self.assertEqual(rows[1]["source_OBJ_X_signed9"],128)
        self.assertFalse(rows[1]["original_visible_pixel_ownership_verified"])
        self.assertFalse(result["original_OAM_to_visible_source_OBJ_pixels_verified"])

    def test_source_oam_geometry_requires_authenticated_configuration_and_bytes(self):
        with self.assertRaisesRegex(ValueError,"witness"):
            add_oam_pixel_sizes(bytes(544),{"schema":"not source"})
        with self.assertRaisesRegex(ValueError,"544-byte"):
            add_oam_pixel_sizes(bytes(543),
                                extract_serialized_ppu_registers(authentic_shape_synthetic_state()))


if __name__=="__main__":
    unittest.main()
