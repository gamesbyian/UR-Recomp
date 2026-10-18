"""Current RF017 guest equality is never inferred from pre-RF017 SHA."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/"tools"))
from tools.qa08_premath_oneplayer_clean_current_guest import compare,full_crc,OLD_GUEST
class TestA(unittest.TestCase):
    def test_old_source_not_equivalence_proof(self):
        self.assertRaisesRegex(ValueError,"5447",full_crc,[])
        x={"schema":"qa08-current-premath-authenticated-Windows-vs-2014-oneplayer-65/1",
           "native_USA_guest_CRC_sha256":"a"*64,
           "actual_Win32_PE_sha256":"b"*64}
        a=compare(x,"c"*64)
        self.assertFalse(a["two_independent_Windows_pe_current_guest_CRC_equal"])
        self.assertEqual(a["old_preRF017_guest_crc_sha256"],OLD_GUEST)
        a=compare(x,"a"*64)
        self.assertTrue(a["two_independent_Windows_pe_current_guest_CRC_equal"])
        self.assertFalse(a["2014_Snes9x_guest_CPU_equivalence_proven"])
if __name__=="__main__":unittest.main()
