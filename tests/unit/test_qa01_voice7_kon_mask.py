"""Voice-7 KON is DSP register $4C bit 7, not only the literal $80 write."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_native_pcm_at_kon as pcm
import qa01_live_kon_pcm as live


def event(value: str, sample: int) -> dict:
    return {"t": "reg", "adr": "0x4c", "val": value, "s": sample}


class Voice7KonMaskTests(unittest.TestCase):
    def test_bit7_identifies_combined_keyons(self):
        self.assertEqual(pcm.kon_candidates([
            event("0x01", 39000), event("0x80", 40000),
            event("0x81", 40500), event("0xff", 41000),
        ]), [40000, 40500, 41000])

    def test_direct_capture_rejects_combined_keyon_inside_window(self):
        with tempfile.TemporaryDirectory() as tmp:
            wav = Path(tmp) / "kon.wav"
            calls = []
            with self.assertRaisesRegex(ValueError, "ambiguous"):
                pcm.capture_kon_pcm(lambda line: calls.append(line),
                    events=[event("0x80", 40000), event("0x81", 41000)],
                    produced=45000, kon_sample_index=40000, wav_path=wav,
                    before=500, after=2000)
            self.assertEqual(calls, [])
            self.assertFalse(wav.exists())

    def test_direct_capture_cannot_mislabel_combined_write_as_exact(self):
        with tempfile.TemporaryDirectory() as tmp:
            wav = Path(tmp) / "kon.wav"
            with self.assertRaisesRegex(ValueError, "missing or ambiguous"):
                pcm.capture_kon_pcm(lambda line: self.fail("WAV must not be requested"),
                    events=[event("0x81", 40000)], produced=45000,
                    kon_sample_index=40000, wav_path=wav, before=500, after=2000)

    def test_live_combined_keyon_before_exact_rejected(self):
        calls = []
        def command(line):
            calls.append(line)
            if line == "audio_stats 0":
                return {"event_count": 100, "produced": 0}
            if line == "audio_events 100 8000 1":
                return {"oldest": 0, "first": 100, "scanned": 2,
                        "events": [event("0x81", 44900), event("0x80", 45000)]}
            self.fail(f"unexpected command {line}")
        capture = Mock()
        with self.assertRaisesRegex(ValueError, "combined voice-7 KON"):
            live.watch_first_kon(command, wav_path=Path("/tmp/unused.wav"),
                before=500, after=2000, timeout=2, interval=.01,
                clock=lambda: 0, sleep=lambda _: None, capture_fn=capture)
        capture.assert_not_called()

    def test_live_combined_keyon_during_wav_rejected(self):
        state = {"head": 101, "stats": 0}
        def command(line):
            if line == "audio_stats 0":
                state["stats"] += 1
                if state["stats"] == 1:
                    return {"event_count": 100, "produced": 0}
                return {"event_count": state["head"], "produced": 47000}
            if line == "audio_events 100 8000 1":
                return {"oldest": 0, "first": 100, "scanned": 1,
                        "events": [event("0x80", 45000)]}
            if line == "audio_events 101 1 1":
                return {"oldest": 0, "first": 101, "scanned": 1,
                        "events": [event("0x81", 46000)]}
            self.fail(f"unexpected command {line}")
        def wav(*args, **kwargs):
            state["head"] = 102
            return {"kon_sample_index": 45000, "sample_frames": 2500}
        capture = Mock(side_effect=wav)
        with self.assertRaisesRegex(ValueError, "combined voice-7 KON"):
            live.watch_first_kon(command, wav_path=Path("/tmp/unused.wav"),
                before=500, after=2000, timeout=2, interval=.01,
                clock=lambda: 0, sleep=lambda _: None, capture_fn=capture)
        capture.assert_called_once()

    def test_other_voice_kon_does_not_poison_exact_voice7(self):
        state = {"stats": 0}
        def command(line):
            if line == "audio_stats 0":
                state["stats"] += 1
                if state["stats"] == 1:
                    return {"event_count": 100, "produced": 0}
                return {"event_count": 102, "produced": 47000}
            if line == "audio_events 100 8000 1":
                return {"oldest": 0, "first": 100, "scanned": 2,
                        "events": [event("0x01", 44000), event("0x80", 45000)]}
            self.fail(f"unexpected command {line}")
        capture = Mock(return_value={"kon_sample_index": 45000, "sample_frames": 2500})
        result = live.watch_first_kon(command, wav_path=Path("/tmp/unused.wav"),
            before=500, after=2000, timeout=2, interval=.01,
            clock=lambda: 0, sleep=lambda _: None, capture_fn=capture)
        self.assertEqual(result["kon_sample_index"], 45000)
        capture.assert_called_once()


if __name__ == "__main__":
    unittest.main()
