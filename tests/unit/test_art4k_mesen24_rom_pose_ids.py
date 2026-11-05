"""No ROM, ZIP or 3D runtime required to audit source-bound 48 pose identities."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

from tools.art.recover_original_mesen24_rom_pose_ids import (
    SCHEMA,ROM_SHA,SOURCE_SHA,PRIMARY_IDS,ROW_TILE_INDEXES,
    ROM_CPU_ANCHORS,recover_unique_identity,source_frame_tiles,
    original_code_contract,audit,decode_4bpp_tile8,render_original_primary_sprite64
)

ROOT=Path(__file__).resolve().parents[2]
REPORT=ROOT/"analysis/data/racer-original-mesen24-exact-ROM-pose-IDs-20261103.json"
REPORT_SHA="6286aedcda6080acf832ecece9fcdb879354db008e870bc00ada02db3ff3aa20"

class ExactOriginalRomPoseRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=REPORT.read_bytes()
        cls.data=json.loads(cls.raw)

    def test_immutable_evidence_and_no_original_3d_recovery_overclaim(self):
        self.assertNotIn(b"\r",self.raw)
        self.assertEqual(hashlib.sha256(self.raw).hexdigest(),REPORT_SHA)
        r=self.data
        self.assertEqual(r["schema"],SCHEMA)
        self.assertEqual(r["original_usa_ROM_sha256"],ROM_SHA)
        self.assertEqual(r["original_Mesen24_source_archive_sha256"],SOURCE_SHA)
        self.assertEqual(len(PRIMARY_IDS),1536)
        self.assertEqual(len(ROW_TILE_INDEXES),30)
        self.assertEqual(r["original_usa_rom_EXACT_24_by_64_primary_state_grid"],True)
        self.assertTrue(r["original_rom_1536_distinct_valid_frame_records_verified"])
        self.assertTrue(r["all_48_observed_primary_5x6_sprite_frames_unique_perfect_rom_match"])
        self.assertTrue(r["all_48_original_64x64_source_index_images_pixel_exact_from_ROM"])
        self.assertEqual(r["original_source_64x64_index_pixel_samples_matched_total"],196608)
        self.assertTrue(r["original_source_remaining_34_tiles_per_sprite_zero_index_verified"])
        self.assertTrue(r["original_executed_24_tick_frames_are_exploratory_not_prospective_blind"])
        self.assertFalse(r["original_racer_1994_art_3D_camera_joint_angles_mesh_or_rig_recovered"])
        self.assertFalse(r["2026_candidate_3D_rig_physical_angle_scale_independently_calibrated"])
        self.assertFalse(r["complete_64tile_held_OBJ_graphics_reconstructed_from_primary_5x6_only"])
        anchors=r["original_65816_selected_executable_byte_witnesses"]
        self.assertEqual(set(anchors),set(ROM_CPU_ANCHORS))
        self.assertEqual({len(v["source_code_bytes_sha256"]) for v in anchors.values()},{64})

    def test_exact_all_24_per_player_source_ids_and_unique_30_tiles(self):
        per=self.data["per_original_source_racer"]
        self.assertEqual(set(per),{"blue","red"})
        for player,entry in per.items():
            self.assertEqual(entry["source_original_OAM_slot"],{"blue":96,"red":97}[player])
            self.assertEqual(entry["source_original_OAM_tile_word9"],{"blue":136,"red":0}[player])
            self.assertEqual(entry["source_original_OBJ_palette_id"],{"blue":4,"red":3}[player])
            self.assertEqual(len(entry["original_source_5x6_tile_VRAM_word_addresses"]),30)
            self.assertEqual(len(set(entry["original_source_5x6_tile_VRAM_word_addresses"])),30)
            records=entry["source_24_unique_per_tick_ROM_primary_frame_IDs"]
            self.assertEqual([r["authentic_original_bridge_tick"] for r in records],
                             list(range(1601,1625)))
            self.assertEqual(len(records),24)
            self.assertTrue(entry["all_24_source_primary_frame_IDs_exact_unique_matches"])
            for row in records:
                ident=row["source_primary_frame_id"]
                self.assertEqual(row["source_primary_frame_hex"],f"0x{ident:04X}")
                self.assertEqual(row["source_primary_phase_index"],ident//64)
                self.assertEqual(row["source_primary_angle_index"],ident%64)
                self.assertEqual(row["source_original_ROM_matched_8x8_tile_count"],30)
                self.assertEqual(row["source_original_ROM_candidate_count"],1536)
                self.assertEqual(row["unique_perfect_tile_match_count"],1)
                self.assertLess(row["next_best_nonidentical_ROM_frame_matched_tiles"],30)
                self.assertEqual(len(row["source_selected_960_4bpp_bytes_sha256"]),64)
                self.assertEqual(len(row["source_held_OAM_local_index_plane_sha256"]),64)
                self.assertEqual(row["source_ROM_reconstructed_64x64_index_plane_sha256"],
                                 row["source_held_OAM_local_index_plane_sha256"])
                self.assertEqual(row["source_ROM_exact_source_index_pixel_matches"],4096)

    def test_source_measured_phase_speed_and_angle_changes(self):
        per=self.data["per_original_source_racer"]
        red=per["red"]
        blue=per["blue"]
        self.assertEqual(red["actual_phase_step_histogram"],{"4":10,"5":13})
        self.assertEqual(blue["actual_phase_step_histogram"],{"2":5,"3":18})
        self.assertEqual(red["actual_source_angle_index_histogram"],{"57":5,"58":19})
        self.assertEqual(blue["actual_source_angle_index_histogram"],{"60":22,"61":2})
        samples={
            "blue":{1601:(253,3,61),1603:(572,8,60),1606:(1084,16,60),1624:(1276,19,60)},
            "red":{1601:(1081,16,57),1603:(121,1,57),1606:(1018,15,58),1624:(122,1,58)},
        }
        for name,rows in samples.items():
            records={r["authentic_original_bridge_tick"]:r
                for r in per[name]["source_24_unique_per_tick_ROM_primary_frame_IDs"]}
            for tick,expected in rows.items():
                r=records[tick]
                self.assertEqual((r["source_primary_frame_id"],
                                  r["source_primary_phase_index"],
                                  r["source_primary_angle_index"]),expected)
            phases=[r["source_primary_phase_index"]
                    for r in per[name]["source_24_unique_per_tick_ROM_primary_frame_IDs"]]
            deltas=[(b-a)%24 for a,b in zip(phases,phases[1:])]
            self.assertEqual(deltas,per[name]["actual_source_23_modulo24_phase_steps"])

    def test_unique_exact_lookup_refuses_ambiguity_or_incomplete_source(self):
        blank=b"\0"*32
        altered=b"\1"*32
        single=tuple([altered]+[blank]*29)
        other=tuple([blank]*30)
        candidates=tuple([single]+[other]*1535)
        actual=recover_unique_identity(single,candidates)
        self.assertEqual((actual["source_primary_frame_id"],
                          actual["source_original_ROM_matched_8x8_tile_count"],
                          actual["next_best_nonidentical_ROM_frame_matched_tiles"]), (0,30,29))
        with self.assertRaisesRegex(ValueError,"unresolved"):
            recover_unique_identity(single,tuple([single,single]+[other]*1534))
        with self.assertRaisesRegex(ValueError,"unresolved"):
            recover_unique_identity(tuple([b"\2"*32]+[blank]*29),candidates)
        with self.assertRaisesRegex(ValueError,"exactly 30"):
            recover_unique_identity(tuple([blank]*29),candidates)
        with self.assertRaisesRegex(ValueError,"1536"):
            recover_unique_identity(single,(single,))

    def test_snes_4bpp_tile_and_64px_raster_are_independently_validated(self):
        # Pixel planes 0,1,2,3 represented by the first pixel of each
        # tile row. Each of the sixteen combinations survives reconstruction.
        for value in range(16):
            raw=bytearray(32)
            for bit in range(4):
                if value & (1<<bit):
                    raw[0 if bit==0 else 1 if bit==1 else 16 if bit==2 else 17]=0x80
            pixels=decode_4bpp_tile8(bytes(raw))
            self.assertEqual(pixels[0],value)
            self.assertTrue(all(p==0 for p in pixels[1:]))
        raster=render_original_primary_sprite64(tuple([bytes([0xFF]*32)] +
                                    [bytes(32)]*29))
        self.assertEqual(len(raster),4096)
        self.assertEqual(set(raster[0:8]),{0})
        self.assertEqual(set(raster[8:16]),{15})
        self.assertEqual(set(raster[16:64]),{0})
        self.assertEqual(set(raster[40*64:]),{0})
        with self.assertRaises(ValueError):
            decode_4bpp_tile8(b"invalid")
        with self.assertRaises(ValueError):
            render_original_primary_sprite64(tuple([bytes(32)]*29))

    def test_fails_closed_on_wrong_original_rom_or_source_archive(self):
        with self.assertRaisesRegex(ValueError,"wrong authentic"):
            original_code_contract(bytes(2*1024*1024))
        with self.assertRaisesRegex(ValueError,"wrong original"):
            source_frame_tiles(b"")
        with self.assertRaisesRegex(ValueError,"wrong canonical"):
            audit(bytes(2*1024*1024),b"PK\x03\x04"+"garbage".encode())


if __name__=="__main__":
    unittest.main()
