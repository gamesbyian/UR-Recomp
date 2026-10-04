import unittest
from pathlib import Path
from tools.check_s2_desktop_digest_reference import check
ROOT=Path(__file__).resolve().parents[2]
class TestS2DesktopDigestReference(unittest.TestCase):
    def test_contract(self):
        self.assertEqual(check(ROOT), [])
if __name__=="__main__":
    unittest.main()
