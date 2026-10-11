"""Native interpreter-only opcode patch and strict source-scoped reporter."""
from __future__ import annotations

import unittest
import sys
import copy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_native_interp_pla_patch as patcher
import qa01_native_interp_pla_report as report

C_SOURCE = (patcher.INCLUDE + patcher.PULLBYTE +
            "static uint16_t interp816_pullWord(Interp816* cpu) {\n"
            "  return interp816_pullByte(cpu);\n"
            "}\n" + patcher.OPCODE)
PLA = (
    "QANATIVEINTPLAREADY\n"
    "QANATIVEINTPLA f=5781 k=80 pcnext=859A sp0=01DC sp1=01DE "
    "a0=0000 a1=4004 m0=0 e0=0 armed=1 "
    "reads=2 ra0=01DD rv0=04 ra1=01DE rv1=40\n"
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
        self.assertEqual(source.count("interp816_read(cpu, cpu->sp)"), 1)
        self.assertIn("ur_qa01_pla_read_value[i] = ur_qa_pla_byte;", source)
        self.assertIn("ur_qa01_pla_active = 0;", source)
        # A literal backslash-n between C statements is a syntax error.
        # Verify the emitted source, not merely the patcher's Python text.
        self.assertIn(
            "ur_qa01_pla_active = 0;\n      ur_qa01_note_interp_pla(cpu,",
            source,
        )
        self.assertNotIn(
            r"ur_qa01_pla_active = 0;\n      ur_qa01_note_interp_pla(cpu,",
            source,
        )
        self.assertIn("QANATIVEINTPLAREADY", source)
        self.assertIn("void ur_qa01_interp_pla_arm(void)", source)
        self.assertIn("(void)ur_qa01_interp_pla_output();", source)
        self.assertNotIn("interp816_init(void*", source)
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
        self.assertEqual(r["interpreter_exact_op_byte_reads"],
                         [{"address": "7E:01DD", "value": "04"},
                          {"address": "7E:01DE", "value": "40"}])
        self.assertTrue(r["interpreter_byte_reads_reconstruct_accumulator"])
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
        r = report.summarize(report.READY + "\n")
        self.assertEqual(r["native_interpreter_pla_observation_count"], 0)
        self.assertTrue(r["no_interpreter_pla_observed_does_not_rule_out_aot_or_other_reads"])
        self.assertTrue(r["native_interpreter_probe_initialized_even_if_no_pla"])
        for bad in ("", "QANATIVEINTPLAREADY\nQANATIVEINTPLAREADY\n",
                    "QANATIVEINTPLAOVERFLOW\\n"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                report.summarize(bad)
        self.assertEqual(r["release_complete_event_credit"], 0)

    def test_8bit_pla_only_restores_one_byte_and_preserves_high_a(self):
        one = PLA.replace("sp1=01DE", "sp1=01DD").replace("m0=0", "m0=1")
        one = one.replace("a0=0000 a1=4004", "a0=4000 a1=4004")
        one = one.replace("reads=2 ra0=01DD rv0=04 ra1=01DE rv1=40",
                          "reads=1 ra0=01DD rv0=04 ra1=0000 rv1=00")
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
            PLA.replace("reads=2", "reads=1"),
            PLA.replace("ra0=01DD", "ra0=01DE"),
            PLA.replace("rv0=04", "rv0=42"),
            PLA.replace("ra1=01DE", "ra1=01DF"),
            PLA.replace("rv1=40", "rv1=41"),
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
            report.summarize(report.READY + "\n"), read_report.summarize(arm))
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

    def test_direct_interpreter_rows_cannot_be_relabelled_by_aggregate_metadata(self):
        import qa01_native_stack_read_report as read_report
        arm = (
            "QANATIVEARM f=5781 bank=00 addr=01DD width=2 value=4004 "
            "A=4004 S=01DD scope=I_NMI_M1X1\n"
        )
        raw = (
            "QANATIVEREAD f=5781 bank=00 addr=01DD width=1 value=0004 "
            "A=0000 S=01DC M=1 scope=InterpPLA\n"
            "QANATIVEREAD f=5781 bank=00 addr=01DE width=1 value=0040 "
            "A=0000 S=01DC M=1 scope=InterpPLA\n"
        )
        validated_read = read_report.summarize(arm + raw)
        data = report.summarize(PLA)
        for field, replacement in (
            ("native_interpreter_saved_4004_pla_candidate_count", 0),
            ("native_interpreter_saved_4004_pla_candidate_frames", []),
            ("native_interpreter_pla_observation_count", 0),
            ("native_interpreter_probe_initialized_even_if_no_pla", False),
            ("release_complete_event_credit", 1),
        ):
            bad = copy.deepcopy(data)
            bad[field] = replacement
            with self.subTest(field=field), self.assertRaises(ValueError):
                report.corroborate_executed_pla_with_read_bus(bad, validated_read)
        for field, replacement in (
            ("interpreter_exact_op_byte_reads", []),
            ("interpreter_exact_op_byte_reads",
             [{"address": "7E:01DD", "value": "40"},
              {"address": "7E:01DE", "value": "04"}]),
            ("interpreter_byte_reads_reconstruct_accumulator", False),
        ):
            bad = copy.deepcopy(data)
            bad["native_interpreter_pla_records"][0][field] = replacement
            with self.subTest(field=field), self.assertRaises(ValueError):
                report.corroborate_executed_pla_with_read_bus(bad, validated_read)

    def test_real_pinned_interpreter_source_probe_without_mutation(self):
        core = ROOT / "baldosa/snesrecomp/runner/src/snes/interp816.c"
        if not core.is_file():
            self.skipTest("disposable Baldosa pin only checked out in opt-in workflow")
        original = core.read_text(encoding="utf-8")
        self.assertEqual(original.count(patcher.PULLBYTE), 1)
        self.assertEqual(original.count(patcher.OPCODE), 1)
        patched = patcher.patch(original)
        self.assertNotEqual(original, patched)
        self.assertIn("uint8_t ur_qa_pla_byte = interp816_read(cpu, cpu->sp);", patched)
        self.assertIn("ur_qa01_pla_read_addr[i] = cpu->sp;", patched)
        self.assertIn("ur_qa01_pla_read_value[i] = ur_qa_pla_byte;", patched)
        self.assertIn("void ur_qa01_interp_pla_arm(void)", patched)
        bridge = ROOT / "baldosa/snesrecomp/runner/src/snes/interp_bridge.c"
        if bridge.is_file():
            live_bridge = bridge.read_text(encoding="utf-8")
            self.assertIn("Interp816 in;", live_bridge)
            self.assertIn("memset(&in, 0, sizeof in);", live_bridge)
            self.assertNotIn("interp816_init(", live_bridge)
        self.assertEqual(patched.count("interp816_read(cpu, cpu->sp);"),
                         original.count("interp816_read(cpu, cpu->sp);"))

    def test_pinned_generated_nmi_trampoline_requires_downstream_restore_probe(self):
        generated = ROOT / "baldosa/src/gen/bank00_part00_v2.c"
        if not generated.is_file():
            self.skipTest("pinned generated native guest only checked out in opt-in workflow")
        text = generated.read_text(encoding="utf-8")
        start = "RecompReturn I_NMI_M1X1(CpuState *cpu) {"
        self.assertEqual(text.count(start), 1)
        segment = text.split(start, 1)[1].split("\nRecompReturn ", 1)[0]
        self.assertIn("CPU_STACK_OP_PHA", segment)
        self.assertEqual(segment.count("CPU_STACK_OP_PHA"), 2)
        self.assertNotIn("CPU_STACK_OP_PLA", segment)
        self.assertNotIn("CPU_STACK_OP_RTI", segment)
        for target in ("0x80f60c", "0x808610", "0x8085a5"):
            self.assertIn(target, segment)
        self.assertIn("interp_tier_dispatch_tail", segment)
        self.assertIn("0x008599u", segment)

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
