import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location(
    "ws_count32", ROOT/"tools/analyze_widescreen_count32_discriminator.py"
)
MOD=importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)

def row(frame,size,payload,camx=100):
    desc={
        "slot":2,"ready":1,"vram":0x0D80,"source":0x0433,
        "size":size,"vmain":0x81,"payload_hex":payload,
    }
    return {
        "frame":frame,"site":"after_build","camx":camx,"camy":10,
        "camdx":2,"camdy":0,
        "gameplay":{"px":1,"py":2,"xs":3,"ys":4,"pitch":5,"contact":6,
                    "laps":7,"checkpoint":8,"finish":9},
        "descriptors":[desc],
    }

class Count32DiscriminatorTests(unittest.TestCase):
    def test_classifies_size_expansion_without_state_change(self):
        p32="AA"*32
        p64=p32+"BB"*32
        report=MOD.analyze([row(1,0x20,p32)],[row(1,0x40,p64)])
        self.assertTrue(report["all_state_equal"])
        self.assertTrue(report["builder_expands_count32_to_64_bytes"])
        self.assertEqual(report["classification"],"count-expands-single-descriptor")
        self.assertTrue(report["rows"][0]["payload_prefix_matches_control"])

    def test_state_difference_is_visible(self):
        a=row(1,0x20,"AA"*32)
        b=row(1,0x40,"AA"*64,camx=101)
        report=MOD.analyze([a],[b])
        self.assertFalse(report["all_state_equal"])

if __name__=="__main__":
    unittest.main()
