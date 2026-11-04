"""ROM-free core guards plus exact checked-in retail-ROM/PPU witness.

Original source ROM and source archive are both repo evidence, not generated mocks.
"""
import hashlib
import json
from pathlib import Path
import unittest

from tools.art.audit_original_rom_rider_phase_dma import (
    ROM_SHA,SOURCE_SHA,SCHEMA,ANCHORS,lorom_offset,verify_rom,
    nmi_effective_vram_word,audit,
)

ROOT=Path(__file__).resolve().parents[2]
ROM=ROOT/"reference/roms/retail/Uniracers_USA.sfc"
SRC=ROOT/"analysis/data/racer-original-mesen-consecutive-1601-1624-20261103.zip"
REPORT=ROOT/"analysis/data/racer-original-usa-rom-phase-dma-source-witness-20261103.json"
REPORT_SHA="538fe21cac2dd5b0e627e75136cda31c451e459ceb6f789ad046d35deb53eeab"


class OriginalRiderROMPhaseDMAEvidenceTests(unittest.TestCase):
    def test_lorom_pc_to_headerless_retail_offset(self):
        self.assertEqual(lorom_offset(0x83,0xED33),0x01ED33)
        self.assertEqual(lorom_offset(0x82,0xB8AB),0x0138AB)
        for bank,pc in ((0x81,0x8000),(0x83,0x7fff),(0x83,0x10000),(3.0,0xED33)):
            with self.assertRaises(ValueError):
                lorom_offset(bank,pc)

    def test_normal_nmi_destination_bit7_selects_second_0x800_word_region(self):
        self.assertEqual(nmi_effective_vram_word(0x6000),0x6000)
        self.assertEqual(nmi_effective_vram_word(0x6070),0x6070)
        self.assertEqual(nmi_effective_vram_word(0x6080),0x6880)
        self.assertEqual(nmi_effective_vram_word(0x60F0),0x68F0)
        self.assertEqual(nmi_effective_vram_word(0x6180),0x6980)
        self.assertEqual(nmi_effective_vram_word(0x7fff),0x07ff)
        for invalid in (-1,0x8000,None,True):
            with self.assertRaises(ValueError):
                nmi_effective_vram_word(invalid)

    def test_actual_original_rom_sha_and_fourteen_machine_code_anchors(self):
        rom=ROM.read_bytes()
        self.assertEqual(hashlib.sha256(rom).hexdigest(),ROM_SHA)
        a=verify_rom(rom)
        self.assertEqual(len(a),14)
        self.assertEqual(set(a),set(ANCHORS))
        self.assertEqual(a["rider_animation_calls_phase_update"]["original_snes_pc"],"83:ED33")
        self.assertEqual(a["modulo_24_original_rider_phase"]["original_snes_pc"],"83:EE53")
        self.assertEqual(a["angle_64_state_mask"]["original_snes_pc"],"83:F054")
        self.assertEqual(a["nmi_vram_destination_selects_second_800_word_region"]["original_snes_pc"],"82:B8F4")

    def test_report_byte_identity_and_all_original_source_constraints(self):
        raw=REPORT.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),REPORT_SHA)
        self.assertNotIn(b"\r",raw)
        j=json.loads(raw)
        self.assertEqual(j["schema"],SCHEMA)
        self.assertEqual(j["retail_original_USA_ROM_sha256"],ROM_SHA)
        self.assertEqual(j["independently_executed_Mesen24_source_zip_sha256"],SOURCE_SHA)
        self.assertEqual(j["original_source_Mesen_bridge_ticks"],list(range(1601,1625)))
        self.assertEqual(j["rider_presentation_phase_modulus_from_original_ROM"],24)
        self.assertEqual(j["rider_angle_index_modulus_from_original_ROM"],64)
        self.assertEqual(j["original_NMI_normal_dma_transfer_bytes_per_entry"],32)
        self.assertEqual(j["original_NMI_bit_7_of_queue_dest_adds_vram_words"],2048)
        self.assertEqual(j["example_queued_dest_red_6000_to_effective_word"],0x6000)
        self.assertEqual(j["example_queued_dest_bit7_6080_to_effective_blue_6880_word"],0x6880)
        self.assertFalse(j["original_DMA_queue_values_at_any_captured_tick_measured"])
        self.assertFalse(j["original_CPU_writer_or_DMA_trigger_PC_captured_at_runtime"])
        self.assertFalse(j["original_1994_3D_mesh_camera_joint_angles_recovered"])
        self.assertTrue(j["original_24_and_64_state_axes_are_representation_indices_not_degrees"])
        self.assertEqual(set(j["per_real_original_source_racer"]),{"blue","red"})
        for who,role in j["per_real_original_source_racer"].items():
            self.assertEqual(role["observed_source_OAM_slot"],{"blue":96,"red":97}[who])
            self.assertEqual(role["source_vram_first_word"],{"blue":0x6880,"red":0x6000}[who])
            self.assertEqual(len(role["actual_source_original_vram_tile_address_words"]),64)
            self.assertEqual(len(set(role["actual_source_original_vram_tile_address_words"])),64)
            self.assertEqual(len(role["actual_held_oam_positions"]),24)

    def test_actual_source_evidence_matches_checked_in_receipt(self):
        # Exactly one whole-archive audit for this unit module, no emulator run.
        result=audit(ROM.read_bytes(),SRC.read_bytes())
        self.assertEqual(result,json.loads(REPORT.read_bytes()))

    def test_tampered_original_rom_and_wrong_source_fail_closed(self):
        original=ROM.read_bytes()
        corrupt=bytearray(original);corrupt[lorom_offset(0x83,0xEE53)]^=1
        with self.assertRaisesRegex(ValueError,"exact"):
            verify_rom(bytes(corrupt))
        with self.assertRaisesRegex(ValueError,"wrong original"):
            audit(original,b"")


if __name__=="__main__":
    unittest.main()
