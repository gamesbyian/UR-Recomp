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
    ALLOWED_STATE_PATHS, EVIDENCE_FOLDER, PRE_RECORDS_FOLDER,
    P2_RECOVERY_FOLDER, P2_RECOVERY_STAGES, P2_RECOVERY_MUTEX,
    OPTIONAL_BOOTSTRAP, _read_owned_file,
    export_ci_created_pair, export_ci_pre_records_pair,
    export_ci_native_p2_recovery_stage,
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

    def test_pre_records_export_retains_only_pair_and_real_stage_bytes(self):
        # These placeholder bytes test transport only, not native game results.
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            user = make_ci_root(out)
            (user / "private_note.txt").write_bytes(b"must-never-export")
            before = export_ci_pre_records_pair(user, out)
            self.assertEqual(before["stage"],
                             "after-real-play-before-first-records-viewer")
            self.assertEqual(set(before["members"]), {
                "multiplayer-runs/synthetic.urrun",
                "multiplayer-runs/synthetic.urrun.urmatch",
            })
            self.assertEqual(before["release_gate_credit"], 0)
            self.assertFalse(before["includes_rom"])
            self.assertEqual(
                json.loads((out / PRE_RECORDS_FOLDER / "manifest.json").read_text()),
                before)
            snapshot = out / PRE_RECORDS_FOLDER / "multiplayer-runs/synthetic.urrun"
            first_bytes = snapshot.read_bytes()
            (user / "multiplayer-runs/synthetic.urrun").write_bytes(b"changed-after-view")
            self.assertEqual(snapshot.read_bytes(), first_bytes)
            after = export_ci_created_pair(user, out)
            self.assertNotEqual(
                before["members"]["multiplayer-runs/synthetic.urrun"]["sha256"],
                after["members"]["multiplayer-runs/synthetic.urrun"]["sha256"])
            self.assertFalse((out / PRE_RECORDS_FOLDER / "private_note.txt").exists())
            with self.assertRaisesRegex(ValueError, "stale or replaced"):
                export_ci_pre_records_pair(user, out)

    def test_pre_records_rejects_duplicate_missing_and_redirected_pair(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            user = make_ci_root(out)
            archive = user / "multiplayer-runs"
            duplicate = archive / "another.urrun"
            duplicate.write_bytes(b"duplicate")
            with self.assertRaisesRegex(ValueError, "exactly two"):
                export_ci_pre_records_pair(user, out)
            duplicate.unlink()
            pair = archive / "synthetic.urrun.urmatch"
            pair.unlink()
            pair.symlink_to(out / "outside")
            with self.assertRaisesRegex(ValueError, "exactly two"):
                export_ci_pre_records_pair(user, out)
            pair.unlink()
            with self.assertRaisesRegex(ValueError, "exactly two"):
                export_ci_pre_records_pair(user, out)


    def test_p2_recovery_real_stage_shape_with_only_source_selected_bytes(self):
        # Synthetic byte fixtures test export safety, never actual source play.
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            user = out / "Interrupted Native P2 Catalog Test Only"
            user.mkdir()
            for name in ALLOWED_STATE_PATHS[:4]:
                p = user / name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(bytes([3]) * 8192 if name.endswith(".srm")
                              else ("single " + name).encode())
            (user / "Uniracers_USA.sfc").write_bytes(b"forbidden-ROM")
            (user / "foreign-user-note.txt").write_text("private")
            early = export_ci_native_p2_recovery_stage(
                user, out, "after-p1-created")
            self.assertEqual(early["schema"],
                             "baldosa-native-p2-catalog-recovery-stage-v1")
            self.assertEqual(set(early["members"]), set(ALLOWED_STATE_PATHS[:4]))
            self.assertEqual(early["source_profiles"], ["mike"])
            self.assertEqual(early["release_gate_credit"], 0)
            self.assertFalse(early["includes_rom"])
            self.assertFalse(early["includes_executable"])
            source = out / P2_RECOVERY_FOLDER
            self.assertEqual(
                json.loads((source / "after-p1-created/manifest.json").read_text()),
                early)
            for name in ALLOWED_STATE_PATHS[4:]:
                p = user / name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(bytes([8]) * 8192 if name.endswith(".srm")
                              else ("second " + name).encode())
            (user / P2_RECOVERY_MUTEX).write_bytes(b"")
            catalogue = user / "profiles-v1.txt"
            catalogue.write_bytes(b"two independently created P1 and P2")
            two = export_ci_native_p2_recovery_stage(
                user, out, "after-p2-created")
            catalogue.write_bytes(b"single P1 only")
            cut = export_ci_native_p2_recovery_stage(
                user, out, "catalog-row-lost")
            catalogue.write_bytes(b"two independently created P1 and P2")
            resumed = export_ci_native_p2_recovery_stage(
                user, out, "after-p2-recovered")
            after_go = export_ci_native_p2_recovery_stage(
                user, out, "after-source-go")
            self.assertEqual({p.name for p in source.iterdir()},
                             set(P2_RECOVERY_STAGES))
            self.assertEqual(len(list(source.iterdir())), 5)
            self.assertEqual(set(two["members"]),
                             {*ALLOWED_STATE_PATHS, P2_RECOVERY_MUTEX})
            self.assertEqual(two["source_profiles"], ["mike", "martin"])
            self.assertEqual(two["members"][P2_RECOVERY_MUTEX]["bytes"], 0)
            self.assertEqual(
                two["members"]["profiles-v1.txt"]["sha256"],
                resumed["members"]["profiles-v1.txt"]["sha256"])
            self.assertEqual(
                two["members"]["profiles-v1.txt"]["sha256"],
                after_go["members"]["profiles-v1.txt"]["sha256"])
            self.assertNotEqual(
                two["members"]["profiles-v1.txt"]["sha256"],
                cut["members"]["profiles-v1.txt"]["sha256"])
            for name in (
                "saves/profile-martin/host-profile.txt",
                "saves/profile-martin/save.srm",
                P2_RECOVERY_MUTEX,
            ):
                digest = two["members"][name]
                self.assertEqual(digest, cut["members"][name])
                self.assertEqual(digest, resumed["members"][name])
                self.assertEqual(digest, after_go["members"][name])
            self.assertFalse((source / "Uniracers_USA.sfc").exists())
            self.assertFalse((source / "foreign-user-note.txt").exists())
            with self.assertRaisesRegex(ValueError, "overwrite"):
                export_ci_native_p2_recovery_stage(
                    user, out, "after-p2-created")

    def test_p2_recovery_source_rejects_foreign_invalid_and_redirected_files(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            user = out / "Interrupted Native P2 Catalog Test Only"
            user.mkdir()
            for name in ALLOWED_STATE_PATHS:
                p = user / name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(bytes(8192) if name.endswith(".srm")
                              else b"typed source")
            mutex = user / P2_RECOVERY_MUTEX
            mutex.write_bytes(b"")
            with self.assertRaisesRegex(ValueError, "Unrecognized"):
                export_ci_native_p2_recovery_stage(user, out, "../escape")
            with self.assertRaisesRegex(ValueError, "disposable"):
                export_ci_native_p2_recovery_stage(
                    out / "unknown-real-user", out, "after-p2-created")
            mutex.write_bytes(b"unexpected data")
            with self.assertRaisesRegex(ValueError, "mutex"):
                export_ci_native_p2_recovery_stage(
                    user, out, "after-p2-created")
            mutex.write_bytes(b"")
            original = user / "saves/profile-martin/save.srm"
            original.write_bytes(b"short")
            with self.assertRaisesRegex(ValueError, "8192"):
                export_ci_native_p2_recovery_stage(
                    user, out, "after-p2-created")
            original.write_bytes(bytes(8192))
            mutex.unlink()
            mutex.symlink_to(user / "host-state-v1.txt")
            with self.assertRaisesRegex(ValueError, "mutex"):
                export_ci_native_p2_recovery_stage(
                    user, out, "after-p2-created")
            mutex.unlink()
            mutex.write_bytes(b"")
            profile = user / "saves/profile-martin"
            moved = user / "saved-original"
            profile.rename(moved)
            profile.symlink_to(moved, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlink"):
                export_ci_native_p2_recovery_stage(
                    user, out, "after-p2-created")

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
