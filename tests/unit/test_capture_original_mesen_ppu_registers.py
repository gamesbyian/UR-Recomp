"""ROM-free source SNES PPU register evidence selection controls."""
import tempfile
from pathlib import Path
import unittest

from tools.art.capture_original_mesen_ppu_registers import (
    FIELD_NAMES, SCHEMA, select_source_state, capture_registers,
)
from tools.art.capture_original_mesen_ppu_raw import REGIONS


class FakeMesen:
    def __init__(self):
        self.frame=0
    def tool(self,name,**args):
        if name=="input.set":
            return {"ok":True}
        if name=="run.step_frames":
            if args.get("reset"):
                self.frame=0
            self.frame+=args["frames"]
            return {"status":{"frame":self.frame}}
        if name=="run.status":
            return {"frame":self.frame}
        if name=="console.state":
            return {"ppu.oammode":3,"ppu.oambaseaddress":4096,"ppu.oamaddressoffset":4096,
                    "ppu.scanline":239,"ppu.forcedblank":False,
                    "ppu.framecount":self.frame}
        if name=="cpu.read_memory":
            return {"memoryType":args["memoryType"],"address":args["address"],
                    "length":args["length"],"bytes":[(self.frame+i)&255
                                                    for i in range(args["length"])]}
        raise AssertionError(name)


class OriginalPpuSerializedTests(unittest.TestCase):
    def test_source_emulator_held_registers_match_real_frame_ticks(self):
        with tempfile.TemporaryDirectory() as d:
            proof=capture_registers(FakeMesen(),[],3,2,Path(d))
            self.assertEqual(proof["schema"],SCHEMA)
            self.assertEqual([r["original_bridge_tick"] for r in proof["actual_original_emulator_frame_states"]],[4,5])
            self.assertEqual([r["exact_source_PPU_register_fields"]["frameCount"]["original_value"]
                              for r in proof["actual_original_emulator_frame_states"]],[4,5])
            self.assertEqual(proof["actual_original_emulator_frame_states"][0]
                             ["exact_source_PPU_register_fields"]["OamMode"]["original_value"],3)
            self.assertFalse(proof["source_PPU_screen_phase_correspondence_verified"])
            self.assertFalse(proof["original_racer_sprite_pixel_ownership_verified"])

    def test_missing_original_PPU_field_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"mandatory"):
            select_source_state({"ppu.oammode":2,"ppu.someotherfield":42})

    def test_ambiguous_source_field_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"ambiguous"):
            select_source_state({"ppu.oammode":1,"ppu.oamMode":2})

    def test_invalid_source_register_values_fail_closed(self):
        for value in ("five",None,2.5,(1<<49)):
            with self.subTest(value=value),self.assertRaisesRegex(ValueError,"non-physical"):
                select_source_state({"ppu.oammode":value})

    def test_time_drift_during_source_state_read_is_rejected(self):
        class Moving(FakeMesen):
            def tool(self,name,**args):
                if name=="console.state":
                    result=super().tool(name,**args)
                    self.frame+=1
                    return result
                return super().tool(name,**args)
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,"advanced during"):
                capture_registers(Moving(),[],1,1,Path(d))

    def test_refuses_unbounded_or_unshaped_console_map(self):
        for invalid in (None,{},[],{str(i):i for i in range(300000)}):
            with self.subTest(which=str(type(invalid))),self.assertRaisesRegex(ValueError,"malformed"):
                select_source_state(invalid)


if __name__=="__main__":
    unittest.main()
