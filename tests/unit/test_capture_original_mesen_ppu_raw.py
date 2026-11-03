"""ROM-free synthetic original-emulator SNES PPU evidence controls."""
import copy
from pathlib import Path
import tempfile
import unittest

from tools.art.capture_original_mesen_ppu_raw import (
    REGIONS, SCHEMA, capture_states, read_region, valid_bytes,
    validate_snapshot_files,
)


class FakeMesen:
    def __init__(self):
        self.frame=0
        self.events=[]
    def tool(self,kind,**arguments):
        self.events.append((kind,dict(arguments)))
        if kind=="input.set":
            return {"ok":True}
        if kind=="run.step_frames":
            if arguments.get("reset"):
                self.frame=0
            self.frame+=arguments["frames"]
            return {"status":{"frame":self.frame}}
        if kind=="run.status":
            return {"frame":self.frame}
        if kind=="cpu.read_memory":
            address=arguments["address"]
            length=arguments["length"]
            mem=arguments["memoryType"]
            if mem not in {v[0] for v in REGIONS.values()}:
                raise AssertionError("invalid memory region")
            return {"memoryType":mem,"address":address,"length":length,
                    "bytes":[(address+i+self.frame+(20 if mem=="snesSpriteRam" else 50 if mem=="snesCgRam" else 0))&255
                             for i in range(length)]}
        raise AssertionError("unexpected emulator tool "+kind)


class OriginalMesenRawPpuTests(unittest.TestCase):
    def test_all_three_exact_raw_memory_regions_and_real_stepped_frames(self):
        fake=FakeMesen()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            report=capture_states(fake,[],3,2,root)
            self.assertEqual(report["schema"],SCHEMA)
            self.assertEqual([x["emulator_bridge_frame"] for x in report["frames"]],[4,5])
            self.assertEqual(report["actual_raw_SNES_sprite_RAM_VRAM_CGRAM_snapshots"],2)
            validate_snapshot_files(root,report)
            for row in report["frames"]:
                self.assertEqual(set(row["raw_original_snes_ppu_memory"]),set(REGIONS))
                self.assertFalse(report["live_original_per_player_64x64_alpha_composition_verified"])
                for name,(_,size) in REGIONS.items():
                    self.assertEqual(row["raw_original_snes_ppu_memory"][name]["byte_size"],size)
            chunks=[x for x in fake.events if x[0]=="cpu.read_memory"]
            self.assertEqual(len(chunks),2*(1+64+1))
            self.assertTrue(all(x[1]["length"]<=1024 for x in chunks))
            self.assertEqual(len([x for x in fake.events if x[0]=="run.step_frames"]),5)

    def test_byte_span_types_and_length_are_enforced(self):
        good={"memoryType":"snesSpriteRam","address":0,"length":3,"bytes":[0,12,255]}
        self.assertEqual(valid_bytes(good,"snesSpriteRam",0,3),bytes([0,12,255]))
        for key,value in (("bytes",[0,2,256]),("bytes",[0,False,2]),
                          ("address",1),("memoryType","snesVideoRam"),("length",2)):
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,"source|PPU|physical|span"):
                valid_bytes({**good,key:value},"snesSpriteRam",0,3)

    def test_strict_reader_rejects_wrong_byte_source(self):
        class Wrong(FakeMesen):
            def tool(self,kind,**arguments):
                if kind=="cpu.read_memory":
                    return {"bytes":[0],"memoryType":arguments["memoryType"],
                            "address":arguments["address"],"length":arguments["length"]}
                return super().tool(kind,**arguments)
        with self.assertRaisesRegex(ValueError,"non-physical"):
            read_region(Wrong(),"snesCgRam",512)

    def test_actual_binary_tamper_nonconsecutive_and_absent_ppu_region_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            report=capture_states(FakeMesen(),[],1,2,root)
            tampered=copy.deepcopy(report)
            tampered["frames"][1]["emulator_bridge_frame"]+=2
            with self.assertRaisesRegex(ValueError,"sequence"):
                validate_snapshot_files(root,tampered)
            tampered=copy.deepcopy(report)
            del tampered["frames"][0]["raw_original_snes_ppu_memory"]["cgram"]
            with self.assertRaisesRegex(ValueError,"sequence"):
                validate_snapshot_files(root,tampered)
            path=root/report["frames"][0]["raw_original_snes_ppu_memory"]["oam"]["relative_file"]
            data=bytearray(path.read_bytes())
            data[0]^=1
            path.write_bytes(data)
            with self.assertRaisesRegex(ValueError,"SHA"):
                validate_snapshot_files(root,report)

    def test_does_not_accept_reusing_existing_capture_folder(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            capture_states(FakeMesen(),[],0,1,root)
            with self.assertRaisesRegex(ValueError,"fresh empty"):
                capture_states(FakeMesen(),[],0,1,root)


if __name__=="__main__":
    unittest.main()
