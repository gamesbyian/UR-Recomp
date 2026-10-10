"""Executed original fresh Switcher PHA vs native NMI-scoped 01DD witness contracts.

A source PC + opcode scope is stronger than a stack-address guess; it still
does not identify the native exact guest opcode/phase or a live stack consumer.
"""
from __future__ import annotations
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/"analysis/data/switcher-original-fresh-01dd-nmi-writer-20261010.json"
NATIVE=ROOT/"analysis/data/switcher-native-stack-actual-writers-20261010.json"
ORIGINAL_MOVIE=ROOT/"analysis/data/switcher-original-jsr-stack-opcode-scopes-20261010.json"

class OriginalFresh01DDOriginalNmiWitnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.e=json.loads(SOURCE.read_text(encoding="utf-8"))
        cls.n=json.loads(NATIVE.read_text(encoding="utf-8"))
        cls.o=json.loads(ORIGINAL_MOVIE.read_text(encoding="utf-8"))

    def test_archive_identity_authentic_result_strict_red_and_zero_credit(self):
        e=self.e
        self.assertEqual(e["schema"],"UR-QA01-SWITCHER-ORIGINAL-FRESH-01DD-NMI-PC/1")
        s=e["source"]
        self.assertEqual(s["execution_run_id"],38094600828)
        self.assertEqual(s["execution_job_id"],114337813101)
        self.assertEqual(s["artifact_id"],11684893524)
        self.assertEqual(s["artifact_zip_sha256"],
                         "a95aba4c9118c80efb5ab1fcafbed996a1ee440e9280560bb076029479034e84")
        self.assertEqual(s["unchanged_archived_movie_sha256"],
                         self.n["reproducibility"]["original_movie_sha256"]
                         if "original_movie_sha256" in self.n["reproducibility"]
                         else "06dce29e9d36997fc2a1fac4bab72180ab6c8096366cfcf05780c1b2dea4b442")
        self.assertEqual(s["original_native_result_same_host_frame"],5783)
        self.assertEqual(s["original_native_penultimate_same_host_frame"],5782)
        self.assertEqual(s["original_native_remaining_wram_different_byte_count"],8)
        self.assertEqual(s["original_native_vram_cgram_different_byte_count"],0)
        self.assertTrue(s["actual_original_native_settled_positive_timed_ppu_result_equal"])
        self.assertEqual(s["strict_guest_relative_original_result_frame"],4704)
        self.assertEqual(s["strict_guest_relative_native_result_frame"],4702)
        self.assertTrue(s["guest_relative_frame_parity_failed"])
        self.assertEqual(s["complete_event_release_credit"],0)

    def test_original_actual_opcode_pha_changes_01dd_once(self):
        x=self.e["executed_fresh_original_cpu"]
        self.assertEqual(x["observed_window_cpu_frames"],[5778,5782])
        self.assertEqual(x["original_cpu_gate_first_observed_frame"],5778)
        self.assertEqual(x["normal_opcode_scope_count_for_7e01dd"],1)
        self.assertEqual(x["changed_byte_opcode_by_cpu_frame"],{"5780":1})
        self.assertEqual(x["changed_byte_opcode_by_pc"],{"00:858E":1})
        self.assertEqual(x["changed_byte_opcode_by_opcode"],{"48":1})
        writer=x["one_actual_original_pha_observation"]
        sample=x["original_normal_opcode_byte_changes"]
        self.assertEqual(len(sample),1)
        self.assertEqual(sample[0]["original_opcode_pc"],writer["pc"])
        self.assertEqual(sample[0]["opcode"],writer["opcode"])
        self.assertTrue(sample[0]["push_opcode_and_stack_address_compatible"])
        self.assertEqual(writer["mnemonic"],"PHA")
        self.assertEqual(writer["ppu_v_counter"],225)
        self.assertEqual(writer["stack_pointer_before"],"01DE")
        self.assertEqual(writer["stack_pointer_after"],"01DC")
        self.assertEqual(writer["stack_word_push_width_inferred_from_sp_decrement"],2)
        self.assertEqual(writer["wram_7e01dd_before"],"08")
        self.assertEqual(writer["wram_7e01dd_after"],"42")

    def test_all_five_original_interrupt_entries_are_real_four_byte_nmi_pushes(self):
        x=self.e["executed_fresh_original_cpu"]
        self.assertEqual(x["original_nmi_entry_observed_count"],5)
        self.assertTrue(x["nmi_entry_never_pushed_to_7e01dd"])
        self.assertTrue(x["nmi_entry_never_changed_7e01dd"])
        rows=x["original_nmi_entries"]
        self.assertEqual([e["original_cpu_frame"] for e in rows],
                         [5778,5779,5780,5781,5782])
        self.assertEqual({e["ppu_vcounter"] for e in rows},{225})
        for row in rows:
            with self.subTest(frame=row["original_cpu_frame"]):
                pre,post=int(row["stack_pointer_before"],16),int(row["stack_pointer_after"],16)
                self.assertEqual((pre-post)&0xFFFF,4)
                self.assertTrue(row["stack_push_width_compatible"])
                self.assertFalse(row["nmi_stack_push_range_covers_01dd"])
                self.assertFalse(row["01dd_changed_during_nmi_entry"])
                self.assertEqual(row["old_byte"],row["new_byte"])

    def test_original_pha_site_is_inside_original_nmi_vector_function(self):
        c=self.e["source_symbol_owner_crosswalk"]
        self.assertEqual(c["symbol_name"],"I_NMI")
        self.assertEqual(c["symbol_fastrom_mirror_address"],"80:8588")
        self.assertEqual(c["original_live_cpu_instruction_pc"],"00:858E")
        self.assertEqual(c["original_fastrom_mirror_pc"],"80:858E")
        self.assertEqual(c["offset_bytes_after_symbol_entry"],6)
        self.assertEqual(int(c["original_fastrom_mirror_pc"].split(":")[1],16)
                         -int(c["symbol_fastrom_mirror_address"].split(":")[1],16),6)
        self.assertEqual(c["native_generated_function_scope"],"I_NMI_M1X1")
        self.assertEqual(c["source"],
                         "reference/imported/reverse-engineering/baldosa-uniracers-recomp/decomp/symbols.txt")
        self.assertEqual(self.e["executed_fresh_original_cpu"]
                         ["one_actual_original_pha_observation"]["pc"],
                         c["original_live_cpu_instruction_pc"])

    def test_native_01dd_same_game_source_but_not_equivalent_instruction_clock(self):
        e=self.e["independent_native_guest"]
        native=self.n["actual_native_stack_writer_window"]
        self.assertEqual(e["execution_run_id"],self.n["reproducibility"]["actual_one_shot_workflow_run"])
        self.assertEqual(e["wram_7e01dd_write_attempts_in_native_result_window"],
                         native["counts_by_wram_address"]["7E:01DD"])
        self.assertEqual(e["native_7e01dd_writer_samples"],
                         native["first_five_actual_write_attempts_per_address"]["7E:01DD"])
        self.assertEqual(e["native_guest_logged_frame"],5781)
        self.assertEqual(e["scope"],"I_NMI_M1X1")
        self.assertEqual(e["native_written_low_byte"],"04")
        self.assertEqual(self.o["observed"]["unchanged_in_bounded_original_result_window"],
                         ["7E:01DD"])
        self.assertEqual(self.e["adjudication"]["qa_release_course_credit"],0)
        self.assertEqual(self.e["adjudication"]["official_usa_event_denominator"],45)

if __name__=="__main__":
    unittest.main()
