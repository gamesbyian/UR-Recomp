#!/usr/bin/env python3
"""Adversarial native-compositor motion receipt validation (no fake SDL proof)."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import verify_modern_menu_motion_capture as m


def source() -> dict:
    return json.loads(m.SOURCE.read_text(encoding="utf-8"))


def capture(width: int = 256, count: int = 40, seed: int = 14,
            reduced_start: int | None = None) -> list[dict[str, int]]:
    steps = source()["transition_main_to_options"]["enter_velocity_px_per_frame"]
    events = []
    for i in range(count):
        tick = seed + i
        reduced = int(reduced_start is not None and i >= reduced_start)
        events.append({
            "ordinal": i,
            "tick60": tick,
            "selection": 0,
            "spin": (tick // 2) % 16,
            "offset": 0,
            "entrance": 0 if reduced else
                256 - sum(steps[:min(39, i)]),
            "reduced": reduced,
            "root_x": 8 if width == 256 else 11,
            "root_w": 240 if width == 256 else 320,
            "surface_w": width,
            "surface_h": 224,
            "painted": 1,
        })
    return events


def log(events: list[dict[str, int]]) -> str:
    lines = ["ordinary host text unrelated to motion receipts"]
    for row in events:
        lines.append("[SDL/native log] " + m.PREFIX +
                     " ".join(f"{k}={row[k]}" for k in m.FIELDS))
    return "\n".join(lines) + "\n"


class NativeModernMotionCaptureTests(unittest.TestCase):
    def test_original_timing_and_two_actual_source_layouts(self):
        for width in (256, 342):
            with self.subTest(width=width):
                report = m.verify_log(log(capture(width)))
                self.assertEqual(report["native_draw_count"], 40)
                self.assertEqual(report["sessions"][0]["logical_width"], width)
                self.assertEqual(
                    report["sessions"][0]["final_source_entrance_remaining_px"], 0)
                self.assertIn("SDL P7 final drawable", report["not_proven"])
                self.assertIn("human visual approval", report["not_proven"])
                with tempfile.TemporaryDirectory() as tmp:
                    src, dst = Path(tmp) / "native.log", Path(tmp) / "receipt.json"
                    src.write_text(log(capture(width)), encoding="utf-8")
                    proc = subprocess.run([
                        sys.executable,
                        str(ROOT / "tools/verify_modern_menu_motion_capture.py"),
                        "--host-log", str(src), "--out", str(dst)],
                        text=True, capture_output=True, check=False)
                    self.assertEqual(proc.returncode, 0, proc.stderr)
                    receipt = json.loads(dst.read_text())
                    self.assertEqual(receipt["original_host_log_sha256"].__len__(), 64)
                    self.assertEqual(receipt["sessions"][0]["logical_width"], width)

    def test_repeated_root_sessions_are_independently_reset(self):
        records = capture(256) + capture(342, seed=100)
        with self.assertRaisesRegex(ValueError, "unexpected native root session"):
            m.verify_log(log(records))
        result = m.verify_log(log(records), allow_multi_session=True)
        self.assertEqual(result["session_count"], 2)
        self.assertEqual([r["logical_width"] for r in result["sessions"]],
                         [256, 342])
        self.assertEqual(result["native_draw_count"], 80)

    def test_partial_session_cannot_hide_behind_later_complete_session(self):
        # Without source hide/reentry proof, a fresh ordinal zero is a
        # duplicate, not evidence of a second independently valid session.
        short_then_full = capture(count=12) + capture(seed=200)
        with self.assertRaisesRegex(ValueError, "unexpected native root session"):
            m.verify_log(log(short_then_full))
        with self.assertRaisesRegex(ValueError, "truncated native root session"):
            m.verify_log(log(short_then_full), allow_multi_session=True)
        complete_then_short = capture() + capture(count=12, seed=200)
        with self.assertRaisesRegex(ValueError, "no complete required"):
            m.verify_log(log(complete_then_short), allow_multi_session=True)

    def test_reduced_motion_and_reenable_never_replay_old_entrance(self):
        records = capture(reduced_start=4)
        for i in range(8, len(records)):
            records[i]["reduced"] = 0
            records[i]["entrance"] = 0
        result = m.verify_log(log(records))
        self.assertEqual(result["sessions"][0]["reduced_motion_frames"], 4)
        bad = deepcopy(records)
        bad[8]["entrance"] = 250
        with self.assertRaisesRegex(ValueError, "entrance phase"):
            m.verify_log(log(bad))

    def test_missing_cursor_or_wrong_clock_is_rejected(self):
        rows = capture()
        for change, expression in [
            ({"ordinal": 9}, "ordinal"),
            ({"tick60": 999}, "tick"),
            ({"spin": 15}, "spin phase"),
            ({"entrance": 255}, "entrance phase"),
            ({"painted": 0}, "invisible"),
            ({"selection": 5}, "semantic selection"),
            ({"root_w": 239}, "rectangle"),
            ({"root_x": 10}, "rectangle"),
            ({"surface_w": 320}, "geometry"),
            ({"surface_h": 240}, "geometry"),
            ({"reduced": 3}, "reduced motion"),
        ]:
            with self.subTest(change=change):
                altered = deepcopy(rows)
                altered[2].update(change)
                with self.assertRaisesRegex(ValueError, expression):
                    m.verify_log(log(altered))

    def test_midsequence_resize_or_bad_movement_is_not_source_proof(self):
        rows = capture()
        wrong = deepcopy(rows)
        wrong[30].update({
            "surface_w": 342, "root_x": 11, "root_w": 320})
        with self.assertRaisesRegex(ValueError, "mid-session"):
            m.verify_log(log(wrong))
        wrong = deepcopy(rows)
        wrong[18]["offset"] = 12
        with self.assertRaisesRegex(ValueError, "jumped"):
            m.verify_log(log(wrong))

    def test_duplicate_broken_or_unbounded_records_fail_closed(self):
        witness = log(capture())
        for corrupt in (
            witness.replace("ordinal=1 ", "ordinal=0 ", 1),
            witness.replace("spin=7 ", "spin=bogus ", 1),
            witness.replace("spin=7 ", "spin=7 spin=7 ", 1),
            witness.replace("offset=0 ", "", 1),
            witness.replace("offset=0 ", "offset=-1 ", 1),
            witness.replace("offset=0 ", "offset=18446744073709551616 ", 1),
        ):
            with self.subTest(example=corrupt[:65]):
                with self.assertRaises(ValueError):
                    m.verify_log(corrupt)
        with self.assertRaisesRegex(ValueError, "no actual"):
            m.verify_log("no host motion observations")
        with self.assertRaisesRegex(ValueError, "no complete required"):
            m.verify_log(log(capture(count=39)))

    def test_source_motion_contract_cannot_be_silently_reinterpreted(self):
        measured = source()
        measured["cursor"]["spin_period_frames"] = 33
        with self.assertRaisesRegex(ValueError, "cadence"):
            m.verify_events(capture(), measured)
        measured = source()
        measured["transition_main_to_options"][
            "enter_velocity_px_per_frame"][0] = 3
        with self.assertRaisesRegex(ValueError, "cadence"):
            m.verify_events(capture(), measured)


if __name__ == "__main__":
    unittest.main()
