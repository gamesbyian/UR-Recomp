"""Fail-closed SHA validation and schema rules for framework patch probe."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("portability", ROOT/"tools/baldosa_patch_portability.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class PatchPortabilityTest(unittest.TestCase):
    def test_sources_are_pinned(self):
        script=(ROOT/"tools/baldosa_patch_portability.py").read_text()
        self.assertIn("cd5875cbdaf19f5e324272b1f8051d671fce9215",script)
        self.assertIn("075fbe4c8e0d97b0013be541795c39cb644a9709",script)

    def test_patch_manifest_must_be_verified(self):
        import json
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            entry=root/"tools/toolchain-entries/snesrecomp.json"
            entry.parent.mkdir(parents=True)
            entry.write_text(json.dumps({"patches":[{"path":"tools/patches/a.patch", "sha256":"0"*64}]}))
            p=root/"tools/patches/a.patch"
            p.parent.mkdir(parents=True)
            p.write_text("not the claimed hash")
            with self.assertRaisesRegex(ValueError, "Invalid manifest hash"):
                mod.assess(root, root)


if __name__=="__main__":
    unittest.main()
