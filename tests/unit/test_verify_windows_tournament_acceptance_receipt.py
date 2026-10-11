"""Read-only Windows tournament receipt checks without game/ROM data."""
import hashlib
from pathlib import Path
import tempfile
import unittest

from tools.verify_windows_tournament_acceptance_receipt import verify, fields, CANDIDATE_KEYS, ARTIFACT_KEYS


def digest(data):
    return hashlib.sha256(data).hexdigest()


class WindowsTournamentReceiptVerifierTests(unittest.TestCase):
    def make(self, root):
        work = root / "tournament work"
        runs = work / "multiplayer-runs"
        fixtures = work / "user data" / "local-tournaments" / ("1" * 32) / "fixtures"
        runs.mkdir(parents=True)
        fixtures.mkdir(parents=True)
        p = runs / "run-123.urrun"
        q = runs / "run-123.urrun.urmatch"
        f = fixtures / "fixture-0.urfixture"
        p.write_bytes(b"fake canonical primary")
        q.write_bytes(b"fake canonical sidecar")
        f.write_bytes(b"fake fixture")
        candidate = root / "windows-tournament-candidate.txt"
        candidate.write_text(
            "schema=ur-windows-qa-candidate/1\n"
            "smoke_run_id=12345\n"
            "source_commit=" + "a" * 40 + "\n"
            "inner_zip_sha256=" + "b" * 64 + "\n"
            "qa_harness_commit=" + "c" * 40 + "\n",
            encoding="ascii",
        )
        report = work / "tournament-artifacts.log"
        report.write_text(
            "schema=ur-windows-tournament-artifacts/1\n"
            "source_commit=" + "a" * 40 + "\n"
            "inner_zip_sha256=" + "b" * 64 + "\n"
            "run_file=run-123.urrun\nrun_sha256=" + digest(p.read_bytes()) + "\n"
            "match_file=run-123.urrun.urmatch\nmatch_sha256=" + digest(q.read_bytes()) + "\n"
            "receipt_file=fixture-0.urfixture\nreceipt_sha256=" + digest(f.read_bytes()) + "\n"
            "fresh_process_reopen=passed\n",
            encoding="ascii",
        )
        return work, candidate, p, q, f, report

    def test_real_files_and_exact_pins_are_cross_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            work, candidate, p, q, f, report = self.make(Path(tmp))
            r = verify(work, candidate, "a" * 40, "b" * 64)
            self.assertEqual(r["smoke_run_id"], "12345")
            self.assertIn("not physical", r["result"])

    def test_wrong_nominated_pins_or_mutated_files_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            work, candidate, p, q, f, report = self.make(Path(tmp))
            for bad_source, bad_zip in (("f" * 40, "b" * 64),
                                        ("a" * 40, "f" * 64),
                                        ("main", "b" * 64)):
                with self.subTest(source=bad_source):
                    with self.assertRaises(ValueError):
                        verify(work, candidate, bad_source, bad_zip)
            for target in (p, q, f):
                before = target.read_bytes()
                target.write_bytes(before + b"mutated")
                with self.subTest(target=target.name):
                    with self.assertRaisesRegex(ValueError, "digest differs"):
                        verify(work, candidate, "a" * 40, "b" * 64)
                target.write_bytes(before)

    def test_spoofed_fields_and_reopen_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            work, candidate, p, q, f, report = self.make(Path(tmp))
            before = report.read_text()
            for after in (before.replace("fresh_process_reopen=passed", "fresh_process_reopen=failed"),
                          before.replace("match_file=run-123.urrun.urmatch", "match_file=other.urmatch"),
                          before.replace("source_commit=" + "a" * 40, "source_commit=" + "f" * 40),
                          before.replace("run_file=run-123.urrun", "run_file=../outside.urrun"),
                          before + "extra=value\n",
                          before.replace("run_sha256=", "run_sha256=0" * 2, 1)):
                report.write_text(after)
                with self.assertRaises(ValueError):
                    verify(work, candidate, "a" * 40, "b" * 64)
            report.write_text(before)

    def test_duplicate_field_noncanonical_crlf_or_symlink_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            work, candidate, p, q, f, report = self.make(root)
            backup = report.read_bytes()
            report.write_bytes(backup.replace(b"\n", b"\r\n"))
            with self.assertRaisesRegex(ValueError, "canonical LF"):
                fields(report, ARTIFACT_KEYS)
            report.write_bytes(backup)
            linked = root / "linked-receipt.txt"
            try:
                linked.symlink_to(report)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable")
            with self.assertRaisesRegex(ValueError, "linked"):
                fields(linked, ARTIFACT_KEYS)
            self.assertEqual(fields(candidate, CANDIDATE_KEYS)["smoke_run_id"], "12345")

    def test_missing_or_duplicate_sidecar_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            work, candidate, p, q, f, report = self.make(Path(tmp))
            q.unlink()
            with self.assertRaisesRegex(ValueError, "exactly one"):
                verify(work, candidate, "a" * 40, "b" * 64)
            q.write_bytes(b"fake canonical sidecar")
            (q.parent / "other.urrun.urmatch").write_bytes(b"extra")
            with self.assertRaisesRegex(ValueError, "exactly one"):
                verify(work, candidate, "a" * 40, "b" * 64)


if __name__ == "__main__":
    unittest.main()
