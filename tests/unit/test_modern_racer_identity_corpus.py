import json
import pathlib
import re
import unittest

from tools.extract_forbidden_name_table import words_from_rom

ROOT = pathlib.Path(__file__).resolve().parents[2]

class ModernRacerIdentityCorpusTests(unittest.TestCase):
    def test_cpp_legacy_presets_match_generated_cast_exactly(self):
        source = (ROOT / "native" / "product" / "modern_racer_identity.cpp").read_text()
        match = re.search(
            r"kLegacyPresets\{\{(.*?)\}\};",
            source,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(match)
        cpp = [
            {
                "rider_index": int(index),
                "name": name,
                "palette_label": colour,
            }
            for index, name, colour in re.findall(
                r'\{(\d+),\s*"([^"]+)",\s*"([^"]+)"\}',
                match.group(1),
            )
        ]
        generated = json.loads(
            (ROOT / "analysis" / "generated" / "legacy-cast-presets.json").read_text()
        )
        expected = [
            {
                "rider_index": entry["rider_index"],
                "name": entry["default_name"],
                "palette_label": entry["colour_label_derived"],
            }
            for entry in generated["racers"]
        ]
        self.assertEqual(cpp, expected)
        self.assertEqual(len(cpp), 16)

    def test_cpp_forbidden_name_table_matches_canonical_rom_exactly(self):
        source = (ROOT / "native" / "product" / "modern_racer_identity.cpp").read_text()
        match = re.search(
            r"kForbiddenWords\{\{(.*?)\}\};",
            source,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(match)
        cpp_words = re.findall(r'"([^"]+)"', match.group(1))
        rom_words = [
            word.decode("ascii")
            for word in words_from_rom(
                (ROOT / "reference" / "roms" / "retail" / "Uniracers_USA.sfc").read_bytes()
            )
        ]
        self.assertEqual(cpp_words, rom_words)
        self.assertEqual(len(cpp_words), 71)

if __name__ == "__main__":
    unittest.main()
