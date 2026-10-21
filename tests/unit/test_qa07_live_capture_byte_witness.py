"""Live audiovisual byte presence witness, never an MP4 encoder or release test."""
import hashlib
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
from qa07_live_capture_byte_witness import LiveMediaWitness
from qa07_live_capture_eligibility import State


class ByteWitnessTests(unittest.TestCase):
    def start(self, **kw):
        witness=LiveMediaWitness(width=2,height=1,audio_samples_per_frame=2)
        witness.start(attempt="attempt-1",profile="P1",race_entry_frame=10,
                      capture_start_frame=10,**kw)
        return witness

    def test_two_real_payloads_and_hashes(self):
        w=self.start()
        frames=(bytes(range(8)),bytes(range(8,16)))
        audio=(b"\x00\x01\x02\x03\x04\x05\x06\x07",
               b"\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f")
        for n in range(2):
            w.append(attempt="attempt-1",frame_number=10+n,bgra=frames[n],
                     pcm_stereo_s16=audio[n])
        result=w.finish(attempt="attempt-1",profile="P1",terminal_frame=11)
        self.assertEqual(result["frames"],2)
        self.assertEqual(result["bgra_sha256"],hashlib.sha256(b"".join(frames)).hexdigest())
        self.assertEqual(result["pcm_sha256"],hashlib.sha256(b"".join(audio)).hexdigest())
        self.assertFalse(result["encoded_video_verified"])
        self.assertEqual(result["release_gate_credit"],0)

    def test_boolean_only_fake_presence_refused(self):
        w=self.start()
        w.append(attempt="attempt-1",frame_number=10,bgra=True,pcm_stereo_s16=True)
        self.assertEqual(w.capture.state,State.INCOMPLETE)
        with self.assertRaises(ValueError):
            w.finish(attempt="attempt-1",profile="P1",terminal_frame=10)

    def test_short_audio_and_frame_gap(self):
        w=self.start()
        w.append(attempt="attempt-1",frame_number=10,bgra=bytes(8),pcm_stereo_s16=b"x")
        self.assertEqual(w.capture.state,State.INCOMPLETE)
        w=self.start()
        w.append(attempt="attempt-1",frame_number=11,bgra=bytes(8),pcm_stereo_s16=bytes(8))
        self.assertEqual(w.capture.state,State.INCOMPLETE)

    def test_identity_rejects_control_bidi_and_non_nfc(self):
        for attempt in (" ", "\x00run", "run\n", "e\u0301", "\u200b", "x"*129):
            with self.subTest(attempt=repr(attempt)),self.assertRaises(ValueError):
                LiveMediaWitness(width=1,height=1).start(
                    attempt=attempt,profile="P1",race_entry_frame=0,capture_start_frame=0)

    def test_wrong_attempt_and_terminal_refuse(self):
        w=self.start()
        w.append(attempt="other",frame_number=10,bgra=bytes(8),pcm_stereo_s16=bytes(8))
        self.assertEqual(w.capture.state,State.INCOMPLETE)
        w=self.start()
        w.append(attempt="attempt-1",frame_number=10,bgra=bytes(8),pcm_stereo_s16=bytes(8))
        with self.assertRaises(ValueError):
            w.finish(attempt="attempt-1",profile="P1",terminal_frame=12)

if __name__=="__main__":
    unittest.main()
