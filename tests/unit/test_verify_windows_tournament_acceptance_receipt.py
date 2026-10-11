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
        (work / "tournament.log").write_text(
            "\n".join((
                "UR_LOCAL_MULTIPLAYER SESSION_READY",
                "UR_LOCAL_TOURNAMENT PANEL_OPENED page=setup",
                "UR_LOCAL_TOURNAMENT CREATED entrants=2 fixtures=1 courses=2 legs=1",
                "UR_LOCAL_TOURNAMENT ARMED fixture=0 course=course:01",
                "UR_LOCAL_TOURNAMENT CAPTURE_TAGGED",
                "UR_MULTIPLAYER_MATCH CAPTURED course=course:01 p1=join.alpha p2=join.bravo outcome=1",
                "UR_LOCAL_TOURNAMENT FIXTURE_COMMITTED",
                "UR_LOCAL_TOURNAMENT RESULT_NOTICE screen=F9 text=CHAMPION: MIKE",
            )) + "\n", encoding="utf-8",
        )
        (work / "reopen.log").write_text(
            "\n".join((
                "UR_LOCAL_TOURNAMENT SESSION_RESTORED",
                "UR_LOCAL_TOURNAMENT HISTORY completed=1 unavailable=0",
                "UR_LOCAL_TOURNAMENT PANEL_OPENED page=overview",
                "UR_LOCAL_TOURNAMENT_PANEL_ACCEPTANCE DONE mode=reopen step=2 armed=0",
            )) + "\n", encoding="utf-8",
        )
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

    def test_harness_commit_and_smoke_run_reverified_against_job_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            work, candidate, p, q, f, report = self.make(Path(tmp))
            good = verify(
                work, candidate, "a" * 40, "b" * 64,
                expected_harness="c" * 40, expected_smoke_run="12345",
            )
            self.assertEqual(good["qa_harness_commit"], "c" * 40)
            for harness, run in (("d" * 40, "12345"), ("c" * 40, "98765"),
                                 ("main", "12345"), ("c" * 40, "bad-id")):
                with self.subTest(harness=harness, run=run):
                    with self.assertRaises(ValueError):
                        verify(
                            work, candidate, "a" * 40, "b" * 64,
                            expected_harness=harness, expected_smoke_run=run,
                        )

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

    def test_missing_or_failed_launch_history_is_rejected_even_with_valid_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            work, candidate, p, q, f, report = self.make(Path(tmp))
            create = work / "tournament.log"
            reopen = work / "reopen.log"
            create_original = create.read_text()
            reopen_original = reopen.read_text()
            create.write_text(create_original.replace(
                "UR_LOCAL_TOURNAMENT FIXTURE_COMMITTED",
                "UR_LOCAL_TOURNAMENT FIXTURE_COMMIT_REJECTED"))
            with self.assertRaisesRegex(ValueError, "lacks required event|failed event"):
                verify(work, candidate, "a" * 40, "b" * 64)
            create.write_text(create_original)
            reopen.write_text(reopen_original.replace(
                "UR_LOCAL_TOURNAMENT HISTORY completed=1 unavailable=0",
                "UR_LOCAL_TOURNAMENT HISTORY completed=0 unavailable=1"))
            with self.assertRaisesRegex(ValueError, "lacks required event"):
                verify(work, candidate, "a" * 40, "b" * 64)
            reopen.write_text(reopen_original + (
                "UR_LOCAL_TOURNAMENT SESSION_RESTORE_REJECTED\n"))
            with self.assertRaisesRegex(ValueError, "failed event"):
                verify(work, candidate, "a" * 40, "b" * 64)
            reopen.unlink()
            with self.assertRaisesRegex(ValueError, "missing, linked or oversized"):
                verify(work, candidate, "a" * 40, "b" * 64)

    def test_symlinked_work_root_rejected_before_resolve(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            work, candidate, p, q, f, report = self.make(root)
            link = root / "forged-work-root"
            try:
                link.symlink_to(work, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable")
            with self.assertRaisesRegex(ValueError, "work root is missing or linked"):
                verify(link, candidate, "a" * 40, "b" * 64)

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

    def test_orphan_sidecar_and_extra_fixture_receipt_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            work, candidate, p, q, f, report = self.make(Path(tmp))
            other = q.parent / "orphan.urmatch"
            other.write_bytes(b"unclaimed match sidecar")
            with self.assertRaisesRegex(ValueError, "exactly one"):
                verify(work, candidate, "a" * 40, "b" * 64)
            other.unlink()
            unexpected = f.parent / "fixture-1.urfixture"
            unexpected.write_bytes(b"unexpected credited fixture")
            with self.assertRaisesRegex(ValueError, "exactly one"):
                verify(work, candidate, "a" * 40, "b" * 64)

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
