import tempfile
import unittest
import wave
from pathlib import Path

from tools.analyze_reference_audio_windows import analyze


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


if __name__ == "__main__":
    unittest.main()
