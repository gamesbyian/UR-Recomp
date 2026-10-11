"""ROM-free tests for art-trial provenance; no Pillow, GPU, or model required."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

SCRIPT = Path(__file__).resolve().parents[2] / "tools" / "art" / "validate_upscale_trials.py"
spec = importlib.util.spec_from_file_location("validate_upscale_trials", SCRIPT)
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


def tiny_png(path, w, h, rgba=(40, 70, 100, 255)):
    def part(tag, value):
        return (struct.pack(">I", len(value)) + tag + value
                + struct.pack(">I", zlib.crc32(tag + value) & 0xffffffff))
    data = b"".join(b"\x00" + bytes(rgba) * w for _ in range(h))
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)
    path.write_bytes(tool.PNG_SIG + part(b"IHDR", ihdr)
                     + part(b"IDAT", zlib.compress(data)) + part(b"IEND", b""))


def identity(path):
    return {"path": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


class UpscaleTrialTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        src, dst = self.base / "raw.png", self.base / "fourx.png"
        tiny_png(src, 3, 2)
        tiny_png(dst, 12, 8)
        self.doc = {
            "schema": tool.SCHEMA,
            "source": {**identity(src), "semantic_id": "test-source-057e",
                       "asset_kind": "racer_pose",
                       "provenance": {"capture_or_extraction": "offline synthetic unit test",
                                      "rom_or_source_identity": "UNIT-ONLY"}},
            "candidates": [{
                "id": "nearest-4x-control",
                "kind": "art_4x",
                "output": identity(dst),
                "method": {"name": "nearest", "revision_or_model_id": "first-party-1",
                           "settings": {"factor": 4}},
                "decision": "unreviewed"
            }]
        }
        self.manifest = self.base / "trial.json"

    def run_trial(self):
        self.manifest.write_text(json.dumps(self.doc))
        return tool.validate(self.manifest)

    def test_good_and_explicitly_unapproved(self):
        report = self.run_trial()
        self.assertEqual(report["candidate_count"], 1)
        self.assertEqual(report["shipping_approvals"], 0)
        self.assertEqual(report["counts"]["unreviewed"], 1)

    def test_wrong_hash_fails_closed(self):
        self.doc["source"]["sha256"] = "0" * 64
        with self.assertRaises(tool.TrialError):
            self.run_trial()

    def test_wrong_4x_dimensions_fail(self):
        tiny_png(self.base / "fourx.png", 6, 4)
        self.doc["candidates"][0]["output"] = identity(self.base / "fourx.png")
        with self.assertRaisesRegex(tool.TrialError, "four times"):
            self.run_trial()

    def test_approval_not_accepted_as_trial_decision(self):
        self.doc["candidates"][0]["decision"] = "shipping_approved"
        with self.assertRaisesRegex(tool.TrialError, "decision"):
            self.run_trial()

    def test_rejected_candidate_requires_reason(self):
        self.doc["candidates"][0]["decision"] = "rejected"
        with self.assertRaisesRegex(tool.TrialError, "review reason"):
            self.run_trial()
        self.doc["candidates"][0]["review_reason"] = "Changed wheel silhouette"
        self.assertEqual(self.run_trial()["counts"]["rejected"], 1)

    def test_generative_requires_replayable_provenance(self):
        self.doc["candidates"][0]["method"]["generative"] = True
        with self.assertRaisesRegex(tool.TrialError, "generative"):
            self.run_trial()
        self.doc["candidates"][0]["generation"] = {
            "provider": "local synthetic generator", "model_version": "test-v1",
            "request_id": "unit-no-network", "prompt_or_prompt_sha256": "same contour"}
        self.assertEqual(self.run_trial()["candidate_count"], 1)

    def test_display_preset_requires_explicit_policy(self):
        dst = self.base / "frame.png"
        tiny_png(dst, 16, 12)
        candidate = self.doc["candidates"][0]
        candidate["output"] = identity(dst)
        candidate["kind"] = "display_reference"
        with self.assertRaisesRegex(tool.TrialError, "display pixel aspect"):
            self.run_trial()
        candidate["display_policy"] = {
            "pixel_aspect": "snes_7_6", "view": "256-wide original",
            "treatment": "CRT guest-advanced"}
        self.assertEqual(self.run_trial()["candidate_count"], 1)

    def test_duplicate_and_escape_paths_rejected(self):
        self.doc["candidates"].append(dict(self.doc["candidates"][0]))
        with self.assertRaisesRegex(tool.TrialError, "unique id"):
            self.run_trial()
        self.doc["candidates"].pop()
        self.doc["source"]["path"] = "../escaped.png"
        with self.assertRaisesRegex(tool.TrialError, "traversal"):
            self.run_trial()


if __name__ == "__main__":
    unittest.main()
