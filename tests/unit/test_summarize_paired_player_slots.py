import tempfile
import unittest
from pathlib import Path

from tools.summarize_paired_player_slots import state


class PairedPlayerSlotsTest(unittest.TestCase):
    def test_finish_progress_fields(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "cp.wram.bin"
            data = bytearray(0x20000)
            values = {
                0x1199: 3, 0x119B: 4,
                0x119D: 0, 0x119F: 1,
                0x0EF1: 2, 0x0EF3: 5,
                0x0411: 0x34, 0x0412: 0x12,
            }
            for addr, value in values.items():
                data[addr] = value
            p.write_bytes(data)

            s = state(p)
            self.assertEqual(s["slot1"]["x_pos"], 0x1234)
            self.assertEqual(s["race_progress"]["player1"], {
                "next_checkpoint": 3,
                "finish_gate": 0,
                "laps_remaining": 2,
            })
            self.assertEqual(s["race_progress"]["player2"], {
                "next_checkpoint": 4,
                "finish_gate": 1,
                "laps_remaining": 5,
            })


if __name__ == "__main__":
    unittest.main()
