import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location(
    "ws_seed", ROOT/"tools/seed_native_widescreen_aot.py"
)
MOD=importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)

class NativeWidescreenAotSeedTests(unittest.TestCase):
    def test_adds_bank1_a52f_emit_root_once(self):
        with tempfile.TemporaryDirectory() as td:
            cfg=Path(td)
            symbols=cfg/"symbols.toml"
            symbols.write_text(
                '[[func]]\nname = "I_RESET"\naddr = "8000"\nbank = 0\nemit = false\n',
                encoding="utf-8",
            )
            first=MOD.ensure_seed(cfg)
            self.assertEqual(first, {"symbols": True, "bank01": True, "bank02": True, "bank03": True})
            st=symbols.read_text(encoding="utf-8")
            bank=(cfg/"bank01.cfg").read_text(encoding="utf-8")
            bank2=(cfg/"bank02.cfg").read_text(encoding="utf-8")
            bank3=(cfg/"bank03.cfg").read_text(encoding="utf-8")
            self.assertIn('name = "WidescreenPrepareWrapper"', st)
            self.assertIn('addr = "A52F"', st)
            self.assertIn('bank = 1', st)
            self.assertIn('emit = true', st)
            self.assertIn('name = "WidescreenPostConsume"', st)
            self.assertIn('addr = "D2D1"', st)
            self.assertIn('bank = 2', st)
            self.assertIn("bank = 1", bank)
            self.assertIn("tier_down_stubs", bank)
            self.assertIn("func WidescreenPrepareWrapper A52F", bank)
            self.assertIn("func WidescreenPostConsume D2D1", bank2)
            self.assertIn("func RaceFrameOrchestratorLoop CBCC", bank3)
            self.assertIn('name = "RaceFrameOrchestratorLoop"', st)
            self.assertIn('addr = "CBCC"', st)
            self.assertIn('bank = 3', st)

            second=MOD.ensure_seed(cfg)
            self.assertEqual(second, {"symbols": False, "bank01": False, "bank02": False, "bank03": False})
            self.assertEqual(st,symbols.read_text(encoding="utf-8"))
            self.assertEqual(bank,(cfg/"bank01.cfg").read_text(encoding="utf-8"))
            self.assertEqual(bank2,(cfg/"bank02.cfg").read_text(encoding="utf-8"))
            self.assertEqual(bank3,(cfg/"bank03.cfg").read_text(encoding="utf-8"))

if __name__=="__main__":
    unittest.main()
