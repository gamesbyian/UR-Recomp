"""RF043 first Zoo 01ED..01F1 writer window is anchored in complete raw WRAM."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf043_zoo_first_stack_window as m

FRAMES=(0,1,2,4,8,16,32,64,120,217,218,219,240,360,480,600,603,604,
605,720,840,841,842,960,1080,1200,1320,1440,1531,1532,1533,1560,
1680,1720,1721,1722,1800,1920,2040,2160,2280,2400,2520,2640,
2760,2880,3000,3120,3240,3360,3480,3600,3720,3840,3960,4080,
4200,4320,4440,4560,4680,4800,4920,5034,5035,5036,5037,5038,
5039,5040,5041,5042,5043,5044,5045,5046,5100,5120)
FOUR=(1,2,4,32,219,604,840,841,1080,1531,1532,1720,1721,1800,
2160,2520,2880,3120,3600,4920)
TWO=(5034,5035,5036,5037,5038)
SOUND=(5040,5045)
class FirstStack(unittest.TestCase):
 def fixture(self):
  assert len(FRAMES)==78
  samples=[]
  for fr in FRAMES:
   add=m.STACK4 if fr in FOUR else (m.STACK2 if fr in TWO else
       (m.SOUND1 if fr in SOUND else ()))
   sample={
    "race_relative_frame":fr,
    "original_absolute_host_frame":1017+fr,
    "native_absolute_host_frame":1017+fr,
    "original_native_full_wram_byte_difference":{
     "full_wram_bytes_per_guest":131072,
     "every_byte_compared":True,
     "excluded_byte_count":0,
     "differing_byte_count":len(add),
     "first_24_differences":[{
        "snes_address":address,"original_byte":38,"native_byte":129}
       for address in add]}}
   samples.append(sample)
  return {"zoo_race_mesh":{
   "mesh_checkpoint_count":78,"masked_or_excluded_wram_bytes":0,
   "raw_byte_exact_sample_count":51,
   "source_original_active_entry_movie_frame":3190,
   "samples":samples}}
 def test_exact_first_frame_and_window_with_zero_admission(self):
  result=m.certify(self.fixture())
  self.assertEqual(result["first_differing_host"],1018)
  self.assertEqual(result["source_movie_active_entry_frame"],3190)
  self.assertEqual(result["stack_differing_byte_occurrences"],90)
  self.assertEqual(result["sound_pointer_differing_byte_occurrences"],2)
  self.assertEqual(result["next_minimal_source_original_native_opcode_NMI_writer_read_window"]["first_causal_transition"],[1017,1018])
  self.assertFalse(result["source_qualified_last_writer_reader_or_NMI_proven"])
  self.assertFalse(result["stack_bytes_safe_to_mask"])
  self.assertEqual(result["accepted_usa_events"],0)
 def test_reject_a_mask_or_an_early_changed_address(self):
  d=self.fixture();d["zoo_race_mesh"]["masked_or_excluded_wram_bytes"]=1
  with self.assertRaisesRegex(ValueError,"unmasked"):m.certify(d)
  d=self.fixture();d["zoo_race_mesh"]["samples"][1]["original_native_full_wram_byte_difference"]["first_24_differences"][0]["snes_address"]="7E:01EC"
  with self.assertRaisesRegex(ValueError,"first Zoo stack"):m.certify(d)
 def test_reject_missing_pairs_and_incomplete_difference_list(self):
  d=self.fixture();d["zoo_race_mesh"]["samples"].pop()
  with self.assertRaisesRegex(ValueError,"per-frame"):m.certify(d)
  d=self.fixture();d["zoo_race_mesh"]["samples"][1]["original_native_full_wram_byte_difference"]["first_24_differences"].pop()
  with self.assertRaisesRegex(ValueError,"incomplete"):m.certify(d)
if __name__=="__main__":unittest.main()
