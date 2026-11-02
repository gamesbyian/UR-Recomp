"""Fail-closed controls for additional voice-7 key-ons in a PCM witness window."""
from __future__ import annotations

import sys
import tempfile
import unittest
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_native_pcm_at_kon as pcm


class KonWindowIsolationTests(unittest.TestCase):
    def capture(self, other_sample: int):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "kon.wav"
            events = [
                {"t": "reg", "adr": "0x4c", "val": "0x80", "s": 40000},
                {"t": "reg", "adr": "0x4c", "val": "0x80", "s": other_sample},
            ]
            calls = []

            def command(line):
                calls.append(line)
                parts = line.split(" ")
                self.assertEqual((parts[0], parts[2:]), ("audio_wav", ["39500", "2500"]))
                staged_path = Path(parts[1])
                self.assertNotEqual(staged_path, path)
                with wave.open(str(staged_path), "wb") as wav:
                    wav.setnchannels(2)
                    wav.setsampwidth(2)
                    wav.setframerate(32040)
                    wav.writeframes(b"\x00\x00\x00\x00" * 2500)
                return {"ok": True, "path": parts[1], "start": 39500, "count": 2500}

            try:
                result = pcm.capture_kon_pcm(
                    command, events=events, produced=45000,
                    kon_sample_index=40000, wav_path=path,
                    before=500, after=2000)
            except ValueError as exc:
                self.assertFalse(path.exists(), "ambiguous window must not write a WAV")
                return str(exc), len(calls)
            return result, len(calls)

    def test_second_kon_inside_wav_window_is_rejected_before_capture(self):
        for sample in (39500, 39999, 40001, 41999):
            with self.subTest(sample=sample):
                result, calls = self.capture(sample)
                self.assertIn("ambiguous", result)
                self.assertEqual(calls, 0)

    def test_second_kon_outside_wav_window_does_not_poison_capture(self):
        for sample in (39499, 42000, 43000):
            with self.subTest(sample=sample):
                result, calls = self.capture(sample)
                self.assertEqual(result["kon_sample_index"], 40000)
                self.assertEqual(calls, 1)


if __name__ == "__main__":
    unittest.main()
