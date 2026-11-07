"""RF095 source-patch and real stereo-sample receipt negative controls."""
from __future__ import annotations

import importlib.util
import io
import os
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

POSIX_DIRFD = (os.name == 'posix' and hasattr(os, 'O_DIRECTORY')
               and hasattr(os, 'O_NOFOLLOW') and os.open in os.supports_dir_fd
               and os.link in os.supports_dir_fd)

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
            wav.writeframes(struct.pack('<hh', 100, -50) * (6445 + 9 * 128))
        ref_map.write_text('frame,samples\n' +
                           ''.join(f'{f},{f if f <= 6445 else 6445 + (f-6445)*128}\n' for f in range(6455)))
        nat_pcm.write_bytes(struct.pack('<hh', 75, -25) * (10 * 128))
        nat_map.write_text('frame,samples\n' +
                           ''.join(f'{f},{(f-6447)*128}\n' for f in range(6447,6458)))
        orig_log.write_text('original genuine replay\n')
        native_log.write_text('native genuine replay\n')
        return original_wav, ref_map, nat_pcm, nat_map, orig_log, native_log

    def test_real_wave_and_native_stereo_receipt(self):
        with tempfile.TemporaryDirectory() as d:
            files = self.fixture(d)
            r = receipt.analyze(*files)
            self.assertEqual(r['original']['frames'], 896)
            self.assertEqual(r['native']['frames'], 1280)
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

    @unittest.skipUnless(POSIX_DIRFD, 'POSIX secure directory-relative publication unavailable')
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
            self.assertEqual(output.read_bytes(), struct.pack('<hh', 100, -50) * 896)
            with self.assertRaisesRegex(ValueError, 'stale original PCM'):
                receipt.analyze(*files, original_window_out=output)

    def test_late_receipt_failure_does_not_publish_original_pcm_window(self):
        # All hashes and JSON serialization must finish before the optional
        # final-named PCM window becomes visible. Preflight alone is insufficient.
        with tempfile.TemporaryDirectory() as d:
            files = self.fixture(d)
            names = ('original-wav', 'original-map', 'native-pcm',
                     'native-map', 'original-log', 'native-log')
            prefix = ['qa01_rf095_pcm_receipt.py']
            for name, path in zip(names, files):
                prefix.extend(('--' + name, str(path)))
            for failure in ('source-read', 'json-serialization'):
                with self.subTest(failure=failure):
                    window = pathlib.Path(d) / (failure + '.pcm')
                    out = pathlib.Path(d) / (failure + '.json')
                    argv = prefix + ['--out', str(out),
                                     '--original-window-out', str(window)]
                    with mock.patch('sys.argv', argv):
                        if failure == 'source-read':
                            # Snapshot reads now supply the exact bytes that
                            # are validated and hashed. Inject the failure at
                            # that real source boundary, not the retired
                            # second-pathname sha256() call.
                            real_read = pathlib.Path.read_bytes

                            def fail_snapshot_read(path):
                                if path == files[5]:
                                    raise OSError('injected late source read failure')
                                return real_read(path)

                            with mock.patch.object(
                                    pathlib.Path, 'read_bytes', autospec=True,
                                    side_effect=fail_snapshot_read):
                                with self.assertRaisesRegex(OSError, 'injected late'):
                                    receipt.main()
                        else:
                            with mock.patch.object(
                                    receipt.json, 'dumps',
                                    side_effect=TypeError('injected late serialization failure')):
                                with self.assertRaisesRegex(TypeError, 'injected late'):
                                    receipt.main()
                    self.assertFalse(window.exists())
                    self.assertFalse(out.exists())

    @unittest.skipUnless(POSIX_DIRFD, 'POSIX secure directory-relative publication unavailable')
    def test_cli_serializes_receipt_only_once_before_window_publication(self):
        # A second json.dumps after the PCM window is published could fail,
        # leaving a plausible final-named window and an empty JSON receipt.
        with tempfile.TemporaryDirectory() as d:
            files = self.fixture(d)
            names = ('original-wav', 'original-map', 'native-pcm',
                     'native-map', 'original-log', 'native-log')
            argv = ['qa01_rf095_pcm_receipt.py']
            for name, path in zip(names, files):
                argv.extend(('--' + name, str(path)))
            window = pathlib.Path(d) / 'one-serialization.pcm'
            out = pathlib.Path(d) / 'one-serialization.json'
            argv.extend(('--out', str(out), '--original-window-out', str(window)))
            real_dumps = receipt.json.dumps
            calls = []

            def fail_on_second_serialization(*args, **kwargs):
                calls.append(True)
                if len(calls) > 1:
                    raise TypeError('injected second serialization failure')
                return real_dumps(*args, **kwargs)

            with mock.patch('sys.argv', argv), mock.patch.object(
                    receipt.json, 'dumps',
                    side_effect=fail_on_second_serialization):
                receipt.main()
            self.assertEqual(len(calls), 1)
            self.assertEqual(window.read_bytes(), struct.pack('<hh', 100, -50) * 896)
            self.assertEqual(receipt.json.loads(out.read_text())['original']['frames'], 896)

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
                    contaminated = canonical + '6458,1280\n'
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
            files[1].write_text(files[1].read_text().replace('6454,7597', '6454,7596'))
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

    @unittest.skipUnless(POSIX_DIRFD, 'POSIX secure directory-relative publication unavailable')
    def test_final_publication_stages_complete_bytes_before_name_is_visible(self):
        with tempfile.TemporaryDirectory() as d:
            final = pathlib.Path(d) / 'receipt.json'
            payload = b'{"complete":true}\\n'
            actual_link = receipt.os.link
            calls = []

            def inspect_link(staged, target, **kwargs):
                self.assertEqual(target, final.name)
                self.assertEqual(kwargs['src_dir_fd'], kwargs['dst_dir_fd'])
                self.assertFalse(final.exists())
                fd = os.open(staged, os.O_RDONLY, dir_fd=kwargs['src_dir_fd'])
                with os.fdopen(fd, 'rb') as source:
                    self.assertEqual(source.read(), payload)
                calls.append(True)
                return actual_link(staged, target, **kwargs)

            with mock.patch.object(receipt.os, 'link', side_effect=inspect_link):
                receipt.publish_bytes_no_replace(final, payload, label='receipt output')
            self.assertEqual(calls, [True])
            self.assertEqual(final.read_bytes(), payload)
            self.assertEqual([p.name for p in pathlib.Path(d).iterdir()], ['receipt.json'])

    @unittest.skipUnless(POSIX_DIRFD, 'POSIX secure directory-relative publication unavailable')
    def test_final_publication_failure_leaves_no_partial_name_or_stage(self):
        with tempfile.TemporaryDirectory() as d:
            final = pathlib.Path(d) / 'window.pcm'
            with mock.patch.object(receipt.os, 'link',
                                   side_effect=OSError('injected link denial')):
                with self.assertRaisesRegex(OSError, 'injected link denial'):
                    receipt.publish_bytes_no_replace(
                        final, b'PCM' * 10, label='original PCM window')
            self.assertFalse(final.exists())
            self.assertEqual(list(pathlib.Path(d).iterdir()), [])

    @unittest.skipUnless(POSIX_DIRFD, 'POSIX secure directory-relative publication unavailable')
    def test_final_publication_racing_foreign_file_is_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            final = pathlib.Path(d) / 'receipt.json'

            def race(staged, target, **kwargs):
                final.write_bytes(b'FOREIGN')
                raise FileExistsError('injected concurrent create')

            with mock.patch.object(receipt.os, 'link', side_effect=race):
                with self.assertRaisesRegex(ValueError, 'stale receipt output'):
                    receipt.publish_bytes_no_replace(
                        final, b'NEW', label='receipt output')
            self.assertEqual(final.read_bytes(), b'FOREIGN')
            self.assertEqual([p.name for p in pathlib.Path(d).iterdir()], ['receipt.json'])

    def test_final_publication_parent_swap_cannot_redirect_bytes(self):
        # Reproduce the real foreign-stage-same-name swap from independent
        # review #5743126927. A mutable parent path must not redirect a link.
        if not hasattr(os, 'O_NOFOLLOW'):
            self.skipTest('POSIX directory descriptors unavailable')
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            intended, foreign = root / 'intended', root / 'foreign'
            old_intended = root / 'old_intended'
            intended.mkdir()
            foreign.mkdir()
            final = intended / 'receipt.json'
            actual_link = receipt.os.link

            def swap_parent(staged, target, **kwargs):
                intended.rename(old_intended)
                intended.symlink_to(foreign, target_is_directory=True)
                (foreign / staged).write_bytes(b'FOREIGN DIFFERENT BYTES')
                return actual_link(staged, target, **kwargs)

            with mock.patch.object(receipt.os, 'link', side_effect=swap_parent):
                with self.assertRaisesRegex(OSError, 'directory identity changed'):
                    receipt.publish_bytes_no_replace(
                        final, b'VALID RECEIPT', label='receipt output')
            self.assertEqual((old_intended / 'receipt.json').read_bytes(),
                             b'VALID RECEIPT')
            self.assertFalse((foreign / 'receipt.json').exists())
            self.assertFalse(any(p.name.startswith('.rf095-stage-')
                                 for p in old_intended.iterdir()))

    def test_final_publication_rejects_symlinked_parent(self):
        if not hasattr(os, 'O_NOFOLLOW'):
            self.skipTest('POSIX directory descriptors unavailable')
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            actual = root / 'actual'
            actual.mkdir()
            alias = root / 'alias'
            alias.symlink_to(actual, target_is_directory=True)
            with self.assertRaises(OSError):
                receipt.publish_bytes_no_replace(
                    alias / 'receipt.json', b'VALID', label='receipt output')
            self.assertEqual(list(actual.iterdir()), [])

    @unittest.skipUnless(POSIX_DIRFD, 'POSIX secure directory-relative publication unavailable')
    def test_cli_publishes_both_final_names_through_staging(self):
        with tempfile.TemporaryDirectory() as d:
            files = self.fixture(d)
            names = ('original-wav', 'original-map', 'native-pcm',
                     'native-map', 'original-log', 'native-log')
            argv = ['qa01_rf095_pcm_receipt.py']
            for name, path in zip(names, files):
                argv.extend(('--' + name, str(path)))
            window = pathlib.Path(d) / 'window.pcm'
            final = pathlib.Path(d) / 'receipt.json'
            argv.extend(('--out', str(final), '--original-window-out', str(window)))
            actual_publish = receipt.publish_bytes_no_replace
            labels = []

            def record_publish(path, payload, *, label):
                labels.append(label)
                return actual_publish(path, payload, label=label)

            with mock.patch('sys.argv', argv), mock.patch.object(
                    receipt, 'publish_bytes_no_replace',
                    side_effect=record_publish):
                receipt.main()
            self.assertEqual(labels, ['original PCM window', 'receipt output'])
            self.assertEqual(receipt.json.loads(final.read_text())['original']['frames'], 896)
            self.assertEqual(len(window.read_bytes()), 896 * 4)

if __name__ == '__main__':
    unittest.main()
