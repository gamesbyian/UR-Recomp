import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location(
    "ws_xphase", ROOT/"tools/analyze_widescreen_xphase_discriminator.py"
)
MOD=importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)

class XPhaseDiscriminatorTests(unittest.TestCase):
    def test_module_imports_and_exposes_base_analyzer(self):
        self.assertTrue(callable(MOD.base.analyze_rows))
        self.assertTrue(callable(MOD.base.parse))

if __name__=="__main__":
    unittest.main()
