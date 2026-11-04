"""Check exact captured original DMA queue vs source OAM tile locations without ROM replay."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
PATH=ROOT/"analysis/data/racer-original-mesen-rider-queue-vram-tile-mapping-eight-20261103.json"
BLOB="e1102a691ac6e5da738187ac83fb69afed6f1497"
TICKS=[1601,1602,1603,1605,1606,1609,1610,1624]
BLUE=[14,15,15,15,15,15,15,15]
RED=[13,13,13,15,15,15,15,15]

class OriginalRiderQueueMappingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=PATH.read_bytes()
        cls.report=json.loads(cls.raw)

    def test_source_log_blob_and_provenance(self):
        raw=self.raw
        self.assertNotIn(b"\r",raw)
        self.assertEqual(hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest(),BLOB)
        r=self.report
        self.assertEqual(r["schema"],"UR-ART4K-EXECUTED-MESEN-RIDER-QUEUED-32B-TILES-TO-ORIGINAL-OBJS/1")
        self.assertEqual(r["source_original_Mesen_workflow_run"],41774019061)
        self.assertEqual(r["source_original_Mesen_job"],126390044838)
        self.assertEqual(r["original_workflow_execution_head"],"23a82d36c514347fae0e3d32844927a575b184c8")
        self.assertEqual(r["original_24tick_ppu_source_ZIP_sha256"],"28dda3647fecb382fdbf824da7383a8116080df6ec8c98da0b3357a018986cf6")
        self.assertEqual(r["source_independent_OAM_tile_address_report_SHA256"],"05c0e44a9143778c15d8119f74931ce65c03b59a638d087f9405f5409c72566c")
        self.assertFalse(r["original_queue_source_32byte_payload_written_to_observed_PPU_at_exact_phase_independently_verified"])
        self.assertFalse(r["original_queue_P1_P2_graphics_ID_to_OAM96_97_source_colour_resolved"])
        self.assertFalse(r["original_1994_3D_mesh_skeleton_camera_physical_angle_recovered"])
        self.assertFalse(r["owner_art_approved"])

    def test_64_authenticated_racer_tile_addresses_are_separate(self):
        r=self.report
        for name,base in (("source_1994_original_OAM96_blue_tile_words",0x6880),
                          ("source_1994_original_OAM97_red_tile_words",0x6000)):
            self.assertEqual(r[name],sorted(base+0x100*y+0x10*x
                                             for y in range(8) for x in range(8)))
            self.assertEqual(len(set(r[name])),64)
        self.assertFalse(set(r["source_1994_original_OAM96_blue_tile_words"]) &
                         set(r["source_1994_original_OAM97_red_tile_words"]))

    def test_all_233_queued_tile_destinations_map_after_original_nmi_flag(self):
        r=self.report
        blue=set(r["source_1994_original_OAM96_blue_tile_words"])
        red=set(r["source_1994_original_OAM97_red_tile_words"])
        rows=r["rows"]
        self.assertEqual([x["original_bridge_tick"] for x in rows],TICKS)
        self.assertEqual([x["source_queue_32_byte_graphics_destinations_by_role"]["blue_OAM96"]
                          for x in rows],BLUE)
        self.assertEqual([x["source_queue_32_byte_graphics_destinations_by_role"]["red_OAM97"]
                          for x in rows],RED)
        self.assertEqual(sum(x["source_queue_transfer_count"] for x in rows),233)
        self.assertEqual(r["source_1994_original_NMI_destination_flag_bit"],0x80)
        self.assertEqual(r["source_1994_original_NMI_destination_plus_words_if_flag"],0x800)
        for row in rows:
            entries=row["source_queue_entries"]
            self.assertEqual(row["source_queue_transfer_count"],len(entries))
            self.assertEqual(row["source_QUEUE_terminator_index"],len(entries))
            self.assertEqual(row["source_queue_32_byte_graphics_destinations_by_role"]["unclassified"],0)
            self.assertEqual(len(row["source_queue_entry_role_sequence"]),len(entries))
            for i,e in enumerate(entries):
                self.assertEqual(e["entry"],i)
                raw=e["vram_destination_word"]
                corrected=raw+(0x800 if raw&0x80 else 0)
                self.assertEqual(e["source_vram_dest_after_nmi_flag_rule"],corrected)
                if corrected in blue:
                    self.assertEqual(e["source_OAM_64px_tile_region"],"blue_OAM96")
                    self.assertNotEqual(raw&0x80,0)
                else:
                    self.assertIn(corrected,red)
                    self.assertEqual(e["source_OAM_64px_tile_region"],"red_OAM97")
                    self.assertEqual(raw&0x80,0)

    def test_original_nmi_queue_pattern_is_consistent_with_both_players(self):
        rows=self.report["rows"]
        self.assertEqual(rows[0]["source_queue_entry_role_sequence"],
                         "RRBBBRRRBBRRRBBBRRRBBBRRBBB")
        for row in rows[3:]:
            self.assertEqual(row["source_queue_entry_role_sequence"],"RRRBBB"*5)
        self.assertTrue(self.report["original_queued_writes_to_racer_tile_region_covered_all_selected_frames"])

if __name__=="__main__":
    unittest.main()
