"""RF044 executed trace attribution: no invented original bus/reader witness."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf044_zoo_stack_nmi_report as m

class Witness(unittest.TestCase):
 def fake(self):
  orig=[];native=[]
  for i,f in enumerate(m.FRAMES):
   pc=("82D4F0" if i%2==0 and f!=1025 else "82D4EE")
   old="8197005526"
   new="26"+pc[4:6]+pc[2:4]+pc[:2]+"26"
   orig.append(f"QA01RF044ORIGNMI f={f} f1={f} pc={pc} S0=01F0 S1=01EC old={old} new={new}")
   for j,(addr,val) in enumerate(zip(m.FIRST_WRITES,m.EXPECTED_NATIVE)):
    native.append(f"f{f}   00:{addr}={val} w1 (none) rf044_S={addr} IPC=80EFDA")
   native.append(f"QA01RF044NATIVEREAD f={f} kind=r1 bank=00 addr=01ED value=0026 S=01ED IPC=80EFDA scope=WaitForNMI_D4EE_M1X0")
  return "\n".join(orig)+"\n","\n".join(native)+"\n"
 def test_actual_NMI_and_native_writer_but_no_source_bus_coverage(self):
  r=m.inspect(*self.fake())
  self.assertEqual(len(r["original_nmi"]),9)
  self.assertEqual(r["original_getset_bus_row_count"],0)
  self.assertEqual(r["native_valid_read_row_count"],9)
  self.assertEqual(len(r["native_first_four_writer_per_frame"]),9)
  self.assertTrue(r["actual_source_nmi_entry_and_four_byte_postimage_proven"])
  self.assertFalse(r["original_single_bus_writer_and_reader_proven"])
  self.assertFalse(r["two_guest_instruction_phase_alignment_proven"])
  self.assertEqual(r["accepted_USA_event_count"],0)
 def test_missing_native_writer_or_source_NMI_fails(self):
  a,b=self.fake()
  with self.assertRaisesRegex(ValueError,"native first"):
   m.inspect(a,b.replace("00:01EF=D4","00:01EF=00",1))
  with self.assertRaisesRegex(ValueError,"nine source"):
   m.inspect("\n".join(a.splitlines()[:-1]),b)
 def test_wrong_SP_status_postimage_or_truncation_fails(self):
  a,b=self.fake()
  with self.assertRaisesRegex(ValueError,"SP"):
   m.inspect(a.replace("S1=01EC","S1=01EB",1),b)
  with self.assertRaisesRegex(ValueError,"postimage"):
   m.inspect(a.replace("new=26F0D48226","new=26F0D48326",1),b)
  with self.assertRaisesRegex(ValueError,"truncation"):
   m.inspect(a,b+"\nQA01RF044NATIVEREAD_TRUNCATED\n")
 def test_source_bus_marker_does_not_magic_writer_proof(self):
  a,b=self.fake()
  a+="QA01RF044ORIGBUS f=1017 v=200 h=300 kind=wb bank=00 addr=01ED w=1 value=0026 pb=82 pc=D4EE S=01ED\n"
  r=m.inspect(a,b)
  self.assertEqual(r["original_getset_bus_row_count"],1)
  self.assertFalse(r["original_single_bus_writer_and_reader_proven"])
if __name__=="__main__": unittest.main()
