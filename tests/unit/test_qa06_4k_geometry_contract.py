"""ROM-free regression checks for the mathematical 4K presentation reference."""
import json
from pathlib import Path
import subprocess
import sys
import unittest
from fractions import Fraction as F

SCRIPT = Path(__file__).resolve().parents[2] / 'tools' / 'qa06_4k_geometry_contract.py'

class FourKGeometryReference(unittest.TestCase):
    def test_exact_source_geometry_and_par(self):
        p = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True, timeout=15)
        self.assertEqual(p.returncode, 0, p.stderr)
        result = json.loads(p.stdout)
        self.assertEqual(result['assertions_passed'], 9)
        self.assertEqual(result['original']['source'], [256,224])
        self.assertEqual(result['wide']['source'], [342,224])
        self.assertEqual(result['original']['par'], '7/6')
        self.assertEqual(result['wide']['par'], '7/6')
        self.assertIn('not an observed physical output', result['scope'])

    def test_uncropped_4k_physical_margins(self):
        result = json.loads(subprocess.check_output([sys.executable, str(SCRIPT)], text=True))
        self.assertEqual(result['original']['physical_extent_exact'], ['2880','2160'])
        self.assertEqual(result['original']['physical_margins_exact'], ['480','0'])
        self.assertEqual(F(result['wide']['physical_extent_exact'][0]), F(3840))
        self.assertEqual(F(result['wide']['physical_extent_exact'][1]), F(2160))
        self.assertEqual(F(result['wide']['physical_margins_exact'][1]), F(0))

if __name__ == '__main__':
    unittest.main()
