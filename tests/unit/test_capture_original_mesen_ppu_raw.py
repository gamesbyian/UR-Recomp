"""ROM-free synthetic original-emulator SNES PPU evidence controls."""
import copy
from pathlib import Path
import tempfile
import unittest

from tools.art.capture_original_mesen_ppu_raw import (
    REGIONS, SCHEMA, capture_states, read_region, valid_bytes,
    validate_snapshot_files, inspect_held_ppm, parse_capture_ticks,
    validate_capture_ticks, RIDER_WRAM_MEMORY_TYPE, RIDER_WRAM_SIZE,
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
            if mem not in ({v[0] for v in REGIONS.values()} | {RIDER_WRAM_MEMORY_TYPE}):
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

    def test_sparse_source_frames_share_one_exact_stepped_replay_and_manifest(self):
        fake=FakeMesen()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            record=capture_states(
                fake,[],0,1,root,source_capture_ticks=(2,5,9),
                source_snes_frame_skipping_disabled_requested=True)
            self.assertEqual(record["source_requested_capture_ticks"],[2,5,9])
            self.assertEqual([f["emulator_bridge_frame"] for f in record["frames"]],
                             [2,5,9])
            self.assertEqual([f["replayed_controller_step_index"] for f in record["frames"]],
                             [1,4,8])
            self.assertEqual(len([a for a in fake.events
                                  if a[0]=="run.step_frames"]),9)
            self.assertEqual(len([a for a in fake.events
                                  if a[0]=="cpu.read_memory"]),3*(1+64+1))
            validate_snapshot_files(root,record)
            changed=copy.deepcopy(record)
            changed["source_requested_capture_ticks"]=[2,5,8]
            with self.assertRaisesRegex(ValueError,"sparse"):
                validate_snapshot_files(root,changed)
            changed=copy.deepcopy(record)
            changed.pop("source_requested_capture_ticks")
            with self.assertRaisesRegex(ValueError,"sequence"):
                validate_snapshot_files(root,changed)
            changed=copy.deepcopy(record)
            changed["source_requested_capture_ticks"]=[2,5,5]
            with self.assertRaisesRegex(ValueError,"sparse"):
                validate_snapshot_files(root,changed)
            changed=copy.deepcopy(record)
            changed["frames"][1]["replayed_controller_step_index"]=2
            with self.assertRaisesRegex(ValueError,"sequence"):
                validate_snapshot_files(root,changed)

    def test_sparse_tick_parser_cannot_accept_duplicate_unsorted_or_unbounded(self):
        self.assertEqual(parse_capture_ticks("1,10,2500"),(1,10,2500))
        self.assertEqual(validate_capture_ticks((1,10,2500)),(1,10,2500))
        for raw in ("",",","0,3","1,1","2,1","1,2501",
                    "-1,2","1.5,2","1, 2","1,,2",
                    ",".join(str(i) for i in range(1,26))):
            with self.subTest(value=raw),self.assertRaises(ValueError):
                parse_capture_ticks(raw)
        for ticks in ([],(0,),(1,1),(2,1),(1,True),(1,2.0),
                      (2501,),tuple(range(1,26))):
            with self.subTest(value=ticks),self.assertRaisesRegex(ValueError,"sparse"):
                validate_capture_ticks(ticks)

    def test_sparse_selection_rejects_empty_or_stale_output_without_work(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            fake=FakeMesen()
            with self.assertRaisesRegex(ValueError,"sparse"):
                capture_states(fake,[],0,1,root,source_capture_ticks=())
            self.assertEqual(fake.events,[])
            root.joinpath("already-here").write_text("do not overwrite")
            with self.assertRaisesRegex(ValueError,"fresh empty"):
                capture_states(fake,[],0,1,root,source_capture_ticks=(2,4))


    def test_manual_original_actions_workflow_accepts_sparse_without_default_drift(self):
        workflow=(Path(__file__).resolve().parents[2] /
                  ".github/workflows/art4k-live-original-mesen-ppu-raw.yml").read_text()
        self.assertIn("      capture_ticks:", workflow)
        self.assertIn('        default: ""', workflow)
        self.assertIn("CAPTURE_TICKS: $" + "{{ github.event_name == 'pull_request' && '1601,1602,1603,1605,1606,1609,1610,1624' || inputs.capture_ticks || '' }}", workflow)
        self.assertIn("RIDER_CAPTURE: $" + "{{ github.event_name == 'pull_request' && '1' || inputs.include_rider_wram && '1' || '0' }}", workflow)
        self.assertIn('rider_args+=(--include-rider-wram)', workflow)
        self.assertIn('print("ART4K_ORIGINAL_RIDER_BOUNDARY"', workflow)
        self.assertIn('selection=(--capture-ticks "$CAPTURE_TICKS")', workflow)
        self.assertIn('selection=(--advance-frames "$ADVANCE_FRAMES" --capture-frames "$CAPTURE_FRAMES")', workflow)
        self.assertIn('parse_capture_ticks(os.environ["CAPTURE_TICKS"])', workflow)
        self.assertIn('assert report["source_requested_capture_ticks"]==desired', workflow)
        self.assertIn('if not sparse and (advance,count)==(1218,2):', workflow)
        self.assertIn('assert "source_requested_capture_ticks" not in report', workflow)
        self.assertIn('MESEN_SNES_DISABLE_FRAME_SKIPPING: "1"', workflow)

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
            report=capture_states(FakeVideoMesen(),[],0,2,root,include_held_framebuffer=True,
                                  source_snes_frame_skipping_disabled_requested=True)
            self.assertTrue(report["original_held_framebuffer_P6_exported"])
            self.assertTrue(report["source_original_snes_frame_skipping_disabled_requested"])
            self.assertFalse(report["original_PPU_RGB_to_source_OBJ_pixel_ownership_verified"])
            self.assertFalse(report["source_held_display_RGB_reproducibility_across_runs_independently_verified"])
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
        self.assertFalse(report["separate_independent_repeatability_cross_check"]["source_held_screen_is_validated_repeatable_PPU_raster"])

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
                          "source_held_display_to_current_PPU_scanout_phase_independently_aligned",
                          "source_held_display_RGB_reproducibility_across_runs_independently_verified"):
                changed=copy.deepcopy(report)
                changed[field]=True
                with self.subTest(field=field),self.assertRaisesRegex(ValueError,"provenance"):
                    validate_snapshot_files(root,changed)
            changed=copy.deepcopy(report)
            changed["frames"][0]["original_emulator_held_display_P6"]["source_display_width"]="2"
            with self.assertRaisesRegex(ValueError,"dimensions"):
                validate_snapshot_files(root,changed)

    def test_original_snes_runner_no_skip_opt_in_and_sanitized_settings(self):
        text=(Path(__file__).resolve().parents[2] /
              "third_party/src/mesen-for-ai/scripts/run_headless.sh").read_text()
        self.assertIn("MESEN_SNES_DISABLE_FRAME_SKIPPING",text)
        self.assertIn('0) SNES_DISABLE_FRAME_SKIPPING_JSON=false ;;',text)
        self.assertIn('1) SNES_DISABLE_FRAME_SKIPPING_JSON=true ;;',text)
        self.assertIn('MESEN_SNES_DISABLE_FRAME_SKIPPING must be 0 or 1',text)
        self.assertIn('"DisableFrameSkipping": $SNES_DISABLE_FRAME_SKIPPING_JSON',text)

    def test_opt_in_rider_wram_same_bridge_ticks_and_exact_span(self):
        fake=FakeMesen()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            report=capture_states(fake,[],0,1,root,
                source_capture_ticks=(2,5),include_rider_wram_full=True,
                source_snes_frame_skipping_disabled_requested=True)
            self.assertEqual([x["emulator_bridge_frame"] for x in report["frames"]],[2,5])
            self.assertTrue(report["source_original_rider_work_ram_0000_17ff_captured"])
            self.assertTrue(report["source_wram_queue_is_post_frame_boundary_not_write_trace"])
            self.assertFalse(report["source_original_CPU_or_DMA_tile_writer_PC_identified"])
            self.assertFalse(report["source_original_1994_3d_pose_recovered_from_wram"])
            validate_snapshot_files(root,report)
            for frame in report["frames"]:
                meta=frame["original_snes_rider_work_ram_0000_17ff"]
                self.assertEqual(meta["byte_size"],RIDER_WRAM_SIZE)
                self.assertEqual(meta["source_memory_type"],RIDER_WRAM_MEMORY_TYPE)
                self.assertEqual(meta["source_offset"],0)
                self.assertEqual(meta["relative_file"],
                    f'frame-{frame["emulator_bridge_frame"]:06d}-wram-0000-17ff.bin')
                self.assertEqual(len((root/meta["relative_file"]).read_bytes()),RIDER_WRAM_SIZE)
            reads=[args for kind,args in fake.events
                   if kind=="cpu.read_memory" and args["memoryType"]==RIDER_WRAM_MEMORY_TYPE]
            self.assertEqual(len(reads),12)
            self.assertEqual([x["address"] for x in reads],
                             list(range(0,RIDER_WRAM_SIZE,1024))*2)

    def test_rider_wram_claims_metadata_and_hash_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            record=capture_states(FakeMesen(),[],0,1,root,include_rider_wram_full=True)
            validate_snapshot_files(root,record)
            for field,value in (
                ("source_original_CPU_or_DMA_tile_writer_PC_identified",True),
                ("source_original_1994_3d_pose_recovered_from_wram",True),
                ("source_wram_queue_is_post_frame_boundary_not_write_trace",False),
                ("source_original_rider_work_ram_0000_17ff_captured",False),
                ("source_original_rider_work_ram_0000_17ff_captured",1),
                ("source_original_rider_work_ram_0000_17ff_captured","true")):
                changed=copy.deepcopy(record)
                changed[field]=value
                with self.subTest(field=field),self.assertRaisesRegex(ValueError,"WRAM|wram"):
                    validate_snapshot_files(root,changed)
            changed=copy.deepcopy(record)
            del changed["source_original_rider_work_ram_0000_17ff_captured"]
            with self.assertRaisesRegex(ValueError,"unclaimed"):
                validate_snapshot_files(root,changed)
            changed=copy.deepcopy(record)
            changed["frames"][0]["original_snes_rider_work_ram_0000_17ff"]["source_offset"]=1
            with self.assertRaisesRegex(ValueError,"identity|metadata"):
                validate_snapshot_files(root,changed)
            file=root/record["frames"][0]["original_snes_rider_work_ram_0000_17ff"]["relative_file"]
            raw=bytearray(file.read_bytes())
            raw[0x0F83]^=1
            file.write_bytes(raw)
            with self.assertRaisesRegex(ValueError,"SHA"):
                validate_snapshot_files(root,record)

    def test_rider_wram_rejects_emulator_advance_and_nonboolean_opt_in(self):
        class Moving(FakeMesen):
            def tool(self,kind,**args):
                out=super().tool(kind,**args)
                if kind=="cpu.read_memory" and args["memoryType"]==RIDER_WRAM_MEMORY_TYPE:
                    self.frame+=1
                return out
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,"advanced during"):
                capture_states(Moving(),[],0,1,Path(d),include_rider_wram_full=True)
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,"bounded"):
                capture_states(FakeMesen(),[],0,1,Path(d),include_rider_wram_full="true")

    def test_optional_wram_workflow_default_and_explicit_dispatch(self):
        workflow=(Path(__file__).resolve().parents[2]/
                 ".github/workflows/art4k-live-original-mesen-ppu-raw.yml").read_text()
        self.assertIn("      include_rider_wram_full:",workflow)
        self.assertIn("  RIDER_FULL_CAPTURE:",workflow)
        self.assertIn("rider_args+=(--include-rider-wram-full)",workflow)
        self.assertIn("github.event_name == 'pull_request'",workflow)
        self.assertIn("        default: false",workflow)

    def test_legacy_raw_capture_no_skip_default_and_invalid_flag(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            record=capture_states(FakeMesen(),[],0,1,root)
            self.assertFalse(record["source_original_snes_frame_skipping_disabled_requested"])
            self.assertFalse(record["original_held_framebuffer_P6_exported"])
            record["source_original_snes_frame_skipping_disabled_requested"]="yes"
            with self.assertRaisesRegex(ValueError,"provenance"):
                validate_snapshot_files(root,record)


if __name__=="__main__":
    unittest.main()
