import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location(
    "ws_oracle", ROOT/"tools/build_widescreen_shadow_oracle.py"
)
MOD=importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)

PAYLOAD_A="00"*32
PAYLOAD_B="11"*32

class WidescreenShadowOracleTests(unittest.TestCase):
    def test_build_retains_only_valid_stock_horizontal_rows(self):
        text=(
            f"URWS_PRIMARY margin=0 camx=100 edge=0D80 count=16 payload={PAYLOAD_A}\n"
            f"URWS_PRIMARY margin=0 camx=108 edge=0D81 count=16 payload={PAYLOAD_B}\n"
            f"URWS_PRIMARY margin=0 camx=116 edge=FFFF count=16 payload={PAYLOAD_A}\n"
            f"URWS_PRIMARY margin=0 camx=124 edge=0D82 count=8 payload={PAYLOAD_A}\n"
            f"URWS_PRIMARY margin=8 camx=132 edge=0D83 count=16 payload={PAYLOAD_A}\n"
        )
        rows=MOD.build(text)
        self.assertEqual(rows,[
            (100,0x0D80,PAYLOAD_A.upper()),
            (108,0x0D81,PAYLOAD_B.upper()),
        ])

    def test_build_fails_closed_without_stock_rows(self):
        with self.assertRaisesRegex(ValueError,"no stock horizontal strip rows"):
            MOD.build("URWS_PRIMARY margin=8 camx=100 edge=0D80 count=16 payload="+PAYLOAD_A)

if __name__=="__main__":
    unittest.main()
