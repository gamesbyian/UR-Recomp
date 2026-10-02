import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location(
    "prep_emit", ROOT/"tools/analyze_preparation_emission_probe.py")
MOD=importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)


class PreparationEmissionTests(unittest.TestCase):
    def test_expected_events_follow_d383_reverse_order(self):
        w=bytearray(0x2200)
        # list A has two entries, emitted index 1 then 0
        w[0x0DCD:0x0DCF]=(2).to_bytes(2,"little")
        w[0x0D8D:0x0D8F]=(0x1234).to_bytes(2,"little")
        w[0x0D8F:0x0D91]=(0x5678).to_bytes(2,"little")
        w[0x0D6D]=1
        w[0x0D6E]=2
        w[0x2134:0x2136]=(0xA1B2).to_bytes(2,"little") # selector 1
        w[0x2136:0x2138]=(0xC3D4).to_bytes(2,"little") # selector 2
        rows=MOD.expected_events(bytes(w))
        self.assertEqual(
            [(r["destination"],r["write_2118"],r["write_2119"]) for r in rows],
            [(0x5678,0xC3,0xD4),(0x1234,0xA1,0xB2)],
        )

    def test_recorded_events_recognizes_snesref_ppu_shape(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"x.tsv"
            p.write_text(
                "1\t12\t34\t2116\t78\tcpu\n"
                "1\t12\t35\t2117\t56\tcpu\n"
                "1\t12\t36\t2118\tC3\tcpu\n"
                "1\t12\t37\t2119\tD4\tcpu\n",
                encoding="utf-8",
            )
            self.assertEqual(
                MOD.recorded_events(p),
                [{"destination":0x5678,"write_2118":0xC3,"write_2119":0xD4}],
            )

    def test_recorded_events_recognizes_exact_ppu_shape(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"x.tsv"
            p.write_text(
                "1\t-1\t2116\t78\tcpu\n"
                "1\t-1\t2117\t56\tcpu\n"
                "1\t-1\t2118\tC3\tcpu\n"
                "1\t-1\t2119\tD4\tcpu\n",
                encoding="utf-8",
            )
            self.assertEqual(
                MOD.recorded_events(p),
                [{"destination":0x5678,"write_2118":0xC3,"write_2119":0xD4}],
            )


if __name__=="__main__":
    unittest.main()
