"""RF040 exact-executed CPU return and SPC echo attribution regression tests."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_rf040_cpu_echo_transport_report as m

class RF040Report(unittest.TestCase):
    def records(self):
        original = [
            "QA01RF037ORIGCPU2 bucket=38 age=103919450 v=116 h=442 port=2 val=24",
        ]
        h = [508, 600, 652, 704, 756, 808]
        age = [103919454, 103919457, 103919461, 103919462, 103919465, 103919468]
        val = ["23"] * 5 + ["24"]
        for j in range(6):
            if j == 5:
                original.append("QA01RF040ORIGSPCECHO age=103919466 pc=1555 port=2 value=24")
            original.append(f"QA01RF040ORIGCPU v=116 h={h[j]} age={age[j]} port=2 value={val[j]}")
            original.append("QA01RF038ORIGOP frame=6091 v=116 pre_h=0 post_v=116 "
                            f"post_h={h[j]+6} pc=82:8301 opcode=CD nextpc=82:8304")
        original.append("QA01RF037ORIGCPU2 bucket=38 age=103919475 v=116 h=972 port=3 val=02")
        native = [
            "QA01RF037NATIVEUP kind=rtl-apu-enter frame=6091 master=2176886834 "
            "reg=2142 val=24 scope=Snd_UploadBlockList_82B4_M1X0",
        ]
        for j, (master, cpuage, v) in enumerate(
            [(2176886940, 103919439, "23"),
             (2176886992, 103919442, "23"),
             (2176887044, 103919444, "24")]
        ):
            native.append("QA01RF038NATIVEPACE frame=6091 "
                          f"master={master} op=read8 bank=80 addr=2142 charge=6 "
                          "scope=Snd_UploadBlockList_82B4_M1X0")
            if j == 2:
                native.append("QA01RF040NATIVESPCECHO frame=6091 age=103919443 "
                              "pc=1555 port=2 value=24")
            native.append(f"QA01RF040NATIVECPU frame=6091 age={cpuage} pc=1555 "
                          f"port=2 raw={v} returned={v}")
        native.append("QA01RF037NATIVEUP kind=rtl-apu-enter frame=6091 "
                      "master=2176887208 reg=2143 val=02 scope=Snd_UploadBlockList_82B4_M1X0")
        return "\n".join(original)+"\n", "\n".join(native)+"\n"

    def test_real_echo_before_first_new_cpu_return(self):
        result = m.analyze(*self.records())
        self.assertEqual([x["returned"] for x in result["original_cpu_polls"]],
                         ["23", "23", "23", "23", "23", "24"])
        self.assertEqual([x["returned"] for x in result["native_cpu_polls"]],
                         ["23", "23", "24"])
        self.assertEqual([x["native_master"] for x in result["native_cpu_polls"]],
                         [2176886940, 2176886992, 2176887044])
        self.assertTrue(result["cpu_return_values_and_actual_echo_order_observed"])
        self.assertFalse(result["source_qualified_timing_change_justified"])
        self.assertFalse(result["cross_guest_absolute_spc_clock_registration_proven"])
        self.assertEqual(result["complete_usa_events_admitted"], 0)

    def test_wrong_return_rejected(self):
        a, b = self.records()
        with self.assertRaisesRegex(ValueError, "six-return"):
            m.analyze(a.replace("h=704 age=103919462 port=2 value=23",
                                "h=704 age=103919462 port=2 value=24"), b)
        with self.assertRaisesRegex(ValueError, "returned value"):
            m.analyze(a, b.replace("age=103919442 pc=1555 port=2 raw=23 returned=23",
                                   "age=103919442 pc=1555 port=2 raw=23 returned=24"))

    def test_missing_or_moved_echo_rejected(self):
        a, b = self.records()
        with self.assertRaisesRegex(ValueError, "echo 24"):
            m.analyze(a.replace("age=103919466 pc=1555", "age=103919467 pc=1555"), b)
        echo = "QA01RF040NATIVESPCECHO frame=6091 age=103919443 pc=1555 port=2 value=24\n"
        b = b.replace(echo, "") + echo
        with self.assertRaisesRegex(ValueError, "not between"):
            m.analyze(a, b)

    def test_missing_true_original_opcode_and_native_paced_read_rejected(self):
        a, b = self.records()
        with self.assertRaisesRegex(ValueError, "original opcode"):
            m.analyze(a.replace("post_h=658", "post_h=657"), b)
        with self.assertRaisesRegex(ValueError, "paced CPU read"):
            m.analyze(a, b.replace("master=2176886992 op=read8", "master=2176886993 op=read8"))

    def test_truncation_or_missing_original_writer_rejected(self):
        a, b = self.records()
        with self.assertRaisesRegex(ValueError, "truncated"):
            m.analyze(a, b+"QA01RF040NATIVECPU_TRUNCATED\n")
        with self.assertRaisesRegex(ValueError, "original port2 writer"):
            m.analyze(a.replace("age=103919450", "age=103919451"), b)

if __name__ == "__main__":
    unittest.main()
