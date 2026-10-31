"""ROM-free adversarial tests for native DSP sample-index registered PCM."""
from __future__ import annotations

import json
import tempfile
import unittest
import wave
from pathlib import Path, PureWindowsPath
import sys
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_native_pcm_at_kon as pcm


class NativeKonPCMTests(unittest.TestCase):
    @staticmethod
    def events():
        return [
            {"s": 30000, "t": "reg", "adr": "0x4c", "val": "0x02"},
            {"s": 40000, "t": "reg", "adr": "0x4c", "val": "0x80"},
            {"s": 40000, "t": "reg", "adr": "0x71", "val": "0x32"},
        ]

    @staticmethod
    def command(path, *, start=39500, count=2500, rate=32040, frames=None):
        def handler(line):
            parts = line.split(" ")
            assert len(parts) == 4 and parts[0] == "audio_wav", line
            assert (int(parts[2]), int(parts[3])) == (start, count), line
            staged_path = Path(parts[1])
            assert staged_path != path and staged_path.parent != path.parent
            with wave.open(str(staged_path), "wb") as wav:
                wav.setnchannels(2)
                wav.setsampwidth(2)
                wav.setframerate(rate)
                wav.writeframes(b"\x01\x00\xfe\xff" * (count if frames is None else frames))
            return {"ok": True, "path": parts[1], "start": start, "count": count}
        return handler

    def test_real_exact_kon_sample_window_and_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "kon.wav"
            r = pcm.capture_kon_pcm(self.command(path), events=self.events(),
                                    produced=45000, kon_sample_index=40000,
                                    wav_path=path, before=500, after=2000)
            self.assertEqual((r["start_sample_index"], r["sample_frames"],
                              r["kon_offset_frames"]), (39500, 2500, 500))
            self.assertEqual(r["sample_rate_hz"], 32040)
            self.assertEqual(r["usa_event_credit"], 0)
            self.assertFalse(r["original_native_audio_parity_proven"])
            self.assertEqual(len(r["pcm_sha256"]), 64)

    def test_missing_ambiguous_or_wrong_voice_keyon_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "kon.wav"
            for events in ([], self.events() * 2,
                           [{"s": 40000, "t": "reg", "adr": "0x4c", "val": "0x01"}]):
                with self.subTest(events=events), self.assertRaisesRegex(ValueError, "missing or ambiguous"):
                    pcm.capture_kon_pcm(lambda _: {}, events=events, produced=45000,
                                        kon_sample_index=40000, wav_path=path,
                                        before=500, after=2000)

    def test_unproduced_window_and_invalid_bounds_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "kon.wav"
            for produced, before, after in ((41999, 500, 2000), (45000, 0, 2000),
                                            (45000, 500, 64001), (45000, 41000, 1)):
                with self.subTest(args=(produced,before,after)), self.assertRaises(ValueError):
                    pcm.capture_kon_pcm(lambda _: {}, events=self.events(),
                                        produced=produced, kon_sample_index=40000,
                                        wav_path=path, before=before, after=after)

    def test_clamped_or_mismatched_server_slice_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "kon.wav"
            def wrong(line):
                self.command(path)(line)
                return {"ok": True, "path": str(path), "start": 39501, "count": 2499}
            with self.assertRaisesRegex(ValueError, "clamped/mismatched"):
                pcm.capture_kon_pcm(wrong, events=self.events(), produced=45000,
                                    kon_sample_index=40000, wav_path=path,
                                    before=500, after=2000)

    def test_wrong_rate_and_short_wav_rejected(self):
        for rate, frames in ((32000, None), (32040, 2499)):
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "kon.wav"
                with self.subTest(rate=rate, frames=frames), self.assertRaisesRegex(ValueError, "format/sample count"):
                    pcm.capture_kon_pcm(self.command(path, rate=rate, frames=frames),
                                        events=self.events(), produced=45000,
                                        kon_sample_index=40000, wav_path=path,
                                        before=500, after=2000)

    def test_appended_wav_bytes_rejected_despite_valid_decoded_pcm(self):
        # Pinned audio_trace_dump_wav writes exactly 44 + 4*count bytes.
        # wave.open() silently ignores a trailer beyond the declared data.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "kon.wav"
            observed_lengths = []
            def contaminated(line):
                reply = self.command(path)(line)
                staged = Path(line.split(" ")[1])
                with staged.open("ab") as out:
                    out.write(b"UNRELATED_TRAILER")
                observed_lengths.append(staged.stat().st_size)
                return reply
            with self.assertRaisesRegex(ValueError, "unexpected native WAV length"):
                pcm.capture_kon_pcm(contaminated, events=self.events(),
                                    produced=45000, kon_sample_index=40000,
                                    wav_path=path, before=500, after=2000)
            self.assertEqual(observed_lengths, [44 + 4 * 2500 + 17])
            self.assertFalse(path.exists())

    def test_existing_file_and_whitespace_path_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "kon.wav"
            path.write_bytes(b"old")
            with self.assertRaisesRegex(ValueError, "existing WAV"):
                pcm.capture_kon_pcm(lambda _: {}, events=self.events(), produced=45000,
                                    kon_sample_index=40000, wav_path=path,
                                    before=500, after=2000)
            with self.assertRaisesRegex(ValueError, "whitespace-free"):
                pcm.capture_kon_pcm(lambda _: {}, events=self.events(), produced=45000,
                                    kon_sample_index=40000, wav_path=Path(tmp) / "kon name.wav",
                                    before=500, after=2000)

    def test_invalid_sample_index_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "malformed native KON"):
            pcm.kon_candidates([{"s": "40000", "t": "reg", "adr": "0x4c", "val": "0x80"}])

    def test_output_alias_rejected_before_debug_server_connect(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            native = root / "native.exe"
            native.write_bytes(b"fake test executable")
            aliased_dir = root / "alias"
            aliased_dir.symlink_to(root, target_is_directory=True)
            for wav_path, json_path in (
                (root / "same.wav", root / "same.wav"),
                (root / "same.wav", aliased_dir / "same.wav"),
                (root / "same.wav", root / "other" / ".." / "same.wav"),
            ):
                with self.subTest(wav=wav_path, json=json_path):
                    with mock.patch.object(sys, "argv", ["pcm", "--kon-sample-index", "40000",
                         "--wav-out", str(wav_path), "--json-out", str(json_path),
                         "--source-sha", "a" * 40, "--native-executable", str(native)]), \
                         mock.patch.object(pcm, "connect", side_effect=AssertionError("must not connect")), \
                         self.assertRaises(SystemExit) as error:
                        pcm.main()
                    self.assertEqual(error.exception.code, 2)
                    self.assertFalse(wav_path.exists())


    def test_raced_foreign_destination_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "kon.wav"
            def race(line):
                path.write_bytes(b"FOREIGN-DO-NOT-CLOBBER")
                return self.command(path)(line)
            with self.assertRaisesRegex(ValueError, "created during capture"):
                pcm.capture_kon_pcm(race, events=self.events(), produced=45000,
                                    kon_sample_index=40000, wav_path=path,
                                    before=500, after=2000)
            self.assertEqual(path.read_bytes(), b"FOREIGN-DO-NOT-CLOBBER")
            self.assertFalse(list(Path(tmp).glob(".qa01-kon-*")))

    def test_raced_symlink_destination_never_followed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "kon.wav"
            foreign = root / "foreign.dat"
            foreign.write_bytes(b"KEEP-FOREIGN")
            def race(line):
                path.symlink_to(foreign)
                return self.command(path)(line)
            with self.assertRaisesRegex(ValueError, "created during capture"):
                pcm.capture_kon_pcm(race, events=self.events(), produced=45000,
                                    kon_sample_index=40000, wav_path=path,
                                    before=500, after=2000)
            self.assertEqual(foreign.read_bytes(), b"KEEP-FOREIGN")

    def test_no_hardlink_volume_falls_back_to_exclusive_create(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "kon.wav"
            with mock.patch.object(pcm.os, "link", side_effect=OSError("unsupported")):
                result = pcm.capture_kon_pcm(self.command(path), events=self.events(),
                                             produced=45000, kon_sample_index=40000,
                                             wav_path=path, before=500, after=2000)
            self.assertEqual(result["wav_bytes"], path.stat().st_size)
            self.assertEqual(result["wav_sha256"], pcm.hashlib.sha256(path.read_bytes()).hexdigest())

class NativeWavWirePathTests(unittest.TestCase):
    def test_windows_drive_and_unc_paths_round_trip_native_json(self):
        for original, expected in (
            (r"C:\qa01\native\voice7.wav", "C:/qa01/native/voice7.wav"),
            (r"\\server\share\voice7.wav", "//server/share/voice7.wav"),
        ):
            with self.subTest(path=original):
                wire = pcm.wav_command_path(PureWindowsPath(original))
                self.assertEqual(wire, expected)
                # Pinned debug_server.c uses send_fmt with an unescaped %s.
                reply = '{"ok":true,"path":"' + wire + '","start":39500,"count":2500}'
                self.assertEqual(json.loads(reply)["path"], wire)

    def test_posix_path_remains_unchanged(self):
        self.assertEqual(pcm.wav_command_path(Path("/tmp/voice7.wav")),
                         "/tmp/voice7.wav")

    def test_server_path_token_byte_limit(self):
        # Pinned debug_server.c uses sscanf("%511s %lld %llu"). A 512-byte
        # token truncates the filename before the server opens it with wb.
        self.assertEqual(pcm.wav_command_path(Path("/" + "a" * 510)),
                         "/" + "a" * 510)
        with self.assertRaisesRegex(ValueError, "511-byte"):
            pcm.wav_command_path(Path("/" + "a" * 511))

    def test_server_path_token_utf8_byte_limit(self):
        # Non-ASCII UTF-8 consumes more wire bytes than Python characters.
        # A 511-byte UTF-8 token still cannot traverse the shared ASCII
        # command transport. A 512-byte token must fail the server bound too.
        with self.assertRaisesRegex(ValueError, "ASCII"):
            pcm.wav_command_path(Path("/" + "a" * 508 + "é"))
        with self.assertRaisesRegex(ValueError, "511-byte"):
            pcm.wav_command_path(Path("/" + "a" * 509 + "é"))

    def test_unicode_basename_publishes_via_ascii_staging(self):
        # A Unicode final basename need not enter the ASCII debug protocol.
        # This exercises a POSIX ASCII parent; Windows Unicode parents still
        # need an independently verified native staging location.
        import io
        from capture_audio_events import command as shared_command

        class NoWriteSocket:
            def sendall(self, payload):
                raise AssertionError("raw Unicode path must not reach the server")

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "José.wav"
            calls = []
            def transport(line):
                calls.append(line)
                self.assertTrue(line.isascii())
                return NativeKonPCMTests.command(path)(line)

            result = pcm.capture_kon_pcm(
                transport, events=NativeKonPCMTests.events(),
                produced=45000, kon_sample_index=40000,
                wav_path=path, before=500, after=2000)
            self.assertEqual(len(calls), 1)
            self.assertTrue(path.is_file())
            self.assertEqual(result["wav_bytes"], path.stat().st_size)
            # Direct Unicode transmission remains unsupported by the producer.
            with self.assertRaises(UnicodeEncodeError):
                shared_command(NoWriteSocket(), io.StringIO('{"ok":true}\\n'),
                               f"audio_wav {path} 39500 2500")

    def test_windows_unicode_parent_rejected_before_transport(self):
        with self.assertRaisesRegex(ValueError, "ASCII"):
            pcm.wav_command_path(PureWindowsPath(r"C:\Users\José\capture.wav"))

    def test_unsafe_posix_paths_fail_before_wav_request(self):
        for name in ("/tmp/has\\backslash.wav", '/tmp/has"quote.wav',
                     "/tmp/has\x00nul.wav"):
            with self.subTest(path=repr(name)):
                with self.assertRaisesRegex(ValueError, "safely"):
                    pcm.wav_command_path(Path(name))


if __name__ == "__main__":
    unittest.main()
