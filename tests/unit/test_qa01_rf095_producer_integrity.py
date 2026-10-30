"""RF095 rejects incomplete native frame synchronization and extra WAV bytes."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest
import wave

ROOT = Path(__file__).resolve().parents[2] / 'tools'


def load_receipt():
    spec = importlib.util.spec_from_file_location('qa01_rf095_pcm_receipt',
                                                  ROOT / 'qa01_rf095_pcm_receipt.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ProducerIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        d = Path(self.temp.name)
        self.wav = d / 'ref.wav'
        self.ref_map = d / 'ref.csv'
        self.pcm = d / 'native.pcm'
        self.native_map = d / 'native.csv'
        self.ref_log = d / 'reference.log'
        self.native_log = d / 'native.log'
        with wave.open(str(self.wav), 'wb') as w:
            w.setnchannels(2)
            w.setsampwidth(2)
            w.setframerate(32040)
            w.writeframes(struct.pack('<hh', 123, -45) * 6454)
        self.ref_map.write_text('frame,samples\n' +
                                ''.join(f'{f},{f}\n' for f in range(6455)))
        self.pcm.write_bytes(struct.pack('<hh', 12, -8) * 10)
        self.native_map.write_text('frame,samples\n' +
                                   ''.join(f'{f},{f - 6447}\n'
                                           for f in range(6447, 6458)))
        self.ref_log.write_text('original replay\n')
        self.native_log.write_text('native replay\n')
        self.receipt = load_receipt()

    def analyze(self):
        return self.receipt.analyze(self.wav, self.ref_map, self.pcm,
                                    self.native_map, self.ref_log, self.native_log)

    def test_normal_complete_producers_are_accepted_as_diagnostics(self):
        result = self.analyze()
        self.assertEqual(result['original']['frames'], 7)
        self.assertEqual(result['native']['frames'], 10)
        self.assertFalse(result['audible_parity_proven'])

    def test_native_frame_boundary_sync_timeout_rejected(self):
        self.native_log.write_text('[apu] frame-boundary guest-clock sync timed out\n')
        with self.assertRaisesRegex(ValueError, 'APU frame-boundary sync timed out'):
            self.analyze()

    def test_native_watchdog_abandoned_frame_rejected(self):
        # Pinned common_cpu_infra.c emits this marker before longjmp;
        # common_rtl.c still advances the frame counter afterward.
        self.native_log.write_text('\\n=== WATCHDOG: Frame 6450 exceeded 5.1s ===\\n')
        with self.assertRaisesRegex(ValueError, 'watchdog abandoned'):
            self.analyze()

    def test_reference_wav_truncated_tail_preserves_specific_rejection(self):
        self.wav.write_bytes(self.wav.read_bytes()[:-4])
        with self.assertRaisesRegex(ValueError, 'original WAV truncated'):
            self.analyze()

    def test_reference_wav_appended_payload_rejected(self):
        # The pinned snesref WAV writer emits exactly 44 bytes of header
        # followed by 4 bytes per callback stereo frame, with no extra chunks.
        with self.wav.open('ab') as f:
            f.write(b'UNTRUSTED-TRAILER')
        with self.assertRaisesRegex(ValueError, 'unexpected original WAV length'):
            self.analyze()


if __name__ == '__main__':
    unittest.main()
