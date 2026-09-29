from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "bootstrap_toolchain", ROOT / "tools" / "bootstrap_toolchain.py"
)
assert SPEC is not None and SPEC.loader is not None
bootstrap = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bootstrap)


class BootstrapOfflineTests(unittest.TestCase):
    def test_offline_pending_component_never_falls_back_to_git(self) -> None:
        tool = {
            "id": "example",
            "url": "https://github.com/example/example.git",
            "revision": "0" * 40,
        }
        island = {"example": {"id": "example", "mode": "pending"}}
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.object(
                bootstrap, "ensure_checkout", side_effect=AssertionError("network fallback")
            ):
                with self.assertRaises(SystemExit) as ctx:
                    bootstrap.ensure_source(tool, Path(td), island, offline=True)
        self.assertIn("--offline forbids GitHub fetch", str(ctx.exception))

    def test_online_pending_component_uses_existing_external_path(self) -> None:
        tool = {
            "id": "example",
            "url": "https://github.com/example/example.git",
            "revision": "0" * 40,
        }
        island = {"example": {"id": "example", "mode": "pending"}}
        sentinel = Path("/tmp/external-example")
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.object(bootstrap, "ensure_checkout", return_value=sentinel) as checkout:
                actual = bootstrap.ensure_source(tool, Path(td), island, offline=False)
        self.assertEqual(actual, sentinel)
        checkout.assert_called_once()


if __name__ == "__main__":
    unittest.main()
