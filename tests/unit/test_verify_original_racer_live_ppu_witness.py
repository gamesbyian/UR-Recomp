"""ROM-free real-file negative controls for live original PPU trace receipts."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from tools.art.verify_original_racer_live_ppu_witness import validate, ROM_SHA, SCHEMA


class LiveOriginalWitnessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "frames").mkdir()
        self.a = bytes([1]) + bytes(4095)
        self.b = bytes([0, 1]) + bytes(4094)
        for key, data in (("a", self.a), ("b", self.b)):
            (self.root / "frames" / key).write_bytes(data)
        self.record = {"schema": SCHEMA, "rom_sha256": ROM_SHA,
                       "source_kind": "live-original-emulator-PPU",
                       "recorded_by_live_emulator": True,
                       "registry_sequence_reused_as_live_capture": False,
                       "emulator": {"identity": "test binary",
                                    "executable_sha256": "a" * 64,
                                    "source_revision_sha256": "b" * 64},
                       "frames": [self.row(10, "a"), self.row(11, "b"),
                                  self.row(13, "b")]}
    def tearDown(self):
        self.temp.cleanup()

    def row(self, i, name, player="p1"):
        return {"emulated_frame_index": i, "input_replay_frame_index": i,
                "player": player, "binary_alpha_file": "frames/" + name,
                "binary_alpha_sha256": hashlib.sha256(
                    self.a if name == "a" else self.b).hexdigest(),
                "oam_sha256": "c" * 64}

    def test_only_actual_consecutive_emulator_ticks_connect(self):
        r = validate(self.record, self.root)
        self.assertEqual(r["live_consecutive_edges"], 1)
        self.assertEqual(r["live_silhouette_change_edges"], 1)
        self.assertEqual(r["captured_player_frame_counts"]["p1"], 3)
        self.assertFalse(r["registry_order_substituted"])

    def test_source_registry_masquerade_rejected(self):
        for k, bad in (("source_kind", "authored-rom-registry"),
                       ("recorded_by_live_emulator", False),
                       ("registry_sequence_reused_as_live_capture", True),
                       ("rom_sha256", "0" * 64)):
            q = copy.deepcopy(self.record)
            q[k] = bad
            with self.subTest(k=k), self.assertRaises(ValueError):
                validate(q, self.root)

    def test_stale_tampered_and_missing_pixels_rejected(self):
        for change in ("sha", "missing", "path", "nonbinary"):
            q = copy.deepcopy(self.record)
            if change == "sha":
                q["frames"][0]["binary_alpha_sha256"] = "0"*64
            elif change == "missing":
                q["frames"][0]["binary_alpha_file"] = "frames/not-found"
            elif change == "path":
                q["frames"][0]["binary_alpha_file"] = "../private"
            else:
                (self.root / "frames" / "a").write_bytes(bytes([2])+bytes(4095))
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate(q, self.root)
            (self.root / "frames" / "a").write_bytes(self.a)

    def test_duplicate_and_backward_frame_rejected(self):
        for i in (10, 9):
            q = copy.deepcopy(self.record)
            q["frames"][1]["emulated_frame_index"] = i
            with self.assertRaises(ValueError):
                validate(q, self.root)

    def test_independent_player_tracks(self):
        q = copy.deepcopy(self.record)
        q["frames"].insert(1, self.row(10, "b", "p2"))
        r = validate(q, self.root)
        self.assertEqual(r["live_consecutive_edges"], 1)
        self.assertEqual(r["captured_player_frame_counts"], {"p1": 3, "p2": 1})


if __name__ == "__main__":
    unittest.main()
