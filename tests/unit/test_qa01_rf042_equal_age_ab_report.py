"""RF042 A/B data gate rejects absent tie/opcode and incomplete whole WRAM."""
import sys,tempfile,unittest,zipfile,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf042_equal_age_ab_report as m
class Trial(unittest.TestCase):
 def make(self,path,trial=True,original_hash="A",marker=True):
  samples=[{"race_relative_frame":i,
    "original_native_full_wram_byte_difference":{
     "original_wram_sha256":original_hash,
     "native_wram_sha256":("B" if trial and i==1 else "A"),
     "differing_byte_count":(1 if trial and i==1 else 0)}}
     for i in range(78)]
  mesh={"mesh_checkpoint_count":78,"masked_or_excluded_wram_bytes":0,
        "samples":samples,"raw_byte_exact_sample_count":77 if trial else 78,
        "late_direct_page_window":{}}
  prod={"source_sram_sha256":"seed","zoo_race_mesh":mesh,
        "zoo_next_bowl_handoff":{},"source_terminal_followthrough":{}}
  orig="\n".join([
   "QA01RF037ORIGCPU2 bucket=38 age=103919450 v=116 h=442 port=2 val=24",
   *[f"QA01RF040ORIGCPU v=116 h={508+52*i} age=1039194{i} port=2 value={('23' if i<5 else '24')}"
     for i in range(6)]])
  native=[
   "QA01RF037NATIVEUP kind=rtl-apu-enter frame=6091 master=2176886834 reg=2142 val=24 scope=x",
   "QA01RF037NATIVEBUS kind=spc-read frame=6091 age=103919434 target=103919434 pc=154F port=2 val=23 q=1"]
  if marker:native.append("QA01RF042TIE frame=6091 age=103919434 pc=154F phase=after-opcode port=2 value=24")
  for i,val in enumerate(("23","23","24")):
   native.append(f"QA01RF038NATIVEPACE frame=6091 master={2176886940+52*i} op=read8 bank=80 addr=2142 charge=6 scope=x")
   native.append(f"QA01RF040NATIVECPU frame=6091 age={103919439+i} pc=154F port=2 raw={val} returned={val}")
  native.append("QA01RF037NATIVEUP kind=rtl-apu-enter frame=6091 master=2176887208 reg=2143 val=02 scope=x")
  with zipfile.ZipFile(path,"w") as z:
   for name,val in [
     ("producer-report.json",prod),("case-result.json",{"source_sha":"frozen","disposition":"strict_candidate","release_credit":0})]:
     z.writestr(name,json.dumps(val))
   z.writestr(m.REF,orig+"\n")
   z.writestr(m.NATIVE,"\n".join(native)+"\n")
 def test_identical_source_and_real_tie_report_only(self):
  with tempfile.TemporaryDirectory() as d:
   a,b=Path(d)/"a.zip",Path(d)/"b.zip"
   self.make(a,False);self.make(b,True)
   r=m.report(a,b)
   self.assertTrue(r["original_all_78_sha256_snapshots_equal"])
   self.assertEqual(r["trial_unmasked_different_byte_occurrences"],1)
   self.assertEqual(r["native_paced_return_values"],["23","23","24"])
   self.assertEqual(r["complete_usa_events_accepted"],0)
   self.assertFalse(r["source_qualified_windows_timing_fix_authorized"])
 def test_reject_missing_tie_or_drifting_source(self):
  with tempfile.TemporaryDirectory() as d:
   a,b=Path(d)/"a.zip",Path(d)/"b.zip"
   self.make(a,False);self.make(b,True,marker=False)
   with self.assertRaisesRegex(ValueError,"tie trial"):
    m.report(a,b)
   self.make(b,True,original_hash="changed")
   with self.assertRaisesRegex(ValueError,"original baseline drifted"):
    m.report(a,b)
if __name__=="__main__":unittest.main()
