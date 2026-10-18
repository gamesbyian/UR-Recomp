"""RF047 only source-pinned, read-only native NMI/RTI phase probe."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf047_native_nmi_phase_witness as rf

class NativePhaseSource(unittest.TestCase):
 def fixture(self):
  beam = (
    "#include <stdint.h>\n"
    "static uint32_t s_resume_pc;\n"
    "static void run_interrupt(uint32_t vector, uint64_t deadline) {\n"
    "  cpu_push_interrupt_frame_at(&g_cpu, s_resume_pc);\n"
    "  interp_bridge_set_master_deadline(deadline);\n"
    "  (void)interp_bridge_run_interrupt(&g_cpu, vector);\n"
    "  interp_bridge_set_master_deadline(0);\n"
    "  update_resume_pc();\n"
    "}\n"
    "void snes_beam_frame_driver_run_frame(void) {\n"
    "  if (!booting && g_snes->nmiEnabled) {\n"
    "    run_interrupt(nmi_vector(), frame_end);\n"
    "  }\n"
    "}\n")
  cpu = (
    "/* UR_QA01_RF044_STACK_BUS */\n"
    "static void ur_rf044_native_read(CpuState *cpu,uint8 bank,uint16 addr,\n"
    "                                uint16 value,unsigned width) {\n"
    "    if (!allow) return;\n"
    "    static unsigned rows;\n"
    "    if (rows++ < 8192u)\n"
    "        fprintf(stderr, \"read\");\n"
    "}\n")
  return beam,cpu
 def test_single_architectural_interrupt_and_reader_unchanged(self):
  beam,cpu=self.fixture()
  after,read=rf.patch(beam,cpu)
  self.assertEqual(after.count("cpu_push_interrupt_frame_at(&g_cpu, s_resume_pc)"),1)
  self.assertEqual(after.count("interp_bridge_run_interrupt(&g_cpu, vector)"),1)
  self.assertEqual(after.count("nmi_vector()"),1)
  self.assertEqual(after.count('ur_rf047_nmi_snapshot("after_push", vector);'),1)
  self.assertEqual(after.count('ur_rf047_nmi_snapshot("handler_return", vector);'),1)
  self.assertEqual(read.count("ur_rf047_native_stack_read(cpu,bank,addr,value,width);"),1)
  self.assertEqual(read.count("static unsigned rows;"),1)
  self.assertEqual(read.count("fprintf(stderr, \"read\")"),1)
 def test_fail_closed_missing_source_or_partial_patch(self):
  b,c=self.fixture()
  with self.assertRaisesRegex(ValueError,"pinned"):
   rf.patch(b.replace("run_interrupt(nmi_vector(), frame_end)",
                      "run_interrupt(irq_vector(), frame_end)"),c)
  with self.assertRaisesRegex(ValueError,"requires precise"):
   rf.patch(b,c.replace("static unsigned rows;","static int rows;"))
  a,d=rf.patch(b,c)
  with self.assertRaisesRegex(ValueError,"already/partially"):
   rf.patch(a,d)

if __name__=="__main__":
 unittest.main()
