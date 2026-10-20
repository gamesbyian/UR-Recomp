"""Generic RF081 width-aware bus footprint, not authenticated RTS operands."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
from qa01_rf081_read_footprint import footprint,bounded_read_summary


class ReadFootprint(unittest.TestCase):
    def test_width_two_at_01f1_touches_01f2_not_01f3(self):
        self.assertEqual(footprint(dict(stage="read",bank="00",addr="01F1",width="2")),
                         ("01F1","01F2"))

    def test_start_address_not_equal_touched_address(self):
        rows=[dict(stage="read",bank="00",addr="01F1",width="2"),
              dict(stage="read",bank="00",addr="01F1",width="1"),
              dict(stage="read",bank="00",addr="0000",width="1")]
        report=bounded_read_summary(rows)
        self.assertFalse(report["starts_at_01F2"])
        self.assertTrue(report["touches_01F2"])
        self.assertFalse(report["touches_01F3"])
        self.assertFalse(report["dynamic_RTS_operand_identity_proven"])
        self.assertEqual(report["accepted_USA_events"],0)

    def test_noncanonical_address_and_other_banks_refuse(self):
        for kw in (dict(stage="read",bank="01",addr="01F1",width="2"),
                   dict(stage="read",bank="00",addr="01f1",width="2"),
                   dict(stage="read",bank="00",addr="01F1",width=True),
                   dict(stage="write",bank="00",addr="01F1",width="2")):
            with self.subTest(kw=kw),self.assertRaises(ValueError):
                footprint(kw)

    def test_bank_boundary_refuses(self):
        with self.assertRaises(ValueError):
            footprint(dict(stage="read",bank="00",addr="FFFF",width="2"))

    def test_source_local_cardinality_required(self):
        with self.assertRaises(ValueError):
            bounded_read_summary([dict(stage="read",bank="00",addr="01F1",width="2")])


if __name__=="__main__":
    unittest.main()
