"""Adversarial crosswalk checks on retained real source-backed QA-08 handoffs."""
from pathlib import Path
import tempfile
import unittest

from tools import check_qa08_channel5_source_to_pixel as subject

ROOT = Path(__file__).resolve().parents[2] / "analysis" / "data"
PATHS = (
    "qa08-original-2p-channel5-executed-opcode-table-layout.json",
    "qa08-original-snes9x-2p-channel5-eighteen-writer-PCs.json",
    "qa08-original-native-channel5-hdma-coldata-source-handoff.json",
    "qa08-2p-original-native-text26-obj-palette-fingerprint.json",
)


def reference():
    return [subject.read(ROOT / p) for p in PATHS]


class OriginalNativeColourCrosswalkTests(unittest.TestCase):
    def test_genuine_source_to_live_colour_and_26_pixels(self):
        report = subject.check(*reference())
        self.assertEqual(report["original_executed_WRAM_store_count"], 18)
        self.assertEqual(report["native_live_COLDATA_writes"], 7)
        self.assertEqual(report["observed_native_row50_live_fixed_RGB15"], "0x000F")
        self.assertEqual(report["observed_native_row162_live_fixed_RGB15"], "0x0260")
        self.assertTrue(report["final_RGB5_26_pixel_fingerprint_revalidated"])
        self.assertFalse(report["source_CPU_journal_is_live_HDMA"])
        self.assertFalse(report["original_native_same_input_frame_parity_proven"])

    def test_original_writer_byte_target_or_opcode_forgery_fails(self):
        for field, value in (("ROM_instruction_hex", "8F87207E"),
                             ("observed_byte", "2E"),
                             ("original_PC", "82:D5D9")):
            with self.subTest(field=field):
                args = reference()
                args[0]["original_executed_65816_writer_PC_and_WRAM_target"][0][field] = value
                with self.assertRaisesRegex(ValueError, "STA-long|executed"):
                    subject.check(*args)
        args = reference()
        args[0]["original_source_opcode_sequence"][0]["original_PC"] = "82:D5D4"
        with self.assertRaisesRegex(ValueError, "duplicate"):
            subject.check(*args)

    def test_original_table_lookup_or_descriptor_forgery_fails(self):
        args = reference()
        args[0]["original_table_triplets"][2]["line_count_byte"] = "6C"
        with self.assertRaisesRegex(ValueError, "descriptor"):
            subject.check(*args)
        args = reference()
        for row in args[0]["original_source_opcode_sequence"]:
            if row["original_PC"] == "82:D612":
                row["actual_ROM_instruction_hex"] = "F008"
                break
        with self.assertRaisesRegex(ValueError, "lookup"):
            subject.check(*args)

    def test_native_wrong_address_order_or_live_colour_fails(self):
        for field, value in (("A_bus_byte_address", "7E:2085"),
                             ("native_write_log_tag", 114),
                             ("COLDATA_value", "0x21"),
                             ("fixed_RGB15_after_write", "0x0261")):
            with self.subTest(field=field):
                args = reference()
                args[2]["native_writes"][4][field] = value
                with self.assertRaisesRegex(ValueError, "native"):
                    subject.check(*args)

    def test_pixel_claims_and_guest_frame_are_fail_closed(self):
        args = reference()
        args[3]["upper_live_fixed_RGB15"] = "0x0260"
        with self.assertRaisesRegex(ValueError, "pixel"):
            subject.check(*args)
        args = reference()
        args[3]["shade_histogram_each_viewport"][0]["normal_final_RGB5"][0] += 1
        with self.assertRaisesRegex(ValueError, "arithmetic"):
            subject.check(*args)
        args = reference()
        args[2]["native_PPU_2P_guest_frame"] = 2209
        with self.assertRaisesRegex(ValueError, "provenance"):
            subject.check(*args)
        args = reference()
        args[0]["full_original_native_same_input_frame_parity_proven"] = True
        with self.assertRaisesRegex(ValueError, "provenance"):
            subject.check(*args)

    def test_duplicate_keys_are_not_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "forged.json"
            path.write_text('{"schema":"a","schema":"b"}', encoding="utf8")
            with self.assertRaisesRegex(ValueError, "duplicate evidence"):
                subject.read(path)


if __name__ == "__main__":
    unittest.main()
