"""RF075: no early gameplay fix from a genuine but conditional RTI ABI split."""
from __future__ import annotations
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf075_native_rti_source_contract as audit

def fixtures():
    codegen = """def _emit_return(op: Return) -> List[str]:
    if op.interrupt:
        # RTI restores real status, skips saved guest return PC and PB
        return [
            "cpu_trace_event(cpu, 0, CPU_TR_RTI, 0, 0);",
            "{ cpu->S = (uint16)(cpu->S + 1); cpu->P = cpu_read8(cpu, 0x00, cpu->S); cpu_p_to_mirrors(cpu);",
            "  cpu->S = (uint16)(cpu->S + 2);  /* pull + discard PC */",
            "  if (!cpu->emulation) cpu->S = (uint16)(cpu->S + 1);  /* native: pull + discard PB */",
            "  return RECOMP_RETURN_NORMAL; /* RTI: popped interrupt frame */ }",
        ]
    # ── Option-1 cpu->S return-frame ABI (RTS / RTL) ──
"""
    interpreter = """void interp_step(void) {
    case 0x40: { // rti imp
      interp816_setFlags(cpu, interp816_pullByte(cpu));
      cpu->cyclesUsed++;
      cpu->pc = interp816_pullWord(cpu);
      cpu->k = interp816_pullByte(cpu);
      break;
    }
    case 0x41: { // eor idx
    }
}
"""
    stack = """static inline void cpu_push_interrupt_frame_at(CpuState *cpu, uint32 pc24) {
    cpu_mirrors_to_p(cpu);
    if (!cpu->emulation) {
        cpu_write8(cpu, 0x00, cpu->S, (uint8)(pc24 >> 16)); cpu->S--;
    }
    cpu_write8(cpu, 0x00, cpu->S, (uint8)(pc24 >> 8)); cpu->S--;
    cpu_write8(cpu, 0x00, cpu->S, (uint8)pc24); cpu->S--;
    cpu_write8(cpu, 0x00, cpu->S, cpu->P); cpu->S--;
}
/* Generated host-C control flow has no runtime PC offset. */
"""
    driver = """static void run_interrupt(uint32_t vector, uint64_t deadline) {
    cpu_push_interrupt_frame_at(&g_cpu, s_resume_pc);
    (void)interp_bridge_run_interrupt(&g_cpu, vector);
    update_resume_pc();
}
void snes_beam_frame_driver_run_frame(void) {}
"""
    bridge = """static int bridge_native_handoff(CpuState *cpu, Interp816 *in, uint32 target,
                                 uint32 yield_pc, int stop_on_rti) {
    const RecompReturn r = cpu_dispatch_pc_from(cpu, target, cpu->S, target);
    sync_cpu_to_interp(cpu, in);
    if (r == RECOMP_RETURN_NORMAL) {
        if (stop_on_rti)
            return 1;
    }
    if (s_lle_unwind_active) { }
}
void interp_bridge_other(void) {
    if (stop_on_rti && op == 0x40) {
        sync_interp_to_cpu(&in, cpu);
        return 1;
    }
        /* Resolved-landing capture */
}
"""
    return [codegen,interpreter,stack,driver,bridge]

class RtiContract(unittest.TestCase):
    def test_static_NMI_return_paths_are_distinct_and_never_a_gamepass(self):
        r=audit.verify(*fixtures())
        self.assertEqual(r["compiled_RTI_guest_status_load_count"],1)
        self.assertEqual(r["compiled_RTI_guest_saved_PC_load_count"],0)
        self.assertEqual(r["compiled_RTI_guest_saved_PB_load_count"],0)
        self.assertTrue(r["compiled_RTI_returns_via_host_C_control_flow"])
        self.assertTrue(r["interpreted_RTI_stacked_status_PC_PB_restored"])
        self.assertFalse(r["any_such_guest_stack_rewrite_actually_observed"])
        self.assertFalse(r["native_actual_fetched_opcode_pc_proven"])
        self.assertEqual(r["accepted_USA_events"],0)

    def test_source_identity_is_an_actual_git_blob_digest(self):
        raw=b"exact pinned upstream\n"
        import hashlib
        expected=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
        self.assertEqual(audit.git_blob_sha(raw),expected)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for _,(path,_) in audit.FILES.items():
                dest=root/path
                dest.parent.mkdir(parents=True,exist_ok=True)
                dest.write_text("cannot stand in for pinned upstream")
            with self.assertRaisesRegex(ValueError,"source blob drift"):
                audit.inspect_root(root)

    def test_compiled_only_status_read_drift_is_rejected(self):
        samples=fixtures()
        errors=(
            samples[0].replace("cpu->P = cpu_read8(cpu, 0x00, cpu->S)","cpu->P = 0"),
            samples[0].replace("cpu->S + 2","cpu->S + 1"),
            samples[0].replace("cpu_p_to_mirrors(cpu);","missing_mirrors();"),
            samples[0].replace("return RECOMP_RETURN_NORMAL;","return 0;"),
            samples[0].replace("cpu->P = cpu_read8(cpu, 0x00, cpu->S);",
                               "cpu->P = cpu_read8(cpu, 0x00, cpu->S); cpu->PB = cpu_read8(cpu, 0x00, cpu->S);"),
        )
        for i,bad in enumerate(errors):
            with self.subTest(i=i),self.assertRaises(ValueError):
                audit.verify(bad,*samples[1:])

    def test_interpreter_must_actually_restore_return_PC_bank(self):
        all_sources=fixtures()
        for bad in (
            all_sources[1].replace("cpu->pc = interp816_pullWord(cpu);","cpu->pc = 0;"),
            all_sources[1].replace("cpu->k = interp816_pullByte(cpu);","cpu->k = 0;"),
            all_sources[1].replace("interp816_setFlags(cpu, interp816_pullByte(cpu));","interp816_setFlags(cpu, 0);")
        ):
            with self.subTest(bad=bad[:45]),self.assertRaises(ValueError):
                audit.verify(all_sources[0],bad,*all_sources[2:])

    def test_actual_entry_push_must_keep_banked_architectural_bytes(self):
        src=fixtures()
        for bad in (
            src[2].replace("(uint8)(pc24 >> 16)","(uint8)cpu->PB"),
            src[2].replace("(uint8)(pc24 >> 8)","(uint8)(pc24 >> 16)"),
            src[2].replace("cpu_mirrors_to_p(cpu);",""),
            src[2].replace("cpu_write8(cpu, 0x00, cpu->S, cpu->P)","unused(cpu->P)")
        ):
            with self.subTest(bad=bad[:35]),self.assertRaises(ValueError):
                audit.verify(*src[:2],bad,*src[3:])

    def test_interrupt_return_must_publish_scheduler_resume_after_handler(self):
        src=fixtures()
        for bad in (
            src[3].replace("update_resume_pc();",""),
            src[3].replace("cpu_push_interrupt_frame_at(&g_cpu, s_resume_pc);",
                           "cpu_push_interrupt_frame_at(&g_cpu, 0);"),
            src[3].replace("    update_resume_pc();",
                           "    cpu_read8(&g_cpu, 0x00, 0x01ED); update_resume_pc();"),
            src[3].replace("(void)interp_bridge_run_interrupt(&g_cpu, vector);","")
        ):
            with self.subTest(bad=bad[:35]),self.assertRaises(ValueError):
                audit.verify(*src[:3],bad,src[4])

    def test_no_relabeling_a_host_return_as_interpreted_stack_read(self):
        src=fixtures()
        bad=src[4].replace("if (stop_on_rti)\n            return 1;",
                           "if (stop_on_rti)\n            continue;")
        with self.assertRaises(ValueError):
            audit.verify(*src[:4],bad)

if __name__=="__main__": unittest.main()
