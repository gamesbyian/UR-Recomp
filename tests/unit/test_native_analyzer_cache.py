"""Bounded, source-only regression tests for owner HP analyzer-cache reuse."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

# A legacy tools/devnode_benchmark.py module shadows the sibling directory,
# so resolve the standalone cache helper by its exact repository-owned path.
import importlib.util

CACHE_SOURCE = Path(__file__).parents[2] / "tools/devnode_benchmark/prepare_native_analyzer_cache.py"
CACHE_SPEC = importlib.util.spec_from_file_location("ur_hp_native_analyzer_cache", CACHE_SOURCE)
if CACHE_SPEC is None or CACHE_SPEC.loader is None:
    raise RuntimeError("native analyzer cache helper cannot be resolved")
cache = importlib.util.module_from_spec(CACHE_SPEC)
CACHE_SPEC.loader.exec_module(cache)

TRUSTED = {
    "GITHUB_REPOSITORY": "gamesbyian/UR-Recomp",
    "GITHUB_REF": "refs/heads/main",
    "GITHUB_EVENT_NAME": "schedule",
    "RUNNER_NAME": "hpmini-ur-recomp",
}


class NativeAnalyzerCacheTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.framework = root / "source"
        self.crate = self.framework / "recompiler-rs"
        (self.crate / "src").mkdir(parents=True)
        (self.crate / "src/main.rs").write_text("fn main() {}\n")
        (self.crate / "Cargo.toml").write_text("[package]\nname = 'test'\n")
        (self.crate / "Cargo.lock").write_text("version = 3\n")
        self.root = root / "cache"
        self.envfile = root / "github-env"
        self.envfile.write_text("")
        self.fixture = {"recipe": cache.RECIPE, "source": "fixture-source-a"}
        self.builds = 0

    def build(self, framework):
        self.builds += 1
        target = framework / "recompiler-rs/target/release"
        target.mkdir(parents=True, exist_ok=True)
        (target / cache.BINARY).write_bytes(b"MZ" + b"A" * 2048)

    def prepare(self, env=None):
        with patch.object(cache, "identity", return_value=self.fixture):
            return cache.prepare(
                self.framework, self.root, self.envfile,
                env=TRUSTED if env is None else env, build=self.build)

    def test_repeat_run_uses_verified_binary_without_rebuild(self):
        self.assertEqual(self.prepare(), "miss_built")
        canonical = self.crate / "target/release" / cache.BINARY
        canonical.unlink()  # Simulate freshly staged framework on the next HP job.
        self.assertEqual(self.prepare(), "hit")
        self.assertEqual(self.builds, 1)
        self.assertEqual(canonical.read_bytes(), b"MZ" + b"A" * 2048)
        path = canonical
        self.assertEqual(self.envfile.read_text().splitlines(), [
            f"SNESRECOMP_NATIVE_ANALYZER={path.absolute()}",
            f"SNESRECOMP_NATIVE_ANALYZER={path.absolute()}"])

    def test_copy_failure_cannot_expose_partial_executable_to_emitter(self):
        self.assertEqual(self.prepare(), "miss_built")
        canonical = self.crate / "target/release" / cache.BINARY
        canonical.unlink()
        self.envfile.write_text("")

        def partial(_source, destination):
            Path(destination).write_bytes(b"MZpartial")
            raise OSError("emulated incomplete copy")

        with patch.object(cache.shutil, "copyfile", side_effect=partial):
            self.assertEqual(self.prepare(), "source_fallback")
        self.assertFalse(canonical.exists())
        self.assertFalse(list(canonical.parent.glob(".analyzer-*.partial")))
        self.assertEqual(self.envfile.read_text(), "")

    def test_tampered_binary_falls_back_without_exporting_path(self):
        self.assertEqual(self.prepare(), "miss_built")
        self.envfile.write_text("")
        entry = self.root / cache.cache_key(self.fixture)
        (entry / cache.BINARY).write_bytes(b"MZ" + b"B" * 2048)
        self.assertEqual(self.prepare(), "invalid_fallback")
        self.assertEqual(self.envfile.read_text(), "")
        self.assertEqual(self.builds, 1)

    def test_tampered_manifest_falls_back(self):
        self.assertEqual(self.prepare(), "miss_built")
        self.envfile.write_text("")
        entry = self.root / cache.cache_key(self.fixture)
        record = json.loads((entry / "manifest.json").read_text())
        record["fingerprint"]["source"] = "wrong"
        (entry / "manifest.json").write_text(json.dumps(record))
        self.assertEqual(self.prepare(), "invalid_fallback")
        self.assertEqual(self.envfile.read_text(), "")

    def test_crate_digest_invalidates_source_changes_not_generated_target(self):
        first = cache.crate_digest(self.crate)
        (self.crate / "src/main.rs").write_text('fn main() { println!("new"); }\n')
        second = cache.crate_digest(self.crate)
        self.assertNotEqual(first, second)
        self.build(self.framework)
        self.assertEqual(second, cache.crate_digest(self.crate))
        (self.crate / "Cargo.lock").write_text("version = 4\n")
        self.assertNotEqual(second, cache.crate_digest(self.crate))

    def test_untrusted_runs_never_publish_or_build(self):
        for item, value in (
            ("GITHUB_REF", "refs/pull/42/merge"),
            ("GITHUB_REPOSITORY", "foreign/repo"),
            ("RUNNER_NAME", "hosted-windows"),
            ("GITHUB_EVENT_NAME", "pull_request"),
        ):
            with self.subTest(item=item):
                self.assertEqual(
                    self.prepare({**TRUSTED, item: value}), "refused_untrusted")
        self.assertEqual(self.builds, 0)
        self.assertEqual(self.envfile.read_text(), "")

    def test_failed_cache_build_falls_back_without_export(self):
        def fail(_):
            raise OSError("emulated disk error")
        with patch.object(cache, "identity", return_value=self.fixture):
            self.assertEqual(cache.prepare(
                self.framework, self.root, self.envfile,
                env=TRUSTED, build=fail), "source_fallback")
        self.assertEqual(self.envfile.read_text(), "")

    def test_cache_rejects_linked_entries_when_supported(self):
        self.root.mkdir()
        real = self.root / "real"
        real.mkdir()
        link = self.root / "linked"
        try:
            link.symlink_to(real, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("cannot create directory link on this filesystem")
        self.assertIsNone(cache.verified_binary(link, self.fixture))
        self.assertEqual(self.prepare(), "miss_built")


if __name__ == "__main__":
    unittest.main()
