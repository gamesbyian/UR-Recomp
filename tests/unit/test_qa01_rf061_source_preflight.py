"""RF061 preflight must refuse shifted emit sites before spending a guest build."""
import sys,unittest,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf061_source_preflight as m

class SourcePreflight(unittest.TestCase):
 def fixture(self,root):
  src=('def emit_function():\n'
   "    src.append(f'  extern const char *g_last_recomp_func;')\n"
   '    for ii, (di_insn, ir_ops) in enumerate(pairs):\n'
   '            if ii in skip_emit_idx:\n'
   '                continue\n'
   '            # Axis-2 step C dynamics: charge runtime-only modifiers (D.l != 0,\n'
   '            for op in ir_ops:\n'
   '                lines.append("effect")\n')
  bridge='extern Snes *g_snes;\n        const uint8_t  op = bridge_bus_read(cpu, pc_before);\n'
  beam=('/* UR_QA01_RF047_NATIVE_NMI_RETURN_SOURCE_PIN */\n'
        'static int ur_rf047_allow_row(void) { return 1; }\n'
        'static void ur_rf047_nmi_snapshot(const char *stage, uint32_t vector) {\n')
  for path,data in ((m.witness.EMITTER,src),(m.witness.BRIDGE,bridge),(m.witness.BEAM,beam)):
   p=root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(data)
  return root/m.witness.EMITTER
 def test_clean_source_structure_and_explicit_nonexecution(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.fixture(root)
   report=m.inspect(root)
   self.assertTrue(report["actual_decoded_PC_site_source_staging_valid"])
   self.assertFalse(report["live_Snd_UploadBlockList_82EF_M1X0_marker_executed"])
   self.assertFalse(report["first_actual_bus_read_guest_PC_bound"])
   self.assertEqual(report["accepted_USA_events"],0)
 def test_moved_skip_and_removed_ir_fail_before_native_regen(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);p=self.fixture(root);base=p.read_text()
   for dirty in (base.replace('                continue\n','                pass\n'),
                 base.replace('            for op in ir_ops:\n','            for op in synthetic_ops:\n'),
                 base.replace('if ii in skip_emit_idx','if ii in wrong_scope')):
    p.write_text(dirty)
    with self.assertRaisesRegex(ValueError,"execution-loop structure"):
     m.inspect(root)
 def test_second_stage_is_not_silently_reused(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);p=self.fixture(root)
   p.write_text(p.read_text()+'\n# '+m.witness.STAMP+'\n')
   with self.assertRaisesRegex(ValueError,"already staged"):
    m.inspect(root)

if __name__=="__main__": unittest.main()
