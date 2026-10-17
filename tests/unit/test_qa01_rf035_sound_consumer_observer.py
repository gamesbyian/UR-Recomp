#!/usr/bin/env python3
"""Fail-closed RF035 disposable observer source-contract tests."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_rf035_sound_consumer_observer as rf


class RF035ObserverTest(unittest.TestCase):
    def test_pinned_baldosa_cpu_bridge_location(self):
        self.assertEqual(rf.NATIVE.as_posix(), "snesrecomp/runner/src/cpu_state.c")

    def test_original_retains_one_real_opcode_and_is_idempotent(self):
        source = "void run() {\n" + rf.ORIG_DISPATCH + "\n}\n"
        new = rf.patch_original(source)
        self.assertEqual(new.count("(*Opcodes[Op].S9xOpcode)();"), 1)
        self.assertEqual(new.count("QA01RF035ORIG frame="), 1)
        self.assertEqual(rf.patch_original(new), new)
        self.assertLess(new.index("const unsigned ur_rf035_pc"), new.index(rf.ORIG_DISPATCH))
        self.assertLess(new.index(rf.ORIG_DISPATCH), new.index("QA01RF035ORIG frame="))
        self.assertIn("QA01RF035ORIG_TRUNCATED", new)
        self.assertIn("ur_rf035_bank == 0x82u", new)
        self.assertIn("ICPU.Frame >= 6000u", new)
        self.assertIn("dp65=%02X", new)

    def test_native_reads_once_and_returns_unchanged_latch_values(self):
        source = (rf.NATIVE_HEADER + "void byte(void) {\n" + rf.NATIVE_BYTE +
                  "}\nvoid word(void) {\n" + rf.NATIVE_WORD + "}\n")
        new = rf.patch_native(source)
        self.assertEqual(new.count("cpu_latch_read8(cpu, value)"), 1)
        self.assertEqual(new.count("cpu_latch_read16(cpu, (uint16)lo | ((uint16)hi << 8))"), 1)
        self.assertEqual(new.count("ur_qa01_rf035_read(cpu, bank, addr"), 2)
        self.assertEqual(rf.patch_native(new), new)
        self.assertIn("QA01RF035NATIVE_TRUNCATED", new)
        self.assertIn("snes_frame_counter < 6053", new)

    def test_unknown_source_and_tamper_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "opcode-dispatch"):
            rf.patch_original("int wrong;")
        with self.assertRaisesRegex(ValueError, "WRAM"):
            rf.patch_native(rf.NATIVE_HEADER + rf.NATIVE_BYTE)
        original = rf.patch_original(rf.ORIG_DISPATCH)
        with self.assertRaisesRegex(ValueError, "tampered"):
            rf.patch_original(original.replace("QA01RF035ORIG frame=", "BROKEN frame="))
        native = rf.patch_native(rf.NATIVE_HEADER + rf.NATIVE_BYTE + rf.NATIVE_WORD)
        with self.assertRaisesRegex(ValueError, "tampered"):
            rf.patch_native(native.replace("ur_qa01_rf035_read(cpu, bank, addr", "renamed(cpu, bank, addr"))


if __name__ == "__main__":
    unittest.main()
