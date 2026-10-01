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
                0x0505: 0xFE, 0x0506: 0xFF,
                0x0507: 0x34, 0x0508: 0x12,
                0x0509: 0xFF, 0x050A: 0xFF,
                0x050B: 0x78, 0x050C: 0x56,
                0x052B: 0x10, 0x052C: 0x00,
                0x052D: 0x08, 0x052E: 0x00,
            }
            for addr, value in values.items():
                data[addr] = value
            data[0x0DCD] = 2
            data[0x0DCF] = 3
            data[0x0D6D:0x0D71] = bytes([1, 0, 2, 0])
            data[0x0D7D:0x0D81] = bytes([0, 3, 4, 0])
            data[0x0D8D:0x0D91] = bytes([0x34, 0x12, 0x78, 0x56])
            data[0x0DAD:0x0DB1] = bytes([0xBC, 0x9A, 0xF0, 0xDE])
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
            self.assertEqual(s["camera_and_viewport"]["world_window"], {
                "camera1_edge_raw": -2,
                "camera2_edge_raw": 0x1234,
                "camera1_span_raw": 0x0010,
                "camera2_span_raw": 0x0008,
                "camera1_fine_raw": -1,
                "camera2_fine_raw": 0x5678,
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
            self.assertEqual(s["vram_update_lists"]["list_a_count_raw"], 2)
            self.assertEqual(s["vram_update_lists"]["list_b_count_raw"], 3)
            self.assertEqual(s["vram_update_lists"]["list_a_nonzero_flags"], 2)
            self.assertEqual(s["vram_update_lists"]["list_b_nonzero_flags"], 2)
            self.assertEqual(s["vram_update_lists"]["list_a_coords"][:2], [0x1234, 0x5678])
            self.assertEqual(s["vram_update_lists"]["list_b_coords"][:2], [0x9ABC, 0xDEF0])
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
