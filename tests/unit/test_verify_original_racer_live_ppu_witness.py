"""ROM-free real-file negative controls for live original PPU trace receipts."""
import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from tools.art.verify_original_racer_live_ppu_witness import validate, ROM_SHA, SCHEMA


class LiveOriginalWitnessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "frames").mkdir()
        (self.root / "oam").mkdir()
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
        image = f"frames/{player}-{i}"
        alpha = self.a if name == "a" else self.b
        (self.root / image).write_bytes(alpha)
        oam = f"oam/{i}"
        oam_bytes = bytes([i % 256]) * 544
        (self.root / oam).write_bytes(oam_bytes)
        return {"emulated_frame_index": i, "input_replay_frame_index": i,
                "player": player, "binary_alpha_file": image,
                "binary_alpha_sha256": hashlib.sha256(alpha).hexdigest(),
                "oam_binary_file": oam,
                "oam_sha256": hashlib.sha256(oam_bytes).hexdigest()}

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
                (self.root / "frames" / "p1-10").write_bytes(bytes([2])+bytes(4095))
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate(q, self.root)
            (self.root / "frames" / "p1-10").write_bytes(self.a)

    def test_duplicate_and_backward_frame_rejected(self):
        for i in (10, 9):
            q = copy.deepcopy(self.record)
            q["frames"][1]["emulated_frame_index"] = i
            with self.assertRaises(ValueError):
                validate(q, self.root)

    def test_authentic_blank_frames_preserve_disappearance_hold_and_return(self):
        # A live original sprite can be hidden or offscreen without a missing
        # capture. Zero-alpha frames are real observations, not registry gaps.
        blank = bytes(4096)
        (self.root / "frames" / "blank-11").write_bytes(blank)
        (self.root / "frames" / "blank-12").write_bytes(blank)
        q = copy.deepcopy(self.record)
        first = self.row(10, "a")
        hidden1 = self.row(11, "a")
        hidden2 = self.row(12, "a")
        last = self.row(13, "b")
        for hidden in (hidden1, hidden2):
            hidden["binary_alpha_file"] = f"frames/blank-{hidden['emulated_frame_index']}"
            hidden["binary_alpha_sha256"] = hashlib.sha256(blank).hexdigest()
        q["frames"] = [first, hidden1, hidden2, last]
        r = validate(q, self.root)
        self.assertEqual(r["live_consecutive_edges"], 3)
        self.assertEqual(r["live_silhouette_change_edges"], 2)
        self.assertEqual(r["live_silhouette_hold_edges"], 1)
        self.assertEqual([x["original_binary_silhouette_changed"]
                          for x in r["edges"]], [True, False, True])
        # Empty captures still require correct actual-byte provenance.
        q["frames"][1]["binary_alpha_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "invalid or stale"):
            validate(q, self.root)

    def test_independent_player_tracks(self):
        q = copy.deepcopy(self.record)
        q["frames"].insert(1, self.row(10, "b", "p2"))
        r = validate(q, self.root)
        self.assertEqual(r["live_consecutive_edges"], 1)
        self.assertEqual(r["captured_player_frame_counts"], {"p1": 3, "p2": 1})


    def test_same_alpha_file_reuse_and_hardlink_rejected(self):
        for alias in ("same-path", "hardlink", "symlink"):
            q = copy.deepcopy(self.record)
            if alias == "same-path":
                q["frames"][2]["binary_alpha_file"] = q["frames"][1]["binary_alpha_file"]
            else:
                target = self.root / f"frames/{alias}-alias"
                source = self.root / q["frames"][1]["binary_alpha_file"]
                if alias == "hardlink":
                    os.link(source, target)
                else:
                    target.symlink_to(source)
                q["frames"][2]["binary_alpha_file"] = f"frames/{alias}-alias"
            with self.subTest(alias=alias), self.assertRaises(ValueError):
                validate(q, self.root)

    def test_distinct_alpha_files_with_equal_bytes_are_real_holds(self):
        q = copy.deepcopy(self.record)
        q["frames"][2] = self.row(12, "b")
        result = validate(q, self.root)
        self.assertEqual(result["live_consecutive_edges"], 2)
        self.assertEqual(result["live_silhouette_hold_edges"], 1)

    def test_actual_oam_bytes_required_and_not_reused_across_ticks(self):
        for case in ("missing", "wrong-sha", "truncated", "reused", "hardlink"):
            q = copy.deepcopy(self.record)
            if case == "missing":
                q["frames"][1].pop("oam_binary_file")
            elif case == "wrong-sha":
                q["frames"][1]["oam_sha256"] = "0" * 64
            elif case == "truncated":
                (self.root / "oam/11").write_bytes(b"x" * 543)
            elif case == "reused":
                q["frames"][2]["oam_binary_file"] = "oam/11"
                q["frames"][2]["oam_sha256"] = q["frames"][1]["oam_sha256"]
            else:
                (self.root / "oam/hardlink").hardlink_to(self.root / "oam/11")
                q["frames"][2]["oam_binary_file"] = "oam/hardlink"
                q["frames"][2]["oam_sha256"] = q["frames"][1]["oam_sha256"]
            with self.subTest(case=case), self.assertRaises(ValueError):
                validate(q, self.root)
            (self.root / "oam/11").write_bytes(bytes([11]) * 544)

    def test_interleaved_players_share_global_frame_replay_and_oam(self):
        q = copy.deepcopy(self.record)
        q["frames"].insert(1, self.row(10, "b", "p2"))
        self.assertEqual(validate(q, self.root)["captured_player_frame_counts"]["p2"], 1)
        for bad in ("replay", "oam", "backward-global", "replay-regression"):
            altered = copy.deepcopy(q)
            if bad == "replay":
                altered["frames"][1]["input_replay_frame_index"] = 9
            elif bad == "oam":
                other = self.root / "oam/other"
                other.write_bytes(b"Z" * 544)
                altered["frames"][1]["oam_binary_file"] = "oam/other"
                altered["frames"][1]["oam_sha256"] = hashlib.sha256(other.read_bytes()).hexdigest()
            elif bad == "backward-global":
                altered["frames"].insert(3, self.row(9, "a", "p2"))
            else:
                altered["frames"][2]["input_replay_frame_index"] = 10
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validate(altered, self.root)

    def test_cli_exclusive_publication_rejects_dangling_symlink_and_existing(self):
        manifest = self.root / "manifest.json"
        manifest.write_text(json.dumps(self.record))
        target = self.root / "foreign-evidence.json"
        out = self.root / "verified.json"
        script = Path(__file__).resolve().parents[2] / "tools/art/verify_original_racer_live_ppu_witness.py"
        def invoke():
            return subprocess.run([sys.executable, str(script), "--manifest", str(manifest),
                                   "--out", str(out)], capture_output=True, text=True)
        out.symlink_to(target)
        self.assertNotEqual(invoke().returncode, 0)
        self.assertFalse(target.exists())
        self.assertTrue(out.is_symlink())
        out.unlink()
        self.assertEqual(invoke().returncode, 0)
        prior = out.read_bytes()
        self.assertNotEqual(invoke().returncode, 0)
        self.assertEqual(out.read_bytes(), prior)


    def test_derived_ledger_retains_distinct_actual_source_corpora(self):
        baseline = validate(self.record, self.root)
        self.assertEqual(len(baseline["capture_observations"]), 3)
        self.assertFalse(baseline["capture_producer_independently_authenticated"])
        self.assertEqual(baseline["capture_observations"][0]["binary_alpha_sha256"],
                         hashlib.sha256(self.a).hexdigest())
        q = copy.deepcopy(self.record)
        alternate = bytes([0, 0, 1]) + bytes(4093)
        (self.root / "frames/p1-10").write_bytes(alternate)
        q["frames"][0]["binary_alpha_sha256"] = hashlib.sha256(alternate).hexdigest()
        other = validate(q, self.root)
        self.assertEqual(baseline["edges"], other["edges"])
        self.assertNotEqual(baseline["capture_observations"],
                            other["capture_observations"])
        changed_oam = b"Z" * 544
        (self.root / "oam/13").write_bytes(changed_oam)
        q["frames"][2]["oam_sha256"] = hashlib.sha256(changed_oam).hexdigest()
        third = validate(q, self.root)
        self.assertEqual(other["edges"], third["edges"])
        self.assertNotEqual(other["capture_observations"],
                            third["capture_observations"])

    def test_atomic_ledger_visibility_and_foreign_writer_race(self):
        from unittest.mock import patch
        from tools.art.no_replace_report import publish_text_once

        destination = self.root / "atomic-ledger.json"
        payload = json.dumps(validate(self.record, self.root), sort_keys=True) + "\\n"
        original_link = os.link

        def inspect_before_link(staged, target):
            self.assertFalse(destination.exists())
            self.assertEqual(Path(staged).read_text(), payload)
            return original_link(staged, target)

        with patch("tools.art.no_replace_report.os.link",
                   side_effect=inspect_before_link):
            publish_text_once(destination, payload)
        self.assertEqual(destination.read_text(), payload)

        foreign = self.root / "foreign-ledger.json"
        def competing_writer(staged, target):
            foreign.write_text("foreign complete report")
            return original_link(staged, target)

        with patch("tools.art.no_replace_report.os.link",
                   side_effect=competing_writer):
            with self.assertRaises(FileExistsError):
                publish_text_once(foreign, payload)
        self.assertEqual(foreign.read_text(), "foreign complete report")
        self.assertFalse(any(self.root.glob(".ur-report-stage-*")))

        failed = self.root / "failed-ledger.json"
        with patch("tools.art.no_replace_report.os.fsync",
                   side_effect=OSError("simulated incomplete staging")):
            with self.assertRaises(OSError):
                publish_text_once(failed, payload)
        self.assertFalse(failed.exists())
        self.assertFalse(any(self.root.glob(".ur-report-stage-*")))


if __name__ == "__main__":
    unittest.main()
