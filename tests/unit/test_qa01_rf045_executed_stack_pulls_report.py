"""RF045 fail-closed source original NMI macro callsite reader/writer reporter."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf045_executed_stack_pulls_report as m

class AuthenticStack(unittest.TestCase):
 def fixture(self):
  src=[];native=[]
  for i,f in enumerate(m.FRAMES):
   pc="82D4F0" if i%2==0 and f!=1025 else "82D4EE"
   def line(kind,addr,width,val,sp0,sp1):
    return f"QA01RF045ORIGSTACK f={f} v=120 h=800 kind={kind} addr={addr} width={width} value={val} sp0={sp0} sp1={sp1} pc={pc[:2]}:{pc[2:]}"
   src.append(line("pushB","01F0",1,"0082","01F0","01EF"))
   src.append(line("pushW","01EE",2,pc[2:],"01EF","01ED"))
   src.append(line("pushB","01ED",1,"0026","01ED","01EC"))
   src.append(f"QA01RF044ORIGNMI f={f} f1={f} pc={pc} S0=01F0 S1=01EC old=8197005526 new=26{pc[4:6]}{pc[2:4]}{pc[:2]}26")
   for addr,val in zip(m.rf044.FIRST_WRITES,m.rf044.EXPECTED_NATIVE):
    native.append(f"f{f}   00:{addr}={val} w1 (none) rf044_S={addr} IPC=80EFDA")
  return "\n".join(src)+"\n","\n".join(native)+"\n"
 def test_exact_NMI_pushes_without_claiming_unobserved_consumption(self):
  r=m.observe(*self.fixture())
  self.assertEqual(len(r["source_real_NMI_push_macro_groups"]),9)
  self.assertEqual(r["source_actual_stack_macro_rows"],27)
  self.assertEqual(r["source_actual_stack_pull_macro_rows"],0)
  self.assertTrue(r["source_actual_NMI_push_instruction_calls_proven"])
  self.assertFalse(r["NMI_stale_frame_bytes_proven_never_consumed"])
  self.assertEqual(r["USA_accepted_count"],0)
 def test_actual_pull_after_NMI_is_counted_not_overclaimed(self):
  a,b=self.fixture()
  a+="QA01RF045ORIGSTACK f=1025 v=150 h=700 kind=pullB addr=01ED width=1 value=0026 sp0=01EC sp1=01ED pc=82:D4EE\n"
  r=m.observe(a,b)
  self.assertEqual(r["source_actual_stack_pull_macro_rows"],1)
  self.assertFalse(r["every_possible_original_memory_writer_observed"])
 def test_wrong_or_missing_NMI_source_macros_fail(self):
  a,b=self.fixture()
  with self.assertRaisesRegex(ValueError,"missing/misaligned"):
   m.observe(a.replace("kind=pushW addr=01EE","kind=pushW addr=01EF",1),b)
  with self.assertRaisesRegex(ValueError,"nine source NMI|NMI calendar"):
   m.observe("\n".join(a.splitlines()[:-1]),b)
  with self.assertRaisesRegex(ValueError,"truncated"):
   m.observe(a+"QA01RF045ORIGSTACK_TRUNCATED\n",b)
if __name__=="__main__":unittest.main()
