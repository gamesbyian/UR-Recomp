import hashlib
import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]


class ToolchainPatchHashTests(unittest.TestCase):
    def test_registered_patch_hashes_match_files(self):
        manifest = json.loads((ROOT / "tools" / "toolchain.json").read_text())
        for tool in manifest["tools"]:
            for patch in tool.get("patches", []):
                path = ROOT / patch["path"]
                self.assertTrue(path.is_file(), f"missing patch: {patch['path']}")
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                self.assertEqual(digest, patch["sha256"], patch["path"])


if __name__ == "__main__":
    unittest.main()
