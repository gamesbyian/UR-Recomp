import importlib.util
import json
import pathlib
import re
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "validate_modern_locale.py"
EXAMPLE = ROOT / "analysis" / "data" / "modern-locale-en.json"
HEADER = ROOT / "native" / "product" / "modern_text_catalog.hpp"

spec = importlib.util.spec_from_file_location("validate_modern_locale", TOOL)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class ModernLocaleValidationTests(unittest.TestCase):
    def load_example(self):
        return json.loads(EXAMPLE.read_text(encoding="utf-8"))

    def test_english_example_is_valid(self):
        payload = self.load_example()
        self.assertIs(module.validate_locale_pack(payload), payload)

    def test_validator_keys_match_cpp_catalog(self):
        header = HEADER.read_text(encoding="utf-8")
        header_keys = set(re.findall(r'"(root\.[a-z]+)"', header))
        self.assertEqual(header_keys, set(module.KNOWN_KEYS))

    def test_missing_or_unknown_keys_fail_closed(self):
        payload = self.load_example()
        del payload["entries"]["root.records"]
        with self.assertRaisesRegex(ValueError, "missing required keys: root.records"):
            module.validate_locale_pack(payload)

        payload = self.load_example()
        payload["entries"]["root.unknown"] = "UNKNOWN"
        with self.assertRaisesRegex(ValueError, "unknown keys: root.unknown"):
            module.validate_locale_pack(payload)

    def test_locale_tag_is_canonical(self):
        payload = self.load_example()
        payload["locale"] = "fr-CA"
        module.validate_locale_pack(payload)

        payload["locale"] = "fr-ca"
        with self.assertRaisesRegex(ValueError, "canonical language"):
            module.validate_locale_pack(payload)

    def test_text_is_bounded_trimmed_and_nonempty(self):
        payload = self.load_example()
        payload["entries"]["root.play"] = " PLAY "
        with self.assertRaisesRegex(ValueError, "leading/trailing whitespace"):
            module.validate_locale_pack(payload)

        payload = self.load_example()
        payload["entries"]["root.play"] = ""
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            module.validate_locale_pack(payload)

        payload = self.load_example()
        payload["entries"]["root.play"] = "x" * 81
        with self.assertRaisesRegex(ValueError, "exceeds 80 characters"):
            module.validate_locale_pack(payload)

    def test_duplicate_json_keys_are_rejected_before_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "duplicate.json"
            path.write_text(
                '{"schema":"ur-recomp-modern-locale-v1",'
                '"locale":"en","locale":"fr",'
                '"entries":{"root.play":"PLAY"}}',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "duplicate JSON key: locale"):
                module.load_locale_pack(path)


if __name__ == "__main__":
    unittest.main()
