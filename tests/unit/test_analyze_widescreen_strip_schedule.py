import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "ws_strip", ROOT / "tools/analyze_widescreen_strip_schedule.py"
)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)

PAYLOAD = "00112233445566778899AABBCCDDEEFF" * 2

def line(margin: int, frame: int, pc: int, camx: int, payload: str = PAYLOAD) -> str:
    desc = f"0:0:0000:0000:0000:0000:,1:0:0000:0000:0000:0000:,2:1:0D80:0433:0020:0081:{payload},3:0:0000:0000:0000:0000:,4:0:0000:0000:0000:0000:,5:0:0000:0000:0000:0000:,6:0:0000:0000:0000:0000:,7:0:0000:0000:0000:0000:"
    return (
        f"WSDMA margin={margin} frame={frame} v=200 cycles=100 pc={pc:06X} "
        f"camx={camx} camy=10 px=100 py=20 xs=3 ys=0 pitch=0 "
        f"contact=1 laps=2 checkpoint=3 finish=4 edgex=384 edgey=0 desc={desc}\n"
    )

class WidescreenStripScheduleTests(unittest.TestCase):
    def test_future_stock_payload_match_and_same_frame_consume(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            control = td / "control.log"
            plus8 = td / "plus8.log"
            control.write_text(
                line(0, 100, 0x81A59D, 100)
                + line(0, 100, 0x82D19B, 100)
                + line(0, 101, 0x81A59D, 108)
                + line(0, 101, 0x82D19B, 108),
                encoding="utf-8",
            )
            plus8.write_text(
                line(8, 100, 0x81A59D, 100)
                + line(8, 100, 0x82D19B, 100),
                encoding="utf-8",
            )
            report, matches = MOD.analyze_rows(MOD.parse(control), MOD.parse(plus8))
            self.assertTrue(report["success"])
            self.assertEqual(report["successful_future_stock_matches"], 1)
            self.assertEqual(matches[0]["camera_x_advance"], 8)

    def test_gameplay_difference_rejects_result(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            control = td / "control.log"
            plus8 = td / "plus8.log"
            control.write_text(
                line(0, 100, 0x81A59D, 100)
                + line(0, 100, 0x82D19B, 100)
                + line(0, 101, 0x81A59D, 108)
                + line(0, 101, 0x82D19B, 108),
                encoding="utf-8",
            )
            bad = line(8, 100, 0x81A59D, 100).replace("px=100", "px=101")
            plus8.write_text(bad + line(8, 100, 0x82D19B, 100), encoding="utf-8")
            report, _ = MOD.analyze_rows(MOD.parse(control), MOD.parse(plus8))
            self.assertFalse(report["authoritative_gameplay_state_equal"])
            self.assertFalse(report["success"])

if __name__ == "__main__":
    unittest.main()
