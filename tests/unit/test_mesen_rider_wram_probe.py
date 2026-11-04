"""ROM-free source WRAM capture tests with a strict deterministic fake bridge."""
import hashlib
import unittest
from tools.art.mesen_rider_wram_probe import WORDS, capture, validate, valid_word, MEM_TYPE

class Fake:
    def __init__(self):
        self.frame = 1603
        self.calls = []
    def tool(self, tool, **kwargs):
        self.calls.append((tool,kwargs))
        if tool == "run.status":
            return {"frame":self.frame}
        assert tool == "cpu.read_memory"
        return {"memoryType":MEM_TYPE,"address":kwargs["address"],
                "length":2,"bytes":[kwargs["address"] & 255,
                                    (kwargs["address"] >> 8) & 255]}

class RiderWramProbeTests(unittest.TestCase):
    def test_source_unattributed_u16_values_and_hash(self):
        fake = Fake()
        row = capture(fake,1603)
        validate(row,1603)
        self.assertEqual(len(WORDS),11)
        self.assertEqual(row["source_u16_le"]["selected_rider_animation_phase_0f83"],0x0F83)
        self.assertEqual(row["source_u16_le"]["dma_queue_pending_0306"],0x0306)
        self.assertEqual(len(row["source_raw_22_bytes_sha256"]),64)
        self.assertEqual(len([t for t,_ in fake.calls if t=="cpu.read_memory"]),11)
        self.assertFalse(row["original_specific_CPU_writer_PC_verified"])
        self.assertFalse(row["original_3D_geometry_camera_or_pose_recovered"])
        self.assertTrue(row["source_unattributed_selected_rider_registers"])

    def test_bad_mesen_read_byte_span_fails_closed(self):
        good={"memoryType":MEM_TYPE,"address":0x0F83,"length":2,"bytes":[1,2]}
        self.assertEqual(valid_word(good,0x0F83),b"\x01\x02")
        for alteration in ({"memoryType":"snesVideoRam"},{"address":42},
                           {"length":3},{"bytes":[1]},{"bytes":[1,256]},
                           {"bytes":[True,1]},{"bytes":None}):
            payload={**good,**alteration}
            with self.assertRaises(ValueError):
                valid_word(payload,0x0F83)

    def test_inconsistent_frame_or_tampering_rejected(self):
        fake=Fake()
        with self.assertRaises(ValueError):
            capture(fake,1602)
        row=capture(fake,1603)
        fake.frame=1604
        with self.assertRaises(ValueError):
            capture(fake,1603)
        for update in ({"original_specific_CPU_writer_PC_verified":True},
                       {"source_raw_22_bytes_sha256":"0"*64},
                       {"source_u16_le":{"oops":1}},
                       {"original_3D_geometry_camera_or_pose_recovered":True}):
            with self.assertRaises(ValueError):
                validate({**row,**update},1603)

    def test_bool_tick_not_accepted(self):
        for tick in (True,-1,0,2501,2.5):
            with self.assertRaises(ValueError):
                capture(Fake(),tick)

if __name__=="__main__":
    unittest.main()

class FakeWrites:
    def __init__(self):
        self.next=0
        self.handles={}
    def tool(self,name,**kwargs):
        if name=="watch.create":
            self.next+=1
            handle=f"watch-{self.next}"
            self.handles[handle]=kwargs["address"]
            return {"handle":handle}
        if name=="watch.list":
            return {"events":[
                {"handle":"watch-1","address":0x0306,"value":1,"frame":1602,
                 "pcDisplay":"$83:F290","masterClock":123,"cpuCycleCount":345},
                {"handle":"watch-2","address":0x0F97,"value":7,"frame":1603,
                 "pcDisplay":"$83:EF0C","masterClock":124,"cpuCycleCount":346},
                {"handle":"watch-2","address":0x0F97,"value":8,"frame":1599,
                 "pcDisplay":"$83:EF0C"},
            ]}
        raise ValueError(name)

class ActualWriterWatchTests(unittest.TestCase):
    def test_bounded_callback_provenance_and_pc_metadata(self):
        from tools.art.mesen_rider_wram_probe import (
            start_watches,recent_writes,validate_recent_writes)
        fake=FakeWrites()
        handles=start_watches(fake)
        self.assertEqual(len(handles),7)
        result=recent_writes(fake,handles,1603)
        validate_recent_writes(result,1603)
        self.assertEqual([r["source_CPU_PC"] for r in result["events"]],
                         ["$83:F290","$83:EF0C"])
        self.assertFalse(result["callback_frame_to_held_PPU_snapshot_phase_independently_aligned"])

    def test_bad_callback_value_or_frame_is_rejected(self):
        from tools.art.mesen_rider_wram_probe import (
            start_watches,recent_writes,validate_recent_writes)
        fake=FakeWrites()
        handles=start_watches(fake)
        good=recent_writes(fake,handles,1603)
        for change in ({"byte_written":256},{"bridge_callback_frame":42},
                       {"source_byte_address":0xDEAD},{"source_CPU_PC":42}):
            invalid={**good,"events":[{**good["events"][0],**change}]}
            with self.assertRaises(ValueError):
                validate_recent_writes(invalid,1603)
