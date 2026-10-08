import hashlib
import math
import struct
import tempfile
import unittest
from pathlib import Path

from tools.analyze_sdl_disk_audio import analyze, parse_disk_format


class SdlDiskAudioTests(unittest.TestCase):
    def write_capture(self, root, samples, *, fmt="S16LE", channels=2, rate=44100):
        log = root / "native.log"
        pcm = root / "audio.raw"
        log.write_text(
            "INFO: You are using the SDL disk i/o audio driver!\n"
            f"INFO: Writing to file [C:\\tmp\\audio.raw], "
            f"format={fmt} channels={channels} freq={rate}.\n",
            encoding="utf-8",
        )
        pcm.write_bytes(b"".join(struct.pack("<hh", *frame) for frame in samples))
        return log, pcm

    def test_stereo_pcm_evidence_and_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frames = [(1000, -2000)] * 9000
            log, pcm = self.write_capture(root, frames, rate=8000)
            report = analyze(log, pcm)
            self.assertEqual(report["audio_origin"], "sdl3-disk-playback")
            self.assertEqual(report["sample_rate"], 8000)
            self.assertEqual(report["pcm_frames"], 9000)
            self.assertEqual(report["peak"], 2000)
            self.assertAlmostEqual(report["rms"], math.sqrt(2500000))
            self.assertEqual(report["channel_peaks"], [1000, 2000])
            self.assertEqual(report["nonzero_fraction"], 1.0)
            self.assertEqual(report["pcm_sha256"], hashlib.sha256(pcm.read_bytes()).hexdigest())

    def test_silent_backend_rejected_even_when_file_nonempty(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log, pcm = self.write_capture(root, [(0, 0)] * 9000, rate=8000)
            with self.assertRaisesRegex(ValueError, "silent/insufficient"):
                analyze(log, pcm)

    def test_invalid_or_ambiguous_sdl_format_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log, pcm = self.write_capture(root, [(100, 100)] * 8)
            for bad in ("F32", "S32LE", "U8"):
                log.write_text(
                    f"Writing to file [audio.raw], format={bad} channels=2 freq=44100.\n"
                )
                with self.assertRaisesRegex(ValueError, "unsupported disk PCM format"):
                    analyze(log, pcm, min_duration_seconds=0)
            log.write_text("audio device opened: freq=44100\n")
            with self.assertRaisesRegex(ValueError, "exactly one SDL disk"):
                parse_disk_format(log)

    def test_invalid_channel_count_or_sample_rate_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log, pcm = self.write_capture(root, [(100, 100)] * 8)
            log.write_text("Writing to file [audio.raw], format=S16LE channels=1 freq=44100.\n")
            with self.assertRaisesRegex(ValueError, "require stereo"):
                analyze(log, pcm, min_duration_seconds=0)
            log.write_text("Writing to file [audio.raw], format=S16LE channels=2 freq=0.\n")
            with self.assertRaisesRegex(ValueError, "invalid SDL disk sample rate"):
                analyze(log, pcm, min_duration_seconds=0)

    def test_short_and_incomplete_captures_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log, pcm = self.write_capture(root, [(100, 200)] * 3, rate=8000)
            with self.assertRaisesRegex(ValueError, "too short"):
                analyze(log, pcm)
            pcm.write_bytes(pcm.read_bytes() + b"\x55")
            with self.assertRaisesRegex(ValueError, "incomplete stereo"):
                analyze(log, pcm, min_duration_seconds=0)

    def test_nonfinite_thresholds_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log, pcm = self.write_capture(root, [(100, 200)] * 5)
            with self.assertRaisesRegex(ValueError, "invalid audio acceptance thresholds"):
                analyze(log, pcm, min_duration_seconds=float("nan"))
            with self.assertRaisesRegex(ValueError, "invalid audio acceptance thresholds"):
                analyze(log, pcm, min_duration_seconds=0, min_nonzero_fraction=2)


if __name__ == "__main__":
    unittest.main()
