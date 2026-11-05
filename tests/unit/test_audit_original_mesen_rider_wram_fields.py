"""ROM-free original rider WRAM parser/provenance tests."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools.art.capture_original_mesen_ppu_raw import (
    capture_states, REGIONS, RIDER_WRAM_SIZE, RIDER_WRAM_MEMORY_TYPE,
)
from tools.art.audit_original_mesen_rider_wram_fields import (
    audit_directory, interpret_raw, read_word_le, CANDIDATE_WORDS,
    QUEUES, SCHEMA,
)

class SyntheticMesen:
    def __init__(self):
        self.frame=0
        self.calls=[]
    def tool(self,kind,**kwargs):
        self.calls.append((kind,kwargs))
        if kind=="input.set":
            return {"ok":True}
        if kind=="run.step_frames":
            if kwargs.get("reset"):self.frame=0
            self.frame+=kwargs["frames"]
            return {"status":{"frame":self.frame}}
        if kind=="run.status":
            return {"frame":self.frame}
        if kind=="cpu.read_memory":
            mem=kwargs["memoryType"]
            if mem not in ({r[0] for r in REGIONS.values()} | {RIDER_WRAM_MEMORY_TYPE}):
                raise ValueError(mem)
            at,n=kwargs["address"],kwargs["length"]
            return {"memoryType":mem,"address":at,"length":n,
                    "bytes":[(at+i+self.frame+(7 if mem==RIDER_WRAM_MEMORY_TYPE else 0))&255
                             for i in range(n)]}
        raise AssertionError(kind)


class OriginalWramFieldTests(unittest.TestCase):
    def test_le16_signedness_endian_and_bounds(self):
        contents=bytearray(RIDER_WRAM_SIZE)
        contents[0x0F83:0x0F85]=b"\xff\x7f"
        contents[0x0F8F:0x0F91]=b"\x00\x80"
        a=read_word_le(bytes(contents),0x0F83)
        self.assertEqual(a["unsigned_16bit"],32767)
        self.assertEqual(a["signed_16bit"],32767)
        self.assertEqual(a["raw_le16_hex"],"7fff")
        b=read_word_le(bytes(contents),0x0F8F)
        self.assertEqual(b["unsigned_16bit"],32768)
        self.assertEqual(b["signed_16bit"],-32768)
        self.assertEqual(b["raw_le16_hex"],"8000")
        for at in (-1,RIDER_WRAM_SIZE-1,RIDER_WRAM_SIZE,True):
            with self.assertRaises(ValueError):
                read_word_le(bytes(contents),at)
        with self.assertRaises(ValueError):
            read_word_le(bytes(contents[:-1]),0)

    def test_candidate_field_names_queue_slices_and_nonclaims(self):
        data=bytearray(RIDER_WRAM_SIZE)
        data[0x0306]=1
        data[0x0F49:0x0F4B]=b"\x2a\x00"
        data[0x15A1:0x15A3]=b"\xff\xff"
        obs=interpret_raw(bytes(data))
        fields=obs["candidate_original_ram_fields"]
        self.assertEqual(set(CANDIDATE_WORDS).issubset(fields),True)
        self.assertEqual(fields["tile_DMA_pending_0306"]["unsigned_8bit"],1)
        self.assertEqual(fields["current_rider_angle_workspace_0f49"]["unsigned_16bit"],42)
        queues=obs["candidate_transfer_list_byte_slices"]
        self.assertEqual(set(queues),set(QUEUES))
        self.assertEqual(queues["source_bank_15a1"]["first_ffff_word_index_or_null"],0)
        self.assertEqual(queues["source_bank_15a1"]["first_four_raw_u16_hex"][0],"ffff")
        for value in queues.values():
            self.assertEqual(value["byte_length"],162)
            self.assertEqual(len(value["sha256"]),64)
        with self.assertRaises(ValueError):
            interpret_raw(bytes(data[:-1]))

    def test_exact_capture_manifest_and_bytes_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            fake=SyntheticMesen()
            report=capture_states(fake,[],0,1,root,
                include_rider_wram_full=True,source_capture_ticks=(2,5))
            (root/"manifest.json").write_text(json.dumps(report),encoding="utf-8")
            result=audit_directory(root)
            self.assertEqual(result["schema"],SCHEMA)
            self.assertEqual(result["actual_observed_bridge_tick_list"],[2,5])
            self.assertTrue(result["original_Wram_snapshot_is_post_frame_not_writer_execution_trace"])
            self.assertTrue(result["source_DMA_list_may_have_been_consumed_before_snapshot"])
            self.assertFalse(result["verified_original_CPU_DMA_writer_PC"])
            self.assertFalse(result["verified_original_1994_wheel_rotation_degree_mapping"])
            self.assertFalse(result["verified_original_1994_3d_rig_pose"])
            self.assertFalse(result["owner_art_likeness_approved"])
            for row in result["source_rows"]:
                self.assertEqual(len(row["exact_original_wram_span_sha256"]),64)
                self.assertEqual(len(row["candidate_original_ram_fields"]),len(CANDIDATE_WORDS)+1)
            file=root/report["frames"][0]["original_snes_rider_work_ram_0000_17ff"]["relative_file"]
            raw=bytearray(file.read_bytes())
            raw[0x0F83]^=1
            file.write_bytes(raw)
            with self.assertRaisesRegex(ValueError,"SHA"):
                audit_directory(root)

    def test_absent_optional_wram_is_not_silent_success(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            record=capture_states(SyntheticMesen(),[],0,1,root)
            (root/"manifest.json").write_text(json.dumps(record),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"opt-in"):
                audit_directory(root)


if __name__=="__main__":
    unittest.main()
