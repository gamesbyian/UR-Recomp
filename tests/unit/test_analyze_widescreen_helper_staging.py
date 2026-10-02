import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location(
    "ws_helper", ROOT/"tools/analyze_widescreen_helper_staging.py"
)
MOD=importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)

class WidescreenHelperStagingTests(unittest.TestCase):
    def test_parse_help_collects_changed_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"run.log"
            p.write_text(
                "WSHELP frame=1188 pc=81A534 changes=0010:01:09,0501:22:2A\n",
                encoding="utf-8",
            )
            rows=MOD.parse_help(p)
            self.assertEqual(rows[1188][0x0010],(0x01,0x09))
            self.assertEqual(rows[1188][0x0501],(0x22,0x2A))

    def test_row_map_selects_requested_pc(self):
        rows=[
            {"frame":1,"pc":0x81A534,"a":1},
            {"frame":1,"pc":0x81A597,"a":2},
            {"frame":2,"pc":0x81A534,"a":3},
        ]
        mapped=MOD.row_map(rows,0x81A534)
        self.assertEqual(mapped[1]["a"],1)
        self.assertEqual(mapped[2]["a"],3)

if __name__=="__main__":
    unittest.main()
