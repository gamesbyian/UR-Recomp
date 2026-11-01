"""RF095 source-patch and real stereo-sample receipt negative controls."""
from __future__ import annotations

import importlib.util
import io
import pathlib
import struct
import tempfile
import unittest
from unittest import mock
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
COMMON = ('bool RtlRunFrame(uint32 inputs) {\n'
          '  if (!g_rtl_speculative_frame)\n'
          '    rtl_sync_apu_frame_boundary();\n'
          '}\n'
          'static void rtl_sync_apu_frame_boundary(void) {\n'
          '  RtlApuLock();\n'
          '  bool synced = true;\n'
          + patch.NATIVE_LOCKED_SYNC + '}\n')
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

    def test_native_map_uses_completed_frame_sync_not_first_dsp_sample(self):
        patched = patch.patch_native_boundary(COMMON)
        self.assertIn(patch.NATIVE_FRAME_SYNC, patched)
        locked_call = '    ur_rf095_native_frame_boundary(snes_frame_counter);'
        self.assertIn('if (synced)\n' + locked_call + '\n  RtlApuUnlock();',
                      patched)
        self.assertLess(patched.index('  RtlApuLock();'),
                        patched.index(locked_call))
        self.assertLess(patched.index(locked_call),
                        patched.index('  RtlApuUnlock();'))
        self.assertEqual(patched.count(locked_call), 1)
        self.assertEqual(patched.count('rtl_sync_apu_frame_boundary();'), 1)
        dsp = patch.patch_native(NATIVE)
        self.assertIn('if (ur_rf095_native_state != 1) return;', dsp)
        self.assertIn('void ur_rf095_native_frame_boundary(int frame)', dsp)
        self.assertIn('if (frame == 6457) ur_rf095_native_state = 2;', dsp)
        self.assertNotIn('const int frame = snes_frame_counter;', dsp)
        with self.assertRaises(ValueError):
            patch.patch_native_boundary(patched)
        with self.assertRaises(ValueError):
            patch.patch_native_boundary(COMMON + patch.NATIVE_FRAME_SYNC)

    def test_native_boundary_rejects_unlocked_gap_and_drift(self):
        # A post-unlock sample-map write races RtlRenderAudio's APU lock.
        unlocked = COMMON.replace(
            '  if (!synced)\n', '  RtlApuUnlock();\n  if (!synced)\n'
        ).replace('  RtlApuUnlock();\n}\n', '}\n')
        with self.assertRaisesRegex(ValueError, 'source drift'):
            patch.patch_native_boundary(unlocked)
        with self.assertRaisesRegex(ValueError, 'source drift'):
            patch.patch_native_boundary(COMMON + patch.NATIVE_LOCKED_SYNC)
        # Failed guest-clock sync must not create a plausible PCM boundary.
        patched = patch.patch_native_boundary(COMMON)
        self.assertIn('if (synced)\n'
                      '    ur_rf095_native_frame_boundary(snes_frame_counter);',
                      patched)
        self.assertNotIn('rtl_sync_apu_frame_boundary();\n'
                         '    ur_rf095_native_frame_boundary(', patched)

    def test_native_staging_rejects_common_source_drift_without_partial_dsp_write(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d) / 'snesrecomp' / 'runner' / 'src'
            dsp = root / 'snes' / 'dsp.c'
            common = root / 'common_rtl.c'
            dsp.parent.mkdir(parents=True)
            dsp.write_text(NATIVE)
            common.write_text('bool RtlRunFrame(uint32 inputs) {}\n')
            with mock.patch('sys.argv', ['rf095', '--root', d, '--side', 'native']):
                with self.assertRaises(ValueError):
                    patch.main()
            self.assertEqual(dsp.read_text(), NATIVE)
            common.write_text(COMMON)
            with mock.patch('sys.argv', ['rf095', '--root', d, '--side', 'native']):
                patch.main()
            self.assertIn('ur_rf095_native_frame_boundary', common.read_text())
            self.assertIn('ur_rf095_native_stereo_sample', dsp.read_text())

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
            self.assertFalse(r['producer_identity_independently_verified'])
            self.assertEqual(r['usa_event_credit'], 0)

    def test_original_and_native_pcm_inputs_must_be_distinct(self):
        # An original WAV can otherwise masquerade as native raw PCM:
        # its 44-byte WAV header becomes eleven stereo int16 frames.
        with tempfile.TemporaryDirectory() as d:
            for hardlink in (False, True):
                files = list(self.fixture(d))
                original_wav, native_pcm = files[0], files[2]
                native_pcm.unlink()
                if hardlink:
                    native_pcm.hardlink_to(original_wav)
                else:
                    files[2] = original_wav
                claimed_native_frames = original_wav.stat().st_size // 4
                files[3].write_text('frame,samples\n' +
                                    ''.join(
                                        f'{f},{f - 6447 if f < 6457 else claimed_native_frames}\n'
                                        for f in range(6447, 6458)))
                with self.subTest(hardlink=hardlink), self.assertRaisesRegex(
                        ValueError, 'distinct physical files'):
                    receipt.analyze(*files)

    def test_invalid_native_cannot_leave_plausible_original_window(self):
        with tempfile.TemporaryDirectory() as d:
            files = self.fixture(d)
            output = pathlib.Path(d) / 'original-window.pcm'
            files[2].write_bytes(files[2].read_bytes()[:-2])
            with self.assertRaisesRegex(ValueError, 'length mismatch'):
                receipt.analyze(*files, original_window_out=output)
            self.assertFalse(output.exists())
            files = self.fixture(d)
            receipt.analyze(*files, original_window_out=output)
            self.assertEqual(output.read_bytes(), struct.pack('<hh', 100, -50) * 7)
            with self.assertRaisesRegex(ValueError, 'stale original PCM'):
                receipt.analyze(*files, original_window_out=output)

    def test_frame_map_rejects_non_lf_delimiters_and_empty_rows(self):
        # Pinned C producers terminate CSV rows with LF, never VT, FF, FS,
        # GS, RS or a bare CR. A checksum-valid forged map must fail closed.
        with tempfile.TemporaryDirectory() as d:
            path = pathlib.Path(d) / 'frame-map.csv'
            for delimiter in (b'\v', b'\f', b'\x1c', b'\x1d',
                              b'\x1e', b'\r'):
                path.write_bytes(b'frame,samples\n0,0' + delimiter +
                                 b'1,100\n2,200\n3,300\n')
                with self.subTest(delimiter=delimiter), self.assertRaisesRegex(
                        ValueError, 'malformed'):
                    receipt.frame_map(path, start=1, end=3,
                                      contiguous_from_zero=True)
            for raw in (b'frame,samples\n0,0\n\n1,100\n2,200\n3,300\n',
                        b'frame,samples\n0,0\n1,100\n2,200\n3,300\n\n'):
                path.write_bytes(raw)
                with self.subTest(empty_row=raw), self.assertRaisesRegex(
                        ValueError, 'malformed'):
                    receipt.frame_map(path, start=1, end=3,
                                      contiguous_from_zero=True)
            for ending in (b'\n', b'\r\n'):
                for terminal in (b'', ending):
                    path.write_bytes(ending.join((b'frame,samples', b'0,0',
                                                  b'1,100', b'2,200', b'3,300')) + terminal)
                    with self.subTest(ending=ending, terminal=terminal):
                        if not terminal:
                            with self.assertRaisesRegex(ValueError, 'unterminated'):
                                receipt.frame_map(
                                    path, start=1, end=3, contiguous_from_zero=True)
                        else:
                            self.assertEqual(receipt.frame_map(
                                path, start=1, end=3, contiguous_from_zero=True)[3], 300)

    def test_source_truncated_final_newline_rejected_on_both_sides(self):
        with tempfile.TemporaryDirectory() as d:
            for index in (1, 3):  # original and native frame maps
                files = self.fixture(d)
                path = files[index]
                self.assertTrue(path.read_bytes().endswith(b'\n'))
                path.write_bytes(path.read_bytes()[:-1])
                with self.subTest(side=index), self.assertRaisesRegex(
                        ValueError, 'unterminated'):
                    receipt.analyze(*files)

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

    def test_native_frame_map_rejects_extra_pre_and_post_rows(self):
        with tempfile.TemporaryDirectory() as d:
            for extra in ('before', 'after'):
                files = self.fixture(d)
                native_map = files[3]
                canonical = native_map.read_text()
                if extra == 'before':
                    contaminated = canonical.replace('frame,samples\n',
                                                     'frame,samples\n6446,0\n', 1)
                else:
                    contaminated = canonical + '6458,10\n'
                native_map.write_text(contaminated)
                with self.subTest(extra=extra), self.assertRaisesRegex(
                        ValueError, 'native frame-map population'):
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
            files = self.fixture(d)
            files[5].write_text('QA01RF095NATIVE_INCOMPLETE\n')
            with self.assertRaisesRegex(ValueError, 'truncation'):
                receipt.analyze(*files)

    def test_original_wav_truncated_after_event_window_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            files = self.fixture(d)
            original_wav = files[0]
            original_wav.write_bytes(original_wav.read_bytes()[:-4])
            # The bounded 6445..6452 sample window remains present, while
            # the WAV header still claims the missing final stereo frame.
            with self.assertRaisesRegex(ValueError, 'original WAV truncated'):
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

    def test_native_hot_path_buffers_without_synchronous_disk_io(self):
        updated = patch.patch_native(NATIVE)
        hot_path = updated.split('static void ur_rf095_native_stereo_sample(', 1)[1].split(
            'void dsp_cycle(', 1)[0]
        self.assertNotIn('fopen(', hot_path)
        self.assertNotIn('fwrite(', hot_path)
        self.assertNotIn('fprintf(ur_rf095_native_map', hot_path)
        self.assertIn('atexit(ur_rf095_native_flush)', hot_path)
        self.assertIn('ur_rf095_native_buffer[ur_rf095_native_samples]', hot_path)
        self.assertIn('QA01RF095NATIVE_INCOMPLETE', updated)
        self.assertIn('ur_rf095_native_previous_frame != 6457', updated)

    def test_cli_rejects_aliased_and_stale_outputs_without_mutation(self):
        with tempfile.TemporaryDirectory() as d:
            files = self.fixture(d)
            before = [path.read_bytes() for path in files]
            absent = pathlib.Path(d) / 'window.pcm'
            names = ('original-wav', 'original-map', 'native-pcm', 'native-map',
                     'original-log', 'native-log')
            prefix = ['qa01_rf095_pcm_receipt.py']
            for name, path in zip(names, files):
                prefix.extend(('--' + name, str(path)))
            for out, window, error in (
                (absent, absent, 'aliases'),
                (files[2], absent, 'aliases'),
                (files[0], absent, 'aliases'),
            ):
                argv = prefix + ['--out', str(out), '--original-window-out', str(window)]
                with self.subTest(out=out), mock.patch('sys.argv', argv):
                    with self.assertRaisesRegex(ValueError, error):
                        receipt.main()
                self.assertFalse(absent.exists())
                self.assertEqual([path.read_bytes() for path in files], before)
            stale = pathlib.Path(d) / 'stale.json'
            stale.write_bytes(b'previous receipt')
            argv = prefix + ['--out', str(stale), '--original-window-out', str(absent)]
            with mock.patch('sys.argv', argv):
                with self.assertRaisesRegex(ValueError, 'stale receipt'):
                    receipt.main()
            self.assertEqual(stale.read_bytes(), b'previous receipt')
            self.assertFalse(absent.exists())
            self.assertEqual([path.read_bytes() for path in files], before)

    def test_receipt_destination_preflight_precedes_pcm_window_publication(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            blocker = root / 'blocked-parent'
            blocker.write_text('SENTINEL')
            window = root / 'original-window.pcm'
            names = ('original-wav', 'original-map', 'native-pcm',
                     'native-map', 'original-log', 'native-log')
            argv = ['qa01_rf095_pcm_receipt.py']
            for index, name in enumerate(names):
                argv.extend(('--' + name, str(root / f'input-{index}')))
            argv.extend(('--out', str(blocker / 'receipt.json'),
                         '--original-window-out', str(window)))
            with mock.patch('sys.argv', argv), mock.patch.object(
                    receipt, 'analyze') as analyze:
                with self.assertRaises(OSError):
                    receipt.main()
                analyze.assert_not_called()
            self.assertFalse(window.exists())
            self.assertEqual(blocker.read_text(), 'SENTINEL')
            good_parent = root / 'writable'
            receipt.preflight_receipt_output(good_parent / 'receipt.json')
            self.assertTrue(good_parent.is_dir())
            self.assertEqual(list(good_parent.iterdir()), [])

if __name__ == '__main__':
    unittest.main()
