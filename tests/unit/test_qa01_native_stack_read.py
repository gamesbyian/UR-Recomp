"""Native pinned WRAM consumer instrumentation and independent bounded report."""
from __future__ import annotations

import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_native_stack_read_patch as patcher
import qa01_native_switcher_stack_gate as gate
import qa01_native_nmi_beam_patch as beam
import qa01_native_stack_read_report as report

SRC = (
    'extern Snes *g_snes;\n'
    + gate.STAMP + "\n" + beam.STAMP + "\n"
    + patcher.LOGGER_START + patcher.LOGGER_END
    + patcher.B8 + patcher.B16
)
ARM = (
    "QANATIVEARM f=5781 bank=00 addr=01DD width=2 value=4004 "
    "A=4004 S=01DD scope=I_NMI_M1X1\n"
)
VALID = (
    "QANATIVEREAD f=5781 bank=00 addr=01DD width=2 value=4004 "
    "A=0000 S=01DC M=0 scope=I_NMI_M1X1\n"
    "QANATIVEREAD f=5782 bank=7E addr=01DE width=1 value=0040 "
    "A=4004 S=01DD M=1 scope=SomeRestore\n"
)


class NativeStackReadTests(unittest.TestCase):
    def test_patches_pinned_native_bus_read_paths_without_changing_return(self):
        x = patcher.patch(SRC)
        self.assertIn(patcher.STAMP, x)
        self.assertIn('getenv("UR_QA_NATIVE_STACK_READ_PATH")', x)
        self.assertIn('width == 1 ? (addr == 0x01DDu || addr == 0x01DEu)', x)
        self.assertIn("ur_qa01_read_01dd(cpu, bank, addr, cpu->ram[off], 1);", x)
        self.assertIn("ur_qa01_read_01dd(cpu, bank, addr,", x)
        self.assertIn("if (ur_qa01_read_suppressed) return;", x)
        self.assertIn("++ur_qa01_read_suppressed;", x)
        self.assertIn("--ur_qa01_read_suppressed;", x)
        self.assertIn("ur_qa01_stack_read_arm();", x)
        self.assertIn("extern void ur_qa01_interp_pla_arm(void);", x)
        self.assertIn("        ur_qa01_interp_pla_arm();", x)
        self.assertIn("QANATIVEOVERFLOW", x)
        self.assertIn("bank == 0x00u", x)
        self.assertEqual(x.count("return cpu_latch_read8(cpu, cpu->ram[off]);"), 1)
        self.assertEqual(x.count("return cpu_latch_read16(cpu, (uint16)lo | ((uint16)hi << 8));"), 1)
        with self.assertRaisesRegex(ValueError, "already installed"):
            patcher.patch(x)
        with self.assertRaisesRegex(ValueError, "prerequisites"):
            patcher.patch(SRC.replace(beam.STAMP, ""))
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            patcher.patch(SRC + patcher.B8)
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            patcher.patch(SRC + patcher.LOGGER_START)

    def test_real_source_scope_is_attempt_not_result_consumer(self):
        data = report.summarize(ARM + VALID)
        self.assertEqual(data["native_bus_read_attempt_count"], 2)
        self.assertEqual(data["native_bus_read_attempts_by_target"],
                         {"7E:01DD": 1, "7E:01DE": 2})
        self.assertFalse(data["zero_count_is_bounded_native_negative_not_no_reader_ever"])
        self.assertEqual(data["release_complete_event_credit"], 0)
        self.assertTrue(data["read_attempt_is_not_proven_original_pha_restore_or_scoring_consumer"])
        self.assertEqual(data["native_stack_read_attempts"][0]["read_value"], "4004")
        self.assertTrue(data["native_stack_read_attempts"][0]
                        ["observed_after_4004_writer_callback_started"])
        self.assertEqual(data[
            "same_native_frame_post_writer_callback_read_4004_candidate_count"], 1)
        self.assertTrue(data["matched_word_read_is_stack_restore_candidate_not_proof"])
        self.assertEqual(data["same_frame_post_writer_stack_position_consistent_word_4004_count"], 0)
        self.assertFalse(data["native_stack_read_attempts"][0]
                         ["stack_pointer_equals_read_start_at_callback"])

    def test_even_stack_pointer_consistent_saved_word_is_only_diagnostic(self):
        near = VALID.replace("S=01DC", "S=01DD", 1)
        result = report.summarize(ARM + near)
        self.assertEqual(result[
            "same_frame_post_writer_stack_position_consistent_word_4004_count"], 1)
        self.assertTrue(result["native_stack_read_attempts"][0]
                        ["stack_pointer_equals_read_start_at_callback"])
        self.assertTrue(result["stack_pointer_matches_bus_start_not_proof_of_pla"])
        self.assertEqual(result["release_complete_event_credit"], 0)
        wrong_mode = near.replace("M=0", "M=1", 1)
        self.assertEqual(report.summarize(ARM + wrong_mode)[
            "same_frame_post_writer_stack_position_consistent_word_4004_count"], 0)

    def test_read_before_writer_arm_is_not_classified_as_later_restore(self):
        before = (
            "QANATIVEREAD f=5780 bank=80 addr=01DD width=2 value=4004 "
            "A=0000 S=01DC M=0 scope=EarlierRead\n"
        )
        data = report.summarize(before + ARM)
        self.assertEqual(data["native_bus_read_attempt_count"], 1)
        self.assertFalse(data["native_stack_read_attempts"][0]
                         ["observed_after_4004_writer_callback_started"])
        self.assertEqual(data[
            "same_native_frame_post_writer_callback_read_4004_candidate_count"], 0)

    def test_all_pinned_low_wram_mirrors_are_accepted_but_7f_is_not(self):
        for bank in ("01", "3F", "81", "BF", "7E"):
            read = (f"QANATIVEREAD f=5782 bank={bank} addr=01DD width=2 "
                    "value=4004 A=0000 S=01DC M=0 scope=ReadAlias\n")
            data = report.summarize(ARM + read)
            self.assertEqual(data["native_bus_read_attempt_count"], 1)
            self.assertEqual(data["native_stack_read_attempts"][0]
                             ["memory_bank_alias"], bank)
            self.assertEqual(data["native_bus_read_attempts_by_target"],
                             {"7E:01DD": 1, "7E:01DE": 1})
        for bank in ("40", "7F", "C0", "FF"):
            invalid = (f"QANATIVEREAD f=5782 bank={bank} addr=01DD width=1 "
                       "value=0004 A=0000 S=01DD M=1 scope=BadAlias\n")
            with self.subTest(bank=bank), self.assertRaises(ValueError):
                report.summarize(ARM + invalid)

    def test_interpreter_two_byte_pull_shape_is_a_candidate_not_pla_proof(self):
        # Pinned interp816_pullWord calls two interp816_pullByte reads,
        # and bridge_bus_read routes them through cpu_read8.
        observed = (
            "QANATIVEREAD f=5781 bank=00 addr=01DD width=1 value=0004 "
            "A=0000 S=01DC M=1 scope=I_NMI_M1X1\n"
            "QANATIVEREAD f=5781 bank=00 addr=01DE width=1 value=0040 "
            "A=0000 S=01DC M=1 scope=I_NMI_M1X1\n"
        )
        data = report.summarize(ARM + observed)
        self.assertEqual(data[
            "native_post_writer_same_frame_4004_two_byte_target_row_pairs"], [[0,1]])
        self.assertEqual(data[
            "native_post_writer_same_frame_4004_two_byte_pair_candidate_count"], 1)
        self.assertEqual(data[
            "same_native_frame_post_writer_callback_read_4004_candidate_count"], 0)
        self.assertTrue(data[
            "cpu_state_s_and_m_at_interpreter_bridge_callback_not_proven_internal_interp_registers"])
        self.assertTrue(data[
            "filtered_read_row_adjacency_does_not_prove_guest_opcode_adjacency"])
        self.assertEqual(data["release_complete_event_credit"], 0)
        for changed in (
            observed.replace("value=0040", "value=0042"),
            observed.replace("addr=01DE", "addr=01DD"),
            observed.replace("f=5781 bank=00 addr=01DE",
                             "f=5782 bank=00 addr=01DE"),
            observed.replace("addr=01DD width=1", "addr=01DD width=2"),
        ):
            with self.subTest(sample=changed[-120:]):
                self.assertEqual(report.summarize(ARM + changed)[
                    "native_post_writer_same_frame_4004_two_byte_pair_candidate_count"], 0)

    def test_following_frame_saved_a_word_and_byte_reads_are_separate_candidates(self):
        # The authentic native writer is in f5781, while an AOT return or
        # interpreter PLA can consume the saved word in f5782.
        following = (
            "QANATIVEREAD f=5782 bank=00 addr=01DD width=2 value=4004 "
            "A=0000 S=01DD M=0 scope=AotReturn\n"
            "QANATIVEREAD f=5782 bank=00 addr=01DD width=1 value=0004 "
            "A=0000 S=01DC M=1 scope=InterpPull\n"
            "QANATIVEREAD f=5782 bank=00 addr=01DE width=1 value=0040 "
            "A=0000 S=01DC M=1 scope=InterpPull\n"
        )
        result = report.summarize(ARM + following)
        self.assertEqual(result[
            "same_native_frame_post_writer_callback_read_4004_candidate_count"], 0)
        self.assertEqual(result[
            "following_frame_post_writer_callback_read_4004_candidate_count"], 1)
        self.assertEqual(result[
            "following_frame_post_writer_stack_position_consistent_word_4004_count"], 1)
        self.assertEqual(result[
            "native_post_writer_same_frame_4004_two_byte_target_row_pairs"], [])
        self.assertEqual(result[
            "native_post_writer_following_frame_4004_two_byte_target_row_pairs"], [[1, 2]])
        self.assertEqual(result[
            "native_post_writer_following_frame_4004_two_byte_pair_candidate_count"], 1)
        self.assertEqual(result["release_complete_event_credit"], 0)
        for altered in (
            following.replace("value=0040", "value=0042"),
            following.replace("f=5782 bank=00 addr=01DE",
                              "f=5781 bank=00 addr=01DE"),
        ):
            # Invalid chronology is rejected; incorrect byte values cannot
            # create a plausible second-frame saved-4004 pull.
            with self.subTest(altered=altered[-105:]):
                if "f=5781 bank=00 addr=01DE" in altered:
                    with self.assertRaises(ValueError):
                        report.summarize(ARM + altered)
                else:
                    self.assertEqual(report.summarize(ARM + altered)[
                        "native_post_writer_following_frame_4004_two_byte_pair_candidate_count"], 0)

    def test_zero_rows_is_only_bounded_negative(self):
        data = report.summarize(ARM)
        self.assertTrue(data["zero_count_is_bounded_native_negative_not_no_reader_ever"])
        self.assertEqual(data["native_bus_read_attempt_count"], 0)
        self.assertEqual(data["release_complete_event_credit"], 0)

    def test_missing_or_duplicate_writer_attestation_is_not_zero_read_evidence(self):
        for journal in ("", VALID, ARM + ARM, ARM.replace("A=4004", "A=4042")):
            with self.subTest(journal=journal[:120]), self.assertRaises(ValueError):
                report.summarize(journal)

    def test_invalid_bus_scope_or_forged_clock_fails_closed(self):
        for bad in (
            VALID.replace("f=5781", "f=5777", 1),
            VALID.replace("f=5782", "f=5780", 1),
            VALID.replace("bank=00", "bank=7F", 1),
            VALID.replace("addr=01DD", "addr=0200", 1),
            VALID.replace("width=2", "width=3", 1),
            VALID.replace("value=4004", "value=XXXX", 1),
            VALID.replace("value=0040", "value=0140", 1),
            VALID.replace("scope=I_NMI_M1X1", "scope=", 1),
            VALID * (report.LIMIT+1),
            "some garbage row\n",
        ):
            with self.subTest(bad=bad[-100:]), self.assertRaises(ValueError):
                report.summarize(ARM + bad)

    def test_workflow_only_enables_in_manual_paired_guest_and_keeps_calibration_isolated(self):
        wf=(ROOT / ".github/workflows/qa01-switcher-original-2014.yml").read_text()
        host=(ROOT / "tools/probe_original_event_complete.py").read_text()
        self.assertIn("qa01_native_stack_read_patch.py", wf)
        self.assertIn("qa01_native_stack_read_report.py", wf)
        self.assertIn("native-01dd-reads-report.json", wf)
        self.assertIn('UR_QA_NATIVE_STACK_READ_ENABLE: "1"', wf)
        self.assertIn('if os.environ.get("UR_QA_NATIVE_STACK_READ_ENABLE")', host)
        self.assertIn('script.name == "complete.script"', host)
        self.assertIn('read_path = output / "qa01-native-01dd-reads.log"', host)
        self.assertIn('env["UR_QA_NATIVE_STACK_READ_PATH"] = str(read_path)', host)
        self.assertIn('env.pop("UR_QA_NATIVE_STACK_READ_PATH", None)', host)


if __name__ == "__main__":
    unittest.main()
