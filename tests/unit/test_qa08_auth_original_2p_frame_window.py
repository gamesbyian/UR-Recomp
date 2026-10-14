"""Strict original 2P 37-frame source capture time-window validation."""
import json
from pathlib import Path
import tempfile
import unittest

from tools import qa08_auth_original_2p_frame_window as check

def fixtures(root):
    receipt={"USA_ROM_SHA256":check.ROM,"original_script_SHA256":check.SCRIPT,
             "original_t480_WRAM_SHA256":check.WRAM,
             "source_65816_writer_PCs":18,
             "actual_executed_original_instruction_count":55,
             "second_camera_0DDB":1,"in_race_0313":1,
             "native_same_input_frame_parity_proven":False}
    live={"schema":check.LIVE_SCHEMA,"actual_original_PPU_2131_2132_writes":96,
          "actual_original_channel5_register_pairs":48,
          "actual_WRAM_PPU_byte_matches":96,
          "source_expected_byte_matches":96}
    go={"original_emulator_frame":1989,"original_source_fb_width":256,
        "original_source_fb_height":224}
    payload=bytearray(check.WIDTH*check.HEIGHT*4)
    for f in check.FRAMES:
        payload[0]=(f%256)
        (root/f"frame_{f:06d}_256x224.raw").write_bytes(payload)
    return receipt,live,go

class AuthenticOriginal2PRasterWindowTests(unittest.TestCase):
    def test_complete_true_original_window_and_distinct_callback_numbering(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);receipt,live,go=fixtures(root)
            z=check.validate(root,receipt,live,go)
            self.assertEqual(z["full_256x224_original_frames"],37)
            self.assertEqual(z["source_original_frames"][0]["original_Snesref_callback_frame_zero_based"],2188)
            self.assertEqual(z["source_original_frames"][0]["corresponding_original_retro_run_one_based"],2189)
            self.assertFalse(z["same_input_guest_phase_and_camera_as_native_proven"])
            self.assertFalse(z["original_vs_native_final_RGBA_parity_proven"])

    def test_missing_extra_or_cropped_images_fail(self):
        for how in ("missing","extra","cropped","bad_size","nonzero_alpha","stale"):
            with self.subTest(how=how),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);receipt,live,go=fixtures(root)
                first=root/"frame_002188_256x224.raw"
                if how=="missing":first.unlink()
                if how=="extra":(root/"frame_002225_256x224.raw").write_bytes(b"bad")
                if how=="cropped":
                    first.rename(root/"frame_002188_342x224.raw")
                if how=="bad_size":first.write_bytes(b"bad")
                if how=="nonzero_alpha":
                    x=bytearray(first.read_bytes());x[3]=255;first.write_bytes(x)
                if how=="stale":
                    data=(root/"frame_002188_256x224.raw").read_bytes()
                    for f in check.FRAMES:
                        (root/f"frame_{f:06d}_256x224.raw").write_bytes(data)
                with self.assertRaises(ValueError):
                    check.validate(root,receipt,live,go)

    def test_route_and_register_source_cannot_be_forged(self):
        for key,value in (("USA_ROM_SHA256","0"*64),
                          ("original_script_SHA256","0"*64),
                          ("native_same_input_frame_parity_proven",True)):
            with self.subTest(field=key),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);receipt,live,go=fixtures(root)
                receipt[key]=value
                with self.assertRaisesRegex(ValueError,"source"):
                    check.validate(root,receipt,live,go)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);receipt,live,go=fixtures(root)
            live["actual_WRAM_PPU_byte_matches"]=95
            with self.assertRaises(ValueError):
                check.validate(root,receipt,live,go)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);receipt,live,go=fixtures(root)
            go["original_emulator_frame"]=1988
            with self.assertRaises(ValueError):
                check.validate(root,receipt,live,go)

if __name__=="__main__": unittest.main()
