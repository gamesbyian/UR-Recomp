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

    def test_runtime_rejects_spoofed_original_smv_with_same_uid(self):
        import json
        import extract_historical_smv_scene_window as archive
        source, member = archive.read_movie(archive.ARCHIVE)
        meta = json.loads(archive.METADATA.read_text(encoding="utf-8"))
        self.assertEqual(member, "100% run.smv")
        verified = probe.verified_archived_scene_input(source, meta)
        self.assertEqual(verified["movie_frame_range"], [3190, 5000])
        self.assertEqual(verified["frames"], 1811)
        # An attacker or accidental local file edit can keep original
        # header UID/ROM CRC/sample count while changing guest controls.
        edited = bytearray(source)
        offset = meta["controller_data_offset"] + 2 * 3190
        edited[offset] ^= 0x10
        with self.assertRaisesRegex(probe.SceneReplayError, "differs from pinned"):
            probe.verified_archived_scene_input(bytes(edited), meta)
        # A mutation past the source prefix affects only archival frame
        # 5000, beyond the final observed +1800 checkpoint; the declared
        # integrity guarantee is intentionally not overstated.
        outside = bytearray(source)
        outside[meta["controller_data_offset"] + 2 * 5000] ^= 0x10
        last = probe.verified_archived_scene_input(bytes(outside), meta)
        self.assertEqual(last["frames"], 1811)

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
        self.assertIn("dump race-plus-0190", script)
        self.assertIn("dump race-plus-0230", script)
        self.assertIn("dump race-plus-0590", script)
        self.assertIn("dump race-plus-0630", script)
        self.assertEqual(script.count("dump race-plus-"), len(probe.CHECKPOINTS) - 1)
        self.assertEqual(probe.DENSE_CONTACT_WINDOWS, ((190, 230), (590, 630)))
        self.assertEqual(probe.ORIGINAL_PROGRESSION_WRITE_FRAMES,
                         (3408, 3794, 4031, 4722, 4911))
        self.assertEqual(probe.ORIGINAL_PROGRESSION_RELATIVE_FRAMES,
                         (218, 604, 841, 1532, 1721))
        self.assertEqual(probe.ADDITIONAL_EVENT_WINDOWS,
                         ((833, 849), (1524, 1540), (1713, 1729)))
        self.assertEqual(len(probe.CHECKPOINTS), 151)
        for event in probe.ORIGINAL_PROGRESSION_RELATIVE_FRAMES:
            for offset in (-1, 0, 1):
                self.assertIn(event + offset, probe.CHECKPOINTS)
        for start, end in probe.ADDITIONAL_EVENT_WINDOWS:
            self.assertTrue(all(frame in probe.CHECKPOINTS
                                for frame in range(start, end + 1)))
        for start, end in probe.DENSE_CONTACT_WINDOWS:
            self.assertTrue(all(frame in probe.CHECKPOINTS for frame in range(start, end + 1)))
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
            self.assertEqual(row["timer_minutes_raw"], 0)
            self.assertEqual(row["timer_subtick_raw"], 0)
            buf[0x00CE] = 2
            path.write_bytes(buf)
            with self.assertRaisesRegex(probe.SceneReplayError, "wrong track"):
                probe.read_guest(path, 210)
            buf[0x0313] = 0
            path.write_bytes(buf)
            inactive = probe.read_guest(path, 210)
            self.assertEqual(inactive["in_race"], 0)
            self.assertNotIn("p1_next_checkpoint", inactive)

    def test_both_runtimes_leaving_original_scene_cannot_pass(self):
        rows = [{"relative_frame": frame, "in_race": 1, "track_id": 1,
                 "menu": 0, "p1_next_checkpoint": 3}
                for frame in probe.CHECKPOINTS]
        self.assertEqual(probe.expected_active_window(rows)["status"],
                         "full_original_active_zoom_zoo_window")
        # Two identical accidental early results must not be claimed to
        # reproduce original archived +1800 Zoom Zoo racing semantics.
        for row in rows[10:]:
            row.update({"in_race": 0, "menu": 0x99})
            row.pop("p1_next_checkpoint")
        self.assertIsNone(probe.compare(rows, [dict(row) for row in rows]))
        observed = probe.expected_active_window(rows)
        self.assertEqual(observed["status"], "left_original_active_zoom_zoo_window")
        self.assertEqual(observed["first_nonactive_relative_frame"], probe.CHECKPOINTS[10])
        self.assertEqual(observed["menu"], 0x99)
        with self.assertRaisesRegex(probe.SceneReplayError, "phases"):
            probe.expected_active_window([
                dict(row, relative_frame=row["relative_frame"] + 1) for row in rows
            ])
        with self.assertRaisesRegex(probe.SceneReplayError, "incomplete"):
            probe.expected_active_window(rows[:-1])

    def test_full_decoded_zoo_payload_is_required_for_live_guest_sample(self):
        from probe_runtime_course_payload import is_fully_loaded_course
        decoded = bytes(range(64))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "frame.wram.bin"
            wr = bytearray(0x20000)
            wr[0x0313] = 1
            wr[0x00CE] = 1
            base = probe.entry.COURSE_RAM_OFFSET
            wr[base:base + len(decoded)] = decoded
            path.write_bytes(wr)
            self.assertTrue(is_fully_loaded_course(decoded, wr[base:]))
            self.assertEqual(probe.read_guest(path, 0, decoded)["in_race"], 1)
            wr[base + 11] ^= 1
            wr[base + 12] ^= 1  # documented loader-mutated cursor is allowed
            path.write_bytes(wr)
            self.assertEqual(probe.read_guest(path, 0, decoded)["track_id"], 1)
            wr[base + 20] ^= 1
            path.write_bytes(wr)
            with self.assertRaisesRegex(probe.SceneReplayError, "fully installed"):
                probe.read_guest(path, 0, decoded)
            wr[0x0313] = 0
            path.write_bytes(wr)
            # The guest may unload 7F after results. Retain the exit rather
            # than masking it with a wrong-payload exception.
            self.assertEqual(probe.read_guest(path, 64, decoded)["in_race"], 0)
            # Matching two incorrect course buffers cannot be promoted as
            # semantic parity merely because the track selector is still 1.

    def test_first_divergence_is_event_relative_and_reports_exact_values(self):
        rows = [
            {"relative_frame": frame, "in_race": 1, "track_id": 1,
             "p1_next_checkpoint": 3} for frame in probe.CHECKPOINTS
        ]
        self.assertIsNone(probe.compare(rows, [dict(x) for x in rows]))
        modified = [dict(x) for x in rows]
        target_index = probe.CHECKPOINTS.index(210)
        modified[target_index]["p1_next_checkpoint"] = 2
        diff = probe.compare(rows, modified)
        self.assertEqual(diff["relative_frame"], 210)
        self.assertEqual(diff["fields"], ["p1_next_checkpoint"])
        self.assertEqual(diff["reference"]["p1_next_checkpoint"], 3)
        self.assertEqual(diff["native"]["p1_next_checkpoint"], 2)
        with self.assertRaisesRegex(probe.SceneReplayError, "incomplete"):
            probe.compare(rows[:-1], rows)
        modified[target_index]["relative_frame"] += 1
        with self.assertRaisesRegex(probe.SceneReplayError, "alignment"):
            probe.compare(rows, modified)


if __name__ == "__main__":
    unittest.main()
