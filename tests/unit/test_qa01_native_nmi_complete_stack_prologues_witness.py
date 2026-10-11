"""QA-01 hash-recovered actual complete native NMI stack-save prologues."""
from __future__ import annotations
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
CAPTURE=ROOT/"analysis/data/switcher-native-nmi-complete-stack-prologues-20261010.json"
NATIVE=ROOT/"analysis/data/switcher-native-nmi-01dd-exact-pha-source-20261010.json"

class CompleteNativeNmiStackBurstsSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=json.loads(CAPTURE.read_text(encoding="utf-8"))
        cls.n=json.loads(NATIVE.read_text(encoding="utf-8"))

    def test_original_hash_attested_artifact_and_no_emulator_replay(self):
        d=self.d
        self.assertEqual(d["schema"],"UR-QA01-NATIVE-SWITCHER-NMI-COMPLETE-6PUSH-PROLOGUES/1")
        x=d["source"]
        self.assertEqual(x["original_paired_native_execution_run"],38090897908)
        self.assertEqual(x["original_native_wram_artifact"],11684141556)
        self.assertEqual(x["original_native_zip_sha256"],
                         "9b202ec36bfd60dc1cece9e0d2c9027275d669f8ab4100d349c69848f250eaf9")
        self.assertEqual(x["hash_verified_source_recovery_run"],38098340646)
        self.assertEqual(x["hash_verified_source_recovery_job"],114348854452)
        self.assertEqual(x["compact_native_recovered_artifact"],11687077615)
        self.assertEqual(x["compact_native_recovered_zip_sha256"],
                         "fb25b33c44ec0539fa7aeb623a3117d61c446740dd4ea57ff659092b775a373c")
        self.assertEqual(x["temporary_workflow_never_merge_pr"],1285)
        self.assertEqual(x["native_source_generated_function"],"I_NMI_M1X1")
        self.assertEqual(self.n["raw_source"]["original_native_execution_run_id"],38090897908)

    def test_four_actual_complete_consecutive_six_stack_save_bursts(self):
        d=self.d
        self.assertEqual(d["native_original_wram_writer_log_observations_with_I_NMI_scope"],27)
        self.assertEqual(d["complete_six_push_prologues_count"],4)
        self.assertEqual(d["verified_native_complete_six_push_frame_histogram"],
                         {"5781":1,"5786":1,"5787":1,"5788":1})
        rows=d["actual_native_complete_six_push_PHA_events"]
        self.assertEqual(len(rows),4)
        expect=[
            (5781,"4004","01DE","01DD","01DC"),
            (5786,"4040","01E3","01E2","01E1"),
            (5787,"4004","01E3","01E2","01E1"),
            (5788,"4004","01E3","01E2","01E1"),
        ]
        for row,(frame,acc,before,addr,after) in zip(rows,expect):
            with self.subTest(frame=frame):
                self.assertEqual(row["native_frame"],frame)
                self.assertEqual(row["native_nmi_pha_accumulator"],acc)
                self.assertEqual(row["native_nmi_pha_SP_before_inferred"],before)
                self.assertEqual(row["native_nmi_pha_SP_write_observed"],addr)
                self.assertEqual(row["native_nmi_pha_SP_after_inferred"],after)
                self.assertEqual(row["native_nmi_pha_stack_word_address"],addr)
                self.assertEqual(int(before,16)-int(after,16),2)
                self.assertEqual(int(addr,16),int(before,16)-1)
                self.assertEqual(row["native_nmi_pha_low_byte"],acc[2:])
                self.assertEqual(row["native_nmi_pha_high_byte"],acc[:2])
                self.assertEqual(row["exact_order"],
                                 ["PHB","PHD","PHX","PHY","PHA16","PHA8"])

    def test_f5781_matches_previous_independent_actual_native_pha(self):
        x=self.d["actual_native_complete_six_push_PHA_events"][0]
        n=self.n["native_01dd_actual_logged_word_write"]
        self.assertEqual(n["native_frame"],x["native_frame"])
        self.assertEqual(n["raw_write_base_address"],x["native_nmi_pha_stack_word_address"])
        self.assertEqual(n["raw_written_word"],x["native_nmi_pha_accumulator"])
        self.assertEqual(n["byte_at_7e01dd"],x["native_nmi_pha_low_byte"])
        self.assertEqual(n["registers_at_write"]["A"],x["native_nmi_pha_accumulator"])
        self.assertEqual(n["registers_at_write"]["S"],
                         hex(int(x["native_nmi_pha_SP_write_observed"],16))[2:].upper())
        self.assertTrue(n["written_word_equals_accumulator"])

    def test_reference_nmi_cpu_frame_cannot_be_equated_to_native_frame(self):
        x=self.d["original_live_source_comparison"]
        self.assertEqual(x["independent_original_nmi_full_A_run"],38097707477)
        self.assertEqual(x["original_cpu_frame_5778_through_5782_full_A"],
                         ["4040","4004","4042","4042","4004"])
        self.assertEqual(x["original_cpu_frame_5778_through_5782_sp_before"],
                         ["01E2","01EA","01DE","01E7","01E5"])
        self.assertEqual(self.d["adjudication"]["release_complete_event_credit"],0)
        self.assertEqual(self.d["adjudication"]["official_usa_course_total"],45)
        self.assertIn("NOT yet calibrated",x["qualification"])
        self.assertIn("partial",x["qualification"])

if __name__=="__main__":
    unittest.main()
