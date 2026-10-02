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


    def test_archive_stage_overlays_nested_cargo_closure(self) -> None:
        tool = {
            "id": "framework",
            "url": "https://github.com/example/framework.git",
            "revision": "0" * 40,
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            archive = root / "framework.tar.gz"
            lock = b"version = 4\n"
            with tarfile.open(archive, "w:gz") as tf:
                for name, payload in (
                    ("recompiler-rs/Cargo.lock", lock),
                    ("recompiler-rs/Cargo.toml", b"[package]\nname='x'\nversion='0.1.0'\n"),
                ):
                    info = tarfile.TarInfo(name)
                    info.size = len(payload)
                    tf.addfile(info, io.BytesIO(payload))

            vendor = root / "cargo" / "vendor" / "dep-1.0.0"
            vendor.mkdir(parents=True)
            (vendor / "Cargo.toml").write_text("[package]\nname='dep'\nversion='1.0.0'\n")
            config = root / "cargo" / "config.toml"
            config.write_text(
                '[source.crates-io]\nreplace-with = "vendored-sources"\n'
                '[source.vendored-sources]\ndirectory = "vendor"\n'
                '[net]\noffline = true\n',
                encoding="utf-8",
            )
            closure_lock = root / "cargo" / "Cargo.lock"
            closure_lock.write_bytes(lock)

            island = {
                "framework": {
                    "id": "framework",
                    "mode": "archive",
                    "archive_path": "framework.tar.gz",
                    "dependency_closure": {
                        "type": "cargo-vendor",
                        "vendor_path": "cargo/vendor",
                        "config_path": "cargo/config.toml",
                        "cargo_lock_path": "cargo/Cargo.lock",
                        "stage_into": "recompiler-rs",
                    },
                }
            }
            stage = root / ".tools" / "src"
            with mock.patch.object(bootstrap, "ROOT", root):
                actual = bootstrap.ensure_source(tool, stage, island, offline=True)

            crate = actual / "recompiler-rs"
            self.assertTrue((crate / "vendor" / "dep-1.0.0" / "Cargo.toml").is_file())
            self.assertTrue((crate / ".cargo" / "config.toml").is_file())
            self.assertEqual((crate / "Cargo.lock").read_bytes(), lock)

    def test_clone_only_applies_registered_patches_before_skipping_build(self) -> None:
        tool = {
            "id": "example",
            "group": "core",
            "revision": "0" * 40,
            "purpose": "test",
            "headless": {"status": "native"},
            "install_mode": "build",
            "build": [["should-not-run"]],
            "patches": [],
        }
        manifest = {"tools": [tool], "install_root": ".tools"}
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            dest = root / ".tools" / "src" / "example"
            dest.mkdir(parents=True)
            with (
                mock.patch.object(bootstrap, "ROOT", root),
                mock.patch.object(bootstrap, "load_manifest", return_value=manifest),
                mock.patch.object(bootstrap, "load_island_manifest", return_value={}),
                mock.patch.object(bootstrap, "ensure_source", return_value=dest),
                mock.patch.object(bootstrap, "apply_patches") as apply_patches,
                mock.patch.object(bootstrap, "run") as run,
                mock.patch.object(
                    bootstrap.sys,
                    "argv",
                    ["bootstrap_toolchain.py", "--tool", "example", "--clone-only"],
                ),
            ):
                self.assertEqual(bootstrap.main(), 0)

            apply_patches.assert_called_once_with(tool, dest)
            run.assert_not_called()


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
