"""Synthetic contract tests for the pinned native Switcher NMI writer beam probe."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_native_switcher_stack_gate as native_gate
import qa01_native_nmi_beam_patch as beam_patch
import qa01_native_nmi_beam_report as report

WRITER = (
    "f5781   7E:01DD=4004 w2 I_NMI_M1X1 A=4004 X=0000 Y=0000 "
    "S=01DD D=0000 DB=80 M=0 Xf=1 IPC=00858E "
    "QAbeam_v=225 QAbeam_h=816 QAbeam_master=1070052 QAcpu_block_start=945130 QAcpu_master=945374\n"
)


class OriginalNativeSwitcherBeamTests(unittest.TestCase):
    def test_disposable_native_log_hook_is_one_shot_and_observational(self):
        core = (beam_patch.HEADER + "head\n" + native_gate.MARKER
                + "    fputc('\\n', g_wlog_addr_fp);\n"
                + "    if (g_wlog_halt_off >= 0) { tail\n")
        with self.assertRaisesRegex(ValueError, "first"):
            beam_patch.patch(core)
        patched = native_gate.patch(core)
        instrumented = beam_patch.patch(patched)
        self.assertIn(native_gate.STAMP, instrumented)
        self.assertIn(beam_patch.STAMP, instrumented)
        self.assertEqual(instrumented.count("    fputc('\\n', g_wlog_addr_fp);"), 1)
        self.assertEqual(instrumented.count(native_gate.MARKER), 1)
        self.assertIn("g_snes->vPos", instrumented)
        self.assertIn("#include <string.h>", instrumented)
        self.assertIn("g_snes->hPos", instrumented)
        self.assertIn("g_snes->beamMasterLast", instrumented)
        self.assertIn("g_cpu.coprocessor_master_cycles", instrumented)
        self.assertIn("g_cpu.master_cycles", instrumented)
        self.assertIn("width == 2", instrumented)
        self.assertIn('strcmp(g_last_recomp_func, "I_NMI_M1X1")', instrumented)
        with self.assertRaisesRegex(ValueError, "already"):
            beam_patch.patch(instrumented)
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            beam_patch.patch(patched.replace(beam_patch.MARKER,
                                                beam_patch.MARKER * 2))

    def test_true_shape_never_certifies_cpu_phase_or_full_course(self):
        data = report.summarize(WRITER)
        self.assertEqual(data["schema"], report.SCHEMA)
        self.assertEqual(data["native_observation_host_frame_window"], [5778, 5782])
        row = data["native_original_nmi_writer_beam"]
        self.assertEqual(row["native_host_frame"], 5781)
        self.assertEqual(row["stack_word_saved"], "4004")
        self.assertEqual(row["framework_beam_vpos"], 225)
        self.assertEqual(row["framework_beam_hpos"], 816)
        self.assertEqual(row["native_cpu_master_cycles"], 945374)
        self.assertEqual(row["native_cpu_basic_block_start_master_cycles"], 945130)
        self.assertEqual(row["native_cpu_charged_delta_from_block_entry"], 244)
        self.assertTrue(data["framework_beam_vs_original_cpu_phase_unaligned"])
        self.assertTrue(data["native_cpu_master_counter_precharged_and_store_paced_not_pha_cycle"])
        self.assertTrue(data["modeled_beam_hpos_not_proven_instruction_aligned"])
        self.assertTrue(data["cpu_write16_paced_charges_before_writer_log"])
        self.assertEqual(data["accepted_usa_course_count_added"], 0)

    def test_manual_workflow_enforces_exact_execution_and_no_redundant_job(self):
        wf = (ROOT / ".github/workflows/qa01-switcher-original-2014.yml").read_text(encoding="utf-8")
        self.assertEqual(wf.count("  fresh-paired-switcher-nmi:"), 1)
        self.assertIn("if: ${{ !inputs.fresh_paired_nmi_probe }}", wf)
        self.assertIn("if: ${{ inputs.fresh_paired_nmi_probe }}", wf)
        self.assertIn('test "${{ inputs.source_horizon }}" = "22000"', wf)
        self.assertIn('test "${{ inputs.stack_writer_probe }}" != "true"', wf)
        self.assertIn("UR_QA_NATIVE_STACK_FIRST: \"5778\"", wf)
        self.assertIn("UR_QA_NATIVE_STACK_LAST: \"5782\"", wf)
        self.assertIn('SNESRECOMP_WLOG_ADDR_CAP: "2048"', wf)
        self.assertIn("qa01_switcher_nmi_beam_crosswalk.py", wf)
        self.assertIn("      - name: Existing fresh-paired Switcher source movie replay", wf)
        self.assertNotIn("\n  pull_request:", wf)

    def test_malformed_misphased_duplicate_or_unauthenticated_fails_closed(self):
        for invalid in (
            "",
            WRITER.replace("w2", "w1"),
            WRITER.replace("7E:01DD", "7E:01DE"),
            WRITER.replace("f5781", "f5782"),
            WRITER.replace("4004 w2", "4042 w2"),
            WRITER.replace("I_NMI_M1X1", "Text_FormatRaceTime"),
            WRITER.replace("A=4004", "A=4042"),
            WRITER.replace("S=01DD", "S=01DB"),
            WRITER.replace("M=0", "M=1"),
            WRITER.replace("QAbeam_v=225", "QAbeam_v=300"),
            WRITER.replace("QAbeam_h=816", "QAbeam_h=4000"),
            WRITER.replace("QAbeam_master=1070052", "QAbeam_master=nope"),
            WRITER.replace("QAcpu_master=945374", "QAcpu_master=-1"),
            WRITER.replace("QAcpu_block_start=945130", "QAcpu_block_start=945375"),
            WRITER.replace("QAcpu_block_start=945130", "QAcpu_block_start=nan"),
            WRITER + WRITER,
            WRITER.replace("QAbeam_h=816", "QAbeam_h=816 QAextra=7"),
        ):
            with self.subTest(invalid=invalid[-140:]):
                with self.assertRaises(ValueError):
                    report.summarize(invalid)


if __name__ == "__main__":
    unittest.main()
