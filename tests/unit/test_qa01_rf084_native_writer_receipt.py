"""RF084 native writer log validation and existing manual workflow wiring.

Synthetic controls only; no emulation, original/native parity or QA credit.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_rf084_native_writer_receipt as m


def row(seq, site, width, frame, offset, *, master=10, after="0001"):
    return (f"QA01RF084NATIVE seq={seq} site={site} width={width} variant=M1X0 "
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
            self.first + "\n" + self.second.replace("variant=M1X0", "variant=M0X0"),
            self.first + "\n" + self.second.replace("native_master=10", "native_master=x"),
            self.first + "\n" + self.second.replace("f=6059", "f=6057"),
            self.first.replace("supplied=0001", "supplied=0101") + "\n" + self.second,
        ]
        for variant in variants:
            with self.subTest(variant=variant[-100:]), self.assertRaises(ValueError):
                m.audit(variant.encode())

    def test_manual_campaign_stages_after_regeneration_and_retains_real_log(self):
        workflow = (ROOT / ".github/workflows/qa01-event-campaign.yml").read_text()
        self.assertEqual(workflow.count("      qa01_rf084_native_sound_dp:"), 2)
        self.assertIn("RF084 requires zoom-zoo + mesh + DP, RF015/017 on, RF018 off", workflow)
        self.assertLess(
            workflow.index("baldosa_dp_indirect_long_pointer_once_patch.py --verify-gen"),
            workflow.index("qa01_rf084_native_sound_dp_committed_writer.py --root baldosa"))
        self.assertLess(
            workflow.index("qa01_rf084_native_sound_dp_committed_writer.py --root baldosa"),
            workflow.index("cmake -S baldosa -B baldosa/build -G Ninja"))
        self.assertIn("UR_QA01_RF084_NATIVE_SOUND_DP: ${{ inputs.qa01_rf084_native_sound_dp && '1' || '0' }}", workflow)
        self.assertIn('--native-log "$ROOT/work/zoom-zoo/replay/native.log"', workflow)
        self.assertIn("${{ runner.temp }}/qa01-case/qa01-rf084-native-writer-receipt.json", workflow)
        self.assertIn("${{ runner.temp }}/qa01-case/work/${{ matrix.case }}/replay/native.log", workflow)
        self.assertIn("cancel-in-progress: false", workflow)
        self.assertNotIn("pull_request:", workflow)
        self.assertNotIn("schedule:", workflow)


if __name__ == "__main__":
    unittest.main()
