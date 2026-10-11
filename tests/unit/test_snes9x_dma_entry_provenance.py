import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from instrument_snes9x143_dma_entry import patch, MARKER
from report_snes9x_dma_entry_provenance import parse

GOOD = "URDMAPROV frame=2208 v=225 cycles=100 pc=00858E channel=2 bank=7E src=0340 bbus=04 count=0220 mode=0 direction=0 fixed=0 decrement=0"

class DmaEntryProvenanceTests(unittest.TestCase):
    def test_descriptor_and_explicit_unknowns(self):
        report = parse([GOOD])
        self.assertEqual(report["count"], 1)
        row = report["entries"][0]
        self.assertEqual(row["a_bus_source"], "7E:0340")
        self.assertEqual(row["b_bus_name"], "OAMDATA")
        self.assertEqual(row["transfer_count"], 544)
        self.assertFalse(row["ppu_port_address_known"])
        self.assertFalse(row["transfer_completed"])
        self.assertFalse(report["complete_ppu_provenance"])

    def test_overflow_unknown_and_reverse_order_rejected(self):
        self.assertEqual(parse([GOOD.replace("channel=2", "channel=9")])["malformed_lines"], [1])
        self.assertEqual(parse([GOOD.replace("count=0220", "count=0000")])["entries"][0]["transfer_count"], 65536)
        lines = [GOOD, GOOD.replace("cycles=100", "cycles=99")]
        self.assertEqual(len(parse(lines)["order_errors"]), 1)
        self.assertEqual(parse([GOOD, "URDMAPROV nonsense"])["malformed_lines"], [2])

    def test_frame_bounding(self):
        self.assertEqual(parse([GOOD], from_frame=2209)["count"], 0)
        with self.assertRaises(ValueError):
            parse([GOOD], from_frame=2209, to_frame=2208)

    def test_fail_closed_source_patch(self):
        src = "void S9xDoDMA (uint8 Channel)\n{\n    SDMA *d = &DMA[Channel];\n}\n"
        result = patch(src)
        self.assertIn(MARKER, result)
        self.assertEqual(patch(result), result)
        with self.assertRaises(ValueError):
            patch("wrong emulator source")
        with self.assertRaises(ValueError):
            patch(src + src)

if __name__ == "__main__":
    unittest.main()
