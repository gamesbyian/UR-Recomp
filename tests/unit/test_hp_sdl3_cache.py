"""Safety and provenance checks for the opt-in pinned Windows SDL3 install."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[2] / "tools/devnode_benchmark/prepare_sdl3_cache.py"
spec = importlib.util.spec_from_file_location("prepare_sdl3_cache", MODULE)
cache = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cache)


class HPSDL3CacheTests(unittest.TestCase):
    def test_cache_key_independent_of_dict_order(self):
        self.assertEqual(cache.cache_key({"a": 1, "b": 2}), cache.cache_key({"b": 2, "a": 1}))
        self.assertNotEqual(cache.cache_key({"a": 1}), cache.cache_key({"a": 2}))

    def test_source_tree_is_content_bound(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.c").write_text("int a;", encoding="utf-8")
            initial = cache.tree_digest(root)
            (root / "a.c").write_text("int b;", encoding="utf-8")
            self.assertNotEqual(initial, cache.tree_digest(root))

    def test_only_exact_complete_static_stage_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stage = root / "stage"
            conf = stage / "lib/cmake/SDL3/SDL3Config.cmake"
            lib = stage / "lib/SDL3-static.lib"
            conf.parent.mkdir(parents=True)
            conf.write_text("# pinned", encoding="utf-8")
            lib.write_bytes(b"fake-test-lib")
            identity = {"source": "exact"}
            record = {"fingerprint": identity, "files": cache.manifest_for_stage(stage)}
            (root / "manifest.json").write_text(json.dumps(record), encoding="utf-8")
            self.assertEqual(cache.validate_stage(root, identity), conf.parent)
            self.assertIsNone(cache.validate_stage(root, {"source": "drift"}))
            lib.write_bytes(b"tampered")
            self.assertIsNone(cache.validate_stage(root, identity))
            lib.write_bytes(b"fake-test-lib")
            (stage / "SDL3.dll").write_bytes(b"bad shared library")
            self.assertIsNone(cache.validate_stage(root, identity))

    def test_corrupt_derived_cache_recovers_without_touching_neighbour(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entry = root / ("a" * 24)
            (entry / "stage").mkdir(parents=True)
            (entry / "stage" / "broken.lib").write_bytes(b"tampered")
            neighbour = root / ("b" * 24)
            neighbour.mkdir()
            (neighbour / "keep.txt").write_text("untouched", encoding="utf-8")
            self.assertIsNone(cache.validate_stage(entry, {"identity": "expected"}))
            cache.discard_invalid_entry(entry)
            self.assertFalse(entry.exists())
            self.assertEqual((neighbour / "keep.txt").read_text("utf-8"), "untouched")
            self.assertFalse(list(root.glob(".invalid-*")))

    def test_corrupt_cache_refuses_arbitrary_path_and_non_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outside = root / "user_data"
            outside.mkdir()
            (outside / "keep.txt").write_text("private", encoding="utf-8")
            with self.assertRaises(ValueError):
                cache.discard_invalid_entry(outside)
            invalid_file = root / ("d" * 24)
            invalid_file.write_text("not a derived directory", encoding="utf-8")
            with self.assertRaises(ValueError):
                cache.discard_invalid_entry(invalid_file)
            self.assertEqual((outside / "keep.txt").read_text("utf-8"), "private")
            self.assertTrue(invalid_file.is_file())

    def test_corrupt_cache_refuses_symlink_to_other_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            user = root / "user"
            user.mkdir()
            entry = root / ("e" * 24)
            try:
                entry.symlink_to(user, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("runner account cannot create Windows symlinks")
            with self.assertRaises(ValueError):
                cache.discard_invalid_entry(entry)
            self.assertTrue(user.is_dir())

    def test_interrupted_quarantine_remains_fail_closed_and_key_reusable(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entry = root / ("f" * 24)
            entry.mkdir()
            with patch.object(cache.shutil, "rmtree", side_effect=OSError("locked")):
                with self.assertRaises(OSError):
                    cache.discard_invalid_entry(entry)
            self.assertFalse(entry.exists())
            self.assertEqual(len(list(root.glob(".invalid-" + entry.name + "-*"))), 1)
            entry.mkdir()  # subsequent run is able to reconstruct the key
            self.assertTrue(entry.is_dir())

    def test_cache_helper_changes_trigger_all_windows_routes(self):
        workflow_dir = MODULE.parents[2] / ".github/workflows"
        required = '"tools/devnode_benchmark/prepare_sdl3_cache.py"'
        for name in ("windows-native-smoke.yml",
                     "owner-hp-main-windows-smoke.yml",
                     "qa05-qa09-windows-candidate.yml"):
            with self.subTest(workflow=name):
                self.assertIn(required, (workflow_dir / name).read_text("utf-8"))

    def test_missing_or_incomplete_install_cannot_be_used(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertIsNone(cache.validate_stage(root, {"k": 1}))
            (root / "manifest.json").write_text("{", encoding="utf-8")
            self.assertIsNone(cache.validate_stage(root, {"k": 1}))


if __name__ == "__main__":
    unittest.main()
