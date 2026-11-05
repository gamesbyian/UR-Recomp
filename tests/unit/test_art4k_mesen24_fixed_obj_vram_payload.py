"""ROM-free exact source original VRAM tilewriter diagnostic checks."""
import hashlib
import json
from pathlib import Path
import unittest

from tools.art.audit_original_mesen24_racer_vram_payload import (
    audit,tile_bytes,SCHEMA,SOURCE_ZIP_SHA,TICKS,ROLES,
)

ROOT=Path(__file__).resolve().parents[2]
REPORT=ROOT/"analysis/data/racer-original-mesen24-fixed-obj-vram-payload-20261103.json"
REPORT_SHA="05c0e44a9143778c15d8119f74931ce65c03b59a638d087f9405f5409c72566c"


class SourceTilePayloadTests(unittest.TestCase):
    def test_4bpp_tile_reads_16_word_addresses_and_wraps_at_7fff(self):
        vram=bytes(i%256 for i in range(65536))
        self.assertEqual(tile_bytes(vram,0),vram[:32])
        self.assertEqual(tile_bytes(vram,0x7fff),
            vram[-2:]+vram[:30])
        for invalid in (b"",bytes(65535)):
            with self.assertRaises(ValueError):
                tile_bytes(invalid,0)
        for addr in (-1,0x8000,0.0,None):
            with self.assertRaises(ValueError):
                tile_bytes(vram,addr)

    def test_canonical_original_source_archive_and_no_3d_or_writer_overclaim(self):
        raw=REPORT.read_bytes()
        self.assertNotIn(b"\r",raw)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),REPORT_SHA)
        r=json.loads(raw)
        self.assertEqual(r["schema"],SCHEMA)
        self.assertEqual(r["original_24tick_source_ZIP_sha256"],SOURCE_ZIP_SHA)
        self.assertEqual(r["original_USA_rom_executed_Mesen_ticks"],list(TICKS))
        self.assertTrue(r["source_prior_register_mode4_base6000_offset1000_assumed_fixed"])
        self.assertFalse(r["source_OBSEL_registers_independently_read_each_new_tick"])
        self.assertTrue(r["original_2d_sprite_changes_explained_by_source_vram_payload_updates_under_stable_tile_addresses"])
        self.assertFalse(r["original_CPU_DMA_PPU_specific_writer_identified"])
        self.assertFalse(r["original_1994_3d_mesh_rig_camera_or_animation_source_recovered"])
        self.assertFalse(r["owner_likeness_approved"])

    def test_fixed_tile_descriptor_and_cgram_but_source_2d_vram_changes_every_tick(self):
        r=json.loads(REPORT.read_bytes())["per_original_source_racer"]
        self.assertEqual(set(r),{"blue","red"})
        for who,record in r.items():
            slot,word,palette=ROLES[who]
            self.assertEqual(record["actual_source_oam_slot"],slot)
            self.assertEqual(record["fixed_oam_source_tileword9"],word)
            self.assertEqual(record["fixed_oam_source_palette_id"],palette)
            self.assertEqual(record["tile_count"],64)
            self.assertEqual(record["backing_4bpp_payload_bytes_per_observation"],2048)
            self.assertEqual(len(record["unique_fixed_original_tile_word_addresses"]),64)
            self.assertEqual(len(set(record["unique_fixed_original_tile_word_addresses"])),64)
            self.assertTrue(record["fixed_source_OAM_large_64px_and_no_flips"])
            self.assertTrue(record["source_relevant_palette_CGRAM_unchanged_24_ticks"])
            self.assertTrue(record["all_23_original_adjacent_source_tile_payloads_change"])
            self.assertTrue(record["all_23_original_adjacent_source_index_planes_change"])
            self.assertEqual(record["source_23_edge_byte_changes_total"],
                             {"blue":1457,"red":1565}[who])
            self.assertEqual(record["source_23_edge_changed_tile_instances_total"],
                             {"blue":122,"red":127}[who])
            edges=record["source_23_edges"]
            self.assertEqual([(e["from_original_bridge_tick"],e["to_original_bridge_tick"])
                              for e in edges],[(n,n+1) for n in range(1601,1624)])
            self.assertEqual(sum(e["source_racer_4bpp_tile_payload_changed_bytes"] for e in edges),
                             record["source_23_edge_byte_changes_total"])
            self.assertEqual(sum(e["source_racer_8x8_tile_payloads_changed"] for e in edges),
                             record["source_23_edge_changed_tile_instances_total"])
            self.assertTrue(all(e["source_racer_4bpp_tile_payload_changed_bytes"]>0 and
                e["source_racer_8x8_tile_payloads_changed"]>0 and
                e["source_index_plane_changed"] and
                e["source_palette_CGRAM_changed_bytes"]==0 for e in edges))
            positions=record["source_OAM_held_positions_by_tick"]
            self.assertEqual([p["tick"] for p in positions],list(TICKS))
            if who=="blue":
                self.assertEqual([p["oam_x"] for p in positions],list(range(82,106)))
                self.assertEqual({p["oam_y"] for p in positions},{151})
            else:
                self.assertEqual({(p["oam_x"],p["oam_y"]) for p in positions},{(48,48)})

    def test_big_upper_source_event_involves_actual_vram_tile_payload_burst(self):
        r=json.loads(REPORT.read_bytes())["per_original_source_racer"]
        for who,event,expected in (
            ("blue",(1602,1603),(253,15)),
            ("red",(1605,1606),(238,15)),
        ):
            relevant=next(x for x in r[who]["source_23_edges"]
                if (x["from_original_bridge_tick"],x["to_original_bridge_tick"])==event)
            self.assertEqual((relevant["source_racer_4bpp_tile_payload_changed_bytes"],
                              relevant["source_racer_8x8_tile_payloads_changed"]),expected)

    def test_wrong_or_absent_original_source_archive_fails_closed(self):
        for invalid in (b"",b"PK\x03\x04"+bytes(200)):
            with self.assertRaisesRegex(ValueError,"exact preserved"):
                audit(invalid)


if __name__=="__main__":
    unittest.main()
