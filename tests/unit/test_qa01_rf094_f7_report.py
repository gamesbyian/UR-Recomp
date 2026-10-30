"""RF094 real previously-retained F7 stream rules, strictly own clock axes."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_rf094_spc_dsp_report as m


def row(side, seq, frame, value, tick):
    if side == "ORIG":
        return (f"QA01RF092SPC seq={seq} frame={frame} kind=SPC_TO_CPU_WRITE "
                f"addr=00F7 val={value:02X} spc_ticks={tick} "
                f"spc_next_pc=0684 clock=original_spc\n")
    return (f"QA01RF093NATIVE seq={seq} f={frame} kind=SPC_TO_CPU_WRITE "
            f"addr=00F7 val={value:02X} spc_ticks={tick} "
            f"spc_next_pc=0684 q=0 target=0 guest=0 clock=native_spc\n")


class LatePortFollowthrough(unittest.TestCase):
    def test_own_entry_relative_source_windows_and_no_false_pcm_conclusion(self):
        original = row("ORIG", 100, 6446, 0x03, 109972551)
        original += row("ORIG", 101, 6449, 0x0D, 110030000)
        original += row("ORIG", 102, 6450, 0x0E, 110030100)
        native = row("NATIVE", 200, 6448, 0x03, 109602378)
        native += row("NATIVE", 201, 6451, 0x0A, 109655472)
        native += row("NATIVE", 202, 6452, 0x0B, 109655600)
        result = m.analyze(original.encode(), native.encode())
        a, b = result["original"], result["native"]
        self.assertEqual(a["f7_bytes"], [0x03, 0x0D, 0x0E])
        self.assertEqual(b["f7_bytes"], [0x03, 0x0A, 0x0B])
        self.assertTrue(a["f7_late_observed"])
        self.assertTrue(b["f7_late_observed"])
        self.assertFalse(result["same_ordered_f7_bytes"])
        self.assertFalse(result["same_ordered_f7_bytes_proves_audio_parity"])
        self.assertFalse(result["cross_core_clock_conversion_proven"])
        self.assertFalse(result["full_guest_event_admitted"])

    def test_preexisting_early_spc_port_rows_do_not_spoil_bowl_stream(self):
        raw = row("ORIG", 10, 6058, 0x00, 100)
        raw += row("ORIG", 11, 6445, 0x01, 200)
        self.assertEqual(m.audit(raw.encode(), "ORIG")["f7_bytes"], [1])

    def test_truncation_bad_order_malformed_and_wrong_window_fail_closed(self):
        valid = row("NATIVE", 100, 6451, 0x0A, 1000)
        self.assertEqual(m.audit(valid.encode(), "NATIVE")["f7_bytes"], [10])
        # The fourth-command tail is valid through native frame 6456.
        self.assertEqual(m.audit(row("NATIVE", 100, 6456, 0x0A, 1000).encode(),
                                 "NATIVE")["f7_bytes"], [10])
        invalid = [
            valid + "QA01RF093NATIVE_TRUNCATED\n",
            valid.replace("q=0", "q=X"),
            valid.replace("spc_next_pc=0684", "spc_next_pc=X684"),
            valid.replace("f=6451", "f=6457"),
            valid.replace("f=6451", "f=6446"),
            valid + row("NATIVE", 99, 6452, 0x0B, 2000),
            valid + row("NATIVE", 101, 6452, 0x0B, 999),
            valid + row("NATIVE", 101, 6450, 0x0B, 2000),
        ]
        for raw in invalid:
            with self.subTest(raw=raw[-100:]), self.assertRaises(ValueError):
                m.audit(raw.encode(), "NATIVE")

if __name__ == "__main__":
    unittest.main()
