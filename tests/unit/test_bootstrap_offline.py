from __future__ import annotations

import hashlib
import io
import importlib.util
from pathlib import Path
import tempfile
import tarfile
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


    def test_offline_archive_component_extracts_without_git_fallback(self) -> None:
        tool = {
            "id": "framework",
            "url": "https://github.com/example/framework.git",
            "revision": "0" * 40,
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            archive = root / "framework.tar.gz"
            payload = b"local archive source\n"
            with tarfile.open(archive, "w:gz") as tf:
                info = tarfile.TarInfo("nested/value.txt")
                info.size = len(payload)
                tf.addfile(info, io.BytesIO(payload))

            island = {
                "framework": {
                    "id": "framework",
                    "mode": "archive",
                    "archive_path": "framework.tar.gz",
                }
            }
            stage = root / ".tools" / "src"
            with mock.patch.object(bootstrap, "ROOT", root):
                with mock.patch.object(
                    bootstrap, "ensure_checkout", side_effect=AssertionError("network fallback")
                ):
                    actual = bootstrap.ensure_source(tool, stage, island, offline=True)

            self.assertEqual(actual, stage / "framework")
            self.assertEqual((actual / "nested" / "value.txt").read_bytes(), payload)

    def test_vendored_patch_targets_staged_copy_without_git_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            dest = root / ".tools" / "src" / "example"
            dest.mkdir(parents=True)
            target = dest / "value.txt"
            target.write_text("old\n", encoding="utf-8")

            patch_rel = Path("patches") / "example.patch"
            patch_path = root / patch_rel
            patch_path.parent.mkdir(parents=True)
            patch_data = (
                "diff --git a/value.txt b/value.txt\n"
                "--- a/value.txt\n"
                "+++ b/value.txt\n"
                "@@ -1 +1 @@\n"
                "-old\n"
                "+new\n"
            )
            patch_path.write_text(patch_data, encoding="utf-8")
            tool = {
                "id": "example",
                "patches": [
                    {
                        "path": patch_rel.as_posix(),
                        "sha256": hashlib.sha256(patch_data.encode("utf-8")).hexdigest(),
                    }
                ],
            }

            with mock.patch.object(bootstrap, "ROOT", root):
                bootstrap.apply_patches(tool, dest)

            self.assertEqual(target.read_text(encoding="utf-8"), "new\n")


if __name__ == "__main__":
    unittest.main()
