import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "prep_intra", ROOT / "tools/analyze_preparation_intraframe_trace.py"
)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)


class PreparationIntraframeTraceTests(unittest.TestCase):
    def test_parse_mirrored_bank_and_resolved_words(self):
        line = (
            "PREPTRACE frame=123 v=225 cycles=42 pc=01D37F y=0000 "
            "ca=2 cb=1 camx=1000 camy=700 edgex=42 edgey=96 camdx=13 "
            "a=1948:01:A1B2,1949:02:C3D4 b=1968:03:E5F6\n"
        )
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "trace.log"
            p.write_text(line, encoding="utf-8")
            rows = MOD.parse_log(p)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["site"], "list_consumer_entry")
        self.assertEqual(row["count_a"], 2)
        self.assertEqual(row["count_b"], 1)
        self.assertEqual(row["list_a"][0]["destination"], 0x1948)
        self.assertEqual(row["list_a"][0]["selector"], 1)
        self.assertEqual(row["list_a"][0]["source_word"], 0xA1B2)
        self.assertEqual(row["list_a"][0]["write_2118"], 0xA1)
        self.assertEqual(row["list_a"][0]["write_2119"], 0xB2)


if __name__ == "__main__":
    unittest.main()
