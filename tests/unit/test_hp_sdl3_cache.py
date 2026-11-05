"""Safety and provenance checks for the opt-in pinned Windows SDL3 install."""
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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

    def test_linker_sdk_same_version_byte_mutation_invalidates_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vs = root / "VS"
            kit = root / "Windows Kits/10"
            msvc = vs / "VC/Tools/MSVC/14.44.35207"
            sdk = kit / "Include/10.0.26100.0/ucrt"
            msvc.mkdir(parents=True)
            sdk.mkdir(parents=True)
            header = msvc / "include/vcruntime.h"
            header.parent.mkdir(parents=True)
            header.write_bytes(b"v1")
            ucrt = sdk / "stdlib.h"
            ucrt.write_bytes(b"SDK-v1")
            a = cache.linker_relevant_identity(vs, kit)
            self.assertIn("MSVC/14.44.35207/include/vcruntime.h", a)
            self.assertIn("Kit/Include/10.0.26100.0/ucrt/stdlib.h", a)
            header.write_bytes(b"v2")
            b = cache.linker_relevant_identity(vs, kit)
            self.assertNotEqual(cache.cache_key(a), cache.cache_key(b))
            ucrt.write_bytes(b"SDK-v2")
            c = cache.linker_relevant_identity(vs, kit)
            self.assertNotEqual(cache.cache_key(b), cache.cache_key(c))

    def test_linker_sdk_sentinel_appearance_changes_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vs = root / "VS"
            kit = root / "Kit"
            (vs / "VC/Tools/MSVC/14.44.35207").mkdir(parents=True)
            (kit / "Include/10.0.26100.0").mkdir(parents=True)
            a = cache.linker_relevant_identity(vs, kit)
            lib = kit / "Lib/10.0.26100.0/um/x64/kernel32.lib"
            lib.parent.mkdir(parents=True)
            lib.write_bytes(b"library")
            b = cache.linker_relevant_identity(vs, kit)
            self.assertEqual(a["Kit/Lib/10.0.26100.0/um/x64/kernel32.lib"], "absent")
            self.assertNotEqual(cache.cache_key(a), cache.cache_key(b))

    def test_linker_sdk_inventory_is_bounded_and_redirects_denied(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vs = root / "VS"
            kit = root / "Kit"
            msvc = vs / "VC/Tools/MSVC"
            msvc.mkdir(parents=True)
            (kit / "Include/10.0.26100.0").mkdir(parents=True)
            for i in range(17):
                (msvc / str(i)).mkdir()
            with self.assertRaises(ValueError):
                cache.linker_relevant_identity(vs, kit)
            for i in range(1, 17):
                (msvc / str(i)).rmdir()
            redir = msvc / "0/include/vcruntime.h"
            redir.parent.mkdir(parents=True)
            actual = root / "actual.h"
            actual.write_bytes(b"content")
            try:
                redir.symlink_to(actual)
            except (OSError, NotImplementedError):
                self.skipTest("runner cannot make a symlink")
            with self.assertRaises(ValueError):
                cache.linker_relevant_identity(vs, kit)

    def test_redirected_msvc_version_directory_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vs, kit = root / "VS", root / "Kit"
            versions = vs / "VC/Tools/MSVC"
            versions.mkdir(parents=True)
            (kit / "Include/10.0.26100.0").mkdir(parents=True)
            target = root / "outside" / "14.44.35207"
            (target / "include").mkdir(parents=True)
            (target / "include/vcruntime.h").write_bytes(b"outside")
            redirect = versions / "14.44.35207"
            try:
                redirect.symlink_to(target, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("runner cannot create directory symlink")
            with self.assertRaisesRegex(ValueError, "redirected SDK or toolchain"):
                cache.linker_relevant_identity(vs, kit)
            self.assertEqual((target / "include/vcruntime.h").read_bytes(), b"outside")

    def test_redirected_sdk_parent_directory_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vs, kit = root / "VS", root / "Kit"
            (vs / "VC/Tools/MSVC/14.44.35207").mkdir(parents=True)
            (kit / "Include").mkdir(parents=True)
            outside = root / "redirect-target"
            (outside / "ucrt").mkdir(parents=True)
            (outside / "ucrt/stdlib.h").write_bytes(b"SDK")
            link = kit / "Include/10.0.26100.0"
            try:
                link.symlink_to(outside, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("runner cannot create directory symlink")
            with self.assertRaisesRegex(ValueError, "redirected SDK or toolchain"):
                cache.linker_relevant_identity(vs, kit)

    def test_source_tree_rejects_untracked_directory_redirect(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            source.mkdir()
            (source / "CMakeLists.txt").write_text("pinned source", encoding="utf-8")
            baseline = cache.tree_digest(source)
            outside = root / "user-data"
            outside.mkdir()
            (outside / "secret.txt").write_text("never hash or mutate", encoding="utf-8")
            redirect = source / "untracked"
            try:
                redirect.symlink_to(outside, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("runner cannot create directory symlinks")
            with self.assertRaisesRegex(ValueError, "redirected source/install"):
                cache.tree_digest(source)
            redirect.unlink()
            self.assertEqual(cache.tree_digest(source), baseline)
            self.assertEqual((outside / "secret.txt").read_text("utf-8"), "never hash or mutate")

    def test_install_manifest_rejects_untracked_directory_redirect(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stage = root / "stage"
            (stage / "include").mkdir(parents=True)
            (stage / "include" / "SDL.h").write_bytes(b"static owned")
            baseline = cache.manifest_for_stage(stage)
            outside = root / "unrelated"
            outside.mkdir()
            (outside / "private.txt").write_text("private", encoding="utf-8")
            try:
                (stage / "extra").symlink_to(outside, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("runner cannot create directory symlinks")
            with self.assertRaisesRegex(ValueError, "redirected source/install"):
                cache.manifest_for_stage(stage)
            self.assertEqual((outside / "private.txt").read_text("utf-8"), "private")
            (stage / "extra").unlink()
            self.assertEqual(cache.manifest_for_stage(stage), baseline)

    def test_install_manifest_rejects_redirected_tree_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            real = root / "genuine"
            real.mkdir()
            (real / "SDL3-static.lib").write_bytes(b"owned")
            try:
                (root / "stage").symlink_to(real, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("runner cannot create directory symlinks")
            with self.assertRaisesRegex(ValueError, "redirected source/install"):
                cache.manifest_for_stage(root / "stage")

    def test_hosted_cache_is_restored_and_saved_before_expensive_build(self):
        workflow = (MODULE.parents[2] / ".github/workflows/windows-native-smoke.yml").read_text()
        restored = workflow.index("- name: Restore hosted Windows verified SDL3 candidate")
        validated = workflow.index("- name: Prepare source-pinned static SDL3 cache")
        saved = workflow.index("- name: Save hosted Windows verified SDL3 candidate")
        built = workflow.index("- name: Configure and build (Visual Studio")
        self.assertLess(restored, validated)
        self.assertLess(validated, saved)
        self.assertLess(saved, built)
        self.assertIn("uses: actions/cache/restore@0400d5f644dc74513175e3cd8d07132dd4860809", workflow)
        self.assertIn("uses: actions/cache/save@0400d5f644dc74513175e3cd8d07132dd4860809", workflow)
        self.assertEqual(workflow.count("id: hosted-sdl3-cache"), 1)
        self.assertEqual(workflow.count(
            "if: ${{ !inputs.run_on_hp && inputs.test_hp_compiler_profile }}"), 1)
        self.assertIn("steps.hosted-sdl3-prepared.outputs.cache-state == 'miss'", workflow)
        self.assertIn("steps.hosted-sdl3-prepared.outputs.cache-state == 'recovered'", workflow)
        self.assertNotIn("steps.hosted-sdl3-cache.outputs.cache-hit != 'true'", workflow)
        # Reuse cannot turn untrusted PR code into a self-hosted HP job.
        host_only = "if: ${{ !inputs.run_on_hp && inputs.test_hp_compiler_profile"
        for name in ("Restore hosted Windows verified SDL3 candidate",
                     "Save hosted Windows verified SDL3 candidate"):
            block = workflow.split("- name: " + name, 1)[1].split("- name:", 1)[0]
            self.assertIn(host_only, block)
            self.assertIn("${{ runner.temp }}/ur-sdl3-canary-cache", block)
            self.assertIn("hashFiles('third_party/archives/SDL3-3.4.10.tar.gz', "
                          "'tools/devnode_benchmark/prepare_sdl3_cache.py')", block)
            self.assertIn("${{ github.run_id }}", block)
            self.assertNotIn("RUNNER_WORKSPACE", block)
        # The original full source/SDK fingerprint and byte manifest checks
        # still gate every reuse before the generated game's CMake config.
        self.assertIn("python tools/devnode_benchmark/prepare_sdl3_cache.py", workflow)
        self.assertIn("--required", workflow)
        self.assertIn("if package_dir is None:", MODULE.read_text())

    def test_main_scoped_seed_keeps_canonical_source_build_and_never_touches_hp(self):
        workflow = (MODULE.parents[2] / ".github/workflows/windows-native-smoke.yml").read_text()
        restore = workflow.index("- name: Restore hosted main-branch SDL3 seed")
        prepare = workflow.index("- name: Validate isolated hosted main SDL3 seed")
        save = workflow.index("- name: Save verified hosted main-branch SDL3 seed")
        hosted = workflow.index("- name: Restore hosted Windows verified SDL3 candidate")
        build = workflow.index("- name: Configure and build (Visual Studio")
        self.assertLess(restore, prepare)
        self.assertLess(prepare, save)
        self.assertLess(save, hosted)
        self.assertLess(hosted, build)
        for name in ("Restore hosted main-branch SDL3 seed",
                     "Validate isolated hosted main SDL3 seed",
                     "Save verified hosted main-branch SDL3 seed"):
            block = workflow.split("- name: " + name, 1)[1].split("- name:", 1)[0]
            self.assertIn("continue-on-error: true", block)
            self.assertIn("github.event_name == 'push'", block)
            self.assertIn("github.ref == 'refs/heads/main'", block)
            self.assertIn("!inputs.run_on_hp", block)
            self.assertIn("!inputs.test_hp_compiler_profile", block)
        seeder = workflow.split("- name: Validate isolated hosted main SDL3 seed", 1)[1]
        seeder = seeder.split("- name: Save verified hosted main-branch", 1)[0]
        self.assertIn("--github-env \"$RUNNER_TEMP/hosted-main-sdl3-private.env\"", seeder)
        self.assertNotIn('--github-env "$GITHUB_ENV"', seeder)
        self.assertIn('--github-output "$GITHUB_OUTPUT"', seeder)
        self.assertIn("continue-on-error: true", seeder)
        self.assertIn("--required", seeder)
        self.assertIn("SDL3_ARGS=(-DSNESRECOMP_SDL3_FETCH=ON)", workflow)
        self.assertIn("if [[ -n \"${UR_SDL3_PREBUILT_DIR:-}\" ]]; then", workflow)
        self.assertIn("steps.main-sdl3-prepared.outcome == 'success'", workflow)
        self.assertIn("steps.main-sdl3-prepared.outputs.cache-state == 'miss'", workflow)
        self.assertIn("steps.main-sdl3-prepared.outputs.cache-state == 'recovered'", workflow)
        self.assertIn("steps.hosted-sdl3-prepared.outputs.cache-state == 'miss'", workflow)
        self.assertIn("steps.hosted-sdl3-prepared.outputs.cache-state == 'recovered'", workflow)
        self.assertNotIn("steps.hosted-sdl3-cache.outputs.cache-hit != 'true'", workflow)

    def test_cache_state_output_is_optional_and_success_bound(self):
        helper = MODULE.read_text()
        self.assertIn('parser.add_argument("--github-output", type=Path', helper)
        self.assertIn('if args.github_output is not None:', helper)
        self.assertIn('f.write("cache-state=" + state + "\\n")', helper)
        self.assertLess(helper.index("package_dir = build_stage("),
                        helper.index('if args.github_output is not None:'))
        self.assertLess(helper.index("package_dir = validate_stage("),
                        helper.index('if args.github_output is not None:'))

    def test_real_helper_emits_output_only_after_verified_install(self):
        # Exercise the actual argument/output path while isolating the
        # compiler-specific fingerprint from this Linux unit environment.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env_file, output = root / "private-env", root / "cache-output"
            args = ["prepare_sdl3_cache.py", "--source", str(root / "source"),
                    "--archive", str(root / "source.tar.gz"),
                    "--cache-root", str(root / "cache"),
                    "--github-env", str(env_file),
                    "--github-output", str(output), "--required"]
            context = {"GITHUB_REPOSITORY": "gamesbyian/UR-Recomp"}
            with patch.object(sys, "argv", args), patch.dict(os.environ, context):
                with patch.object(cache, "visual_studio_root", return_value=root), \
                     patch.object(cache, "fingerprint", return_value={"known": True}), \
                     patch.object(cache, "cache_key", return_value="a" * 24), \
                     patch.object(cache, "validate_stage", return_value=root / "verified"), \
                     patch.object(cache, "build_stage") as build:
                    self.assertEqual(cache.main(), 0)
                    build.assert_not_called()
            self.assertEqual(output.read_text(), "cache-state=hit\n")
            self.assertIn("UR_SDL3_PREBUILT_DIR=", env_file.read_text())
            env_file.unlink()
            output.unlink()
            with patch.object(sys, "argv", args), patch.dict(os.environ, context):
                with patch.object(cache, "visual_studio_root", return_value=root), \
                     patch.object(cache, "fingerprint", return_value={"known": True}), \
                     patch.object(cache, "cache_key", return_value="a" * 24), \
                     patch.object(cache, "validate_stage", return_value=None), \
                     patch.object(cache, "build_stage", side_effect=ValueError("incomplete")):
                    self.assertEqual(cache.main(), 1)
            self.assertFalse(output.exists())
            self.assertFalse(env_file.exists())

    def test_scheduled_hp_cache_allows_only_trusted_main_and_owner_runner(self):
        # The existing owner-only 2P cron calls the SAME SDL3 helper with
        # --hp; rejecting schedule before the actual Windows build would
        # strand every unattended science run. PR/fork/foreign runners still
        # cannot invoke this trusted-machine path.
        workflow = (MODULE.parents[2] /
                    ".github/workflows/owner-hp-seeded-2p-research.yml").read_text()
        self.assertIn("github.event_name == 'schedule'", workflow)
        self.assertIn("run_on_hp: true", workflow)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args = ["prepare_sdl3_cache.py", "--source", str(root / "source"),
                    "--archive", str(root / "source.tar.gz"),
                    "--cache-root", str(root / "cache"), "--github-env",
                    str(root / "private.env"), "--hp"]
            trusted = {"GITHUB_REPOSITORY": "gamesbyian/UR-Recomp",
                       "GITHUB_REF": "refs/heads/main",
                       "GITHUB_EVENT_NAME": "schedule",
                       "RUNNER_NAME": "hpmini-ur-recomp"}
            with patch.object(sys, "argv", args), patch.dict(os.environ, trusted):
                with patch.object(cache, "visual_studio_root", return_value=root), \
                     patch.object(cache, "fingerprint", return_value={"known": True}), \
                     patch.object(cache, "cache_key", return_value="a" * 24), \
                     patch.object(cache, "validate_stage", return_value=root / "verified"), \
                     patch.object(cache, "build_stage") as build:
                    self.assertEqual(cache.main(), 0)
                    build.assert_not_called()
            self.assertIn("UR_SDL3_PREBUILT_DIR=", (root / "private.env").read_text())
            for key, value in (("GITHUB_EVENT_NAME", "pull_request"),
                               ("GITHUB_REF", "refs/heads/foreign"),
                               ("RUNNER_NAME", "github-hosted"),
                               ("GITHUB_REPOSITORY", "foreign/repo")):
                with self.subTest(field=key):
                    denied = dict(trusted, **{key: value})
                    with patch.object(sys, "argv", args), \
                         patch.dict(os.environ, denied):
                        with self.assertRaises(SystemExit):
                            cache.main()

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
