"""QA-01 executed native NMI PHA stack word vs original Switcher PHA witness."""
from __future__ import annotations
import json
import re
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
NATIVE=ROOT/"analysis/data/switcher-native-nmi-01dd-exact-pha-source-20261010.json"
ORIGINAL=ROOT/"analysis/data/switcher-original-fresh-01dd-nmi-writer-20261010.json"
WLOG=ROOT/"analysis/data/switcher-native-stack-actual-writers-20261010.json"

class NativeNmiPhaSourceWitnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=json.loads(NATIVE.read_text(encoding="utf-8"))
        cls.original=json.loads(ORIGINAL.read_text(encoding="utf-8"))
        cls.old_native=json.loads(WLOG.read_text(encoding="utf-8"))

    def test_immutable_native_original_artifact_provenance(self):
        p=self.d["raw_source"]
        self.assertEqual(self.d["schema"],"UR-QA01-NATIVE-SWITCHER-NMI-01DD-EXACT-PHA-WRITER/1")
        self.assertEqual(p["original_native_execution_run_id"],38090897908)
        self.assertEqual(p["original_native_trace_artifact_id"],11684141556)
        self.assertEqual(p["original_native_artifact_zip_sha256"],
                         "9b202ec36bfd60dc1cece9e0d2c9027275d669f8ab4100d349c69848f250eaf9")
        self.assertEqual(p["immutable_artifact_recovery_run_id"],38095592659)
        self.assertEqual(p["immutable_artifact_recovery_job_id"],114340708426)
        self.assertEqual(p["recovered_compact_artifact_id"],11685473365)
        self.assertEqual(p["original_fresh_source_run_id"],38094600828)
        self.assertEqual(p["original_fresh_source_artifact_id"],11684893524)
        self.assertEqual(p["native_game_commit"],
                         "gamesbyian/uniracers-recomp@10b864b9d14a7b7416dd909eb7b054c88faef101")
        self.assertEqual(p["native_generated_file"],"src/gen/bank00_part00_v2.c")

    def test_native_exact_written_word_is_full_accumulator_at_stack_pointer(self):
        x=self.d["native_01dd_actual_logged_word_write"]
        self.assertEqual(x["native_frame"],5781)
        self.assertEqual(x["native_generated_scope"],"I_NMI_M1X1")
        self.assertEqual(x["raw_write_base_address"],"01DD")
        self.assertEqual(x["raw_written_word"],"4004")
        self.assertEqual(x["word_width"],2)
        self.assertEqual(x["byte_offset_within_write"],0)
        self.assertEqual(x["byte_at_7e01dd"],"04")
        self.assertTrue(x["is_word_write_at_logged_stack_pointer"])
        self.assertTrue(x["written_word_equals_accumulator"])
        for k in ("written_word_equals_x","written_word_equals_y",
                  "written_word_equals_direct_page"):
            self.assertFalse(x[k])
        regs=x["registers_at_write"]
        self.assertEqual(regs["A"],"4004")
        self.assertEqual(regs["S"],"1DD")
        self.assertEqual(regs["M"],"0")
        self.assertEqual(regs["Xf"],"0")
        self.assertEqual(self.old_native["actual_native_stack_writer_window"]
                         ["counts_by_wram_address"]["7E:01DD"],1)
        self.assertEqual(self.old_native["actual_native_stack_writer_window"]
                         ["first_five_actual_write_attempts_per_address"]["7E:01DD"][0]
                         ["written_byte"],"04")

    def test_original_raw_log_sequence_is_exact_native_generated_nmi_prologue(self):
        x=self.d["native_immediate_sequence"]
        self.assertEqual([a["instruction"] for a in x],
                         ["PHB","PHD","PHX","PHY","PHA 16-bit","PHA 8-bit, after SEP"])
        self.assertEqual([a["native_written_addr"] for a in x],
                         ["01E5","01E3","01E1","01DF","01DD","01DC"])
        self.assertEqual([a["native_value"] for a in x],
                         ["80","0000","1400","87D8","4004","00"])
        raw=self.d["actual_raw_wram_log_lines_around_write"]
        body=[a for a in raw if " I_NMI_M1X1 " in a]
        self.assertEqual(len(body),6)
        for item,line in zip(x,body):
            self.assertIn(f"00:{item['native_written_addr']}={item['native_value']} ",line)
        self.assertIn(" A=4004 ",body[4])
        self.assertIn(" S=01DD ",body[4])
        self.assertIn(" M=0 ",body[4])
        self.assertIn(" w2 ",body[4])
        self.assertEqual(self.d["register_consistency"]["observed_byte_at_7e01dd"],"04")

    def test_exact_original_pha_and_native_pha_source_owner_but_not_parity(self):
        x=self.d["cross_original_source"]
        self.assertEqual(x["original_cpu_pc"],"00:858E")
        self.assertEqual(x["original_fastrom_mirror_pc"],"80:858E")
        self.assertEqual(x["original_NMI_vector_symbol"],"80:8588 I_NMI")
        self.assertEqual(x["original_opcode"],"48")
        self.assertEqual(x["original_mnemonic"],"PHA")
        self.assertEqual(x["original_original_cpu_frame"],5780)
        self.assertEqual(x["original_sp_before"],"01DE")
        self.assertEqual(x["original_sp_after"],"01DC")
        self.assertEqual(x["original_7e01dd_byte_after"],"42")
        self.assertEqual(x["original_automatic_NMI_entry_pushes_not_01dd"],5)
        self.assertTrue(x["original_and_native_NMI_handler_16bit_PHA_instruction_category_matches"])
        self.assertFalse(x["native_original_accumulator_low_byte_equal"])
        self.assertEqual(x["result_absolute_host_frame_both"],5783)
        self.assertTrue(x["guest_relative_result_frame_parity_failed"])
        self.assertEqual((x["original_result_guest_relative_frame"],
                          x["native_result_guest_relative_frame"]),(4704,4702))
        self.assertEqual(self.original["executed_fresh_original_cpu"]
                         ["one_actual_original_pha_observation"]["wram_7e01dd_after"],"42")
        self.assertEqual(self.d["adjudication"]["release_complete_event_credit"],0)
        self.assertEqual(self.d["adjudication"]["official_usa_events"],45)

if __name__=="__main__":
    unittest.main()
