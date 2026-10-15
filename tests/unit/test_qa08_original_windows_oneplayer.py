"""Fail-closed 1P original Snes9x / unchanged exact Win32 candidate source tests."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import qa08_original_oneplayer_source_manifest as original  # noqa: E402
import qa08_windows_oneplayer_source_capture as windows  # noqa: E402
import qa08_compare_original_windows_oneplayer as compare  # noqa: E402


class OnePlayerSourceTests(unittest.TestCase):
    def test_requires_real_complete_native_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            pixel=windows.HEADER+b"\x00\x00\x00\xff"*(256*224)
            name=folder/"ur-baldosa-original-source-002208.pam"
            name.write_bytes(pixel)
            log=("UR_QA08_WINDOWS_ORIGINAL_SOURCE frame=2208 logical=256x224 "
                 "saved=1 source=post-original-ppu-before-present\n")
            crcs=["0x00112233"]*5447
            out=windows.verify_capture(folder,log,crcs)
            self.assertEqual(out["actual_observed_source_guest_frames"],[2208])
            self.assertTrue(out["guest2208_captured_in_source"])
            self.assertFalse(out["release_gate_approved"])
            with self.assertRaises(ValueError):
                windows.verify_capture(folder,"",crcs)
            with self.assertRaises(ValueError):
                windows.verify_capture(folder,log,crcs[:200])
            with self.assertRaises(ValueError):
                windows.verify_capture(folder,log+"UR_QA08_WINDOWS_SOURCE_REJECT",crcs)
            name.write_bytes(pixel[:-1])
            with self.assertRaises(ValueError):
                windows.verify_capture(folder,log,crcs)

    def test_original_real_window_requires_complete_sixtyfive_distinct_frames(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            frames=p/"frames"
            frames.mkdir()
            script=p/"route.script"
            script.write_text("until16 0053 == 8610\nquit\n")
            log=p/"log.txt"
            log.write_text("script f=5447 quit\n")
            rom=p/"rom.sfc"
            rom.write_bytes(b"synthetic-not-original")
            core=p/"snes9x_libretro.so"
            core.write_bytes(b"dummy")
            with self.assertRaisesRegex(ValueError,"ROM"):
                original.observe(frames,script,log,rom,core)
            # Negative gate must reject a true 1P ROM without all callbacks.
            with patch.object(original,"ROM_SHA",hashlib.sha256(rom.read_bytes()).hexdigest()):
                with self.assertRaisesRegex(ValueError,"missing/extra"):
                    original.observe(frames,script,log,rom,core)

    def test_original_rgb5_is_green6_downquantization_only(self):
        bgrx=bytearray(256*224*4)
        p7=bytearray(256*224*4)
        bgrx[:4]=bytes([0x21,0xA7,0xFF,0x00])
        green5=0xA7>>3
        p7[:4]=bytes([0xFF,(green5<<3)|(green5>>2),0x21,0xFF])
        equal=compare.compare(bytes(bgrx),bytes(p7))
        self.assertEqual(equal["wrong_RGB5_pixels"],0)
        self.assertEqual(equal["same_RGB5_pixels"],256*224)
        p7[1]^=8
        wrong=compare.compare(bytes(bgrx),bytes(p7))
        self.assertEqual(wrong["wrong_RGB5_pixels"],1)
        self.assertIn(0,wrong["wrong_pixels_by_row"])
        with self.assertRaises(ValueError):
            compare.compare(bytes(bgrx[:-4]),bytes(p7))

    def test_rendered_source_is_full_256_by_224_not_216_crop(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"real.pam"
            p.write_bytes(windows.HEADER+b"\x00"*(256*224*4))
            self.assertEqual(len(compare.read_native(p)),256*224*4)
            p.write_bytes(windows.HEADER+b"\x00"*(256*216*4))
            with self.assertRaises(ValueError):
                compare.read_native(p)

    def test_shared_input_deletes_only_turbo_directive(self):
        source=b"turbo on\nuntil16 0053 == 8610\npress right 600\n"
        self.assertEqual(compare.no_turbo(source),
                         b"until16 0053 == 8610\npress right 600\n")
        self.assertNotEqual(compare.sha(source),compare.sha(compare.no_turbo(source)))

    def test_exact_replayed_windows_source_identity_is_preexisting(self):
        self.assertEqual(windows.EXE_SHA,
          "7431889698913feadab76261caf3b00b82d1d9a1466a8260d9b7512d8328324e")
        self.assertEqual(original.FIRST,2176)
        self.assertEqual(original.LAST,2240)
        self.assertEqual(compare.SCHEMA, "qa08-real-original-snes9x-vs-exact-windows-1p-rgb5-window/1")
        self.assertEqual(tuple(compare.WINDOW), tuple(range(2176, 2241)))


if __name__=="__main__":
    unittest.main()
