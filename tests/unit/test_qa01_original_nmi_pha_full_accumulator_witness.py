"""QA-01 actual original five-frame I_NMI PHA A/M/SP vs native PHA A=4004."""
from __future__ import annotations
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/"analysis/data/switcher-original-nmi-pha-full-accumulator-executed-20261010.json"
ORIGINAL=ROOT/"analysis/data/switcher-original-fresh-01dd-nmi-writer-20261010.json"
NATIVE=ROOT/"analysis/data/switcher-native-nmi-01dd-exact-pha-source-20261010.json"

class OriginalNmiPhaFiveFramesWitnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=json.loads(EVIDENCE.read_text(encoding="utf-8"))
        cls.o=json.loads(ORIGINAL.read_text(encoding="utf-8"))
        cls.n=json.loads(NATIVE.read_text(encoding="utf-8"))

    def test_real_2014_paired_guest_execution_and_artifact_are_pinned(self):
        d=self.d
        self.assertEqual(d["schema"],"UR-QA01-ORIGINAL-SWITCHER-NMI-PHA-FULL-A-EXECUTED/1")
        x=d["run"]
        self.assertEqual(x["execution_run_id"],38097707477)
        self.assertEqual(x["execution_job_id"],114346974308)
        self.assertEqual(x["artifact_id"],11686632783)
        self.assertEqual(x["artifact_zip_sha256"],
                         "c2bb347de619e4e17418a3645c2a678a6624794199fa5120ee7b5eb235472a19")
        self.assertEqual(x["rom_sha256"],self.o["source"]["canonical_rom_sha256"])
        self.assertEqual(x["original_movie_sha256"],self.o["source"]["unchanged_archived_movie_sha256"])
        self.assertEqual(x["original_native_same_host_penultimate"],5782)
        self.assertEqual(x["original_native_same_host_result"],5783)
        self.assertTrue(x["rendered_actual_positive_timed_race_result_matched"])
        self.assertEqual(x["strict_original_native_result_guest_relative"],[4704,4702])
        self.assertIs(x["strict_guest_relative_result_frame_parity"],False)
        self.assertEqual(x["release_complete_event_credit"],0)

    def test_actual_original_nmi_pha_accumulator_cycle_is_five_distinct_frames(self):
        rows=self.d["actual_original_I_NMI_plus6_pha_cpu_register_scopes"]
        expected=[
            (5778,"4040","01E2","01E0"),
            (5779,"4004","01EA","01E8"),
            (5780,"4042","01DE","01DC"),
            (5781,"4042","01E7","01E5"),
            (5782,"4004","01E5","01E3"),
        ]
        self.assertEqual(len(rows),5)
        for row,(frame,a,s0,s1) in zip(rows,expected):
            with self.subTest(frame=frame):
                self.assertEqual(row["original_cpu_frame_before"],frame)
                self.assertEqual(row["original_cpu_frame_after"],frame)
                self.assertEqual(row["ppu_vcounter_before"],225)
                self.assertEqual(row["original_instruction_pc"],"00:858E")
                self.assertEqual(row["opcode"],"48")
                self.assertEqual(row["accumulator_before"],a)
                self.assertEqual(row["accumulator_after"],a)
                self.assertEqual(row["memory_width_flag_before"],0)
                self.assertEqual(row["memory_width_flag_after"],0)
                self.assertEqual(row["stack_pointer_before"],s0)
                self.assertEqual(row["stack_pointer_after"],s1)
                self.assertEqual((int(s0,16)-int(s1,16)),2)
                self.assertEqual(row["processor_status_low_before"],
                                 row["processor_status_low_after"])
        self.assertEqual(self.d["original_nmi_hardware_entry_5778_through_5782_count"],5)

    def test_original_full_4042_word_writes_low_42_high_40_at_01dd(self):
        x=self.d["actual_original_pha_01dd_writer"]
        self.assertEqual(x,self.d["actual_original_I_NMI_plus6_pha_cpu_register_scopes"][2])
        self.assertEqual(x["original_cpu_frame_before"],5780)
        self.assertEqual(x["accumulator_before"],"4042")
        self.assertTrue(x["low_byte_matches_accumulator"])
        self.assertEqual(x["stack_pointer_before"],"01DE")
        self.assertEqual(x["stack_pointer_after"],"01DC")
        self.assertEqual([x["01dd_before"],x["01dd_after"]],["08","42"])
        self.assertEqual([x["01de_before"],x["01de_after"]],["00","40"])
        self.assertEqual(self.o["executed_fresh_original_cpu"]
                         ["one_actual_original_pha_observation"]["wram_7e01dd_after"],"42")

    def test_native_recovered_a4004_at_same_stack_depth_but_unaligned_clock(self):
        d=self.d["actual_cross_guest_comparison"]
        native=self.n["native_01dd_actual_logged_word_write"]
        self.assertEqual(d["original_accumulator_value_at_same_observed_stack_pointer_prePHA"],
                         "4042")
        self.assertEqual(d["native_accumulator_value_at_same_observed_stack_pointer_prePHA"],
                         "4004")
        self.assertEqual(d["original_cpu_frame_for_4042_at_sp_01de"],5780)
        self.assertEqual(d["native_snes_frame_counter_for_4004_at_sp_01de"],5781)
        self.assertEqual(native["raw_written_word"],"4004")
        self.assertEqual(native["raw_write_base_address"],"01DD")
        self.assertEqual(native["registers_at_write"]["A"],"4004")
        self.assertEqual(
            self.d["native_pha_dynamically_recovered"]["native_SP_before_inferred"],
            "01DE")
        self.assertEqual(
            self.d["native_pha_dynamically_recovered"]["native_SP_after_inferred"],
            "01DC")
        self.assertEqual(d["original_other_cpu_frames_in_same_bounded_window_with_accumulator_4004"],
                         [{"original_cpu_frame":5779,"SP_before":"01EA","SP_after":"01E8"},
                          {"original_cpu_frame":5782,"SP_before":"01E5","SP_after":"01E3"}])
        self.assertTrue(d["same_high_stack_byte_40"])
        self.assertFalse(d["same_low_stack_byte"])
        self.assertIs(d["source_original_cpu_Frame_vs_native_snes_frame_counter_directly_equated"],False)
        self.assertTrue(d["same_real_guest_instruction_boundary_or_NMI_phase_not_proven"])
        self.assertEqual(self.d["adjudication"]["official_usa_course_acceptances"],0)
        self.assertEqual(self.d["adjudication"]["denominator_usa"],45)

if __name__=="__main__":
    unittest.main()
