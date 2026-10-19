"""RF047 single native ordered interrupt/read witness, negative source guards."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf047_native_nmi_phase_report as m

class NmiPhase(unittest.TestCase):
 def fixture(self, return_stage=None):
  lines=[]
  n=0
  for f in m.FRAMES:
   def snap(stage,sp):
    nonlocal n
    n+=1
    return ("QA01RF047NATIVE seq=%d stage=%s f=%d resume=82D4EE vector=00B0E1"
            " PB=82 P=26 S=%s emu=0 master=2200000 beamMaster=2199988"
            " beamV=225 beamH=42 stack=%s" %
             (n,stage,f,sp, "81970055" if stage=="entry" else "26EED482"))
   lines.append(snap("entry","01F0"))
   lines.append(snap("after_push","01EC"))
   n+=1
   lines.append("QA01RF047NATIVE seq=%d stage=read f=%d bank=00 addr=01ED width=1 value=0026 PB=82 P=26 S=01EC master=2200001 beamV=226 beamH=111 nmi=1"%(n,f))
   if return_stage is not None:
    n+=1
    lines.append("QA01RF047NATIVE seq=%d stage=%s f=%d opcodePC=008588 returnPC=82D4EE P=26 S=01F0 master=2200002 beamV=226 beamH=112"%(n,return_stage,f))
   lines.append(snap("handler_return","01F0"))
  return "\n".join(lines)+"\n"
 def test_exact_executed_window_with_genuine_ordered_reads(self):
  r=m.classify(self.fixture())
  self.assertEqual(r["native_nmi_frames"],9)
  self.assertEqual(sum(x["native_inhandler_actual_read_helper_count"] for x in r["native_interrupt_paired_operations"]),9)
  self.assertFalse(r["native_exact_RTI_opcode_proven"])
  self.assertEqual(r["complete_USA_event_credit"],0)
 def test_actual_interpreted_return_pc_and_source_opcode(self):
  r=m.classify(self.fixture("interp_rti"))
  self.assertTrue(r["native_exact_RTI_opcode_proven"])
  self.assertEqual(r["native_explicit_RTI_evidence_frames"],9)
  self.assertEqual([x["native_actual_RTI_return_PC"] for x in r["native_interrupt_paired_operations"]],["82D4EE"]*9)
  self.assertTrue(all(x["native_RTI_return_PC_matches_saved_resume"] for x in r["native_interrupt_paired_operations"]))
 def test_compiled_return_does_not_prove_opcode_pc(self):
  r=m.classify(self.fixture("compiled_rti"))
  self.assertFalse(r["native_exact_RTI_opcode_proven"])
  self.assertEqual(r["native_explicit_RTI_evidence_frames"],9)
  self.assertTrue(all(p["native_actual_RTI_return_PC"] is None and p["native_RTI_return_PC_matches_saved_resume"] is None for p in r["native_interrupt_paired_operations"]))
  with self.assertRaisesRegex(ValueError,"partial actual RTI"):
   m.classify(self.fixture("interp_rti").replace("stage=interp_rti f=1017","stage=read f=1017",1))
 def test_genuine_opcode_marker_has_ordinal_but_is_not_a_read(self):
  text=self.fixture()
  text=text.replace("QA01RF047NATIVE seq=4 stage=handler_return",
    "QA01RF047NATIVE seq=4 stage=opcode f=1017 guestPC=82D4F0 tier=aot master=2200002\n"
    "QA01RF047NATIVE seq=5 stage=handler_return",1)
  # Shift later ordinals to preserve a single physical execution sequence.
  import re
  lines=text.splitlines()
  for idx,line in enumerate(lines):
   if idx>4 and line.startswith("QA01RF047NATIVE seq="):
    n=int(re.search(r"seq=(\d+)",line).group(1))
    if n>=5:lines[idx]=line.replace(f"seq={n} ",f"seq={n+1} ",1)
  result=m.classify("\n".join(lines))
  self.assertEqual(result["native_actual_executed_opcode_markers"],1)
  self.assertTrue(result["native_opcode_marker_is_not_bus_consumer_proof"])
  with self.assertRaisesRegex(ValueError,"executed native guest PC"):
   m.classify("\n".join(lines).replace("guestPC=82D4F0","guestPC=FFFFFFX"))
 def test_incomplete_native_trace_fails_closed(self):
  s=self.fixture()
  with self.assertRaisesRegex(ValueError,"sequence gap|duplication"):
   m.classify(s.replace("seq=1 stage=entry","seq=2 stage=entry",1))
  with self.assertRaisesRegex(ValueError,"missing or repeated"):
   m.classify(s.replace("stage=handler_return","stage=read",1))
  with self.assertRaisesRegex(ValueError,"truncated"):
   m.classify(s+"QA01RF047NATIVE_TRUNCATED\n")
  with self.assertRaisesRegex(ValueError,"pushed state"):
   m.classify(s.replace("stage=after_push f=1017 resume=82D4EE vector=00B0E1 PB=82 P=26 S=01EC emu=0 master=2200000 beamMaster=2199988 beamV=225 beamH=42 stack=26EED482",
     "stage=after_push f=1017 resume=82D4EE vector=00B0E1 PB=82 P=26 S=01EC emu=0 master=2200000 beamMaster=2199988 beamV=225 beamH=42 stack=26EFD482",1))
if __name__=="__main__":unittest.main()
