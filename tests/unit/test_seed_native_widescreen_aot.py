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
    def test_adds_live_race_frame_root_once(self):
        with tempfile.TemporaryDirectory() as td:
            cfg=Path(td)
            symbols=cfg/"symbols.toml"
            symbols.write_text(
                '[[func]]\nname = "I_RESET"\naddr = "8000"\nbank = 0\nemit = false\n',
                encoding="utf-8",
            )
            first=MOD.ensure_seed(cfg)
            self.assertEqual(
                first, {"symbols": True, "bank00": True, "bank03": True})
            st=symbols.read_text(encoding="utf-8")
            bank0=(cfg/"bank00.cfg").read_text(encoding="utf-8")
            bank3=(cfg/"bank03.cfg").read_text(encoding="utf-8")
            self.assertIn(
                "func TourConfirmGenerationSnapshot E6A2", bank0)
            self.assertIn(
                'name = "TourConfirmGenerationSnapshot"', st)
            self.assertIn('addr = "E6A2"', st)
            self.assertIn('bank = 0', st)
            self.assertIn("func RaceFrameOrchestratorLoop CBCC", bank3)
            self.assertIn('name = "RaceFrameOrchestratorLoop"', st)
            self.assertIn('addr = "CBCC"', st)
            self.assertIn('bank = 3', st)

            second=MOD.ensure_seed(cfg)
            self.assertEqual(
                second, {"symbols": False, "bank00": False, "bank03": False})
            self.assertEqual(st,symbols.read_text(encoding="utf-8"))
            self.assertEqual(bank0,(cfg/"bank00.cfg").read_text(encoding="utf-8"))
            self.assertEqual(bank3,(cfg/"bank03.cfg").read_text(encoding="utf-8"))

if __name__=="__main__":
    unittest.main()
