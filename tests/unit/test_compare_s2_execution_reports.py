import tempfile
import unittest
from pathlib import Path

from tools.compare_s2_execution_reports import compare, parse_report

BASE = """UR-S2-DESKTOP-REFERENCE/1
snes_init=1
checkpoint frame=0 master=00000001 cpu=00000002 wram=00000003 apu=00000004 ppu=00000005 dma=00000006 cart=00000007
checkpoint frame=1 master=00000011 cpu=00000012 wram=00000013 apu=00000014 ppu=00000015 dma=00000016 cart=00000017
checkpoint frame=60 master=00000021 cpu=00000022 wram=00000023 apu=00000024 ppu=00000025 dma=00000026 cart=00000027
checkpoint frame=120 master=00000031 cpu=00000032 wram=00000033 apu=00000034 ppu=00000035 dma=00000036 cart=00000037
execution_complete=1
"""

class S2ExecutionReportComparatorTest(unittest.TestCase):
    def parse(self, text):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "report.txt"
            path.write_text(text)
            return parse_report(path)

    def test_identical_reports_match(self):
        parsed = self.parse(BASE)
        self.assertTrue(compare(parsed, parsed)["match"])

    def test_first_partition_difference_is_named(self):
        observed = BASE.replace("frame=60 master=00000021", "frame=60 master=deadbeef")
        result = compare(self.parse(BASE), self.parse(observed))
        self.assertFalse(result["match"])
        self.assertEqual(result["first_difference"]["frame"], 60)
        self.assertEqual(result["first_difference"]["partition"], "master")

    def test_missing_checkpoint_is_rejected(self):
        broken = "\n".join(line for line in BASE.splitlines() if "frame=60 " not in line)
        with self.assertRaises(ValueError):
            self.parse(broken)

    def test_failed_execution_is_rejected(self):
        result = compare(self.parse(BASE), self.parse(BASE.replace("execution_complete=1", "execution_complete=0")))
        self.assertFalse(result["match"])
        self.assertIn("observed execution_complete != 1", result["errors"])

if __name__ == "__main__":
    unittest.main()
