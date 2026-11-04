"""Direct ROM verification and synthetic arithmetic for original rider lookup."""
import unittest
from pathlib import Path
from tools.art.audit_original_rom_rider_graphics_lookup import (
    ROM_LENGTH, ROM_SHA, FINGERPRINTS, audit, default_index, pointer, rom_offset,
)
import hashlib

ROOT = Path(__file__).resolve().parents[2]
ROM = ROOT / "reference/roms/retail/Uniracers_USA.sfc"

class OriginalRiderLookupTests(unittest.TestCase):
    def test_source_exact_retail_identity_and_27_real_opcode_sites(self):
        data = ROM.read_bytes()
        self.assertEqual(len(data), ROM_LENGTH)
        self.assertEqual(hashlib.sha256(data).hexdigest(), ROM_SHA)
        result = audit(data)
        self.assertEqual(len(FINGERPRINTS), 27)
        self.assertEqual(len(result["source_instruction_fingerprints"]), 27)
        self.assertEqual(result["ordinary_distinct_presentation_indices"], 1536)
        self.assertEqual(result["pointer_entries"], 1536)
        self.assertEqual(result["ordinary_index_formula"], "(phase << 6) + orientation")
        self.assertFalse(result["original_executed_rider_runtime_PC_trace"])
        self.assertFalse(result["original_writer_cause_1994_3D_geometry_approved"])

    def test_six_shifts_do_not_alias_24_phase_64_orientation_pairs(self):
        observed = [default_index(p, a) for p in range(24) for a in range(64)]
        self.assertEqual(len(set(observed)), 1536)
        self.assertEqual(observed, list(range(1536)))
        self.assertEqual(default_index(23,63), 1535)
        for bad in ((-1,0),(24,0),(0,-1),(0,64),(True,0),(1,2.0)):
            with self.assertRaises(ValueError):
                default_index(*bad)

    def test_lorom_translation_and_pointer_bank_offset(self):
        self.assertEqual(rom_offset(0x83,0xED33), 0x1ED33)
        self.assertEqual(rom_offset(0x82,0xB8AB), 0x138AB)
        self.assertEqual(rom_offset(0xA0,0x8000), 0x100000)
        fake = bytearray(ROM_LENGTH)
        fake[0x100000:0x100003] = bytes.fromhex("008000")
        fake[0x100003:0x100006] = bytes.fromhex("188001")
        p0,p1=pointer(bytes(fake),0),pointer(bytes(fake),1)
        self.assertEqual(p0["source_bank"],"23")
        self.assertEqual(p0["source_address"],"8000")
        self.assertEqual(p1["source_bank"],"24")
        self.assertEqual(p1["source_address"],"8018")
        self.assertEqual(pointer(bytes(fake),1535)["table_address"],"20:91FD")
        for bad in (-1,1536,True):
            with self.assertRaises(ValueError):
                pointer(bytes(fake),bad)
        for bank,addr in ((0x83,0x7000),(0x80,0),(0xFF,0xFFFF)):
            with self.assertRaises(ValueError):
                rom_offset(bank,addr)

    def test_wrong_source_data_cannot_pass_audit(self):
        for payload in (b"",bytes(ROM_LENGTH),bytes(10)):
            with self.assertRaisesRegex(ValueError,"wrong original USA ROM identity"):
                audit(payload)

if __name__ == "__main__":
    unittest.main()
