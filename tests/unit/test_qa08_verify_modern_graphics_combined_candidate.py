"""Candidate SHA and immutable source-archive boundaries, no release waiver."""
import sys
import tempfile
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools import qa08_verify_modern_graphics_combined_candidate as q

class CombinedActualWindowsCandidate(unittest.TestCase):
    def test_package_and_identity_constants(self):
        self.assertEqual(q.SOURCE,"5c5c992ecdc156f638c13a0d6d6c20a3331c52d6")
        self.assertEqual(q.PE_SHA,"1786c474399b245305ba6ab22ff816653ad762ea36d4ac6a4667ec6a74e7ef53")
        self.assertEqual(q.PACKAGE_INNER,"fdd53e041772459e2df3b78275a959d81ca379c1cec48ffc41fa5c2991a122eb")
        self.assertEqual(len(q.ALLOWED),4)
        self.assertNotIn("Uniracers_USA.sfc",q.ALLOWED)
    def test_fake_or_incomplete_archive_cannot_produce_source_acceptance(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/"fabricated.zip"
            f.write_bytes(b"not genuine source")
            with self.assertRaisesRegex(ValueError,"authenticated GitHub artifact"):
                q.verify(f,f)
        with self.assertRaises(Exception):
            q.exact_zip(b"not a zip",{"candidate-binding.json"})
    def test_receipt_prohibits_inferred_release_or_snes_result_parity(self):
        s=(ROOT/"tools/qa08_verify_modern_graphics_combined_candidate.py").read_text()
        self.assertIn('"release_QA_accepted":False',s)
        self.assertIn('"original_2014_RGB5_result_parity_proven":False',s)
        self.assertIn('not physical-pad, release-gate or independent acceptance',s)
        self.assertNotIn("PpuSetOverlayOamRange",s)

if __name__=="__main__":
    unittest.main()
