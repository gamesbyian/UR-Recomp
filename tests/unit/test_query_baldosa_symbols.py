"""Pure-parser tests for imported baldosa symbol lookup."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from query_baldosa_symbols import address, parse_rows, query


class BaldosaSymbolLookupTest(unittest.TestCase):
    def test_address_forms(self):
        self.assertEqual(address("81:8050"), 0x818050)
        self.assertEqual(address("$818050"), 0x818050)
        self.assertEqual(address("0x818050"), 0x818050)
        with self.assertRaises(ValueError):
            address("81:80XX")

    def test_functions_and_ram_are_independent(self):
        functions = parse_rows("818050 Uni_CheckLapLine ; lap timing\n# no", "function")
        ram = parse_rows("77074B sEventType 1 ; 0 race", "ram")
        self.assertEqual(functions[0]["name"], "Uni_CheckLapLine")
        self.assertEqual(ram[0]["width"], 1)
        self.assertEqual(query(functions + ram, addr=0x818050)[0]["kind"], "function")
        self.assertEqual(query(functions + ram, pattern="lap|event"), functions + ram)
        self.assertEqual(query(functions + ram, kind="ram"), ram)

    def test_rejects_non_records(self):
        self.assertFalse(parse_rows("hello\n818050 Invalid 23 extra fields", "function"))
        with self.assertRaises(ValueError):
            parse_rows("", "unsupported")


if __name__ == "__main__":
    unittest.main()
