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
                0x0419: 0x78, 0x041A: 0x56,
                0x041B: 0xBC, 0x041C: 0x9A,
                0x041D: 0x11, 0x041E: 0x22,
                0x041F: 0x33, 0x0420: 0x44,
                0x04F5: 0xFE, 0x04F6: 0xFF,
                0x04F7: 0x04, 0x04F8: 0x00,
                0x04F9: 0x03, 0x04FA: 0x00,
                0x04FB: 0xFB, 0x04FC: 0xFF,
                0x1501: 10, 0x1502: 11,
                0x1505: 12, 0x1506: 13,
                0x1509: 14, 0x150A: 15,
                0x150D: 16, 0x150E: 17,
                0x1599: 0x30,
                0x0DDB: 1,
                0x121B: 1,
                0x121D: 0,
            }
            for addr, value in values.items():
                data[addr] = value
            p.write_bytes(data)

            s = state(p)
            self.assertEqual(s["slot1"]["x_pos"], 0x1234)
            self.assertEqual(s["camera_and_viewport"]["mode"], {
                "split_screen_active_raw": 1,
                "player1_offscreen_raw": 1,
                "player2_offscreen_raw": 0,
            })
            self.assertEqual(s["camera_and_viewport"]["camera"], {
                "player1_x": 0x5678,
                "player2_x": 0x9ABC,
                "player1_y": 0x2211,
                "player2_y": 0x4433,
                "player1_x_velocity": -2,
                "player2_x_velocity": 4,
                "player1_y_velocity": 3,
                "player2_y_velocity": -5,
            })
            self.assertEqual(s["camera_and_viewport"]["screen_relative"], {
                "screen2_player2_x": 10,
                "screen2_player2_y": 11,
                "screen2_player1_x": 12,
                "screen2_player1_y": 13,
                "screen1_player1_x": 14,
                "screen1_player1_y": 15,
                "screen1_player2_x": 16,
                "screen1_player2_y": 17,
                "screen1_player1_visibility_raw": 0x30,
            })
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
