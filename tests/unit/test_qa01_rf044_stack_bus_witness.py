"""RF044 ensure only authentic existing bus helpers and NMI are instrumented."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf044_stack_bus_witness as m

def orig_header():
 return "/* Header */\n"+ "".join(
   f"{marker}    /* genuine {kind} body */\n}}\n"
   for marker,kind,_,_ in m.ORIG_FUNC)

def native_src():
 return (m.NATIVE_HEADER+"\nvoid cpu_read8(void) {\n"+m.NATIVE_READ_8+"}\n"
        +"void cpu_read16(void) {\n"+m.NATIVE_READ_16+"}\n"
        +"void wlog_addr_note_via(void) {\n"+m.NATIVE_WRITER_END+"}\n")

class FrameStack(unittest.TestCase):
 def test_original_fully_source_pinned_one_call_and_repeat_idempotent(self):
  old=orig_header()
  after=m.original_getset(old)
  self.assertEqual(m.original_getset(after),after)
  self.assertEqual(after.count("ur_rf044_orig_bus("),5)
  self.assertEqual(after.count("S9xGetByte("),old.count("S9xGetByte("))
  self.assertEqual(after.count("S9xSetByte("),old.count("S9xSetByte("))
  self.assertIn("QA01RF044ORIGBUS_TRUNCATED",after)
  for k in ("rb","rw","wb","ww"):
   self.assertIn('ur_rf044_orig_bus("'+k+'"',after)
 def test_original_non_opcode_nmi_one_call_and_byte_window(self):
  old=m.NMI_OLD+"\n"
  out=m.original_cpu(old)
  self.assertEqual(out.count("S9xOpcode_NMI();"),1)
  self.assertEqual(m.original_cpu(out),out)
  self.assertIn("QA01RF044ORIGNMI",out)
  self.assertIn("Memory.RAM[0x01f1]",out)
 def test_native_actual_ram_reads_and_writer_journal(self):
  old=native_src()
  out=m.native_cpu(old)
  self.assertEqual(m.native_cpu(out),out)
  for op in ("cpu_latch_read8(", "cpu_latch_read16(", "fputc("):
   self.assertEqual(out.count(op),old.count(op))
  self.assertIn("QA01RF044NATIVEREAD_TRUNCATED",out)
  self.assertIn("rf044_S=",out)
  self.assertIn("sn es_frame_counter".replace(" ",""),out)
 def test_reject_unrecognized_upstream_source(self):
  for fn in (m.original_getset,m.original_cpu,m.native_cpu):
   with self.assertRaisesRegex(ValueError,"source"):fn("nothing known\n")
 def test_explicit_bounded_real_host_and_no_extra_bus(self):
  s=m.ORIG_HELPER+m.NATIVE_HELPER
  for marker in ("1017","1025","0x01ed","0x01f1"):
   self.assertIn(marker.lower(),s.lower())
  self.assertNotIn("S9xGetByte(Address);",m.ORIG_HELPER)
  self.assertNotIn("cpu_read8(cpu,",m.NATIVE_HELPER)

if __name__=="__main__":unittest.main()
