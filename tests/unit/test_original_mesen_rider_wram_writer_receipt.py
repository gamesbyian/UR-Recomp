"""ROM-free integrity and causal-boundary checks for real original Mesen rider trace."""
import hashlib
import json
from pathlib import Path
import unittest
from tools.art.mesen_rider_wram_probe import WORDS, validate, validate_recent_writes

ROOT=Path(__file__).resolve().parents[2]
PATH=ROOT/"analysis/data/racer-original-mesen-rider-wram-queue-writers-eight-20261103.json"
BLOB_SHA1="95daf2e1f11ffbe1e8f4e37dc73cd91e17a0bdcc"
TICKS=[1601,1602,1603,1605,1606,1609,1610,1624]
PHASES=[5,8,11,16,19,4,7,22]
ORIENTATIONS=[61,60,60,60,60,60,60,60]
P1=[1401,121,441,1018,1338,698,954,442]
P2=[381,572,764,1084,1276,316,508,1468]

class OriginalRiderExecutedTraceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=PATH.read_bytes()
        cls.receipt=json.loads(cls.raw)

    def test_exact_github_blob_bytes_and_source_provenance(self):
        raw=self.raw
        self.assertNotIn(b"\r",raw)
        blob=b"blob "+str(len(raw)).encode()+b"\0"+raw
        self.assertEqual(hashlib.sha1(blob).hexdigest(),BLOB_SHA1)
        r=self.receipt
        self.assertEqual(r["schema"],"UR-ART4K-EXECUTED-MESEN-RIDER-WRAM-DMA-CALLBACK-8TICKS/1")
        self.assertEqual(r["source_workflow_run_id"],41773225199)
        self.assertEqual(r["source_workflow_job_id"],126387503637)
        self.assertEqual(r["source_workflow_execution_head"],"58952694a712338f39c63d19aac4614f400e2119")
        self.assertEqual(r["source_original_rom_sha256"],"859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478")
        self.assertEqual(r["original_selected_bridge_ticks"],TICKS)
        for flag in ("WRAM_active_rider_context_alone_proves_P2_geometry",
                     "source_callback_frame_equals_PPU_held_sample_frame",
                     "source_specific_CPU_to_original_64px_racer_vram_tile_ownership_verified",
                     "original_3D_articulated_skeleton_camera_or_pose_recovered",
                     "owner_likeness_approved"):
            self.assertFalse(r[flag])

    def test_observed_original_phase_angle_and_graphics_ID_exact_matches(self):
        rows=self.receipt["rows"]
        self.assertEqual([row["tick"] for row in rows],TICKS)
        self.assertEqual(len(rows),8)
        for i,row in enumerate(rows):
            wr=row["WRAM"]
            phase=wr["selected_rider_animation_phase_0f83"]
            angle=wr["selected_rider_orientation_0f77"]
            self.assertEqual((phase,angle),(PHASES[i],ORIENTATIONS[i]))
            self.assertEqual(wr["selected_rider_graphics_id_0f97"],phase*64+angle)
            self.assertEqual(wr["p1_queued_graphics_id_0fe9"],P1[i])
            self.assertEqual(wr["p2_queued_graphics_id_0feb"],P2[i])
            self.assertEqual(wr["selected_rider_graphics_id_0f97"],P2[i])
            self.assertEqual(wr["dma_queue_pending_0306"],1)
            self.assertEqual(wr["first_dma_source_bank_15a1"],39)
            self.assertEqual(wr["first_dma_vram_destination_16e9"],0x6020)
            self.assertIn(wr["first_dma_source_address_1645"],(0xD440,0xD5C0))
            validate({"original_bridge_tick":row["tick"],"memory_type":"snesWorkRam",
                      "source_raw_22_bytes_sha256":row["WRAM_SHA256"],
                      "source_unattributed_selected_rider_registers":True,
                      "source_dma_queue_may_be_cleared_by_NMI":True,
                      "original_specific_CPU_writer_PC_verified":False,
                      "original_3D_geometry_camera_or_pose_recovered":False,
                      "source_u16_le":wr},row["tick"])

    def test_actual_rom_writer_callback_PC_events_are_bounded(self):
        expected_pc={
            ("dma_pending_0306","$82:B8BA"),("dma_pending_0306","$83:F295"),
            ("selected_graphics_0f97","$83:EF0F"),
            ("p1_graphics_0fe9","$82:8E72"),("p2_graphics_0feb","$82:9360"),
            ("first_dma_source_address_1645","$83:F21D"),
            ("first_dma_bank_15a1","$83:F22A"),
            ("first_dma_vram_destination_16e9","$83:F26E"),
        }
        for row in self.receipt["rows"]:
            events=row["writer_events"]
            self.assertEqual(len(events),20)
            self.assertTrue(all(e["bridge_callback_frame"]==row["tick"]-1 for e in events))
            observed={(e["watched_source_word"],e["source_CPU_PC"]) for e in events}
            self.assertTrue(expected_pc.issubset(observed))
            validate_recent_writes({
                "original_bridge_capture_tick":row["tick"],
                "watch_event_buffer_retention_may_drop_earlier_events":True,
                "callback_frame_to_held_PPU_snapshot_phase_independently_aligned":False,
                "events":events},row["tick"])

    def test_no_inference_of_1994_original_3d_degrees_or_owner_acceptance(self):
        r=self.receipt
        self.assertTrue(r["observed_ordinary_phase_orientation_index_matches_all_samples"])
        self.assertTrue(r["observed_selected_graphics_id_equals_P2_queued_at_all_samples"])
        self.assertTrue(r["source_specific_CPU_WRAM_writer_callbacks_observed"])
        self.assertFalse(r["original_3D_articulated_skeleton_camera_or_pose_recovered"])
        self.assertEqual(len(WORDS),11)

if __name__=="__main__":
    unittest.main()
