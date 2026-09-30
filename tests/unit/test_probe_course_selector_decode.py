import unittest
from tools.probe_course_selector_decode import find_calls

class CourseSelectorDecodeTests(unittest.TestCase):
    def test_jsr_is_bank_local_and_jsl_accepts_mirror(self):
        rom=bytearray(bytes([0])*0x10000)
        rom[0x10:0x13]=bytes.fromhex("20 00 90")
        rom[0x20:0x24]=bytes.fromhex("22 00 90 80")
        hits=find_calls(bytes(rom),0,0x9000)
        self.assertEqual([h["kind"] for h in hits],["JSR","JSL-mirror"])

if __name__=="__main__":
    unittest.main()
