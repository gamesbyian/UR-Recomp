import tempfile
import unittest
import wave
from pathlib import Path

from tools.analyze_reference_audio_windows import analyze, window_metrics, parse_log


class ReferenceAudioWindowTests(unittest.TestCase):
    def test_named_checkpoint_window(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            log=root/"run.log"
            wav=root/"run.wav"
            log.write_text(
                "core timing: fps=60.0000 sample_rate=600.00\n"
                "script f=60 dump main-menu-ready fb=256x224\n"
                "script f=120 dump now-playing-ready fb=256x224\n"
                "script f=180 dump race-entered fb=256x224\n"
            )
            with wave.open(str(wav),"wb") as w:
                w.setnchannels(2); w.setsampwidth(2); w.setframerate(600)
                frame=(1000).to_bytes(2,"little",signed=True)*2
                w.writeframes(frame*2000)
            report=analyze(log,wav,["main-menu-ready","race-entered"])
            self.assertGreater(report["checkpoints"]["main-menu-ready"]["rms"],0)
            self.assertEqual(report["checkpoints"]["race-entered"]["peak"],1000)


    def test_truncated_race_tail_is_reported_not_hidden(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            wav = root / "tail.wav"
            with wave.open(str(wav), "wb") as w:
                w.setnchannels(2)
                w.setsampwidth(2)
                w.setframerate(600)
                w.writeframes((1).to_bytes(2, "little") * 2 * 110)
            row = window_metrics(wav, center_frame=10, fps=60, radius_frames=30)
            self.assertTrue(row["window_truncated"])
            self.assertEqual(row["pcm_start_frame"], 0)
            self.assertEqual(row["pcm_end_frame"], 110)
            self.assertEqual(row["pcm_frames"], 110)

    def test_out_of_capture_checkpoint_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            wav = Path(td) / "short.wav"
            with wave.open(str(wav), "wb") as w:
                w.setnchannels(2)
                w.setsampwidth(2)
                w.setframerate(600)
                w.writeframes(bytes(4 * 100))
            with self.assertRaisesRegex(ValueError, "beyond captured PCM"):
                window_metrics(wav, center_frame=100, fps=60)
            with self.assertRaisesRegex(ValueError, "invalid audio checkpoint"):
                window_metrics(wav, center_frame=-1, fps=60)

    def test_invalid_core_timing_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "run.log"
            for text in ("core timing: fps=0 sample_rate=600", "core timing: fps=60 sample_rate=0"):
                log.write_text(text + chr(10))
                with self.assertRaisesRegex(ValueError, "invalid core timing"):
                    parse_log(log)


if __name__ == "__main__":
    unittest.main()
