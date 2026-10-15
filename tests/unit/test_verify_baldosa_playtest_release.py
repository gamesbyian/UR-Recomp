"""ROM-free owner preview security and provenance contracts, no native build."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import verify_baldosa_playtest_release as release


SHA = "a" * 40


def write_fixture(root: Path) -> tuple[Path, Path, Path, dict]:
    exported = root / "tested"
    candidate = root / "candidate"
    bindings = root / "binding"
    for path in (exported, candidate, bindings):
        path.mkdir()
    values = {
        release.EXE: b"source-bound-real-exe-unit-only",
        release.FIXTURE: b"source-bound-fixture-unit-only",
        release.ZIP: b"fake-zip-used-only-in-synthetic-python-test",
    }
    for name, blob in values.items():
        (exported / name).write_bytes(blob)
    sums = {name: hashlib.sha256(value).hexdigest()
            for name, value in values.items()}
    (exported / "SHA256SUMS").write_text(
        "".join(f"{digest}  {name}\n" for name, digest in sums.items()),
        encoding="ascii",
    )
    (exported / "source-commit.txt").write_text(SHA + "\n", encoding="ascii")
    (candidate / release.ZIP).write_bytes(values[release.ZIP])
    (candidate / release.SIDECAR).write_text(
        sums[release.ZIP] + "  " + release.ZIP + "\n", encoding="ascii",
    )
    expected = {
        "source_revision": SHA,
        "zip_sha256": sums[release.ZIP],
        "journey_and_packaged_executable_sha256": sums[release.EXE],
        "manifest_immutable_files": {release.EXE: sums[release.EXE]},
    }
    (bindings / "candidate-binding.json").write_text(
        json.dumps(expected), encoding="utf-8",
    )
    return exported, candidate, bindings, expected


class ManualPlaytestSourceBinding(unittest.TestCase):
    def fake_audit(self, *args, **kwargs):
        return {
            "rom_bundled": False,
            "profile_data_bundled": False,
            "all_immutable_members_verified": True,
        }

    def prepare(self, root: Path, *, mutate=None, audit=None):
        exported, candidate, bindings, receipt = write_fixture(root)
        if mutate:
            mutate(exported, candidate, bindings, receipt)
        with mock.patch.object(release.binding, "bind", return_value=receipt), \
             mock.patch.object(release.audit, "inspect",
                               side_effect=audit or self.fake_audit):
            return release.prepare(
                exported=exported, candidate=candidate,
                binding_root=bindings, expected_sha=SHA,
                out=root / "playtest-output",
            )

    def test_exact_source_bound_romfree_preview_is_explicitly_uncertified(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            proof = self.prepare(root)
            self.assertEqual(proof["source_commit"], SHA)
            self.assertEqual(proof["github_release_tag"], "playtest-" + SHA[:12])
            self.assertEqual(proof["release_gate_credit"], 0)
            self.assertTrue(proof["not_a_certified_beta"])
            self.assertFalse(proof["physical_gamepad_or_audio_verified"])
            self.assertEqual(
                {p.name for p in (root / "playtest-output").iterdir()},
                {release.ZIP, release.SIDECAR,
                 "PLAYTEST-PROVENANCE.json", "RELEASE-NOTES.md"},
            )
            notes = (root / "playtest-output/RELEASE-NOTES.md").read_text()
            self.assertIn("no copyrighted game ROM", notes)
            self.assertIn("provisional technical playtest", notes)
            self.assertIn(SHA, notes)
            data = json.loads(
                (root / "playtest-output/PLAYTEST-PROVENANCE.json").read_text()
            )
            self.assertEqual(data, proof)

    def test_real_windows_binary_sha256sum_sidecar_is_canonical(self):
        # Real source Windows bridge artifact 11948142744 used GNU '*name'.
        # Both strict encodings must bind to the identical ZIP and output.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def windows_binary(a, c, b, r):
                digest = release.sha256(c / release.ZIP)
                (c / release.SIDECAR).write_bytes(
                    (digest + " *" + release.ZIP + "\n").encode("ascii"))
            proof = self.prepare(root, mutate=windows_binary)
            self.assertEqual(proof["release_gate_credit"], 0)
            self.assertTrue(proof["not_a_certified_beta"])
            self.assertEqual(
                (root / "playtest-output" / release.SIDECAR).read_bytes(),
                (root / "candidate" / release.SIDECAR).read_bytes())

    def test_only_two_exact_single_line_sidecar_encodings_are_accepted(self):
        digest = hashlib.sha256(
            b"fake-zip-used-only-in-synthetic-python-test").hexdigest()
        bad_lines = (
            "0" * 64 + " *" + release.ZIP + "\n",
            digest + " *wrong-name.zip\n",
            digest + " **" + release.ZIP + "\n",
            digest + "\t*" + release.ZIP + "\n",
            digest + " *" + release.ZIP + "\n\n",
            digest + " *" + release.ZIP + "\r\n",
            digest + "  " + release.ZIP + ".extra\n",
        )
        for line in bad_lines:
            with self.subTest(sidecar=repr(line)), \
                 tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                def corrupted(a, c, b, r):
                    (c / release.SIDECAR).write_bytes(line.encode("ascii"))
                with self.assertRaisesRegex(ValueError, "noncanonical"):
                    self.prepare(root, mutate=corrupted)
                self.assertFalse((root / "playtest-output").exists())

    def test_wrong_revision_zip_sidecar_binding_and_extra_files_fail_closed(self):
        def wrong_source(a, c, b, r):
            (a / "source-commit.txt").write_text("b" * 40 + "\n")
        def wrong_zip(a, c, b, r):
            (c / release.ZIP).write_bytes(b"modified")
        def wrong_sidecar(a, c, b, r):
            (c / release.SIDECAR).write_text("0" * 64 + "  " + release.ZIP + "\n")
        def wrong_binding(a, c, b, r):
            (b / "candidate-binding.json").write_text("{}")
        def extra_member(a, c, b, r):
            (a / "saves.srm").write_bytes(b"PRIVATE")
        def missing_member(a, c, b, r):
            (a / release.FIXTURE).unlink()
        def symlink(a, c, b, r):
            (c / release.ZIP).unlink()
            (c / release.ZIP).symlink_to(a / release.ZIP)
        for mutate in (wrong_source, wrong_zip, wrong_sidecar,
                       wrong_binding, extra_member, missing_member, symlink):
            with self.subTest(case=mutate.__name__), \
                 tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                with self.assertRaises(ValueError):
                    self.prepare(root, mutate=mutate)
                self.assertFalse((root / "playtest-output").exists())

    def test_audited_rom_presence_and_invalid_checksum_population_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "unsafe"):
                self.prepare(Path(directory), audit=lambda *args, **kwargs: {
                    "rom_bundled": True,
                    "profile_data_bundled": False,
                    "all_immutable_members_verified": True,
                })
        with self.assertRaisesRegex(ValueError, "population"):
            release.parse_sums("0" * 64 + "  " + release.ZIP + "\n")
        with self.assertRaisesRegex(ValueError, "repeated"):
            line = "0" * 64 + "  " + release.ZIP + "\n"
            release.parse_sums(line + line)

    def test_existing_destination_must_not_be_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "playtest-output").mkdir()
            with self.assertRaisesRegex(ValueError, "already exist"):
                self.prepare(root)

    def test_manual_workflow_has_no_automatic_builds_and_requires_explicit_publish(self):
        text = (ROOT / ".github/workflows/manual-romfree-windows-playtest.yml"
                ).read_text(encoding="utf-8")
        self.assertIn("  workflow_dispatch:", text)
        self.assertNotIn("  pull_request:", text)
        self.assertNotIn("  push:", text)
        self.assertNotIn("  schedule:", text)
        self.assertIn("export_campaign_inputs: true", text)
        self.assertIn("uses: ./.github/workflows/baldosa-windows-native-bridge.yml", text)
        self.assertIn("default: verify_only", text)
        self.assertIn("inputs.mode == 'publish_provisional_preview'", text)
        self.assertIn("contents: write", text)
        self.assertIn("--prerelease --latest=false", text)


if __name__ == "__main__":
    unittest.main()
