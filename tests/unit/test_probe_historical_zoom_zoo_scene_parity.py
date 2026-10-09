"""ROM-free scene-aligned original input transfer and guest-state guard tests."""
from __future__ import annotations

import struct
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import probe_historical_zoom_zoo_scene_parity as probe


def segment_report() -> dict:
    return {
        "movie_frame_range": [3190, 5000],
        "frames": 1811,
        "relative_input_segments": [
            {"start": 0, "duration": 3, "mask": "0x080"},
            {"start": 5, "duration": 2, "mask": "0x081"},
            {"start": 10, "duration": 7, "mask": "0x800"},
        ],
    }


class ZoomZooSceneRelativeProbeTests(unittest.TestCase):
    def test_original_archived_zoo_inputs_share_pinned_1810_frame_digest(self):
        import json
        import extract_historical_smv_scene_window as archived
        source, member = archived.read_movie(archived.ARCHIVE)
        self.assertEqual(member, "100% run.smv")
        meta = json.loads(archived.METADATA.read_text(encoding="utf-8"))
        window = archived.window(source, meta, 3190, 1810)
        self.assertEqual(
            window["raw_controller_window_sha256"],
            "e77f10e4d652dfb2ed9afcf4c252e3e9f14e551a30edbbaa2a69ec50996f90b6",
        )
        self.assertEqual(len(window["relative_input_segments"]), 116)

    def test_exact_event_rebasing_includes_phase_hypothesis(self):
        source = segment_report()
        self.assertEqual(probe.movie_events(source, 1200, 0), [
            (1200, 3, 0x080), (1205, 2, 0x081), (1210, 7, 0x800)
        ])
        self.assertEqual(probe.movie_events(source, 1300, -1), [
            (1299, 3, 0x080), (1304, 2, 0x081), (1309, 7, 0x800)
        ])
        self.assertEqual(probe.movie_events(source, 1400, 1)[0], (1401, 3, 0x080))
        for bad_phase in (-2, 2, True, 0.5):
            with self.assertRaises(probe.SceneReplayError):
                probe.movie_events(source, 1200, bad_phase)
        with self.assertRaises(probe.SceneReplayError):
            probe.movie_events(source, -1, 0)

    def test_wrong_scene_origin_or_overlapping_input_rejected(self):
        row = segment_report()
        row["movie_frame_range"] = [3189, 4999]
        with self.assertRaisesRegex(probe.SceneReplayError, "window"):
            probe.movie_events(row, 1200)
        row = segment_report()
        row["relative_input_segments"][1]["start"] = 2
        with self.assertRaisesRegex(probe.SceneReplayError, "overlapping"):
            probe.movie_events(row, 1200)

    def test_script_extends_only_after_original_menu_route(self):
        script = probe.replay_script()
        self.assertIn("until 009F == D7 3600", script)
        self.assertIn("until 009B == 01 600", script)
        self.assertEqual(script.count("dump race-entered"), 1)
        self.assertIn("dump race-plus-0064", script.replace("race-plus-064", "race-plus-0064"))
        self.assertIn("dump race-plus-0210", script)
        self.assertIn("dump race-plus-1800", script)
        self.assertEqual(script.count("quit"), 1)
        self.assertNotIn("poke ", script)
        self.assertEqual(tuple(sorted(probe.CHECKPOINTS)), probe.CHECKPOINTS)
        self.assertLess(probe.CHECKPOINTS[-1], probe.ORIGINAL_WINDOW_FRAMES)

    def test_state_read_requires_real_size_and_valid_track(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.wram.bin"
            with self.assertRaises(probe.SceneReplayError):
                probe.read_guest(path, 0)
            path.write_bytes(b"too short")
            with self.assertRaises(probe.SceneReplayError):
                probe.read_guest(path, 0)
            buf = bytearray(0x20000)
            buf[0x0313] = 1
            buf[0x00CE] = 1
            struct.pack_into("<H", buf, 0x0E95, 0x2024)
            struct.pack_into("<H", buf, 0x1199, 3)
            struct.pack_into("<H", buf, 0x119D, 0)
            struct.pack_into("<H", buf, 0x0EF1, 1)
            path.write_bytes(buf)
            row = probe.read_guest(path, 210)
            self.assertEqual(row["p1_stored_contact"], 0x2024)
            self.assertEqual(row["p1_next_checkpoint"], 3)
            self.assertEqual(row["p1_laps_remaining"], 1)
            buf[0x00CE] = 2
            path.write_bytes(buf)
            with self.assertRaisesRegex(probe.SceneReplayError, "wrong track"):
                probe.read_guest(path, 210)
            buf[0x0313] = 0
            path.write_bytes(buf)
            inactive = probe.read_guest(path, 210)
            self.assertEqual(inactive["in_race"], 0)
            self.assertNotIn("p1_next_checkpoint", inactive)

    def test_first_divergence_is_event_relative_and_reports_exact_values(self):
        rows = [
            {"relative_frame": frame, "in_race": 1, "track_id": 1,
             "p1_next_checkpoint": 3} for frame in probe.CHECKPOINTS
        ]
        self.assertIsNone(probe.compare(rows, [dict(x) for x in rows]))
        modified = [dict(x) for x in rows]
        modified[9]["p1_next_checkpoint"] = 2
        diff = probe.compare(rows, modified)
        self.assertEqual(diff["relative_frame"], 210)
        self.assertEqual(diff["fields"], ["p1_next_checkpoint"])
        self.assertEqual(diff["reference"]["p1_next_checkpoint"], 3)
        self.assertEqual(diff["native"]["p1_next_checkpoint"], 2)
        with self.assertRaisesRegex(probe.SceneReplayError, "incomplete"):
            probe.compare(rows[:-1], rows)
        modified[9]["relative_frame"] += 1
        with self.assertRaisesRegex(probe.SceneReplayError, "alignment"):
            probe.compare(rows, modified)


if __name__ == "__main__":
    unittest.main()
