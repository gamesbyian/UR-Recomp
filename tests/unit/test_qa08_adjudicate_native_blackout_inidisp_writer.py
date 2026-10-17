"""Original/native 2P $2100 CPU versus host PPU replay must stay separate."""
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import qa08_adjudicate_native_blackout_inidisp_writer as m

class NativeBlackoutWriterSource(unittest.TestCase):
    def test_authentic_original_beam_and_native_cpu_replay_labels(self):
        self.assertEqual(m.ORIGINAL_FRAMES,tuple(range(4017,4024)))
        self.assertEqual(m.CPU_FRAMES,tuple(range(4015,4022)))
        self.assertEqual(m.REPLAY_FRAMES,tuple(range(4016,4023)))
        self.assertEqual(m.ORIGINAL_V,(230,230,230,230,230,230,231))
        self.assertEqual(m.VALUES,("02","04","06","08","0a","0c","0e"))
        self.assertIn("native_emulated_CPU_instruction_count_phase_or_frame_label_root_proven",
            (ROOT/"tools/qa08_adjudicate_native_blackout_inidisp_writer.py").read_text())
        self.assertNotIn("forcepoke(",(
            ROOT/"tools/qa08_adjudicate_native_blackout_inidisp_writer.py").read_text())
    def test_fake_artifact_rejected_by_original_source_pins(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as t:
            p=Path(t)/"invented.zip"
            p.write_bytes(b"forged original game")
            with self.assertRaises(ValueError):
                m.opened(p,m.ORIGINAL_ZIP)

if __name__=="__main__":
    unittest.main()
