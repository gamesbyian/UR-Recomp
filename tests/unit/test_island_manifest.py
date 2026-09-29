from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "validate_island", ROOT / "tools" / "validate_island.py"
)
assert SPEC is not None and SPEC.loader is not None
validate_island = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_island)


class IslandManifestTests(unittest.TestCase):
    def test_repository_manifest_is_valid(self) -> None:
        errors, notes = validate_island.validate()
        self.assertEqual(errors, [])
        self.assertTrue(notes)

    def test_pending_components_do_not_claim_local_sources(self) -> None:
        manifest = validate_island.load(ROOT / "third_party" / "manifest.json")
        pending = [c for c in manifest["components"] if c["mode"] == "pending"]
        self.assertTrue(pending)
        for component in pending:
            self.assertIsNone(component["source_path"])
            self.assertIsNone(component["archive_path"])
            self.assertIsNone(component["source_sha256"])


if __name__ == "__main__":
    unittest.main()
