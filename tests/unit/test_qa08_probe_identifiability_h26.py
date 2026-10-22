from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import unittest
from fractions import Fraction
from qa08_probe_identifiability import expanded,predicted,distinguishable,census,interval
class Probe(unittest.TestCase):
 def test_all_32_channels_with_one_count_uncertainty(self):
  self.assertTrue(all(not distinguishable(v,1) for v in range(32)))
 def test_exact_model_gap_is_at_most_one(self):
  self.assertEqual(max(abs(predicted(v,'renderer_14_over_15')-predicted(v,'alternative_187_over_200')) for v in range(32)),1)
 def test_unquantized_max_gap(self):
  self.assertEqual(Fraction(expanded(31),600),Fraction(255,600))
 def test_census_is_explicit_hold(self):
  r=census();self.assertTrue(r['all_single_channel_probes_ambiguous_at_plus_minus_one']);self.assertEqual(r['release_gate_credit'],0)
 def test_bad_inputs(self):
  for v in (-1,32,True,1.5):
   with self.assertRaises(ValueError):expanded(v)
  with self.assertRaises(ValueError):interval(10,-1)
if __name__=='__main__':unittest.main()
