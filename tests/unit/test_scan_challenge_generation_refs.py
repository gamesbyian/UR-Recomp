import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import scan_challenge_generation_refs as scan  # noqa: E402


class ChallengeGenerationRefScanTests(unittest.TestCase):
    def test_direct_long_reference_classification(self):
        rom = bytes.fromhex(
            "00 00 af d1 10 77 00 "
            "8f d1 10 77 00 "
            "12 d1 10 77 00")
        refs = scan.scan(rom)
        self.assertEqual(len(refs), 3)
        self.assertEqual(refs[0]["mnemonic"], "LDA.l")
        self.assertTrue(refs[0]["recognized_long_address_instruction"])
        self.assertEqual(refs[0]["cpu_address"], "80:8002")
        self.assertEqual(refs[1]["mnemonic"], "STA.l")
        self.assertTrue(refs[1]["recognized_long_address_instruction"])
        self.assertIsNone(refs[2]["mnemonic"])
        self.assertFalse(refs[2]["recognized_long_address_instruction"])


if __name__ == "__main__":
    unittest.main()
