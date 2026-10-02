import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location(
    "ws_boundary", ROOT/"tools/analyze_widescreen_preparation_boundary.py"
)
MOD=importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)

class WidescreenPreparationBoundaryTests(unittest.TestCase):
    def test_finds_post_camera_pre_edge_boundary(self):
        rows=[
            {"frame":1188,"pc":0x81A530,"camx":100,"camdx":8,
             "edgex":10,"edgex2":20,"edgey":30,"edgey2":40,"c0":0,"c1":0,"c2":0,"c3":0},
            {"frame":1188,"pc":0x81A533,"camx":108,"camdx":8,
             "edgex":10,"edgex2":20,"edgey":30,"edgey2":40,"c0":0,"c1":0,"c2":0,"c3":0},
            {"frame":1188,"pc":0x81A536,"camx":108,"camdx":8,
             "edgex":11,"edgex2":20,"edgey":30,"edgey2":40,"c0":1,"c1":0,"c2":0,"c3":0},
            {"frame":1188,"pc":0x81A539,"camx":108,"camdx":8,
             "edgex":11,"edgex2":20,"edgey":30,"edgey2":40,"c0":1,"c1":0,"c2":0,"c3":0},
        ]
        report=MOD.analyze(rows)
        self.assertTrue(report["boundary_isolation_supported"])
        self.assertEqual(report["stable_boundary"]["candidate_hook_pc"],0x81A533)
        self.assertEqual(report["stable_boundary"]["first_edge_change_pc"],0x81A536)

if __name__=="__main__":
    unittest.main()
