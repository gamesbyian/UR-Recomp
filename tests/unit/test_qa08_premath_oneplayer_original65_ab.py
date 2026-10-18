"""Negative source guards for 65 actual source callbacks."""
import unittest,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/"tools"))
from tools.qa08_premath_oneplayer_original65_ab import compare,FIRST,LAST,SCRIPT
class Case(unittest.TestCase):
    def test_source_slots(self):
        self.assertEqual(LAST-FIRST+1,65)
        self.assertEqual((FIRST+1,LAST+1),(2177,2241))
        self.assertEqual(len(SCRIPT),64)
    def test_no_missing_real_guest_crc(self):
        with self.assertRaisesRegex(ValueError,"5447"):
            compare(None,Path("/unavailable"),"",[])
        with self.assertRaisesRegex(ValueError,"consecutive"):
            compare(None,Path("/unavailable"),"",["0x00000000"]*5447)
if __name__=="__main__":unittest.main()
