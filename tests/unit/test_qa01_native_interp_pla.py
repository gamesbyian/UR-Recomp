"""Native interpreter-only opcode patch and strict source-scoped reporter."""
from __future__ import annotations

import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_native_interp_pla_patch as patcher
import qa01_native_interp_pla_report as report

C_SOURCE = (patcher.INCLUDE +
            "static uint16_t interp816_pullWord(Interp816* cpu) {\n"
            "  return interp816_pullByte(cpu);\n"
            "}\n" + patcher.OPCODE)
PLA = (
    "QANATIVEINTPLA f=5781 k=80 pcnext=859A sp0=01DC sp1=01DE "
    "a0=0000 a1=4004 m0=0 e0=0 armed=1\n"
)


class NativeInterpreterPlaTests(unittest.TestCase):
    def test_observer_patches_one_pinned_pla_without_guest_changes(self):
        source = patcher.patch(C_SOURCE)
        self.assertIn(patcher.STAMP, source)
        self.assertIn("ur_qa01_stack_saved_writer_seen()", source)
        self.assertEqual(source.count("interp816_pullWord(cpu)"), 1)
        self.assertEqual(source.count("interp816_setZN(cpu, cpu->a, cpu->mf);"), 1)
        self.assertIn("ur_qa01_note_interp_pla(cpu", source)
        self.assertIn("UR_QA_NATIVE_INTERP_PLA_PATH", source)
        with self.assertRaisesRegex(ValueError, "already installed"):
            patcher.patch(source)
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            patcher.patch(C_SOURCE + patcher.OPCODE)

    def test_interpreter_saved_word_is_actual_opcode_candidate_no_event_credit(self):
        data = report.summarize(PLA)
        self.assertEqual(data["native_interpreter_pla_observation_count"], 1)
        self.assertEqual(data["native_interpreter_saved_4004_pla_candidate_count"], 1)
        self.assertEqual(data["native_interpreter_saved_4004_pla_candidate_frames"], [5781])
        r = data["native_interpreter_pla_records"][0]
        self.assertEqual(r["physically_touched_stack_bytes"], ["7E:01DD","7E:01DE"])
        self.assertTrue(r["real_native_4004_writer_callback_precedes_interpreter_pla"])
        self.assertTrue(r["guest_pla_opcode_executed"])
        self.assertTrue(r["interpreter_pc_is_post_fetch_not_exact_instruction_pc"])
        self.assertFalse(data["source_original_and_native_cpu_frame_alignment_proven"])
        self.assertEqual(data["release_complete_event_credit"], 0)

    def test_authentic_saved_a_could_be_pulled_in_following_native_frame(self):
        # The writer callback is frame 5781; a guest interpreter PLA might
        # legitimately restore the saved A in frame 5782. Do not throw it
        # away merely because this is not the writer's *same* host frame.
        observed = PLA.replace("f=5781", "f=5782")
        result = report.summarize(observed)
        self.assertEqual(result["native_interpreter_saved_4004_pla_candidate_count"], 1)
        self.assertEqual(result["native_interpreter_saved_4004_pla_candidate_frames"], [5782])
        self.assertFalse(result["source_original_and_native_cpu_frame_alignment_proven"])
        self.assertEqual(result["release_complete_event_credit"], 0)

    def test_empty_scope_does_not_downgrade_event_or_claim_no_aot_reader(self):
        r = report.summarize("")
        self.assertEqual(r["native_interpreter_pla_observation_count"], 0)
        self.assertTrue(r["no_interpreter_pla_observed_does_not_rule_out_aot_or_other_reads"])
        self.assertEqual(r["release_complete_event_credit"], 0)

    def test_8bit_pla_only_restores_one_byte_and_preserves_high_a(self):
        one = PLA.replace("sp1=01DE", "sp1=01DD").replace("m0=0", "m0=1")
        one = one.replace("a0=0000 a1=4004", "a0=4000 a1=4004")
        data = report.summarize(one)
        self.assertEqual(data["native_interpreter_saved_4004_pla_candidate_count"], 0)
        self.assertEqual(data["native_interpreter_pla_records"][0]
                         ["physically_touched_stack_bytes"], ["7E:01DD"])

    def test_malformed_or_unauthenticated_interpreter_scopes_fail_closed(self):
        for bad in (
            PLA.replace("f=5781", "f=5783"),
            PLA.replace("f=5781", "f=5780"),
            PLA.replace("armed=1", "armed=0").replace("f=5781", "f=5782"),
            PLA.replace("sp1=01DE", "sp1=01DD"),
            PLA.replace("sp0=01DC", "sp0=0200"),
            PLA.replace("m0=0", "m0=1"),
            PLA.replace("a1=4004", "a1=zzzz"),
            PLA.replace("e0=0", "e0=1"),
            PLA.replace("pcnext=859A", "pcnext=????"),
            PLA + PLA.replace("f=5781", "f=5780"),
            PLA * (report.LIMIT+1),
            "QANATIVEINTPLAOVERFLOW\n",
        ):
            with self.subTest(case=bad[-100:]), self.assertRaises(ValueError):
                report.summarize(bad)

    def test_actual_interpreter_pla_needs_corresponding_byte_bus_pair(self):
        import qa01_native_stack_read_report as read_report
        arm = (
            "QANATIVEARM f=5781 bank=00 addr=01DD width=2 value=4004 "
            "A=4004 S=01DD scope=I_NMI_M1X1\n"
        )
        physical_pair = (
            "QANATIVEREAD f=5781 bank=00 addr=01DD width=1 value=0004 "
            "A=0000 S=01DC M=1 scope=InterpPLA\n"
            "QANATIVEREAD f=5781 bank=00 addr=01DE width=1 value=0040 "
            "A=0000 S=01DC M=1 scope=InterpPLA\n"
        )
        doc = read_report.summarize(arm + physical_pair)
        result = report.corroborate_executed_pla_with_read_bus(
            report.summarize(PLA), doc)
        self.assertTrue(result[
            "interpreter_saved_4004_pla_has_required_target_bus_byte_pair"])
        self.assertEqual(result[
            "interpreter_saved_4004_pla_byte_pair_count_by_frame"], {"5781": 1})
        self.assertFalse(result["source_original_and_native_cpu_frame_alignment_proven"])
        for invalid in (
            arm,
            arm + physical_pair.replace("value=0040", "value=0042"),
            arm + physical_pair.replace("addr=01DE", "addr=01DD"),
        ):
            candidate = read_report.summarize(invalid)
            with self.subTest(bad=invalid[-110:]), self.assertRaises(ValueError):
                report.corroborate_executed_pla_with_read_bus(
                    report.summarize(PLA), candidate)
        # No observed interpreter PLA is a limited, not a causal, negative.
        empty = report.corroborate_executed_pla_with_read_bus(
            report.summarize(""), read_report.summarize(arm))
        self.assertEqual(empty["native_interpreter_saved_4004_pla_candidate_count"], 0)
        self.assertEqual(empty["release_complete_event_credit"], 0)

    def test_following_frame_interp_pla_requires_following_frame_bus_reads(self):
        import qa01_native_stack_read_report as read_report
        arm = (
            "QANATIVEARM f=5781 bank=00 addr=01DD width=2 value=4004 "
            "A=4004 S=01DD scope=I_NMI_M1X1\n"
        )
        frame82 = (
            "QANATIVEREAD f=5782 bank=00 addr=01DD width=1 value=0004 "
            "A=0000 S=01DC M=1 scope=InterpPLA\n"
            "QANATIVEREAD f=5782 bank=00 addr=01DE width=1 value=0040 "
            "A=0000 S=01DC M=1 scope=InterpPLA\n"
        )
        paired = report.corroborate_executed_pla_with_read_bus(
            report.summarize(PLA.replace("f=5781", "f=5782")),
            read_report.summarize(arm + frame82))
        self.assertEqual(paired[
            "interpreter_saved_4004_pla_byte_pair_count_by_frame"], {"5782": 1})
        with self.assertRaises(ValueError):
            report.corroborate_executed_pla_with_read_bus(
                report.summarize(PLA.replace("f=5781", "f=5782")),
                read_report.summarize(arm + frame82.replace("f=5782", "f=5781")))

    def test_existing_manual_replay_path_only(self):
        workflow = (ROOT / ".github/workflows/qa01-switcher-original-2014.yml").read_text()
        host = (ROOT / "tools/probe_original_event_complete.py").read_text()
        writer = (ROOT / "tools/qa01_native_stack_read_patch.py").read_text()
        self.assertIn("qa01_native_interp_pla_patch.py", workflow)
        self.assertIn("qa01_native_interp_pla_report.py", workflow)
        self.assertIn("native-interpreter-pla-report.json", workflow)
        self.assertIn("UR_QA_NATIVE_INTERP_PLA_PATH", host)
        self.assertIn("script.name == \"complete.script\"", host)
        self.assertIn("ur_qa01_stack_saved_writer_seen", writer)


if __name__ == "__main__":
    unittest.main()
