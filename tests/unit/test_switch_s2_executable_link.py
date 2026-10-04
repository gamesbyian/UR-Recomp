import unittest
from pathlib import Path
from tools.check_switch_s2_executable_link import check
ROOT=Path(__file__).resolve().parents[2]
class TestSwitchS2ExecutableLink(unittest.TestCase):
    def test_contract(self): self.assertEqual(check(ROOT),[])
if __name__=="__main__": unittest.main()
