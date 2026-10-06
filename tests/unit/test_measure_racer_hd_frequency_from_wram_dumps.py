import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "measure_dumps",
    ROOT / "tools" / "measure_racer_hd_frequency_from_wram_dumps.py",
)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)


class RacerHdWramCensusTests(unittest.TestCase):
    def test_row_reads_exact_guest_snapshot_words(self):
        data = bytearray(0x20000)
        values = {
            "p1_primary": 0x0545,
            "p2_primary": 0x057C,
            "p1_companion": 0x0000,
            "p2_companion": 0x0C27,
            "p1_selector": 0,
            "p2_selector": 0,
            "p1_gate": 0,
            "p2_gate": 1,
        }
        for key, value in values.items():
            off = MOD.ADDR[key]
            data[off] = value & 0xFF
            data[off + 1] = value >> 8
        row = MOD.row_from_wram(1401, bytes(data))
        self.assertEqual(row["frame"], 1401)
        self.assertEqual(row["p1_primary"], "0x0545")
        self.assertEqual(row["p2_primary"], "0x057C")
        self.assertEqual(row["p2_companion"], "0x0C27")
        self.assertEqual(row["p2_gate"], "0x0001")
        self.assertEqual(row["p1_selector"], 0)

    def test_generated_script_is_dense_and_exact(self):
        text = MOD.generate_script(10, 12, "sample")
        self.assertEqual(
            text.splitlines(),
            [
                "# Generated dense Racer semantic sampling route.",
                "wait 10",
                "dump sample-10",
                "wait 1",
                "dump sample-11",
                "wait 1",
                "dump sample-12",
                "quit",
            ],
        )

    def test_loader_rejects_missing_frame(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload = bytes(0x20000)
            (root / "sample-10.wram.bin").write_bytes(payload)
            (root / "sample-12.wram.bin").write_bytes(payload)
            with self.assertRaisesRegex(ValueError, "not dense/contiguous"):
                MOD.load_rows(root, "sample")


if __name__ == "__main__":
    unittest.main()
