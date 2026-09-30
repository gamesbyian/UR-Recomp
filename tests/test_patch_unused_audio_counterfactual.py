#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/patch_unused_audio_counterfactual.py"
SPEC = importlib.util.spec_from_file_location("patch_unused_audio_counterfactual", TOOL)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class UnusedAudioCounterfactualTests(unittest.TestCase):
    def synthetic_rom_for(self, case_name):
        case = MODULE.CASES[case_name]
        off = case["ldx_file_offset"]
        rom = bytearray(off + 64)
        rom[off:off + 14] = MODULE.expected_sequence(
            case["from_selector"], case["package_seed"]
        )
        return bytes(rom)

    def test_demo_package_changes_only_selector(self):
        name = "unused-song-1-demo-package"
        original = self.synthetic_rom_for(name)
        patched, report = MODULE.patch_rom(
            original, name, require_canonical_hash=False
        )
        off = MODULE.CASES[name]["ldx_file_offset"]
        self.assertEqual(report["changed_byte_count"], 1)
        self.assertEqual(patched[off + 1], 0x3B)
        self.assertEqual(patched[off + 8:off + 10], bytes([0x15, 0xFB]))

    def test_race_package_changes_only_selector(self):
        name = "unused-song-2-race-package"
        original = self.synthetic_rom_for(name)
        patched, report = MODULE.patch_rom(
            original, name, require_canonical_hash=False
        )
        off = MODULE.CASES[name]["ldx_file_offset"]
        self.assertEqual(report["changed_byte_count"], 1)
        self.assertEqual(patched[off + 1], 0x3D)
        self.assertEqual(patched[off + 8:off + 10], bytes([0x55, 0xFB]))

    def test_rejects_wrong_surrounding_bytes(self):
        name = "unused-song-1-demo-package"
        original = bytearray(self.synthetic_rom_for(name))
        off = MODULE.CASES[name]["ldx_file_offset"]
        original[off + 7] ^= 0x01
        with self.assertRaises(ValueError):
            MODULE.patch_rom(bytes(original), name, require_canonical_hash=False)


if __name__ == "__main__":
    unittest.main()
