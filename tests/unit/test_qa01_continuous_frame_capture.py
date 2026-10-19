"""ROM-free contracts for actual Snesref/Baldosa script frame capture bridge."""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_frame_capture_replay as bridge
import qa01_frame_fingerprint as frames
import qa01_qualify_authentic_bowl_frames as authentic_bowl
import qa01_verify_frame_capture as verifier
import probe_original_event_complete as replay


class SourceAcknowledgedCaptureTests(unittest.TestCase):
    def identity(self):
        return {
            "source_sha": "a" * 40,
            "rom_sha256": "b" * 64,
            "movie_sha256": "c" * 64,
            "input_sha256": "d" * 64,
            "observation_phase": "post-script-dump",
            "original_frame_origin": 1017,
            "native_frame_origin": 2017,
            "masked_wram_bytes": 0,
            "masked_sram_bytes": 0,
        }

    def fixture(self, root):
        sides = {}
        for guest, frame_origin in (("original", 1017), ("native", 2017)):
            directory = root / guest
            directory.mkdir()
            log = root / (guest + ".log")
            lines = []
            for relative in range(1, 4):
                tag = f"qa01-frame-{relative:06d}"
                host = frame_origin + relative
                tail = ("fb=256x224 RGB565 sram=8192 ppuw=0"
                        if guest == "original" else "ok")
                lines.append(f"script f={host} dump {tag} {tail}")
                wram = bytearray(frames.WRAM)
                sram = bytearray(frames.SRAM)
                if guest == "native" and relative == 2:
                    wram[0x1ED] = 0x83
                if guest == "native" and relative == 3:
                    sram[37] = 0x21
                (directory / f"{tag}.wram.bin").write_bytes(wram)
                (directory / f"{tag}.sram.bin").write_bytes(sram)
            # These are real permitted extra semantic checkpoints; a requested
            # continuous subinterval must not refuse other acknowledged tags.
            lines.append(f"script f={frame_origin + 4} dump scene-00004 ok")
            log.write_text("\n".join(lines) + "\n")
            sides[guest] = (directory, log)
        return sides

    def audit(self, root, sides, *, cap=10):
        return bridge.audit_replay(
            original_root=sides["original"][0],
            native_root=sides["native"][0],
            original_log=sides["original"][1],
            native_log=sides["native"][1],
            identity=self.identity(), start=1, end=3,
            prefix="qa01-frame-", width=6,
            report=root / "fingerprints.json",
            retained=root / "retained",
            review=root / "independent.json",
            max_retained=cap)

    def test_full_raw_reopened_with_real_guest_frame_acknowledgments(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            sides = self.fixture(root)
            stats = self.audit(root, sides)
            report = json.loads((root / "fingerprints.json").read_text())
            verdict = json.loads((root / "independent.json").read_text())
            self.assertEqual(stats["original_guest_acknowledged_frames"], 3)
            self.assertEqual(stats["native_guest_acknowledged_frames"], 3)
            self.assertEqual(stats["retained_full_raw_image_bytes"], 6 * (frames.WRAM + frames.SRAM))
            self.assertEqual(report["full_unmasked_differing_byte_occurrences"],
                             {"wram": 1, "sram": 1})
            self.assertEqual(report["first_differing_relative_frame"],
                             {"wram": 2, "sram": 3})
            self.assertEqual(verdict["verified_raw_files"], 12)
            self.assertEqual(verdict["complete_USA_events_accepted"], 0)
            raw = root / "retained" / "native-relative-000002-wram.bin"
            data = bytearray(raw.read_bytes())
            data[0x1ED] ^= 0x01
            raw.write_bytes(data)
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                verifier.verify(report, root / "retained")

    def test_bounded_window_independently_reopens_even_equal_middle_frame(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            sides = self.fixture(root)
            native = sides["native"][0]
            # All three observed source/native frames are exactly equal.
            # Frames 1 and 3 are boundaries. Frame 2 would previously have
            # only a self-asserted digest, not independent retained bytes.
            (native / "qa01-frame-000002.wram.bin").write_bytes(
                bytes(frames.WRAM))
            (native / "qa01-frame-000003.sram.bin").write_bytes(
                bytes(frames.SRAM))
            metrics = self.audit(root, sides)
            report = json.loads((root / "fingerprints.json").read_text())
            verdict = json.loads((root / "independent.json").read_text())
            self.assertEqual(report["raw_retained_scope"],
                             "all compared frame pairs")
            self.assertEqual(report["full_unmasked_differing_byte_occurrences"],
                             {"wram": 0, "sram": 0})
            self.assertEqual(len(report["raw_retained_members"]), 12)
            self.assertEqual(verdict["verified_raw_frames"], 3)
            self.assertEqual(
                verdict["digest_only_equal_frames_not_independently_reopened"], 0)
            self.assertTrue(metrics["all_observed_raw_frames_independently_reopened"])
            # The interior unchanged frame has now been re-opened, and its
            # actual evidence cannot be modified without invalidating review.
            interior = root / "retained" / "native-relative-000002-wram.bin"
            original = bytearray(interior.read_bytes())
            original[494] ^= 0x01
            interior.write_bytes(original)
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                verifier.verify(report, root / "retained")

    def test_large_window_refuses_silent_raw_retention_truncation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            sides = self.fixture(root)
            with self.assertRaises(ValueError):
                self.audit(root, sides, cap=2)

    def test_no_dropped_relabelled_duplicated_or_truncated_frame(self):
        for fault in ("missing_log", "duplicate_log", "shifted_host",
                      "missing_wram", "truncated_sram", "retention_cap",
                      "fake_original_success", "fake_native_success"):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                sides = self.fixture(root)
                original_dir, original_log = sides["original"]
                if fault == "missing_log":
                    original_log.write_text(original_log.read_text().replace(
                        "script f=1019 dump qa01-frame-000002 fb=256x224 RGB565 sram=8192 ppuw=0\n", ""))
                elif fault == "duplicate_log":
                    original_log.write_text(original_log.read_text() +
                                            "script f=1019 dump qa01-frame-000002 fb=256x224 RGB565 sram=8192 ppuw=0\n")
                elif fault == "shifted_host":
                    original_log.write_text(original_log.read_text().replace(
                        "script f=1019 dump qa01-frame-000002",
                        "script f=1020 dump qa01-frame-000002"))
                elif fault == "fake_original_success":
                    original_log.write_text(original_log.read_text().replace(
                        "fb=256x224 RGB565 sram=8192 ppuw=0",
                        "failed", 1))
                elif fault == "fake_native_success":
                    nat_log = sides["native"][1]
                    nat_log.write_text(nat_log.read_text().replace(
                        " dump qa01-frame-000002 ok",
                        " dump qa01-frame-000002 FAILED"))
                elif fault == "missing_wram":
                    (original_dir / "qa01-frame-000002.wram.bin").unlink()
                elif fault == "truncated_sram":
                    (original_dir / "qa01-frame-000003.sram.bin").write_bytes(b"x")
                with self.assertRaises(ValueError):
                    self.audit(root, sides, cap=1 if fault == "retention_cap" else 10)
                if fault in ("missing_log", "duplicate_log", "shifted_host",
                             "missing_wram", "truncated_sram",
                             "fake_original_success", "fake_native_success"):
                    self.assertFalse((root / "fingerprints.json").exists())

    def test_archived_result_relative_tags_and_sparse_extra_captures(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            sides = self.fixture(root)
            for name, (directory, log) in sides.items():
                for relative in range(1, 4):
                    original = directory / f"qa01-frame-{relative:06d}"
                    changed = directory / f"bowl-next-switcher-{relative:03d}"
                    for kind in ("wram", "sram"):
                        (original.with_suffix(f".{kind}.bin")).rename(
                            changed.with_suffix(f".{kind}.bin"))
                log.write_text(log.read_text().replace(
                    "qa01-frame-00000", "bowl-next-switcher-00"))
            metrics = bridge.audit_replay(
                original_root=sides["original"][0],
                native_root=sides["native"][0],
                original_log=sides["original"][1],
                native_log=sides["native"][1], identity=self.identity(),
                start=1, end=3, prefix="bowl-next-switcher-", width=3,
                report=root / "r.json", retained=root / "raw", review=root / "v.json")
            self.assertEqual(metrics["original_guest_acknowledged_frames"], 3)
            self.assertEqual(metrics["accepted_USA_events"], 0)


class ArchivedGenuineInputGateTests(unittest.TestCase):
    def test_fake_or_modified_archive_never_enters_real_data_qualification(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fake = root / "bogus.zip"
            fake.write_bytes(b"not a genuine source archive")
            with self.assertRaisesRegex(ValueError, "SHA-256 changed"):
                authentic_bowl.qualify(fake, root / "never-created")
            self.assertFalse((root / "never-created").exists())


class FrameScriptTests(unittest.TestCase):
    def test_adds_each_frame_once_preserving_semantic_scene_and_wait_budget(self):
        frames_list = replay.sample_frames("zoom-zoo", 5163)
        baseline = replay.replay_script(2, 0xBC, frames_list, False)
        expanded = replay.replay_script(
            2, 0xBC, frames_list, False, continuous_window=(1, 16))
        for frame in range(1, 17):
            self.assertEqual(expanded.count(
                f"dump qa01-frame-{frame:06d}\n"), 1)
        self.assertEqual(
            [line for line in baseline.splitlines() if line.startswith("dump scene-")],
            [line for line in expanded.splitlines() if line.startswith("dump scene-")])
        # Capture is an extra observation, not an extra frame. The total
        # waits in the race-relative segment before the result stay exact.
        def wait_total(script):
            race = script.split("dump race-entered\n", 1)[1]
            race = race.split("until 009F == BC 9000", 1)[0]
            return sum(int(line.split()[1]) for line in race.splitlines()
                       if line.startswith("wait "))
        self.assertEqual(wait_total(expanded), wait_total(baseline))
        self.assertEqual(replay.replay_script(
            2, 0xBC, frames_list, False, continuous_window=None), baseline)

    def test_complete_entry_to_real_result_onset_dumps_every_frame(self):
        samples = replay.sample_frames("zoom-zoo", 5163)
        baseline = replay.replay_script(2, 0xBC, samples, False)
        expanded = replay.replay_script(
            2, 0xBC, samples, False,
            continuous_window=(0, 5163), source_result_frame=5163)
        # Entry is part of the same clock: two dumps without an extra wait.
        self.assertIn(
            "dump race-entered\ndump qa01-frame-000000\n", expanded)
        self.assertIn(
            "dump result-onset\ndump qa01-frame-005163\n", expanded)
        labels = [line for line in expanded.splitlines()
                  if line.startswith("dump qa01-frame-")]
        self.assertEqual(len(labels), 5164)
        self.assertEqual(len(set(labels)), 5164)
        self.assertEqual(labels[0], "dump qa01-frame-000000")
        self.assertEqual(labels[-1], "dump qa01-frame-005163")
        # The result is still reached by the guest's semantic predicate.
        self.assertEqual(expanded.count("until 009F == BC 9000"), 1)
        self.assertEqual(expanded.count("dump result-onset"), 1)
        # The baseline's final sparse observation is much earlier than
        # source result onset; baseline `until` implicitly advances all the
        # remaining frames. Continuous capture makes those advances explicit.
        # Therefore the *sum of literal wait commands* must differ, while
        # every pre-existing semantic scene dump keeps the same frame.
        def pre_result(script):
            return script.split("dump race-entered\n", 1)[1].split(
                "until 009F == BC 9000", 1)[0]

        def timeline(script):
            host_frame = 0
            semantic = []
            diagnostics = []
            for line in pre_result(script).splitlines():
                if line.startswith("wait "):
                    host_frame += int(line.split()[1])
                elif line.startswith("dump scene-"):
                    semantic.append((host_frame, line))
                elif line.startswith("dump qa01-frame-"):
                    diagnostics.append((host_frame, line))
            return host_frame, semantic, diagnostics

        old_frame, old_scene, _ = timeline(baseline)
        frame, scene, diagnostic = timeline(expanded)
        self.assertGreater(frame, old_frame)
        self.assertEqual(frame, 5162)
        self.assertEqual(scene, old_scene)
        self.assertEqual(
            diagnostic,
            [(index, f"dump qa01-frame-{index:06d}")
             for index in range(5163)])
        # At +5162 the script still invokes the *actual* result predicate,
        # which may advance to +5163; no fabricated frame-5163 wait or
        # synthetic menu state is inserted.
        self.assertIn(
            "dump qa01-frame-005162\nuntil 009F == BC 9000\n"
            "dump result-onset\ndump qa01-frame-005163\n", expanded)

    def test_bad_window_rejected_without_emulator(self):
        samples = replay.sample_frames("zoom-zoo", 5163)
        for bounds in ((-1, 3), (0, -1), (5, 2), (1, 20001),
                       (1.5, 4), (1, 4.0)):
            with self.subTest(bounds=bounds), self.assertRaises(ValueError):
                replay.replay_script(
                    2, 0xBC, samples, False, continuous_window=bounds)
        with self.assertRaisesRegex(ValueError, "invalid bounded"):
            replay.replay_script(
                2, 0xBC, samples, False, continuous_window=(0, 5164),
                source_result_frame=5163)


if __name__ == "__main__":
    unittest.main()
