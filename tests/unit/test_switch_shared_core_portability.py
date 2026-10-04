import json
import tempfile
import unittest
from pathlib import Path

from tools.build_switch_shared_core_probe import validate_contract

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "analysis/switch-shared-core-contract.json"


class SwitchSharedCorePortabilityTest(unittest.TestCase):
    def test_repository_contract_is_clean(self):
        contract = json.loads(CONTRACT.read_text())
        self.assertEqual(validate_contract(ROOT, contract), [])

    def test_desktop_adapter_is_explicitly_excluded(self):
        contract = json.loads(CONTRACT.read_text())
        excluded = {entry["path"] for entry in contract["excluded_adapters"]}
        portable = set(contract["portable_translation_units"])
        self.assertIn("native/product/uniracers_modern_host.cpp", excluded)
        self.assertNotIn("native/product/uniracers_modern_host.cpp", portable)
        self.assertIn("native/title/uniracers_ws_margins.c", excluded)
        self.assertNotIn("native/title/uniracers_ws_margins.c", portable)

    def test_direct_sdl_leak_is_rejected(self):
        contract = json.loads(CONTRACT.read_text())
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "native/product/example.cpp"
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("int f() { return SDL_PushEvent(nullptr); }\n")
            (root / "native/title").mkdir(parents=True)
            excluded = root / "native/product/uniracers_modern_host.cpp"
            excluded.write_text("// adapter\n")
            test_contract = dict(contract)
            test_contract["portable_translation_units"] = [rel]
            test_contract["include_dirs"] = ["native/product", "native/title"]
            errors = validate_contract(root, test_contract)
            self.assertTrue(any("SDL_" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
