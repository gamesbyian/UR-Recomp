"""Synthetic ROM-free QA-01 route input/source script integrity negative tests."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_event_route_artifact_audit as route


def make_fixture(folder: Path, case: str = "bowl") -> dict:
    replay = folder / "work" / case / "replay"
    replay.mkdir(parents=True, exist_ok=True)
    script = (
        "dump race-entered\n"
        "dump scene-00001\n"
        "dump scene-00002\n"
        "dump result-onset\n"
        "dump result-stable\n"
        + ("dump result-tally\n" if case == "bowl" else "")
    )
    (replay / "complete.script").write_text(script, encoding="ascii")
    (replay / "ref.input").write_text("100:3:12\n110:2:7\n", encoding="ascii")
    (replay / "pinned-baldosa.input").write_text("102:3:012\n112:2:007\n", encoding="ascii")
    sha = hashlib.sha256(script.encode("ascii")).hexdigest()
    return {
        "name": case, "native_frame_shift": 2,
        "relative_sample_frames": [0, 1, 2],
        "input_sha256": sha, "reference_script_sha256": sha,
    }


class EventRouteArtifactsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.report = make_fixture(self.root)
        self.replay = self.root / "work" / "bowl" / "replay"

    def test_original_and_native_masks_same_independently_shifted_route(self):
        result = route.audit(self.root, self.report)
        self.assertTrue(result["original_native_supplied_masks_and_durations_equal"])
        self.assertEqual(result["input_event_rows_per_guest"], 2)
        self.assertEqual(result["native_supplied_input_shift_exact"], 2)
        self.assertFalse(result["guest_controller_consumption_proven"])
        self.assertEqual(result["release_credit"], 0)

    def test_missing_corrupt_or_reordered_actual_input_denied(self):
        path = self.replay / "pinned-baldosa.input"
        original = path.read_bytes()
        for data in (b"", b"102:3:012\n", b"102:3:012\n111:2:007\n",
                     b"102:3:013\n112:2:007\n", b"112:2:007\n102:3:012\n",
                     b"102:0:012\n112:2:007\n", b"102:3:012\n112:2:000\n",
                     b"102:3:012\n112:2:007"):
            with self.subTest(data=data):
                path.write_bytes(data)
                with self.assertRaises(ValueError):
                    route.audit(self.root, self.report)
        path.write_bytes(original)

    def test_replay_script_changed_missing_or_observation_removed_denied(self):
        p = self.replay / "complete.script"
        source = p.read_text()
        for change in (source.replace("dump result-stable", "wait 6"),
                       source.replace("dump scene-00002\n", ""),
                       source + "dump result-onset\n"):
            p.write_text(change)
            with self.assertRaises(ValueError):
                route.audit(self.root, self.report)
        p.unlink()
        with self.assertRaises(ValueError):
            route.audit(self.root, self.report)

    def test_declared_shift_or_script_hash_cannot_forge_supplied_events(self):
        for corrupt in (
            dict(self.report, native_frame_shift=3),
            dict(self.report, input_sha256="a"*64),
            dict(self.report, reference_script_sha256="b"*64),
        ):
            with self.subTest(corrupt=corrupt):
                with self.assertRaises(ValueError):
                    route.audit(self.root, corrupt)

    def test_original_only_switcher_script_retained_and_hashed(self):
        report = make_fixture(self.root, "switcher")
        replay = self.root / "work" / "switcher" / "replay"
        extra = (replay / "complete.script").read_text() + "dump source-host-minus-one\n"
        other = replay / "switcher-reference-penultimate.script"
        other.write_text(extra)
        report["reference_script_sha256"] = hashlib.sha256(extra.encode()).hexdigest()
        self.assertEqual(
            route.audit(self.root, report)["original_reference_script_sha256"],
            report["reference_script_sha256"],
        )
        other.unlink()
        with self.assertRaises(ValueError):
            route.audit(self.root, report)


if __name__ == "__main__":
    unittest.main()
