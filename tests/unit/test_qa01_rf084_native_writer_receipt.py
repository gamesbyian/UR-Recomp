"""RF084 native writer log validation and existing manual workflow wiring.

Synthetic controls only; no emulation, original/native parity or QA credit.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_rf084_native_writer_receipt as m


def row(seq, site, width, frame, offset, *, master=10, after="0001", variant="M1X0"):
    return (f"QA01RF084NATIVE seq={seq} site={site} width={width} variant={variant} "
            f"f={frame} D=0000 addr={offset:04X} old=0000 supplied=0001 "
            f"rawAfter={after} native_master={master}")


class NativeRF084Receipt(unittest.TestCase):
    def setUp(self):
        self.first = row(1, "8280E0", 1, 6058, 0x69)
        self.second = row(2, "828154", 2, 6059, 0x63)

    def test_valid_both_sites_and_unrelated_log_lines(self):
        data = ("guest startup\n" + self.first + "\n" + self.second + "\n").encode()
        v = m.audit(data)
        self.assertEqual(v["native_writer_events"], 2)
        self.assertEqual(v["site_counts"], {"8280E0": 1, "828154": 1})
        self.assertEqual(v["release_credit"], 0)
        self.assertFalse(v["original_native_parity_proven"])
        self.assertEqual(v["raw_after_mismatch_count"], 0)
        self.assertEqual(v["native_boundary_writer_events"],2)
        self.assertFalse(v["native_first_boundary_writer_parity_proven"])

    def test_real_m0x0_pointer_variant_and_late_only_negative(self):
        m0 = row(2, "828154", 2, 6059, 0x63, variant="M0X0")
        v = m.audit((self.first + "\n" + m0 + "\n").encode())
        self.assertEqual(v["variant_counts"], {"M0X0": 1, "M1X0": 1})
        self.assertEqual(v["native_boundary_writer_events"], 2)
        self.assertEqual(v["native_first_boundary_writer"]["frame"], 6058)
        self.assertFalse(v["native_first_boundary_writer_parity_proven"])
        late = m.audit((row(1,"8280E0",1,6066,0x69) + "\n" +
                        row(2,"828154",2,6068,0x63,variant="M0X0") + "\n").encode())
        self.assertEqual(late["native_boundary_writer_events"], 0)
        self.assertIsNone(late["native_first_boundary_writer"])

    def test_real_mismatch_is_recorded_not_erased(self):
        v = m.audit((self.first + "\n" + self.second.replace(
            "rawAfter=0001", "rawAfter=0000") + "\n").encode())
        self.assertEqual(v["raw_after_mismatch_count"], 1)

    def test_missing_or_invalid_rows_fail_closed(self):
        variants = [
            "", self.first, self.second,
            self.first + "\n" + self.second + "\nQA01RF084NATIVE_TRUNCATED",
            self.first + "\n" + self.second.replace("seq=2", "seq=3"),
            self.first + "\n" + self.second.replace("addr=0063", "addr=0064"),
            self.first + "\n" + self.second.replace("width=2", "width=1"),
            self.first + "\n" + self.second.replace("f=6059", "f=6069"),
            self.first + "\n" + self.second.replace("site=828154", "site=FFFFFF"),
            self.first + "\n" + self.second.replace("variant=M1X0", "variant=M2X0"),
            self.first.replace("variant=M1X0", "variant=M0X0") + "\n" + self.second,
            self.first + "\n" + self.second.replace("native_master=10", "native_master=x"),
            self.first + "\n" + self.second.replace("f=6059", "f=6057"),
            self.first.replace("supplied=0001", "supplied=0101") + "\n" + self.second,
        ]
        for variant in variants:
            with self.subTest(variant=variant[-100:]), self.assertRaises(ValueError):
                m.audit(variant.encode())

    def test_original_inc16_postwrite_is_strict_alternative_to_missing_setword(self):
        # The genuine 2026-10-27 case had 3122 opcode deltas but no
        # S9xSetWord hook entries. An actual original INC16 call-site with
        # direct post-write raw verification is a stronger bounded witness.
        hearts = "".join(f"QA01RF083ORIG_HEART frame={f} v=0 h=0\n"
                         for f in range(6069, 6080))
        def delta(seq, pc, slot):
            return (f"QA01RF083ORIG seq={seq} type=opcode_delta frame=6072 "
                    f"pc={pc} op=E6 pre_v=0 pre_h=0 post_v=0 post_h=1 "
                    f"slot={slot} old=00 new=01 setterCount=0 "
                    f"setterAddr=FFFFFFFF setterVal=00 clock=original_cpu\n")
        rows = delta(1, "8280E0", "0069") + delta(2, "828154", "0063")
        inc = ("QA01RF083ORIG_INC16 seq=1 frame=6072 pc=828154 "
               "addr=000063 wrap=1 old=0000 supplied=0001 rawAfter=0001\n")
        result = m.audit_original((hearts + rows + inc).encode())
        self.assertEqual(result["original_word_setter_entries"], 0)
        self.assertEqual(result["original_inc16_committed_rows"], 1)
        self.assertTrue(result["original_inc16_postwrite_proven"])
        self.assertFalse(result["native_clock_registration_proven"])
        for bad in (hearts + rows,
                    hearts + rows + inc.replace("rawAfter=0001", "rawAfter=0000"),
                    hearts + rows + inc.replace("supplied=0001", "supplied=0002"),
                    hearts + rows + inc.replace("addr=000063", "addr=000064"),
                    hearts + rows + inc.replace("seq=1", "seq=2"),
                    hearts + rows + inc + "QA01RF083ORIG_INC16_TRUNCATED\n"):
            with self.subTest(bad=bad[-90:]), self.assertRaises(ValueError):
                m.audit_original(bad.encode())

    def test_early_first_divergence_window_and_strict_negative_controls(self):
        hearts = "".join(f"QA01RF085EARLY_HEART frame={f} v=0 h=0\n"
                         for f in range(6051, 6066))
        def event(seq, frame, slot, old, new):
            return (f"QA01RF085EARLY seq={seq} type=opcode_delta frame={frame} "
                    f"pc=828154 op=E6 pre_v=100 pre_h=20 post_v=100 post_h=26 "
                    f"slot={slot} old={old} new={new} setterCount=0 "
                    f"setterAddr=FFFFFFFF setterVal=00 clock=original_cpu\n")
        rows = event(1, 6056, "0063", "B0", "73") + event(2, 6057, "0069", "9F", "BE")
        report = m.audit_early((hearts + rows).encode())
        self.assertEqual(report["original_early_changes_by_slot"]["0063"], 1)
        self.assertEqual(report["original_early_first_boundary_change"]["frame"], 6056)
        self.assertEqual(report["original_late_port_heartbeats"], [])
        self.assertFalse(report["original_late_port_heartbeat_complete"])
        self.assertFalse(report["original_native_first_writer_parity_proven"])
        self.assertEqual(report["release_credit"], 0)
        # Sequence 19 emits additional source-qualified RF085 heartbeat
        # rows as a side effect of activating actual CPU RF090/RF091 reads
        # and writes at Bowl +265..269. Admit the exact five late frames
        # without relaxing the compulsory 15 early frames or accepting any
        # late opcode_delta as an "early boundary" observation.
        late_hearts = "".join(
            f"QA01RF085EARLY_HEART frame={f} v=0 h=0\\n"
            for f in range(6445, 6450))
        late_result = m.audit_early((hearts + rows + late_hearts).encode())
        self.assertEqual(
            late_result["original_early_heartbeats"], list(range(6051, 6066)))
        self.assertEqual(
            late_result["original_late_port_heartbeats"], list(range(6445, 6450)))
        self.assertTrue(late_result["original_late_port_heartbeat_complete"])
        self.assertEqual(
            late_result["original_early_observations"],
            report["original_early_observations"])
        for invalid in (
            late_hearts,                         # missing early heartbeats
            late_hearts + hearts,                # reversed windows
            hearts + late_hearts.replace("frame=6447", "frame=6446"),
            hearts + late_hearts.replace("frame=6449", "frame=6450"),
            hearts + late_hearts.replace("frame=6445", "frame=6444"),
            hearts + late_hearts.splitlines(keepends=True)[0],
            hearts + late_hearts + late_hearts, # duplicate late window
            hearts + rows + late_hearts +
                event(3, 6449, "0063", "00", "01"),
        ):
            with self.subTest(invalid=invalid[-100:]), self.assertRaises(
                ValueError):
                m.audit_early(invalid.encode())

        # Actual #40487975108 had 8192 early rows and an explicit
        # truncation marker by frame 6062. The new budget must admit
        # >8192 while still rejecting any stream above 16384.
        expanded = "".join(event(i, 6057, "0063", "00", "01")
                           for i in range(1, 8194))
        self.assertEqual(m.audit_early((hearts + expanded).encode())[
            "original_early_observations"], 8193)
        overflow = expanded + "".join(event(i, 6057, "0063", "00", "01")
                                       for i in range(8194, 16386))
        with self.assertRaisesRegex(ValueError, "coverage incomplete"):
            m.audit_early((hearts + overflow).encode())
        # Zero actual changes is allowed with 15 heartbeats: an absent writer
        # is a negative observation, never fabricated source execution.
        self.assertIsNone(m.audit_early(hearts.encode())["original_early_first_change"])
        for bad in (rows, hearts.replace("frame=6065", "frame=6064") + rows,
                    hearts + rows + "QA01RF085EARLY_TRUNCATED\n",
                    hearts + rows.replace("seq=2", "seq=3"),
                    hearts + rows.replace("slot=0069", "slot=00FF"),
                    hearts + rows.replace("new=BE", "new=9F"),
                    hearts + rows.replace("frame=6057", "frame=6066")):
            with self.subTest(bad=bad[-90:]), self.assertRaises(ValueError):
                m.audit_early(bad.encode())

    def test_manual_campaign_stages_after_regeneration_and_retains_real_log(self):
        workflow = (ROOT / ".github/workflows/qa01-event-campaign.yml").read_text()
        self.assertEqual(workflow.count("      qa01_rf084_native_sound_dp:"), 2)
        self.assertIn("RF084 requires zoom-zoo + mesh + DP, RF015/017 on, RF016/018/019/APU off", workflow)
        self.assertIn("QA01_RF016: ${{ inputs.baldosa_spc_reference_rate }}", workflow)
        self.assertIn("QA01_RF019: ${{ inputs.baldosa_hdma_cpu_stall }}", workflow)
        self.assertIn('"$QA01_RF016" == "true"', workflow)
        self.assertIn('"$QA01_RF019" == "true"', workflow)
        self.assertLess(
            workflow.index("baldosa_dp_indirect_long_pointer_once_patch.py --game baldosa --verify-gen"),
            workflow.index("qa01_rf084_native_sound_dp_committed_writer.py --root baldosa"))
        self.assertLess(
            workflow.index("qa01_rf084_native_sound_dp_committed_writer.py --root baldosa"),
            workflow.index("cmake -S baldosa -B baldosa/build -G Ninja"))
        self.assertIn("UR_QA01_RF084_NATIVE_SOUND_DP: ${{ inputs.qa01_rf084_native_sound_dp && '1' || '0' }}", workflow)
        self.assertIn('--native-log "$ROOT/work/zoom-zoo/replay/native.log"', workflow)
        self.assertIn('--original-log "$ROOT/work/zoom-zoo/replay/reference.log"', workflow)
        self.assertIn('export UR_QA01_RF083_ZOO_DP=1', workflow)
        self.assertIn('qa01_rf083_original_sound_dp_first_writer.py --root "$CORE_SRC"', workflow)
        self.assertLess(
            workflow.index('qa01_rf083_original_sound_dp_first_writer.py --root "$CORE_SRC"'),
            workflow.index('cmake -S baldosa -B baldosa/build -G Ninja'))
        self.assertIn("${{ runner.temp }}/qa01-case/qa01-rf084-native-writer-receipt.json", workflow)
        self.assertIn("${{ runner.temp }}/qa01-case/work/${{ matrix.case }}/replay/native.log", workflow)
        self.assertIn("cancel-in-progress: false", workflow)
        self.assertNotIn("pull_request:", workflow)
        self.assertNotIn("schedule:", workflow)

    def test_original_rf083_paired_source_heartbeats_and_opcode_delta(self):
        hearts = "".join(f"QA01RF083ORIG_HEART frame={f} v=0 h=0\n"
                         for f in range(6069, 6080))
        def original(seq, pc, slot):
            return (f"QA01RF083ORIG seq={seq} type=opcode_delta frame=6072 "
                    f"pc={pc} op=E6 pre_v=0 pre_h=0 post_v=0 post_h=1 "
                    f"slot={slot} old=00 new=01 setterCount=0 "
                    f"setterAddr=FFFFFFFF setterVal=00 clock=original_cpu\n")
        rows = original(1, "8280E0", "0069") + original(2, "828154", "0063")
        word = ("QA01RF083ORIG_WORD seq=1 frame=6072 pc=828154 "
                "addr=000063 word=0001 wrap=0 order=1 rawBefore=0000\n")
        v = m.audit_original((hearts + word + rows).encode())
        self.assertEqual(v["original_word_setter_entries"], 1)
        self.assertTrue(v["original_word_entry_not_commit"])
        self.assertEqual(v["original_writer_rows"], 2)
        self.assertFalse(v["native_clock_registration_proven"])
        for bad in (hearts + rows,  # word setter is mandatory, byte setter alone insufficient
                    hearts + word + original(1, "8280E0", "0069"),
                    hearts + word + rows + "QA01RF083ORIG_TRUNCATED\n",
                    hearts + word + rows + "QA01RF083ORIG_WORD_TRUNCATED\n",
                    hearts.replace("frame=6079", "frame=6078") + word + rows,
                    hearts + word + rows.replace("seq=2", "seq=3"),
                    hearts + word + rows.replace("op=E6", "op=00"),
                    hearts + word + rows.replace("new=01", "new=00"),
                    hearts + word.replace("addr=000063", "addr=000064") + rows,
                    hearts + word.replace("order=1", "order=2") + rows,
                    hearts + word.replace("seq=1", "seq=2") + rows,
                    hearts + word.replace("pc=828154", "pc=828155") + rows):
            with self.subTest(bad=bad[-60:]), self.assertRaises(ValueError):
                m.audit_original(bad.encode())


if __name__ == "__main__":
    unittest.main()
