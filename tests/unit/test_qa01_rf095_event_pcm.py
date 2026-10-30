"""RF095 source-patch and real stereo-sample receipt negative controls."""
from __future__ import annotations

import importlib.util
import io
import pathlib
import struct
import tempfile
import unittest
import wave

ROOT = pathlib.Path(__file__).resolve().parents[2] / "tools"

def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

patch = module('qa01_rf095_event_pcm')
receipt = module('qa01_rf095_pcm_receipt')

REF = (patch.REF_WAV_INDEX + '\n'
       'static void something() {}\n'
       'void run() {\n' + patch.REF_RUN + patch.REF_CLOSE + '}\n')
NATIVE = ('#include <stdio.h>\n#include <stdint.h>\n#include <stdlib.h>\n'
          + patch.NATIVE_ENTRY +
          '  dsp_handleEcho(dsp, &totalL, &totalR);\n' +
          patch.NATIVE_SAMPLE + '}\n')

class RF095Tests(unittest.TestCase):
    def test_original_hook_singleton_and_idempotence(self):
        updated = patch.patch_reference(REF)
        self.assertIn('g_wav_sample_frames', updated)
        self.assertEqual(updated.count('p_retro_run();'), 1)
        self.assertIn('ur_rf095_reference_pcm_map_row();', updated)
        self.assertIn('if (fclose(ur_rf095_ref_map) != 0)', updated)
        with self.assertRaises(ValueError): patch.patch_reference(updated)

    def test_native_hook_after_real_sample_and_echo(self):
        updated = patch.patch_native(NATIVE)
        self.assertEqual(updated.count('audio_trace_on_sample('), 1)
        self.assertLess(updated.index('dsp_handleEcho('),
                        updated.index('ur_rf095_native_stereo_sample((int16_t)totalL'))
        self.assertIn('QA01RF095NATIVE_TRUNCATED', updated)
        with self.assertRaises(ValueError): patch.patch_native(updated)

    def test_ambiguous_source_anchor_rejected(self):
        for text in (REF + patch.REF_RUN, REF.replace(patch.REF_RUN, '')):
            with self.assertRaises(ValueError): patch.patch_reference(text)
        with self.assertRaises(ValueError): patch.patch_native(NATIVE + patch.NATIVE_SAMPLE)

    def fixture(self, directory):
        p = pathlib.Path(directory)
        original_wav = p / 'ref.wav'
        ref_map = p / 'ref.csv'
        nat_pcm = p / 'nat.pcm'
        nat_map = p / 'nat.csv'
        orig_log = p / 'original.log'
        native_log = p / 'native.log'
        with wave.open(str(original_wav), 'wb') as wav:
            wav.setnchannels(2); wav.setsampwidth(2); wav.setframerate(32040)
            wav.writeframes(struct.pack('<hh', 100, -50) * 6454)
        ref_map.write_text('frame,samples\n' +
                           ''.join(f'{f},{f}\n' for f in range(6455)))
        nat_pcm.write_bytes(struct.pack('<hh', 75, -25) * 10)
        nat_map.write_text('frame,samples\n' +
                           ''.join(f'{f},{f-6447}\n' for f in range(6447,6458)))
        orig_log.write_text('original genuine replay\n')
        native_log.write_text('native genuine replay\n')
        return original_wav, ref_map, nat_pcm, nat_map, orig_log, native_log

    def test_real_wave_and_native_stereo_receipt(self):
        with tempfile.TemporaryDirectory() as d:
            files = self.fixture(d)
            r = receipt.analyze(*files)
            self.assertEqual(r['original']['frames'], 7)
            self.assertEqual(r['native']['frames'], 10)
            self.assertEqual(r['original']['peak'], [100, 50])
            self.assertEqual(r['native']['peak'], [75, 25])
            self.assertFalse(r['audible_parity_proven'])
            self.assertEqual(r['usa_event_credit'], 0)

    def test_missing_frame_or_regression_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            files = self.fixture(d)
            files[3].write_text('frame,samples\n6447,0\n6449,1\n6457,10\n')
            with self.assertRaisesRegex(ValueError, 'boundaries absent'):
                receipt.analyze(*files)
            files = self.fixture(d)
            files[1].write_text('frame,samples\n0,0\n1,1\n3,2\n')
            with self.assertRaisesRegex(ValueError, 'missing or unordered'):
                receipt.analyze(*files)

    def test_truncated_or_mismatched_audio_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            files = self.fixture(d)
            files[2].write_bytes(files[2].read_bytes()[:-2])
            with self.assertRaisesRegex(ValueError, 'length mismatch'):
                receipt.analyze(*files)
            files = self.fixture(d)
            files[5].write_text('QA01RF095NATIVE_TRUNCATED\n')
            with self.assertRaisesRegex(ValueError, 'truncation'):
                receipt.analyze(*files)

    def test_original_frame_zero_counter_cannot_be_forged(self):
        with tempfile.TemporaryDirectory() as d:
            files = self.fixture(d)
            files[1].write_text(files[1].read_text().replace('0,0\n', '0,1\n', 1))
            with self.assertRaisesRegex(ValueError, 'frame-zero'):
                receipt.analyze(*files)

    def test_no_silent_wav_map_false_positive(self):
        with tempfile.TemporaryDirectory() as d:
            files = self.fixture(d)
            files[1].write_text(files[1].read_text().replace('6454,6454', '6454,6453'))
            with self.assertRaisesRegex(ValueError, 'count/WAV frame mismatch'):
                receipt.analyze(*files)

if __name__ == '__main__':
    unittest.main()
