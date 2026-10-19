"""RF074: actual scheduler resume assignment is NOT executed opcode evidence."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf047_native_nmi_phase_witness as rf47
import qa01_rf074_nmi_resume_origin_source as source
import qa01_rf074_nmi_resume_origin_report as report

def source_fixture():
    return ('#include "snes/interp_bridge.h"\n'
            'static uint32_t s_resume_pc;\n'
            'static bool s_wai_halted;\n'
            +rf47.NOTE
            +'static void run_interrupt(uint32_t vector, uint64_t deadline) {\n'
            '  ur_rf047_nmi_snapshot("entry", vector);\n'
            '  cpu_push_interrupt_frame_at(&g_cpu, s_resume_pc);\n'
            '  ur_rf047_nmi_snapshot("after_push", vector);\n'
            '  (void)interp_bridge_run_interrupt(&g_cpu, vector);\n}\n'
            'void driver_nmi(void) {\n'
            '    g_snes->inNmi = true;\n'
            '    s_wai_halted = false;\n}\n')

def native_fixture():
    seq=0
    rows=[]
    for frame in range(1017,1026):
        def add(stage,detail):
            nonlocal seq
            seq+=1
            rows.append(f"QA01RF047NATIVE seq={seq} stage={stage} f={frame} {detail}")
        master=1000+frame*357368
        add("entry",f"resume=82D4EE vector=008588 PB=82 P=26 S=01F0 master={master}")
        add("resume_origin",f"phase=before_real_interrupt_push resume=82D4EE vector=008588 "
            f"sourceFound=1 originMatches=1 ringTotal={frame-900} ringSeq={frame-901} "
            f"oldPC=82D4F0 newPC=82D4EE kind=set site=wai "
            f"sourceFrame={frame-1} sourceS=01F0 bridgeDepth=1 schedDepth=0 "
            f"waiBeforeNMI={1 if frame%2 else 0} waiAtPush=0 master={master} beamV=225 beamH=0")
        add("after_push",f"resume=82D4EE vector=008588 PB=82 P=26 S=01EC master={master}")
        add("read",f"bank=00 addr=01ED width=1 value=0026 nmi=1 master={master+1}")
        add("compiled_rti",f"opcodePC=008588 returnPC=808588 P=26 S=01F0 master={master+1}")
        add("handler_return",f"resume=82D4EE vector=008588 PB=80 P=26 S=01F0 master={master+1}")
        add("read",f"bank=00 addr=01F1 width=1 value=0026 nmi=0 master={master+2}")
    return "\n".join(rows)+"\n"

class RealSourceResumeProvenance(unittest.TestCase):
    def test_stage_only_on_rf047_pinned_native_NMI_before_real_push(self):
        old=source_fixture()
        new=source.patch(old)
        self.assertEqual(new.count(source.STAMP),1)
        self.assertEqual(new.count("ur_rf074_native_nmi_resume_origin("),2)
        self.assertLess(new.index('ur_rf047_nmi_snapshot("entry", vector);'),
                        new.index("  ur_rf074_native_nmi_resume_origin(vector);"))
        self.assertLess(new.index("  ur_rf074_native_nmi_resume_origin(vector);"),
                        new.index("  cpu_push_interrupt_frame_at(&g_cpu, s_resume_pc);"))
        for op in ("cpu_push_interrupt_frame_at(&g_cpu, s_resume_pc);",
                   "interp_bridge_run_interrupt(&g_cpu, vector);",
                   "snes_read(g_snes,", "cpu_read8(", "cpu_write8("):
            self.assertEqual(old.count(op),new.count(op))
        self.assertIn("interp_bridge_resume_total();",new)
        self.assertIn("interp_bridge_resume_get(this_seq, &row)",new)
        self.assertIn("INTERP_RESUME_KIND_RESTORE",new)
        self.assertIn("UR_QA01_RF074_NMI_RESUME_ORIGIN",new)
        self.assertIn("ur_rf074_wai_before_nmi = s_wai_halted ? 1u : 0u;",new)
        self.assertLess(new.index("ur_rf074_wai_before_nmi = s_wai_halted ? 1u : 0u;"),
                        new.index("    s_wai_halted = false;"))

    def test_absent_pinned_source_and_double_install_fail(self):
        old=source_fixture()
        with self.assertRaisesRegex(ValueError,"already"):
            source.patch(source.patch(old))
        for mutation in (
            old.replace(rf47.STAMP,"MISSING_TAG"),
            old.replace("ur_rf047_nmi_snapshot", "wrong_NMI_snapshot"),
            old.replace('#include "snes/interp_bridge.h"', '#include "old_header.h"'),
            old.replace("cpu_push_interrupt_frame_at(&g_cpu, s_resume_pc);","nothing();"),
        ):
            with self.subTest(mutation=mutation[:50]),self.assertRaises(ValueError):
                source.patch(mutation)

class GuestSchedulerVsFetchedOpcode(unittest.TestCase):
    def test_all_nine_real_NMI_brackets_have_last_origin_but_no_fetched_PC_credit(self):
        v=report.inspect(native_fixture())
        self.assertEqual(v["native_RF047_sequenced_event_count"],63)
        self.assertEqual(v["native_resume_assignment_bound_to_actual_NMI_before_push_count"],9)
        self.assertEqual(v["per_frame"][0]["last_resume_ring_assignment_site"],"wai")
        self.assertTrue(v["per_frame"][0]["wai_halted_before_the_native_NMI_wake"])
        self.assertFalse(v["per_frame"][0]["wai_halted_at_actual_guest_NMI_push"])
        self.assertFalse(v["every_native_resume_origin_is_an_independently_executed_opcode_PC"])
        self.assertFalse(v["original_native_same_NMI_semantic_phase_proven"])
        self.assertEqual(v["accepted_USA_events"],0)

    def test_older_rf073_event_log_without_origin_stays_unqualified(self):
        s=native_fixture()
        s="\n".join(x for x in s.splitlines() if "stage=resume_origin" not in x)
        # Missing RF074 stage is a hard stop even if RF073 real NMI events remain.
        with self.assertRaises(ValueError):
            report.inspect(s)

    def test_rejects_untrusted_assignment_and_wrong_phase_order(self):
        raw=native_fixture()
        for a,b in (
            ("originMatches=1","originMatches=0"),
            ("sourceFound=1","sourceFound=0"),
            ("site=wai","site=unknown_site"),
            ("kind=set site=wai","kind=unwind_arm site=wai"),
            ("ringTotal=117 ringSeq=116","ringTotal=117 ringSeq=117"),
            ("newPC=82D4EE","newPC=82D4F0"),
            ("sourceFrame=1016","sourceFrame=1018"),
            ("phase=before_real_interrupt_push","phase=after_return"),
            ("resume=82D4EE vector=008588 sourceFound","resume=82D4F0 vector=008588 sourceFound"),
            ("bridgeDepth=1 schedDepth=0","bridgeDepth=999 schedDepth=0"),
            ("waiBeforeNMI=1 waiAtPush=0","waiBeforeNMI=1 waiAtPush=1"),
            ("waiBeforeNMI=1 waiAtPush=0","waiBeforeNMI=3 waiAtPush=0"),
            ("seq=3 stage=after_push","seq=30 stage=after_push"),
        ):
            with self.subTest(a=a),self.assertRaises(ValueError):
                report.inspect(raw.replace(a,b,1))

    def test_valid_old_logger_prefix_and_source_restores(self):
        raw=native_fixture().replace("QA01RF047NATIVE seq=2 ",
                                     "QA01RF044_FRAGMENTQA01RF047NATIVE seq=2 ",1)
        raw=raw.replace("kind=set site=wai","kind=restore site=rollback",1)
        v=report.inspect(raw)
        self.assertEqual(v["per_frame"][0]["last_resume_ring_assignment_kind"],"restore")
        self.assertEqual(v["per_frame"][0]["last_resume_ring_assignment_site"],"rollback")

if __name__=="__main__":
    unittest.main()
