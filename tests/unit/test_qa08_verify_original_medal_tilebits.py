"""Original sprite 4bpp production parser negative and source 16x16 checks."""
import sys
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import qa08_verify_original_medal_tilebits as x


class SourceOriginalFourBppVerifierTest(unittest.TestCase):
    def test_stable_source_contract_dimensions_slots_and_registration(self):
        self.assertEqual(x.CALLBACKS,(4031,4175))
        self.assertEqual(x.SLOTS,(96,97,98,99,112,113,114))
        self.assertEqual(x.COORDS,((207,91),(205,115),(205,139),(225,96),(225,120)))
        self.assertEqual(x.NAME[4031][98],0xe6)
        self.assertEqual(x.NAME[4175][98],0xe2)
    def test_invalid_partial_duplicate_or_outside_bpp_log_fails_closed(self):
        for text in ("", "QA08_ORIGINAL_4BPP_REJECT callback=4031\n",
                     "QA08_ORIGINAL_TILE_SOURCE cb=4031 slot=112",
                     "QA08_ORIGINAL_TILE_SAMPLE cb=4031 x=207 y=91 s112=outside"):
            with self.subTest(text=text),self.assertRaises(ValueError):
                x.parse_records(text)
        with self.assertRaises(ValueError):
            x.fields("QA08_ORIGINAL_TILE_SOURCE cb=1 cb=2","QA08_ORIGINAL_TILE_SOURCE")
        with self.assertRaises(ValueError):
            x.fields("QA08_ORIGINAL_TILE_SOURCE junk-noequals","QA08_ORIGINAL_TILE_SOURCE")
    def test_original_refuses_unpinned_source_without_reading_rom_or_vram(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as folder:
            bad=Path(folder)/"fake.zip";bad.write_bytes(b"not the 2014 source ZIP")
            with self.assertRaisesRegex(ValueError,"foreign original"):
                x.verify(Path(folder),bad)
if __name__=="__main__":
    unittest.main()
