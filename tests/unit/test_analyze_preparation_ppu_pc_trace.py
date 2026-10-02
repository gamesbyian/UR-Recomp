import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "prep_ppu_pc", ROOT / "tools/analyze_preparation_ppu_pc_trace.py"
)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)


class PreparationPpuPcTraceTests(unittest.TestCase):
    def test_direct_quad_and_compact_counts(self):
        log = (
            "script f=1005 dump prep-emission-before-scroll fb=256x224\n"
            "PPUPCTRACE frame=1006 v=239 cycles=10 pc=82D390 addr=2116 val=48 "
            "ca=16 cb=16 camx=1000 camy=700 edgex=42 edgey=96 camdx=13\n"
            "PPUPCTRACE frame=1006 v=239 cycles=11 pc=82D393 addr=2117 val=19 "
            "ca=16 cb=16 camx=1000 camy=700 edgex=42 edgey=96 camdx=13\n"
            "PPUPCTRACE frame=1006 v=239 cycles=12 pc=82D3A0 addr=2118 val=00 "
            "ca=16 cb=16 camx=1000 camy=700 edgex=42 edgey=96 camdx=13\n"
            "PPUPCTRACE frame=1006 v=239 cycles=13 pc=82D3A0 addr=2119 val=38 "
            "ca=16 cb=16 camx=1000 camy=700 edgex=42 edgey=96 camdx=13\n"
        )
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "run.log"
            p.write_text(log, encoding="utf-8")
            start, rows = MOD.parse(p)
        self.assertEqual(start, 1005)
        q = MOD.quads(rows)
        self.assertEqual(len(q), 1)
        self.assertEqual(q[0]["destination"], 0x1948)
        self.assertEqual((q[0]["write_2118"], q[0]["write_2119"]), (0, 0x38))
        self.assertEqual((q[0]["count_a"], q[0]["count_b"]), (16, 16))


if __name__ == "__main__":
    unittest.main()
