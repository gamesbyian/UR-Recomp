#!/usr/bin/env python3
"""ROM-free safety tests for exporting CI-only *already-authenticated* bytes.

Fake fixture bytes below are never native results or acceptance witnesses.
Actual match creation/publication and readback belong to the Win32 test.
"""
from pathlib import Path
import hashlib
import json
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from baldosa_native_ci_paired_evidence_export import (
    ALLOWED_STATE_PATHS, EVIDENCE_FOLDER, OPTIONAL_BOOTSTRAP,
    _read_owned_file, export_ci_created_pair,
)


def make_ci_root(out: Path) -> Path:
    user = out / "New Player-Created Named Racers"
    user.mkdir()
    for name in ALLOWED_STATE_PATHS:
        target = user / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(bytes(8192) if name.endswith(".srm")
                           else ("CI " + name + "\n").encode())
    archive = user / "multiplayer-runs"
    archive.mkdir()
    (archive / "synthetic.urrun").write_bytes(b"unit-placeholder-run")
    (archive / "synthetic.urrun.urmatch").write_bytes(b"unit-placeholder-pair")
    return user


class DisposableNativePairEvidenceExportTest(unittest.TestCase):
    def test_allowlisted_exact_state_and_pair_not_rom_or_arbitrary_user_files(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            user = make_ci_root(out)
            (user / "Uniracers_USA.sfc").write_bytes(b"must-never-export")
            (user / "private_note.txt").write_text("must-never-export")
            (user / OPTIONAL_BOOTSTRAP).write_bytes(bytes([0x72]) * 8192)
            data = export_ci_created_pair(user, out)
            self.assertEqual(data["release_gate_credit"], 0)
            self.assertFalse(data["includes_rom"])
            self.assertFalse(data["includes_executable"])
            self.assertEqual(set(data["members"]), {
                *ALLOWED_STATE_PATHS, OPTIONAL_BOOTSTRAP,
                "multiplayer-runs/synthetic.urrun",
                "multiplayer-runs/synthetic.urrun.urmatch",
            })
            manifest = out / EVIDENCE_FOLDER / "manifest.json"
            self.assertEqual(json.loads(manifest.read_text()), data)
            for relative, details in data["members"].items():
                source = user / relative
                exported = out / EVIDENCE_FOLDER / relative
                self.assertEqual(source.read_bytes(), exported.read_bytes())
                self.assertEqual(details["bytes"], len(source.read_bytes()))
                self.assertEqual(details["sha256"],
                                 hashlib.sha256(source.read_bytes()).hexdigest())
            self.assertFalse((out / EVIDENCE_FOLDER / "Uniracers_USA.sfc").exists())
            self.assertFalse((out / EVIDENCE_FOLDER / "private_note.txt").exists())
            with self.assertRaisesRegex(ValueError, "stale or replaced"):
                export_ci_created_pair(user, out)

    def test_reject_unexpected_pair_duplication_partial_and_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            user = make_ci_root(out)
            archive = user / "multiplayer-runs"
            extra = archive / "another.urrun"
            extra.write_bytes(b"fake")
            with self.assertRaisesRegex(ValueError, "Exactly two"):
                export_ci_created_pair(user, out)
            extra.unlink()
            pair = archive / "synthetic.urrun.urmatch"
            pair.rename(archive / "mismatch.urmatch")
            with self.assertRaisesRegex(ValueError, "name mismatch"):
                export_ci_created_pair(user, out)
            (archive / "mismatch.urmatch").rename(pair)
            pair.unlink()
            pair.symlink_to(user / "private-note")
            with self.assertRaisesRegex(ValueError, "Exactly two"):
                export_ci_created_pair(user, out)

    def test_reject_bad_bytes_missing_profiles_and_redirected_ancestors(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            user = make_ci_root(out)
            srm = user / "saves/profile-martin/save.srm"
            srm.write_bytes(b"short")
            with self.assertRaisesRegex(ValueError, "8192"):
                export_ci_created_pair(user, out)
            srm.write_bytes(bytes(8192))
            srm.unlink()
            with self.assertRaisesRegex(ValueError, "Missing ordinary"):
                export_ci_created_pair(user, out)
            srm.write_bytes(bytes(8192))
            profile = user / "saves/profile-martin"
            mirror = user / "redirected"
            profile.rename(mirror)
            profile.symlink_to(mirror, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlink"):
                export_ci_created_pair(user, out)

    def test_reject_path_escape_and_foreign_user_root(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            user = make_ci_root(out)
            for bad in ("../outside", "/tmp/foo", "C:\\users\\private",
                        "saves/../bad"):
                with self.subTest(bad=bad), self.assertRaises(ValueError):
                    _read_owned_file(user, bad)
            user.rename(out / "Real Personal Profile")
            with self.assertRaisesRegex(ValueError, "disposable generated"):
                export_ci_created_pair(out / "Real Personal Profile", out)


if __name__ == "__main__":
    unittest.main()
