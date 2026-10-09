"""Baldosa experiment evidence must never inflate our course acceptance."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("baldosa_spike", ROOT / "tools/baldosa_core_spike_report.py")
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class BaldosaSpikeReportTest(unittest.TestCase):
    def test_unobserved_routes_not_passed(self):
        with tempfile.TemporaryDirectory() as td:
            x = mod.summarize(Path(td))
            self.assertEqual(len(x["routes"]), 3)
            self.assertTrue(all(r["exit_code"] is None for r in x["routes"]))
            self.assertTrue(all(not r["ran_and_exited_cleanly"] for r in x["routes"]))
            self.assertTrue(all(r["complete_event_qa_credit"] == 0 for r in x["routes"]))

    def test_exit_zero_not_terminal_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "race_1p.exit").write_text("0\n")
            sub = root / "race_1p"
            (sub / "dump").mkdir(parents=True)
            (sub / "log.txt").write_text("script complete\n")
            (sub / "dump" / "end.wram.bin").write_bytes(b"WRAM")
            (sub / "dump" / "end.oam.bin").write_bytes(b"OAM")
            x = mod.summarize(root)["routes"][0]
            self.assertTrue(x["ran_and_exited_cleanly"])
            self.assertEqual(x["wram_checkpoints"], ["end.wram.bin"])
            self.assertEqual(x["oam_checkpoints"], ["end.oam.bin"])
            self.assertFalse(x["original_native_terminal_result_admitted"])
            self.assertEqual(x["complete_event_qa_credit"], 0)


if __name__ == "__main__":
    unittest.main()
