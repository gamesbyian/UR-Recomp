"""ROM-free synthetic original-emulator SNES PPU evidence controls."""
import copy
from pathlib import Path
import tempfile
import unittest

from tools.art.capture_original_mesen_ppu_raw import (
    REGIONS, SCHEMA, capture_states, read_region, valid_bytes,
    validate_snapshot_files, inspect_held_ppm,
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

    def test_original_emulator_held_rgb_screen_is_p6_and_source_sha_bound(self):
        class FakeVideoMesen(FakeMesen):
            def tool(self,kind,**arguments):
                if kind=="video.export_frame":
                    path=Path(arguments["path"])
                    path.write_bytes(b"P6\n3 2\n255\n"+bytes([self.frame,20,40])*6)
                    return {"path":str(path),"format":"P6","width":3,"height":2,
                            "pixels":6}
                return super().tool(kind,**arguments)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            report=capture_states(FakeVideoMesen(),[],0,2,root,include_held_framebuffer=True)
            self.assertTrue(report["original_held_framebuffer_P6_exported"])
            self.assertFalse(report["original_PPU_RGB_to_source_OBJ_pixel_ownership_verified"])
            self.assertEqual(len(report["frames"]),2)
            for frame in report["frames"]:
                meta=frame["original_emulator_held_display_P6"]
                self.assertEqual((meta["source_display_width"],meta["source_display_height"]),(3,2))
                self.assertEqual(meta["source_rgb_byte_length"],18)
                self.assertRegex(meta["source_framebuffer_RGB_sha256"],r"\A[0-9a-f]{64}\Z")
            validate_snapshot_files(root,report)
            self.assertNotEqual(
                report["frames"][0]["original_emulator_held_display_P6"]["source_framebuffer_RGB_sha256"],
                report["frames"][1]["original_emulator_held_display_P6"]["source_framebuffer_RGB_sha256"])
            old=report["frames"][0]["original_emulator_held_display_P6"]
            target=root/old["relative_file"]
            corrupt=bytearray(target.read_bytes())
            corrupt[-1]^=1
            target.write_bytes(corrupt)
            with self.assertRaisesRegex(ValueError,"SHA/metadata"):
                validate_snapshot_files(root,report)

    def test_false_video_size_format_and_rgb_length_fail_closed(self):
        raw=b"P6\n2 2\n255\n"+bytes(12)
        ack={"path":"/private/source.ppm","format":"P6","width":2,"height":2,"pixels":4}
        self.assertEqual(inspect_held_ppm(raw,ack,"/private/source.ppm")["source_rgb_byte_length"],12)
        for label,change in (("path",{"path":"/other.ppm"}),
                             ("format",{"format":"P3"}),
                             ("size",{"width":1025,"pixels":2050}),
                             ("count",{"pixels":3}),
                             ("bool",{"width":True,"pixels":2})):
            with self.subTest(label=label),self.assertRaisesRegex(ValueError,"source|video"):
                inspect_held_ppm(raw,{**ack,**change},"/private/source.ppm")
        for bad in (raw[:-1],b"P3"+raw[2:],b"P6\n3 2\n255\n"+bytes(12)):
            with self.assertRaisesRegex(ValueError,"P6"):
                inspect_held_ppm(bad,ack,"/private/source.ppm")

    def test_original_emulator_must_remain_paused_during_screen_export(self):
        class MovingVideo(FakeMesen):
            def tool(self,kind,**arguments):
                if kind=="video.export_frame":
                    path=Path(arguments["path"])
                    path.write_bytes(b"P6\n2 1\n255\n"+bytes(6))
                    self.frame+=1
                    return {"path":str(path),"format":"P6","width":2,"height":1,"pixels":2}
                return super().tool(kind,**arguments)
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,"advanced during held display"):
                capture_states(MovingVideo(),[],0,1,Path(d),include_held_framebuffer=True)

    def test_historic_held_P6_receipt_remains_source_only(self):
        import json
        root=Path(__file__).resolve().parents[2]
        report=json.loads((root/"analysis/data/racer-original-mesen-held-framebuffer-20261103.json").read_text())
        self.assertEqual(report["real_original_emulator_workflow_run"],41565384581)
        self.assertEqual(report["source_original_emulated_bridge_ticks"],[1219,1220])
        self.assertEqual(report["source_screen_P6_dimensions"],{"width":256,"height":239})
        self.assertEqual(report["original_held_display_changed_pixel_count_between_consecutive_ticks"],0)
        self.assertEqual(report["original_raw_PPU_memory_changed_bytes_between_ticks"],
                         {"oam":0,"vram":38,"cgram":17})
        self.assertFalse(report["original_scanout_content_contemporaneous_with_held_PPU_RAM_verified"])
        self.assertFalse(report["original_racer_OBJ_pixel_ownership_reconstructed"])

    def test_held_display_claim_escalation_and_malformed_dimensions_rejected(self):
        class FakeVideo(FakeMesen):
            def tool(self,kind,**arguments):
                if kind=="video.export_frame":
                    path=Path(arguments["path"])
                    path.write_bytes(b"P6\n2 1\n255\n"+bytes(6))
                    return {"path":str(path),"format":"P6","width":2,"height":1,"pixels":2}
                return super().tool(kind,**arguments)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            report=capture_states(FakeVideo(),[],0,1,root,include_held_framebuffer=True)
            for field in ("original_PPU_RGB_to_source_OBJ_pixel_ownership_verified",
                          "source_held_display_to_current_PPU_scanout_phase_independently_aligned"):
                changed=copy.deepcopy(report)
                changed[field]=True
                with self.subTest(field=field),self.assertRaisesRegex(ValueError,"provenance"):
                    validate_snapshot_files(root,changed)
            changed=copy.deepcopy(report)
            changed["frames"][0]["original_emulator_held_display_P6"]["source_display_width"]="2"
            with self.assertRaisesRegex(ValueError,"dimensions"):
                validate_snapshot_files(root,changed)


if __name__=="__main__":
    unittest.main()
