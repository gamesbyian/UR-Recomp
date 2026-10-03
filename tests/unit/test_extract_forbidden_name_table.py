import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import extract_forbidden_name_table as fnt  # noqa: E402


class ForbiddenNameTableTests(unittest.TestCase):
    def test_substring_rule(self) -> None:
        words = [b"sega", b"sonic"]
        self.assertTrue(fnt.is_forbidden("SONIC", words))
        self.assertTrue(fnt.is_forbidden("xsegax", words))
        self.assertFalse(fnt.is_forbidden("MIKE", words))

    def test_words_from_synthetic_rom(self) -> None:
        rom = bytearray(0x20000)
        ptr = fnt.lorom(fnt.BANK, fnt.POINTER_TABLE)
        data = fnt.lorom(fnt.BANK, 0x9000)
        cursor = data
        for i in range(fnt.WORD_COUNT):
            word = b"w" + bytes([0x61 + i % 26])
            addr = 0x9000 + (cursor - data)
            rom[ptr + 2 * i], rom[ptr + 2 * i + 1] = addr & 0xFF, addr >> 8
            rom[cursor:cursor + len(word) + 1] = word + b"\xff"
            cursor += len(word) + 1
        words = fnt.words_from_rom(bytes(rom))
        self.assertEqual(len(words), fnt.WORD_COUNT)
        self.assertEqual(words[0], b"wa")

    def test_canonical_rom_structure(self) -> None:
        report = fnt.analyze(fnt.ROM.read_bytes())
        self.assertTrue(report["all_checks_pass"], report["checks"])
        self.assertEqual(report["word_count"], 71)
        self.assertNotIn("words", report)


if __name__ == "__main__":
    unittest.main()
