import math
import struct
import tempfile
import unittest
from pathlib import Path

from tools.analyze_sdl_audio_envelope import extract_envelope


class AudioDeviceEnvelopeTests(unittest.TestCase):
    def make_capture(self, root: Path, frames: list, *, rate: int = 8000):
        log, pcm = root / "capture.log", root / "audio.raw"
        log.write_text(
            f"Writing to file [{pcm}], format=S16LE channels=2 freq={rate}.\n",
            encoding="utf-8",
        )
        pcm.write_bytes(b"".join(struct.pack("<hh", *pair) for pair in frames))
        return log, pcm

    def test_100ms_windows_report_rms_peak_and_end_relative_offsets(self):
        with tempfile.TemporaryDirectory() as folder:
            log, pcm = self.make_capture(
                Path(folder),
                [(1000, -2000)] * 8000 + [(0, 0)] * 8000,
            )
            report = extract_envelope(log, pcm, last_seconds=2.0, window_ms=100)
            self.assertEqual(report["audio_origin"], "sdl3-disk-playback")
            self.assertEqual(report["sample_rate"], 8000)
            self.assertEqual(report["captured_tail_frames"], 16000)
            self.assertEqual(len(report["windows"]), 20)
            first, boundary, last = (
                report["windows"][0], report["windows"][10], report["windows"][-1]
            )
            self.assertEqual(first["rms"], [1000, 2000])
            self.assertEqual(first["peak"], [1000, 2000])
            self.assertEqual(first["start_seconds_before_end"], 2)
            self.assertEqual(first["end_seconds_before_end"], 1.9)
            self.assertEqual(boundary["rms"], [0, 0])
            self.assertEqual(boundary["peak_adjacent_step"], [1000, 2000])
            self.assertEqual(last["end_seconds_before_end"], 0)
            self.assertEqual(last["zero_fraction"], [1, 1])

    def test_transient_just_before_pause_boundary_is_not_erased_by_rms(self):
        with tempfile.TemporaryDirectory() as folder:
            frames = [(0, 0)] * 8000
            frames[500] = (32767, -32768)
            log, pcm = self.make_capture(Path(folder), frames)
            report = extract_envelope(log, pcm, last_seconds=1, window_ms=100)
            self.assertGreater(report["windows"][0]["peak_adjacent_step"][0], 30000)
            self.assertGreater(report["windows"][0]["peak_adjacent_step"][1], 30000)
            self.assertLess(report["windows"][0]["combined_rms"], 2000)
            self.assertEqual(report["windows"][1]["peak_adjacent_step"], [0, 0])

    def test_partial_capture_and_final_short_bucket_remain_bounded(self):
        with tempfile.TemporaryDirectory() as folder:
            log, pcm = self.make_capture(Path(folder), [(500, -500)] * 17)
            r = extract_envelope(log, pcm, last_seconds=1, window_ms=100)
            self.assertEqual(len(r["windows"]), 1)
            self.assertEqual(r["windows"][0]["frames"], 17)
            self.assertEqual(r["windows"][0]["rms"], [500, 500])
            self.assertAlmostEqual(r["captured_tail_seconds"], 17 / 8000, places=6)

    def test_mismatched_log_pcm_invalid_format_and_corrupt_frame_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            log, pcm = self.make_capture(Path(folder), [(0, 0)] * 8000)
            log.write_text(
                f"Writing to file [{Path(folder) / 'stale.raw'}], "
                "format=S16LE channels=2 freq=8000.\n"
            )
            with self.assertRaisesRegex(ValueError, "destination does not match"):
                extract_envelope(log, pcm)
            log.write_text(f"Writing to file [{pcm}], format=F32 channels=2 freq=8000.\n")
            with self.assertRaisesRegex(ValueError, "unsupported disk PCM format"):
                extract_envelope(log, pcm)
            log.write_text(f"Writing to file [{pcm}], format=S16LE channels=2 freq=8000.\n")
            with pcm.open("ab") as fd:
                fd.write(b"x")
            with self.assertRaisesRegex(ValueError, "incomplete stereo PCM"):
                extract_envelope(log, pcm)

    def test_bounded_windows_and_nonfinite_parameters(self):
        with tempfile.TemporaryDirectory() as folder:
            log, pcm = self.make_capture(Path(folder), [(1, -1)] * 8000)
            for length, width in ((float("nan"), 100), (1, 0), (11, 100),
                                  (1, 501), (1, True), (False, 100)):
                with self.subTest(length=length, width=width):
                    with self.assertRaisesRegex(ValueError, "invalid audio envelope"):
                        extract_envelope(log, pcm, last_seconds=length, window_ms=width)


if __name__ == "__main__":
    unittest.main()
