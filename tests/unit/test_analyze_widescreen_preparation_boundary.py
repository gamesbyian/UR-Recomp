import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location(
    "ws_boundary", ROOT/"tools/analyze_widescreen_preparation_boundary.py"
)
MOD=importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)


def row(frame, pc, op, a, camx, edgex, c0):
    return {
        "frame":frame,
        "pc":pc,
        "op":op,
        "a":a,
        "x":0,
        "y":0,
        "camx":camx,
        "camdx":8,
        "edgex":edgex,
        "edgex2":20,
        "edgey":30,
        "edgey2":40,
        "c0":c0,
        "c1":0,
        "c2":0,
        "c3":0,
    }


class WidescreenPreparationBoundaryTests(unittest.TestCase):
    def test_finds_post_camera_pre_edge_boundary(self):
        rows=[
            row(1188,0x81A530,0xEA,100,100,10,0),
            row(1188,0x81A533,0x29,108,108,10,0),
            row(1188,0x81A536,0xEA,108,108,11,1),
            row(1188,0x81A539,0xEA,108,108,11,1),
        ]
        report=MOD.analyze(rows)
        self.assertTrue(report["boundary_isolation_supported"])
        self.assertEqual(report["stable_boundary"]["candidate_hook_pc"],0x81A533)
        self.assertEqual(report["stable_boundary"]["first_edge_change_pc"],0x81A536)
        self.assertTrue(report["stable_boundary"]["a_equals_camera_x"])
        self.assertEqual(report["stable_boundary"]["hook_opcode"],0x29)

    def test_parser_accepts_multiple_observations_in_one_physical_line(self):
        sample=(
            "WSBND frame=1188 v=48 cycles=1 pc=81A53E op=EA b1=00 b2=00 "
            "a=0064 x=0000 y=0000 d=0000 p=0000 "
            "camx=100 camy=20 camdx=8 camdy=0 edgex=10 edgex2=20 edgey=30 edgey2=40 cnt=0,0,0,0\\n"
            "WSBND frame=1188 v=48 cycles=2 pc=81A541 op=29 b1=00 b2=00 "
            "a=006C x=0000 y=0000 d=0000 p=0000 "
            "camx=108 camy=20 camdx=8 camdy=0 edgex=10 edgex2=20 edgey=30 edgey2=40 cnt=0,0,0,0\\n"
            "WSBND frame=1188 v=48 cycles=3 pc=81A59A op=20 b1=88 b2=AB "
            "a=006C x=0000 y=0000 d=0000 p=0000 "
            "camx=108 camy=20 camdx=8 camdy=0 edgex=11 edgex2=20 edgey=30 edgey2=40 cnt=1,0,0,0"
        )
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"trace.log"
            p.write_text(sample,encoding="utf-8")
            rows=MOD.parse(p)
            self.assertEqual(len(rows),3)
            report=MOD.analyze(rows)
            self.assertEqual(report["stable_boundary"]["candidate_hook_pc"],0x81A541)
            self.assertTrue(report["stable_boundary"]["a_equals_camera_x"])


if __name__=="__main__":
    unittest.main()
