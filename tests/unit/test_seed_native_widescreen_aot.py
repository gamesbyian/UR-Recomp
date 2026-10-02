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
            p=Path(td)/"symbols.toml"
            p.write_text('[[func]]\nname = "I_RESET"\naddr = "8000"\nbank = 0\nemit = false\n',encoding="utf-8")
            self.assertTrue(MOD.ensure_seed(p))
            first=p.read_text(encoding="utf-8")
            self.assertIn('name = "WidescreenPrepareWrapper"', first)
            self.assertIn('addr = "A52F"', first)
            self.assertIn('bank = 1', first)
            self.assertIn('emit = true', first)
            self.assertFalse(MOD.ensure_seed(p))
            self.assertEqual(first,p.read_text(encoding="utf-8"))

if __name__=="__main__":
    unittest.main()
